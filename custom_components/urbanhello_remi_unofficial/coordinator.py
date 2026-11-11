"""DataUpdateCoordinator for the UrbanHello Remi integration."""
from __future__ import annotations

import logging
from time import monotonic
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RemiApiClient, RemiApiError
from .const import (
    DOMAIN,
    FIRMWARE_METADATA_INTERVAL_SECONDS,
    FIRMWARE_METADATA_RETRY_SECONDS,
    SCAN_INTERVAL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)


class RemiDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls the Remi API and stores all device data."""

    def __init__(self, hass: HomeAssistant, client: RemiApiClient) -> None:
        """Start the coordinator with an empty firmware metadata cache."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.client = client
        self.faces: list[dict[str, Any]] = []
        self.config_params: dict[str, Any] = {}
        self._config_checked_at: float | None = None
        self._config_retry_at: float | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest data from the Remi API."""
        try:
            remi, events = await _gather(
                self.client.get_remi(),
                self.client.get_events(),
            )
            if self._config_due():
                try:
                    await self._async_refresh_config()
                except RemiApiError:
                    # A firmware metadata failure must not discard valid device data.
                    _LOGGER.debug("Could not refresh REMI firmware metadata")
            return {"remi": remi, "events": events}
        except RemiApiError as err:
            raise UpdateFailed(f"Error communicating with Remi API: {err}") from err

    def _config_due(self) -> bool:
        """Return True when the firmware metadata should be read again."""
        now = monotonic()
        if self._config_retry_at is not None and now < self._config_retry_at:
            # A recent failure is cooling down; do not spend a poll on it.
            return False
        return (
            self._config_checked_at is None
            or now - self._config_checked_at >= FIRMWARE_METADATA_INTERVAL_SECONDS
        )

    async def async_setup(self) -> None:
        """Fetch static data (faces, config) once at setup."""
        try:
            self.faces = await self.client.get_faces()
            await self._async_refresh_config()
        except RemiApiError as err:
            _LOGGER.warning("Could not fetch static Remi data: %s", err)

    async def _async_refresh_config(self) -> None:
        """Refresh cached informational firmware configuration."""
        try:
            config = await self.client.get_config()
        except RemiApiError:
            # Remember the failure so the next polls wait instead of retrying.
            self._config_retry_at = monotonic() + FIRMWARE_METADATA_RETRY_SECONDS
            raise
        self.config_params = config.get("params", {})
        self._config_checked_at = monotonic()
        self._config_retry_at = None

    async def async_check_firmware(self) -> None:
        """Read firmware metadata and device state; never request installation."""
        try:
            await self._async_refresh_config()
        except RemiApiError as err:
            raise HomeAssistantError("Could not check REMI firmware metadata") from err
        await self.async_refresh()
        if not self.last_update_success:
            raise HomeAssistantError("Could not refresh REMI firmware status")

    @property
    def remi(self) -> dict[str, Any]:
        """Return the current Remi device state."""
        if self.data is None:
            return {}
        return self.data.get("remi", {})

    @property
    def events(self) -> list[dict[str, Any]]:
        """Return the current list of alarm events."""
        if self.data is None:
            return []
        return self.data.get("events", [])

    @property
    def latest_firmware_version(self) -> int | None:
        """Return the latest firmware version from server config."""
        return self.config_params.get("default_firmware_update_version")


async def _gather(*coros):
    """Run multiple coroutines and return results as a list."""
    import asyncio
    return await asyncio.gather(*coros)
