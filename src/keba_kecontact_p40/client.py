"""Async REST client for the KEBA P40 / P40 Pro wallbox."""

from __future__ import annotations

from typing import Any

import aiohttp

from .exceptions import KebaP40AuthError, KebaP40ConnectionError, KebaP40Error
from .models import LoadManagement, Wallbox

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

    async def get_load_management(self) -> LoadManagement:
        """Return load-management current bounds."""
        data = await self._request_json("GET", "/v2/configs/lmgmt")
        return LoadManagement.from_api(data)
