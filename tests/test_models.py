"""Tests for models and enums."""

import json
from pathlib import Path
from typing import Any

import pytest

from keba_kecontact_p40 import LoadManagement, Wallbox, WallboxState
from keba_kecontact_p40.models import parse_state

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict[str, Any]:
    """Read a JSON fixture file by name."""
    return json.loads((FIXTURES / name).read_text())


def test_known_state() -> None:
    assert parse_state("CHARGING") is WallboxState.CHARGING


def test_unknown_state_is_none() -> None:
    assert parse_state("SOMETHING_NEW") is None


def test_missing_state_is_none() -> None:
    assert parse_state(None) is None


def test_wallbox_state_is_string() -> None:
    assert WallboxState.CHARGING == "CHARGING"
    assert f"{WallboxState.IDLE}" == "IDLE"


@pytest.mark.parametrize("member", list(WallboxState))
def test_every_state_round_trips(member: WallboxState) -> None:
    assert parse_state(member.value) is member


def test_wallbox_from_api() -> None:
    wb = Wallbox.from_api(_load("wallbox.json"))
    assert wb.serial_number == "21900042"
    assert wb.model == "P40 Pro"
    assert wb.firmware_version == "1.2.3"
    assert wb.state is WallboxState.CHARGING
    assert wb.vehicle_plugged is True
    assert wb.max_phases == 3
    assert wb.meter is not None
    assert wb.meter.energy_mwh == 1706672700
    assert wb.meter.power_mw == 11040000
    assert wb.meter.current_offered_ma == 16000
    assert wb.meter.temperature_centi_c == 2416
    assert len(wb.meter.lines) == 3
    assert wb.meter.lines[0].voltage_v == 230


def test_wallbox_without_meter() -> None:
    wb = Wallbox.from_api({"serialNumber": "S1", "state": "IDLE", "maxPhases": 1})
    assert wb.serial_number == "S1"
    assert wb.meter is None
    assert wb.max_phases == 1


def test_loadmanagement_from_api() -> None:
    lm = LoadManagement.from_api(_load("lmgmt.json"))
    assert lm.max_available_current_ma == 32000
    assert lm.min_default_current_ma == 6000
