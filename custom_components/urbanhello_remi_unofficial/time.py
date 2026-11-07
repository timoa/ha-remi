"""Editable alarm times in the REMI device's local time zone."""
from __future__ import annotations

from datetime import time
from typing import Any

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RemiDataUpdateCoordinator
from .entity import RemiEntity


def alarm_time(event: dict[str, Any]) -> time | None:
    """Decode the clock time without inventing a date or applying a UTC offset."""
    value = event.get("event_time")
    if not isinstance(value, list) or len(value) != 2:
        return None
    if not all(type(part) is int for part in value):
        return None
    try:
        return time(*value)
    except ValueError:
        return None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Keep alarm time entities synchronized with the app's alarm list."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    known: set[str] = set()

    @callback
    def synchronize() -> None:
        if not coordinator.last_update_success:
            return
        current = {event["objectId"]: event for event in coordinator.events
                   if isinstance(event.get("objectId"), str) and event["objectId"]}
        new = [RemiAlarmTime(coordinator, event) for key, event in current.items()
               if key not in known]
        if new:
            async_add_entities(new)
        registry = er.async_get(hass)
        for key in known - current.keys():
            unique_id = f"{coordinator.client.remi_id}_alarm_{key}_time"
            entity_id = registry.async_get_entity_id("time", DOMAIN, unique_id)
            if entity_id:
                registry.async_remove(entity_id)
        known.clear()
        known.update(current)

    synchronize()
    entry.async_on_unload(coordinator.async_add_listener(synchronize))


class RemiAlarmTime(RemiEntity, TimeEntity):
    """Change the hour/minute of one existing alarm without changing its days."""

    _attr_icon = "mdi:alarm"
    _attr_translation_key = "alarm_time"

    def __init__(self, coordinator: RemiDataUpdateCoordinator, event: dict) -> None:
        super().__init__(coordinator)
        self._event_id = event["objectId"]
        self._attr_unique_id = f"{self._remi_id}_alarm_{self._event_id}_time"
        self._attr_translation_placeholders = {
            "name": event.get("name") or self._event_id
        }

    def _event(self) -> dict[str, Any]:
        return next((event for event in self.coordinator.events
                     if event.get("objectId") == self._event_id), {})

    @property
    def available(self) -> bool:
        return super().available and bool(self._event())

    @property
    def native_value(self) -> time | None:
        return alarm_time(self._event())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"event_id": self._event_id}

    async def async_set_value(self, value: time) -> None:
        if not self._event():
            raise ServiceValidationError("This REMI alarm no longer exists")
        if value.second or value.microsecond or value.tzinfo is not None:
            raise ServiceValidationError("Use hours and minutes in the REMI time zone")
        await self.coordinator.client.update_event(
            self._event_id, {"event_time": [value.hour, value.minute]}
        )
        await self.coordinator.async_request_refresh()
