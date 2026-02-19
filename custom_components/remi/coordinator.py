"""DataUpdateCoordinator for the UrbanHello Remi integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RemiApiClient, RemiApiError
from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class RemiDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls the Remi API and stores all device data."""

    def __init__(self, hass: HomeAssistant, client: RemiApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.client = client
        self.faces: list[dict[str, Any]] = []
        self.config_params: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest data from the Remi API."""
        try:
            remi, events = await _gather(
                self.client.get_remi(),
                self.client.get_events(),
            )
            return {"remi": remi, "events": events}
        except RemiApiError as err:
            raise UpdateFailed(f"Error communicating with Remi API: {err}") from err

    async def async_setup(self) -> None:
        """Fetch static data (faces, config) once at setup."""
        try:
            self.faces = await self.client.get_faces()
            config = await self.client.get_config()
            self.config_params = config.get("params", {})
        except RemiApiError as err:
            _LOGGER.warning("Could not fetch static Remi data: %s", err)

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
