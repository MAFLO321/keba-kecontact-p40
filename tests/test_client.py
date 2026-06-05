"""Tests for KebaP40Client."""

import aiohttp
import pytest
from aioresponses import aioresponses

from keba_kecontact_p40 import (
    KebaP40AuthError,
    KebaP40Client,
    KebaP40ConnectionError,
    KebaP40Error,
)

BASE = "https://host:8443"


@pytest.fixture
async def session() -> aiohttp.ClientSession:
    async with aiohttp.ClientSession() as sess:
        yield sess


async def test_login_stores_token(session: aiohttp.ClientSession) -> None:
    client = KebaP40Client("host", "pw", session=session)
    with aioresponses() as mock:
        mock.post(
            f"{BASE}/v2/jwt/login",
            payload={"accessToken": "tok", "refreshToken": "ref"},
        )
        await client.login()
    assert client._access_token == "tok"


async def test_login_bad_credentials_raises_auth(
    session: aiohttp.ClientSession,
) -> None:
    client = KebaP40Client("host", "pw", session=session)
    with aioresponses() as mock:
        mock.post(f"{BASE}/v2/jwt/login", status=401)
        with pytest.raises(KebaP40AuthError):
            await client.login()


async def test_connection_error_raised(session: aiohttp.ClientSession) -> None:
    client = KebaP40Client("host", "pw", session=session)
    with aioresponses() as mock:
        mock.post(f"{BASE}/v2/jwt/login", exception=aiohttp.ClientError())
        with pytest.raises(KebaP40ConnectionError):
            await client.login()


async def test_relogin_on_401(session: aiohttp.ClientSession) -> None:
    client = KebaP40Client("host", "pw", session=session)
    with aioresponses() as mock:
        mock.post(
            f"{BASE}/v2/jwt/login",
            payload={"accessToken": "tok1", "refreshToken": "r"},
        )
        await client.login()
        # First GET returns 401 -> client should re-login then retry.
        mock.get(f"{BASE}/v2/wallboxes", status=401)
        mock.post(
            f"{BASE}/v2/jwt/login",
            payload={"accessToken": "tok2", "refreshToken": "r"},
        )
        mock.get(f"{BASE}/v2/wallboxes", payload={"wallboxes": []})
        result = await client.get_wallboxes()
    assert result == []
    assert client._access_token == "tok2"


async def test_server_error_raises_keba_error(
    session: aiohttp.ClientSession,
) -> None:
    client = KebaP40Client("host", "pw", session=session)
    with aioresponses() as mock:
        mock.post(f"{BASE}/v2/jwt/login", payload={"accessToken": "t"})
        await client.login()
        mock.get(f"{BASE}/v2/wallboxes", status=500)
        with pytest.raises(KebaP40Error):
            await client.get_wallboxes()


async def test_get_wallbox(session: aiohttp.ClientSession) -> None:
    client = KebaP40Client("host", "pw", session=session)
    with aioresponses() as mock:
        mock.post(f"{BASE}/v2/jwt/login", payload={"accessToken": "t"})
        await client.login()
        mock.get(
            f"{BASE}/v2/wallboxes/S1",
            payload={"serialNumber": "S1", "state": "IDLE"},
        )
        wb = await client.get_wallbox("S1")
    assert wb.serial_number == "S1"


async def test_get_load_management(session: aiohttp.ClientSession) -> None:
    client = KebaP40Client("host", "pw", session=session)
    with aioresponses() as mock:
        mock.post(f"{BASE}/v2/jwt/login", payload={"accessToken": "t"})
        await client.login()
        mock.get(
            f"{BASE}/v2/configs/lmgmt",
            payload={"configs": [{"key": "max_available_current", "value": 32000}]},
        )
        lm = await client.get_load_management()
    assert lm.max_available_current_ma == 32000


async def test_login_missing_token_raises_auth(
    session: aiohttp.ClientSession,
) -> None:
    client = KebaP40Client("host", "pw", session=session)
    with aioresponses() as mock:
        mock.post(f"{BASE}/v2/jwt/login", payload={"unexpected": "shape"})
        with pytest.raises(KebaP40AuthError):
            await client.login()
