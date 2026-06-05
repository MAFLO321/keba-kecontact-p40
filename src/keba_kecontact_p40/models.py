"""Typed models for the KEBA P40 REST API."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class WallboxState(StrEnum):
    """Operational state of the wallbox (v2Wbstate)."""

    CHARGING = "CHARGING"
    IDLE = "IDLE"
    READY_FOR_CHARGING = "READY_FOR_CHARGING"
    RECOVER_FROM_ERROR = "RECOVER_FROM_ERROR"
    INSTALLER_MODE = "INSTALLER_MODE"
    SUSPENDED = "SUSPENDED"
    TOKEN_PROGRAMMING_MODE = "TOKEN_PROGRAMMING_MODE"
    UNRECOVERABLE_ERROR = "UNRECOVERABLE_ERROR"
    UNAVAILABLE = "UNAVAILABLE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"


def parse_state(value: str | None) -> WallboxState | None:
    """Return the WallboxState for value.

    Returns None if value is None or not a recognised state string.
    """
    if value is None:
        return None
    try:
        return WallboxState(value)
    except ValueError:
        return None


@dataclass(frozen=True)
class MeterLine:
    """Per-phase line measurement. current is in mA, voltage in V."""

    phase: str | None
    current_ma: int | None
    voltage_v: int | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> MeterLine:
        return cls(
            phase=data.get("socketPhase"),
            current_ma=data.get("current"),
            voltage_v=data.get("voltage"),
        )


@dataclass(frozen=True)
class Meter:
    """Meter readings. Raw API units (mWh, mW, mA, 0.01 degC, cosphi*1000)."""

    energy_mwh: int | None
    power_mw: int | None
    power_factor: int | None
    phases_supported: int | None
    current_offered_ma: int | None
    temperature_centi_c: int | None
    lines: tuple[MeterLine, ...]

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Meter:
        return cls(
            energy_mwh=data.get("meterValue"),
            power_mw=data.get("totalActivePower"),
            power_factor=data.get("totalPowerFactor"),
            phases_supported=data.get("phasesSupported"),
            current_offered_ma=data.get("currentOffered"),
            temperature_centi_c=data.get("temperature"),
            lines=tuple(MeterLine.from_api(line) for line in data.get("lines", [])),
        )


@dataclass(frozen=True)
class Wallbox:
    """A single wallbox (v2Wallbox)."""

    serial_number: str
    number: int | None
    model: str | None
    alias: str | None
    firmware_version: str | None
    firmware_version_metering: str | None
    firmware_version_safety: str | None
    ip_address: str | None
    state: WallboxState | None
    vehicle_plugged: bool | None
    session_active: bool | None
    max_current_ma: int | None
    max_phases: int | None
    phase_used: str | None
    permanently_locked: bool | None
    reserved: bool | None
    authorization_enabled: bool | None
    error_code: str | None
    meter: Meter | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Wallbox:
        meter = data.get("meter")
        error_code = data.get("errorCode")
        return cls(
            serial_number=str(data["serialNumber"]),
            number=data.get("number"),
            model=data.get("model"),
            alias=data.get("alias"),
            firmware_version=data.get("firmwareVersion"),
            firmware_version_metering=data.get("firmwareVersionMetering"),
            firmware_version_safety=data.get("firmwareVersionSafety"),
            ip_address=data.get("ipAddress"),
            state=parse_state(data.get("state")),
            vehicle_plugged=data.get("vehiclePlugged"),
            session_active=data.get("sessionActive"),
            max_current_ma=data.get("maxCurrent"),
            max_phases=data.get("maxPhases"),
            phase_used=data.get("phaseUsed"),
            permanently_locked=data.get("permanentlyLocked"),
            reserved=data.get("reserved"),
            authorization_enabled=data.get("authorizationEnabled"),
            error_code=None if error_code is None else str(error_code),
            meter=None if meter is None else Meter.from_api(meter),
        )


@dataclass(frozen=True)
class LoadManagement:
    """Load-management bounds parsed from /v2/configs/lmgmt. Currents in mA."""

    max_available_current_ma: int | None
    min_default_current_ma: int | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> LoadManagement:
        pairs = {item["key"]: item.get("value") for item in data.get("configs", [])}
        return cls(
            max_available_current_ma=pairs.get("max_available_current"),
            min_default_current_ma=pairs.get("min_default_current"),
        )
