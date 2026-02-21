"""The UrbanHello Remi integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .api import RemiApiClient
from .const import CONF_INSTALLATION_ID, CONF_REMI_ID, CONF_SESSION_TOKEN, DOMAIN
from .coordinator import RemiDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

SERVICE_CREATE_ALARM = "create_alarm"
SERVICE_UPDATE_ALARM = "update_alarm"
SERVICE_DELETE_ALARM = "delete_alarm"

SERVICE_CREATE_ALARM_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Required("time"): cv.string,
        vol.Optional("enabled", default=True): cv.boolean,
        vol.Optional("repeat", default=[]): vol.All(
            cv.ensure_list, [vol.In(range(7))]
        ),
        vol.Optional("face_define"): cv.string,
        vol.Optional("volume"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    }
)

SERVICE_UPDATE_ALARM_SCHEMA = vol.Schema(
    {
        vol.Required("event_id"): cv.string,
        vol.Optional("name"): cv.string,
        vol.Optional("time"): cv.string,
        vol.Optional("enabled"): cv.boolean,
        vol.Optional("repeat"): vol.All(cv.ensure_list, [vol.In(range(7))]),
        vol.Optional("face_define"): cv.string,
        vol.Optional("volume"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    }
)

SERVICE_DELETE_ALARM_SCHEMA = vol.Schema(
    {
        vol.Required("event_id"): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Remi from a config entry."""
    session = async_get_clientsession(hass)
    client = RemiApiClient(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        session,
        entry.data.get(CONF_INSTALLATION_ID, ""),
    )
    client._session_token = entry.data.get(CONF_SESSION_TOKEN)
    client._remi_id = entry.data[CONF_REMI_ID]

    coordinator = RemiDataUpdateCoordinator(hass, client)
    await coordinator.async_setup()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _register_services(hass, coordinator)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok


def _register_services(hass: HomeAssistant, coordinator: RemiDataUpdateCoordinator) -> None:
    """Register alarm CRUD services."""

    async def handle_create_alarm(call: ServiceCall) -> None:
        """Handle create_alarm service call."""
        from .const import FACE_DEFINE_TO_OBJECT_ID

        event_data: dict[str, Any] = {
            "name": call.data["name"],
            "time": {"__type": "Date", "iso": call.data["time"]},
            "enabled": call.data.get("enabled", True),
            "repeat": call.data.get("repeat", []),
        }
        face_define = call.data.get("face_define")
        if face_define and face_define in FACE_DEFINE_TO_OBJECT_ID:
            event_data["face"] = {
                "__type": "Pointer",
                "className": "Face",
                "objectId": FACE_DEFINE_TO_OBJECT_ID[face_define],
            }
        if "volume" in call.data:
            event_data["volume"] = call.data["volume"]

        await coordinator.client.create_event(event_data)
        await coordinator.async_request_refresh()

    async def handle_update_alarm(call: ServiceCall) -> None:
        """Handle update_alarm service call."""
        from .const import FACE_DEFINE_TO_OBJECT_ID

        event_id = call.data["event_id"]
        fields: dict[str, Any] = {}

        if "name" in call.data:
            fields["name"] = call.data["name"]
        if "time" in call.data:
            fields["time"] = {"__type": "Date", "iso": call.data["time"]}
        if "enabled" in call.data:
            fields["enabled"] = call.data["enabled"]
        if "repeat" in call.data:
            fields["repeat"] = call.data["repeat"]
        if "volume" in call.data:
            fields["volume"] = call.data["volume"]
        face_define = call.data.get("face_define")
        if face_define and face_define in FACE_DEFINE_TO_OBJECT_ID:
            fields["face"] = {
                "__type": "Pointer",
                "className": "Face",
                "objectId": FACE_DEFINE_TO_OBJECT_ID[face_define],
            }

        await coordinator.client.update_event(event_id, fields)
        await coordinator.async_request_refresh()

    async def handle_delete_alarm(call: ServiceCall) -> None:
        """Handle delete_alarm service call."""
        await coordinator.client.delete_event(call.data["event_id"])
        await coordinator.async_request_refresh()

    if not hass.services.has_service(DOMAIN, SERVICE_CREATE_ALARM):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CREATE_ALARM,
            handle_create_alarm,
            schema=SERVICE_CREATE_ALARM_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_UPDATE_ALARM):
        hass.services.async_register(
            DOMAIN,
            SERVICE_UPDATE_ALARM,
            handle_update_alarm,
            schema=SERVICE_UPDATE_ALARM_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_DELETE_ALARM):
        hass.services.async_register(
            DOMAIN,
            SERVICE_DELETE_ALARM,
            handle_delete_alarm,
            schema=SERVICE_DELETE_ALARM_SCHEMA,
        )
