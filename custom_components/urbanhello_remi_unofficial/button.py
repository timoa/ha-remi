"""Read-only firmware check for REMI; installation is managed by UrbanHello."""
from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory

from .const import DOMAIN
from .entity import RemiEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Add a manual refresh button for this device."""
    async_add_entities([RemiCheckFirmwareButton(hass.data[DOMAIN][entry.entry_id])])


class RemiCheckFirmwareButton(RemiEntity, ButtonEntity):
    """Refresh the device firmware target and the informational server default."""

    _attr_translation_key = "check_firmware"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:update"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._remi_id}_check_firmware"

    async def async_press(self) -> None:
        await self.coordinator.async_check_firmware()
