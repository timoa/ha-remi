"""Number platform for the UrbanHello Remi integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RemiDataUpdateCoordinator
from .entity import RemiEntity


@dataclass(frozen=True, kw_only=True)
class RemiNumberEntityDescription(NumberEntityDescription):
    """Describes a Remi number entity."""

    field: str = ""
    value_fn: Any = None


NUMBER_DESCRIPTIONS: tuple[RemiNumberEntityDescription, ...] = (
    RemiNumberEntityDescription(
        key="volume",
        translation_key="volume",
        name="Volume",
        icon="mdi:volume-high",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        field="volume",
        value_fn=lambda remi: remi.get("volume", 50),
    ),
    RemiNumberEntityDescription(
        key="luminosity",
        translation_key="luminosity",
        name="Screen Brightness",
        icon="mdi:brightness-6",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        field="luminosity",
        value_fn=lambda remi: remi.get("luminosity", 50),
    ),
    RemiNumberEntityDescription(
        key="noise_threshold",
        translation_key="noise_threshold",
        name="Noise Alert Threshold",
        icon="mdi:microphone",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        mode=NumberMode.SLIDER,
        field="noise_notification_threshold",
        value_fn=lambda remi: remi.get("noise_notification_threshold", 0),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Remi number entities from a config entry."""
    coordinator: RemiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        RemiNumberEntity(coordinator, description)
        for description in NUMBER_DESCRIPTIONS
    )


class RemiNumberEntity(RemiEntity, NumberEntity):
    """Representation of a Remi number entity."""

    entity_description: RemiNumberEntityDescription

    def __init__(
        self,
        coordinator: RemiDataUpdateCoordinator,
        description: RemiNumberEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self._remi_id}_{description.key}"

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self.entity_description.value_fn(self.coordinator.remi)

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value."""
        await self.coordinator.client.update_remi(
            {self.entity_description.field: int(value)}
        )
        await self.coordinator.async_request_refresh()
