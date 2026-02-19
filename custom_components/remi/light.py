"""Light platform for the UrbanHello Remi integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RemiDataUpdateCoordinator
from .entity import RemiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Remi light entities from a config entry."""
    coordinator: RemiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            RemiNightLightEntity(coordinator),
            RemiBackgroundLightEntity(coordinator),
        ]
    )


class RemiRgbLightEntity(RemiEntity, LightEntity):
    """Base class for Remi RGB light entities."""

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    _field: str = ""

    def __init__(self, coordinator: RemiDataUpdateCoordinator) -> None:
        super().__init__(coordinator)

    def _get_rgb(self) -> list[int]:
        return self.coordinator.remi.get(self._field, [255, 255, 255])

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the current RGB color."""
        rgb = self._get_rgb()
        if isinstance(rgb, list) and len(rgb) == 3:
            return (rgb[0], rgb[1], rgb[2])
        return None

    @property
    def is_on(self) -> bool:
        """Return true if the light is on (any non-zero channel)."""
        rgb = self._get_rgb()
        return any(v > 0 for v in rgb)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light, optionally setting RGB color."""
        rgb = kwargs.get(ATTR_RGB_COLOR)
        if rgb is None:
            current = self._get_rgb()
            if all(v == 0 for v in current):
                rgb = (255, 255, 255)
            else:
                rgb = tuple(current)
        await self.coordinator.client.update_remi(
            {self._field: list(rgb)}
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light by setting RGB to [0, 0, 0]."""
        await self.coordinator.client.update_remi(
            {self._field: [0, 0, 0]}
        )
        await self.coordinator.async_request_refresh()


class RemiNightLightEntity(RemiRgbLightEntity):
    """Night light entity for the Remi."""

    _attr_name = "Night Light"
    _attr_icon = "mdi:weather-night"
    _field = "lightnight"

    def __init__(self, coordinator: RemiDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._remi_id}_night_light"


class RemiBackgroundLightEntity(RemiRgbLightEntity):
    """Background color light entity for the Remi."""

    _attr_name = "Background Color"
    _attr_icon = "mdi:palette"
    _field = "background_color"

    def __init__(self, coordinator: RemiDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._remi_id}_background_color"
