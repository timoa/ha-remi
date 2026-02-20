"""Sensor platform for the UrbanHello Remi integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, FACE_OBJECT_ID_TO_DEFINE, FACE_DEFINE_TO_NAME
from .coordinator import RemiDataUpdateCoordinator
from .entity import RemiEntity


@dataclass(frozen=True, kw_only=True)
class RemiSensorEntityDescription(SensorEntityDescription):
    """Describes a Remi sensor entity."""

    value_fn: Any = None


SENSOR_DESCRIPTIONS: tuple[RemiSensorEntityDescription, ...] = (
    RemiSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda remi: (remi.get("temp", 0) - 115) / 2,
    ),
    RemiSensorEntityDescription(
        key="luminosity",
        translation_key="luminosity",
        name="Luminosity",
        device_class=SensorDeviceClass.ILLUMINANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="lx",
        value_fn=lambda remi: remi.get("luminosity"),
    ),
    RemiSensorEntityDescription(
        key="rssi",
        translation_key="rssi",
        name="WiFi Signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_registry_enabled_default=False,
        value_fn=lambda remi: remi.get("rssi"),
    ),
    RemiSensorEntityDescription(
        key="firmware_version",
        translation_key="firmware_version",
        name="Firmware Version",
        icon="mdi:chip",
        value_fn=lambda remi: remi.get("current_firmware_version"),
    ),
    RemiSensorEntityDescription(
        key="ip_address",
        translation_key="ip_address",
        name="IP Address",
        icon="mdi:ip-network",
        entity_registry_enabled_default=False,
        value_fn=lambda remi: remi.get("ipv4Address"),
    ),
    RemiSensorEntityDescription(
        key="current_face",
        translation_key="current_face",
        name="Current Face",
        icon="mdi:emoticon-outline",
        value_fn=lambda remi: FACE_DEFINE_TO_NAME.get(
            FACE_OBJECT_ID_TO_DEFINE.get(
                (remi.get("face") or {}).get("objectId", ""), ""
            ),
            "Unknown",
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Remi sensors from a config entry."""
    coordinator: RemiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        RemiSensorEntity(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )


class RemiSensorEntity(RemiEntity, SensorEntity):
    """Representation of a Remi sensor."""

    entity_description: RemiSensorEntityDescription

    def __init__(
        self,
        coordinator: RemiDataUpdateCoordinator,
        description: RemiSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self._remi_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.remi)
