"""Validate the app's event schema, including the weekday index conversion."""
from unittest.mock import AsyncMock, MagicMock

import pytest
import voluptuous as vol

from custom_components.urbanhello_remi_unofficial import _register_services
from custom_components.urbanhello_remi_unofficial.const import DOMAIN


@pytest.fixture
def coordinator(hass):
    """Register the alarm services on a coordinator holding one alarm."""
    coordinator = MagicMock(
        events=[{"objectId": "alarm"}], async_request_refresh=AsyncMock()
    )
    coordinator.client.create_event = AsyncMock()
    coordinator.client.update_event = AsyncMock()
    hass.data[DOMAIN] = {"entry": coordinator}
    _register_services(hass)
    return coordinator


async def test_create_uses_app_fields(hass, coordinator):
    await hass.services.async_call(DOMAIN, "create_alarm", {
        "name": "Week morning", "time": "07:30", "repeat": [1, 2, 3, 4, 5]
    }, blocking=True)
    coordinator.client.create_event.assert_awaited_once_with({
        "name": "Week morning", "event_time": [7, 30], "enabled": True,
        "recurrence": [1, 1, 1, 1, 1, 0, 0],
    })


async def test_update_weekend_and_time_without_overwriting_other_fields(hass, coordinator):
    await hass.services.async_call(DOMAIN, "update_alarm", {
        "event_id": "alarm", "time": "09:00:00", "repeat": [0, 6]
    }, blocking=True)
    coordinator.client.update_event.assert_awaited_once_with("alarm", {
        "event_time": [9, 0], "recurrence": [0, 0, 0, 0, 0, 1, 1],
    })


@pytest.mark.parametrize("value", ["invalid", "24:00", "07:60", "07:30:15",
                                   "2026-02-20T07:00:00Z", "07:30+02:00"])
async def test_invalid_or_ambiguous_time_does_not_write(hass, coordinator, value):
    """Reject any clock time the services cannot store without guessing."""
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(DOMAIN, "update_alarm", {
            "event_id": "alarm", "time": value
        }, blocking=True)
    coordinator.client.update_event.assert_not_called()
