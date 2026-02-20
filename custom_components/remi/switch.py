"""Switch platform for the UrbanHello Remi integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DAYS_OF_WEEK, DOMAIN, FACE_OBJECT_ID_TO_DEFINE, FACE_DEFINE_TO_NAME
from .coordinator import RemiDataUpdateCoordinator
from .entity import RemiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Remi alarm switch entities from a config entry."""
    coordinator: RemiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    known_event_ids: set[str] = set()

    def _add_new_alarms() -> None:
        """Add switch entities for any events not yet tracked."""
        new_entities = []
        for event in coordinator.events:
            event_id = event.get("objectId")
            if event_id and event_id not in known_event_ids:
                known_event_ids.add(event_id)
                new_entities.append(RemiAlarmSwitchEntity(coordinator, event))
        if new_entities:
            async_add_entities(new_entities)

        _remove_stale_alarms()

    def _remove_stale_alarms() -> None:
        """Remove switch entities for events that no longer exist."""
        current_ids = {e.get("objectId") for e in coordinator.events if e.get("objectId")}
        stale_ids = known_event_ids - current_ids
        if not stale_ids:
            return

        ent_registry = er.async_get(hass)
        remi_id = coordinator.remi.get("objectId", "")
        for event_id in stale_ids:
            unique_id = f"{remi_id}_alarm_{event_id}"
            entity_id = ent_registry.async_get_entity_id("switch", DOMAIN, unique_id)
            if entity_id:
                ent_registry.async_remove(entity_id)
            known_event_ids.discard(event_id)

    _add_new_alarms()
    entry.async_on_unload(coordinator.async_add_listener(lambda: _add_new_alarms()))


class RemiAlarmSwitchEntity(RemiEntity, SwitchEntity):
    """Switch entity representing a single Remi alarm (Event)."""

    _attr_icon = "mdi:alarm"

    def __init__(
        self,
        coordinator: RemiDataUpdateCoordinator,
        event: dict[str, Any],
    ) -> None:
        super().__init__(coordinator)
        self._event_id: str = event["objectId"]
        self._attr_unique_id = f"{self._remi_id}_alarm_{self._event_id}"
        self._attr_name = event.get("name") or f"Alarm {self._event_id}"

    def _get_event(self) -> dict[str, Any]:
        """Return the current event data from the coordinator."""
        for event in self.coordinator.events:
            if event.get("objectId") == self._event_id:
                return event
        return {}

    @property
    def is_on(self) -> bool:
        """Return true if the alarm is enabled."""
        return self._get_event().get("enabled", False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return alarm details as state attributes."""
        event = self._get_event()
        attrs: dict[str, Any] = {}

        event_time = event.get("event_time")
        if isinstance(event_time, list) and len(event_time) >= 2:
            attrs["time"] = f"{event_time[0]:02d}:{event_time[1]:02d}"

        recurrence = event.get("recurrence")
        if isinstance(recurrence, list):
            attrs["recurrence"] = [
                DAYS_OF_WEEK[i]
                for i, active in enumerate(recurrence)
                if active and i < len(DAYS_OF_WEEK)
            ]

        for field in ("brightness", "volume", "length_min"):
            value = event.get(field)
            if value is not None:
                attrs[field] = value

        face_ptr = event.get("face") or {}
        if isinstance(face_ptr, dict):
            face_object_id = face_ptr.get("objectId", "")
            define = FACE_OBJECT_ID_TO_DEFINE.get(face_object_id, "")
            face_name = FACE_DEFINE_TO_NAME.get(define)
            if face_name:
                attrs["face"] = face_name

        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the alarm."""
        await self.coordinator.client.update_event(self._event_id, {"enabled": True})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the alarm."""
        await self.coordinator.client.update_event(self._event_id, {"enabled": False})
        await self.coordinator.async_request_refresh()
