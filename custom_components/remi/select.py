"""Select platform for the UrbanHello Remi integration."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    FACE_DEFINE_TO_NAME,
    FACE_DEFINE_TO_OBJECT_ID,
    FACE_OBJECT_ID_TO_DEFINE,
    MUSIC_MODE_OPTIONS,
)
from .coordinator import RemiDataUpdateCoordinator
from .entity import RemiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Remi select entities from a config entry."""
    coordinator: RemiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            RemiFaceSelectEntity(coordinator),
            RemiClockFormatSelectEntity(coordinator),
            RemiMusicModeSelectEntity(coordinator),
        ]
    )


class RemiFaceSelectEntity(RemiEntity, SelectEntity):
    """Select entity for the Remi clock face."""

    _attr_name = "Clock Face"
    _attr_icon = "mdi:emoticon-outline"
    _attr_options = list(FACE_DEFINE_TO_NAME.values())

    def __init__(self, coordinator: RemiDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._remi_id}_face"

    @property
    def current_option(self) -> str | None:
        """Return the current face name."""
        face_ptr = self.coordinator.remi.get("face") or {}
        object_id = face_ptr.get("objectId", "")
        define = FACE_OBJECT_ID_TO_DEFINE.get(object_id, "")
        return FACE_DEFINE_TO_NAME.get(define)

    async def async_select_option(self, option: str) -> None:
        """Change the clock face."""
        define = next(
            (k for k, v in FACE_DEFINE_TO_NAME.items() if v == option), None
        )
        if define is None:
            return
        object_id = FACE_DEFINE_TO_OBJECT_ID.get(define)
        if object_id is None:
            return
        await self.coordinator.client.update_remi(
            {
                "face": {
                    "__type": "Pointer",
                    "className": "Face",
                    "objectId": object_id,
                }
            }
        )
        await self.coordinator.async_request_refresh()


class RemiClockFormatSelectEntity(RemiEntity, SelectEntity):
    """Select entity for the Remi clock format (12h / 24h)."""

    _attr_name = "Clock Format"
    _attr_icon = "mdi:clock-outline"
    _attr_options = ["12h", "24h"]

    def __init__(self, coordinator: RemiDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._remi_id}_clock_format"

    @property
    def current_option(self) -> str | None:
        """Return the current clock format."""
        return "24h" if self.coordinator.remi.get("hourFormat24", True) else "12h"

    async def async_select_option(self, option: str) -> None:
        """Change the clock format."""
        await self.coordinator.client.update_remi(
            {"hourFormat24": option == "24h"}
        )
        await self.coordinator.async_request_refresh()


class RemiMusicModeSelectEntity(RemiEntity, SelectEntity):
    """Select entity for the Remi music mode."""

    _attr_name = "Music Mode"
    _attr_icon = "mdi:music"
    _attr_options = list(MUSIC_MODE_OPTIONS.values())

    def __init__(self, coordinator: RemiDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._remi_id}_music_mode"

    @property
    def current_option(self) -> str | None:
        """Return the current music mode label."""
        mode = self.coordinator.remi.get("musicMode", 0)
        return MUSIC_MODE_OPTIONS.get(mode)

    async def async_select_option(self, option: str) -> None:
        """Change the music mode."""
        mode = next(
            (k for k, v in MUSIC_MODE_OPTIONS.items() if v == option), 0
        )
        await self.coordinator.client.update_remi({"musicMode": mode})
        await self.coordinator.async_request_refresh()
