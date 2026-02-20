"""API client for the UrbanHello Remi integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import (
    API_APP_BUILD_VERSION,
    API_APP_DISPLAY_VERSION,
    API_APP_ID,
    API_BASE_URL,
    API_CLIENT_VERSION,
    API_OS_VERSION,
    API_USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)


class RemiAuthError(Exception):
    """Raised when authentication fails."""


class RemiApiError(Exception):
    """Raised when an API call fails."""


class RemiApiClient:
    """Client for the UrbanHello Remi Parse Server API."""

    def __init__(self, username: str, password: str, session: aiohttp.ClientSession, installation_id: str = "") -> None:
        self._username = username
        self._password = password
        self._session = session
        self._installation_id = installation_id
        self._session_token: str | None = None
        self._remi_id: str | None = None

    @property
    def remi_id(self) -> str | None:
        return self._remi_id

    @property
    def session_token(self) -> str | None:
        return self._session_token

    def _base_headers(self, authenticated: bool = True) -> dict[str, str]:
        headers = {
            "X-Parse-Client-Version": API_CLIENT_VERSION,
            "X-Parse-Application-Id": API_APP_ID,
            "X-Parse-Installation-Id": self._installation_id,
            "X-Parse-OS-Version": API_OS_VERSION,
            "X-Parse-App-Build-Version": API_APP_BUILD_VERSION,
            "X-Parse-App-Display-Version": API_APP_DISPLAY_VERSION,
            "Accept": "*/*",
            "Accept-Language": "en-gb",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": API_USER_AGENT,
            "Connection": "keep-alive",
        }
        if authenticated and self._session_token:
            headers["X-Parse-Session-Token"] = self._session_token
        return headers

    def set_remi_id(self, remi_id: str) -> None:
        """Set the active Remi device ID."""
        self._remi_id = remi_id

    async def login(self) -> tuple[str, str, list[str]]:
        """Authenticate and return (session_token, current_remi_id, all_remi_ids)."""
        url = f"{API_BASE_URL}/parse/login"
        payload = {
            "_method": "GET",
            "username": self._username,
            "password": self._password,
        }
        async with self._session.post(
            url, json=payload, headers=self._base_headers(authenticated=False)
        ) as resp:
            if resp.status == 401:
                raise RemiAuthError("Invalid username or password")
            if resp.status != 200:
                raise RemiApiError(f"Login failed with status {resp.status}")
            data = await resp.json()

        session_token = data.get("sessionToken")
        current_remi = data.get("currentRemi", {})
        current_remi_id = current_remi.get("objectId") if isinstance(current_remi, dict) else None
        all_remi_ids: list[str] = data.get("remis", [])

        if not session_token or not current_remi_id:
            raise RemiAuthError("Login response missing sessionToken or currentRemi")

        if not all_remi_ids:
            all_remi_ids = [current_remi_id]

        self._session_token = session_token
        self._remi_id = current_remi_id
        return session_token, current_remi_id, all_remi_ids

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        retry_auth: bool = True,
    ) -> Any:
        """Make an authenticated API request, re-logging in on 401."""
        url = f"{API_BASE_URL}{path}"
        async with self._session.request(
            method, url, json=payload, headers=self._base_headers()
        ) as resp:
            if resp.status == 401 and retry_auth:
                _LOGGER.debug("Session expired, re-authenticating")
                await self.login()
                return await self._request(method, path, payload, retry_auth=False)
            if resp.status not in (200, 201):
                text = await resp.text()
                raise RemiApiError(f"API error {resp.status} on {path}: {text}")
            return await resp.json()

    async def get_remi(self) -> dict[str, Any]:
        """Fetch the Remi device state."""
        data = await self._request(
            "POST",
            "/parse/classes/Remi",
            {
                "limit": "1",
                "where": {"objectId": self._remi_id},
                "_method": "GET",
            },
        )
        results = data.get("results", [])
        if not results:
            raise RemiApiError("No Remi device found")
        return results[0]

    async def update_remi(self, fields: dict[str, Any]) -> dict[str, Any]:
        """Update Remi device fields via PUT."""
        return await self._request(
            "PUT",
            f"/parse/classes/Remi/{self._remi_id}",
            fields,
        )

    async def get_faces(self) -> list[dict[str, Any]]:
        """Fetch all available clock faces."""
        data = await self._request(
            "POST",
            "/parse/classes/Face",
            {"order": "index", "_method": "GET"},
        )
        return data.get("results", [])

    async def get_config(self) -> dict[str, Any]:
        """Fetch server config (used for firmware update version)."""
        return await self._request("GET", "/parse/config")

    async def get_events(self) -> list[dict[str, Any]]:
        """Fetch all alarms/events for this Remi."""
        data = await self._request(
            "POST",
            "/parse/classes/Event",
            {
                "where": {
                    "remi": {
                        "__type": "Pointer",
                        "className": "Remi",
                        "objectId": self._remi_id,
                    }
                },
                "_method": "GET",
            },
        )
        return data.get("results", [])

    async def create_event(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new alarm event."""
        payload = {
            **event_data,
            "remi": {
                "__type": "Pointer",
                "className": "Remi",
                "objectId": self._remi_id,
            },
        }
        return await self._request("POST", "/parse/classes/Event", payload)

    async def update_event(self, event_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        """Update an existing alarm event."""
        return await self._request("PUT", f"/parse/classes/Event/{event_id}", fields)

    async def delete_event(self, event_id: str) -> None:
        """Delete an alarm event."""
        await self._request("DELETE", f"/parse/classes/Event/{event_id}")
