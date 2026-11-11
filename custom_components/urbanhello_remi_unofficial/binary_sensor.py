"""Binary sensor platform for the UrbanHello Remi integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RemiDataUpdateCoordinator
from .entity import RemiEntity
from .firmware import firmware_update_available, firmware_update_requested, firmware_version


@dataclass(frozen=True, kw_only=True)
class RemiBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Remi binary sensor entity."""

    value_fn: Any = None


BINARY_SENSOR_DESCRIPTIONS: tuple[RemiBinarySensorEntityDescription, ...] = (
    RemiBinarySensorEntityDescription(
        key="online",
        translation_key="online",
        name="Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda remi: remi.get("online", False),
    ),
    RemiBinarySensorEntityDescription(
        key="alive",
        translation_key="alive",
        name="Alive",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_registry_enabled_default=False,
        value_fn=lambda remi: remi.get("alive", False),
    ),
    RemiBinarySensorEntityDescription(
        key="firmware_update",
        translation_key="firmware_update",
        name="Firmware Update Available",
        device_class=BinarySensorDeviceClass.UPDATE,
        value_fn=firmware_update_available,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Remi binary sensors from a config entry."""
    coordinator: RemiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        RemiBinarySensorEntity(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class RemiBinarySensorEntity(RemiEntity, BinarySensorEntity):
    """Representation of a Remi binary sensor."""

    entity_description: RemiBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: RemiDataUpdateCoordinator,
        description: RemiBinarySensorEntityDescription,
    ) -> None:
        """Bind the entity to its description and unique id."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self._remi_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        remi = self.coordinator.remi
        if self.entity_description.key == "firmware_update":
            return self.entity_description.value_fn(
                remi, self.coordinator.latest_firmware_version
            )
        return self.entity_description.value_fn(remi)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Explain the device-specific firmware status without exposing account data."""
        if self.entity_description.key != "firmware_update":
            return None
        remi = self.coordinator.remi
        return {
            "installed_version": firmware_version(remi.get("current_firmware_version")),
            "target_version": firmware_version(remi.get("update_firmware_version")),
            "server_default_version": firmware_version(self.coordinator.latest_firmware_version),
            "update_requested": firmware_update_requested(remi),
            "update_method": "automatic_wifi",
        }
