"""Alarm time edits preserve the rest of the REMI schedule."""
from copy import deepcopy
from datetime import time, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.urbanhello_remi_unofficial.const import DOMAIN
from custom_components.urbanhello_remi_unofficial.time import (
    RemiAlarmTime, alarm_time, async_setup_entry,
)
from .conftest import MOCK_EVENT_DATA, MOCK_REMI_DATA, MOCK_REMI_ID


@pytest.fixture
def coordinator(hass, mock_api_client):
    """Return a coordinator holding one cloud alarm."""
    return MagicMock(
        hass=hass, client=mock_api_client, remi=MOCK_REMI_DATA,
        events=[dict(MOCK_EVENT_DATA[0])], last_update_success=True,
        async_request_refresh=AsyncMock(),
    )


@pytest.mark.parametrize("value", [None, [], [7], [24, 0], [7, 60],
                                        [True, 30], [7, "30"], [7, 30, 0]])
def test_bad_cloud_time_is_unknown(value):
    assert alarm_time({"event_time": value}) is None


async def test_edit_changes_only_clock_time(coordinator):
    entity = RemiAlarmTime(coordinator, coordinator.events[0])
    assert entity.native_value == time(7, 30)
    assert entity.unique_id == f"{MOCK_REMI_ID}_alarm_event_id_1_time"
    assert entity.available
    await entity.async_set_value(time(8, 15))
    coordinator.client.update_event.assert_awaited_once_with(
        "event_id_1", {"event_time": [8, 15]}
    )
    coordinator.async_request_refresh.assert_awaited_once()
    # No optimistic value: retain the last confirmed reading until the refresh.
    assert entity.native_value == time(7, 30)


async def test_missing_alarm_cannot_be_edited(coordinator):
    """Refuse to edit an alarm that no longer exists in the cloud."""
    entity = RemiAlarmTime(coordinator, coordinator.events[0])
    coordinator.events = []
    assert not entity.available
    with pytest.raises(ServiceValidationError):
        await entity.async_set_value(time(8))
    coordinator.client.update_event.assert_not_called()


@pytest.mark.parametrize("value", [time(8, 0, 1), time(8, tzinfo=timezone.utc)])
async def test_precision_or_timezone_not_silently_discarded(coordinator, value):
    """Refuse a value that would lose precision or timezone."""
    entity = RemiAlarmTime(coordinator, coordinator.events[0])
    with pytest.raises(ServiceValidationError):
        await entity.async_set_value(value)
    coordinator.client.update_event.assert_not_called()


async def test_alarm_lifecycle_and_failed_poll(hass, coordinator):
    hass.data[DOMAIN] = {"entry": coordinator}
    entry = MagicMock(entry_id="entry")
    add = MagicMock()
    await async_setup_entry(hass, entry, add)
    assert len(add.call_args.args[0]) == 1
    listener = coordinator.async_add_listener.call_args.args[0]
    listener()
    assert add.call_count == 1
    registry = er.async_get(hass)
    registered = registry.async_get_or_create(
        "time", DOMAIN, f"{MOCK_REMI_ID}_alarm_event_id_1_time"
    )
    coordinator.events = []
    coordinator.last_update_success = False
    listener()
    assert registry.async_get(registered.entity_id) is not None
    coordinator.last_update_success = True
    listener()
    assert registry.async_get(registered.entity_id) is None
    coordinator.events = [dict(MOCK_EVENT_DATA[0])]
    listener()
    assert add.call_count == 2


async def test_alarm_rename_updates_the_entity_name(
    hass, enable_custom_integrations, mock_api_client, mock_config_entry_data,
):
    """Relabel the alarm time entity when the alarm is renamed in the app."""
    entry = MockConfigEntry(domain=DOMAIN, data=mock_config_entry_data, title="Test REMI")
    entry.add_to_hass(hass)
    mock_api_client.get_remi.return_value = deepcopy(MOCK_REMI_DATA)
    mock_api_client.get_events.return_value = deepcopy(MOCK_EVENT_DATA)
    with (
        patch("custom_components.urbanhello_remi_unofficial.RemiApiClient", return_value=mock_api_client),
        patch("custom_components.urbanhello_remi_unofficial.async_get_clientsession"),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("time", DOMAIN, f"{MOCK_REMI_ID}_alarm_event_id_1_time")
    assert entity_id is not None
    assert hass.states.get(entity_id).attributes["friendly_name"] == "Remi Bedroom Morning Alarm time"

    coordinator = hass.data[DOMAIN][entry.entry_id]
    mock_api_client.get_events.return_value = [{**MOCK_EVENT_DATA[0], "name": "Evening Alarm"}]
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).attributes["friendly_name"] == "Remi Bedroom Evening Alarm time"
    assert registry.async_get(entity_id).original_name == "Evening Alarm time"

    # A name chosen by the user wins over the cloud name.
    registry.async_update_entity(entity_id, name="My alarm")
    await hass.async_block_till_done()
    mock_api_client.get_events.return_value = [{**MOCK_EVENT_DATA[0], "name": "Night Alarm"}]
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).attributes["friendly_name"] == "My alarm"
    assert registry.async_get(entity_id).original_name == "Night Alarm time"
