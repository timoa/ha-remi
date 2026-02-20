"""Base entity for the UrbanHello Remi integration."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RemiDataUpdateCoordinator


class RemiEntity(CoordinatorEntity[RemiDataUpdateCoordinator]):
    """Base class for all Remi entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: RemiDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        remi = coordinator.remi
        self._remi_id = remi.get("objectId", "")

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this Remi."""
        remi = self.coordinator.remi
        return DeviceInfo(
            identifiers={(DOMAIN, self._remi_id)},
            name=remi.get("name", "Remi"),
            manufacturer="UrbanHello",
            model="Remi",
            sw_version=str(remi.get("current_firmware_version", "")),
            serial_number=remi.get("uniqueID"),
            configuration_url=f"http://{remi.get('ipv4Address', '')}",
        )
