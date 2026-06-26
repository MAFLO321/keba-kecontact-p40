"""Async REST client for the KEBA P40 / P40 Pro wallbox."""

from __future__ import annotations

from typing import Any

import aiohttp

from .exceptions import KebaP40AuthError, KebaP40ConnectionError, KebaP40Error
from .models import parse_state, LoadManagement, Wallbox, WallboxState

_TIMEOUT = aiohttp.ClientTimeout(total=10)


class KebaP40Client:
    """Client for the local KEBA P40 REST API (v3.0.3)."""

    def __init__(
        self,
        host: str,
        password: str,
        *,
        session: aiohttp.ClientSession,
        username: str = "admin",
        port: int = 8443,
    ) -> None:
        """Initialize the client. The session controls TLS verification."""
        self._session = session
        self._username = username
        self._password = password
        self._base_url = f"https://{host}:{port}"
        self._access_token: str | None = None

    async def login(self) -> None:
        """Authenticate and store the access token."""
        data = await self._request_json(
            "POST",
            "/v2/jwt/login",
            json={"username": self._username, "password": self._password},
            authenticated=False,
        )
        token = data.get("accessToken")
        if not isinstance(token, str):
            raise KebaP40AuthError("Login response did not contain an access token")
        self._access_token = token

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        authenticated: bool = True,
        _retry: bool = True,
    ) -> Any:
        """Perform a request, re-logging in once on a 401."""
        headers: dict[str, str] = {}
        if authenticated and self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        try:
            async with self._session.request(
                method,
                f"{self._base_url}{path}",
                json=json,
                params=params,
                headers=headers,
                timeout=_TIMEOUT,
            ) as resp:
                if resp.status == 401:
                    if authenticated and _retry:
                        await self.login()
                        return await self._request(
                            method,
                            path,
                            json=json,
                            params=params,
                            authenticated=authenticated,
                            _retry=False,
                        )
                    raise KebaP40AuthError(f"Authentication failed for {path}")
                if resp.status >= 400:
                    raise KebaP40Error(f"{method} {path} failed: HTTP {resp.status}")
                if resp.content_type == "application/json":
                    return await resp.json()
                return None
        except (aiohttp.ClientError, TimeoutError) as err:
            raise KebaP40ConnectionError(f"Error talking to {path}: {err}") from err

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        authenticated: bool = True,
    ) -> dict[str, Any]:
        """Like _request, but require a JSON object response."""
        data = await self._request(
            method,
            path,
            json=json,
            params=params,
            authenticated=authenticated,
        )
        if not isinstance(data, dict):
            raise KebaP40Error(f"Expected a JSON object from {path}")
        return data

    async def get_wallboxes(self) -> list[Wallbox]:
        """Return all wallboxes reported by the device."""
        data = await self._request_json("GET", "/v2/wallboxes")
        return [Wallbox.from_api(item) for item in data.get("wallboxes", [])]

    async def get_wallbox(self, serial: str) -> Wallbox:
        """Return a single wallbox by serial number."""
        data = await self._request_json("GET", f"/v2/wallboxes/{serial}")
        return Wallbox.from_api(data)

    async def get_wallbox_state(self, serial: str) -> WallboxState | None:
        """Return wallbox state by serial number."""
        data = await self._request_json("GET", f"/v2/wallboxes/{serial}/state")
        return parse_state(data.get("state"))

    async def get_load_management(self) -> LoadManagement:
        """Return load-management current bounds."""
        data = await self._request_json("GET", "/v2/configs/lmgmt")
        return LoadManagement.from_api(data)

    _ALL_DAYS = (
        "MONDAY",
        "TUESDAY",
        "WEDNESDAY",
        "THURSDAY",
        "FRIDAY",
        "SATURDAY",
        "SUNDAY",
    )

    async def start_charging(self, serial: str) -> None:
        """Start a charging session."""
        await self._request("POST", f"/v2/wallboxes/{serial}/start-charging")

    async def start_charging_sync(self, serial: str, timeout: float | int | None = None) -> WallboxState | None:
        """Start a charging session and return wallbox status."""
        data = await self._request_json(
            "POST",
            f"/v2/wallboxes/{serial}/start-charging-sync",
            params={"timeout": timeout} if timeout is not None else None,
        )
        return parse_state(data.get("state"))

    async def stop_charging(self, serial: str) -> None:
        """Stop the active charging session."""
        await self._request("POST", f"/v2/wallboxes/{serial}/stop-charging")

    async def stop_charging_sync(self, serial: str, timeout: float | int | None = None) -> WallboxState | None:
        """Stop the active charging session and return wallbox status."""
        data = await self._request_json(
            "POST",
            f"/v2/wallboxes/{serial}/stop-charging-sync",
            params={"timeout": timeout} if timeout is not None else None,
        )
        return parse_state(data.get("state"))

    async def set_phases(self, serial: str, number_of_phases: int) -> None:
        """Switch between single- (1) and three-phase (3) charging."""
        if number_of_phases not in (1, 3):
            raise ValueError(f"number_of_phases must be 1 or 3, got {number_of_phases}")
        await self._request(
            "POST",
            f"/v2/wallboxes/{serial}/phase-toggle",
            params={"numberOfPhases": number_of_phases},
        )

    async def set_availability(self, serial: str, available: bool) -> None:
        """Mark the wallbox available or unavailable."""
        await self._request(
            "POST",
            f"/v2/wallboxes/{serial}/change-availability",
            json={"available": available},
        )

    async def lock(self, serial: str) -> None:
        """Activate the permanently-locked socket feature."""
        await self._request("POST", f"/v2/wallboxes/{serial}/permanently-lock")

    async def unlock(self, serial: str) -> None:
        """Unlock the socket / release the connector."""
        await self._request("POST", f"/v2/wallboxes/{serial}/unlock")

    async def set_max_current(self, milliamps: int) -> None:
        """Set the chargepoint max-current limit (OCPP ChargePointMaxProfile)."""
        await self._request(
            "POST",
            "/v2/profiles/chargepointmaxprofilezero",
            json={
                "profileItems": [
                    {
                        "maxCurrentOffered": milliamps,
                        "startTime": "00:00:00",
                        "stopTime": "24:00:00",
                        "daysOfWeek": list(self._ALL_DAYS),
                    }
                ]
            },
        )
