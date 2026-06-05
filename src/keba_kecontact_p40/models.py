"""Typed models for the KEBA P40 REST API."""

from __future__ import annotations

from enum import StrEnum


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
