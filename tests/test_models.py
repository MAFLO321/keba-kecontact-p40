"""Tests for models and enums."""

import pytest

from keba_kecontact_p40 import WallboxState
from keba_kecontact_p40.models import parse_state


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
