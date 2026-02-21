"""Tests for the Remi alarm switch platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.urbanhello_remi_unofficial.switch import RemiAlarmSwitchEntity

from .conftest import MOCK_EVENT_DATA, MOCK_REMI_DATA, MOCK_REMI_ID, mock_api_client


MOCK_EVENT = MOCK_EVENT_DATA[0]


@pytest.fixture
def coordinator(hass, mock_api_client):
    """Return a minimal coordinator mock with remi + events data."""
    from custom_components.urbanhello_remi_unofficial.coordinator import (
        RemiDataUpdateCoordinator,
    )

    coord = MagicMock(spec=RemiDataUpdateCoordinator)
    coord.hass = hass
    coord.client = mock_api_client
    coord.data = {"remi": MOCK_REMI_DATA, "events": list(MOCK_EVENT_DATA)}
    coord.remi = MOCK_REMI_DATA
    coord.events = list(MOCK_EVENT_DATA)
    coord.async_request_refresh = AsyncMock()
    coord.async_add_listener = MagicMock(return_value=lambda: None)
    return coord


@pytest.fixture
def alarm_switch(coordinator):
    """Return a RemiAlarmSwitchEntity for the first mock event."""
    entity = RemiAlarmSwitchEntity(coordinator, MOCK_EVENT)
    return entity


class TestRemiAlarmSwitchEntity:
    """Tests for RemiAlarmSwitchEntity."""

    def test_unique_id(self, alarm_switch):
        assert alarm_switch.unique_id == f"{MOCK_REMI_ID}_alarm_{MOCK_EVENT['objectId']}"

    def test_name_from_event(self, alarm_switch):
        assert alarm_switch.name == MOCK_EVENT["name"]

    def test_name_fallback_when_no_name(self, coordinator):
        event = {"objectId": "ev_no_name"}
        entity = RemiAlarmSwitchEntity(coordinator, event)
        assert entity.name == f"Alarm ev_no_name"

    def test_is_on_when_enabled(self, alarm_switch, coordinator):
        coordinator.events = [{"objectId": MOCK_EVENT["objectId"], "enabled": True}]
        assert alarm_switch.is_on is True

    def test_is_off_when_disabled(self, alarm_switch, coordinator):
        coordinator.events = [{"objectId": MOCK_EVENT["objectId"], "enabled": False}]
        assert alarm_switch.is_on is False

    def test_is_off_when_event_not_found(self, alarm_switch, coordinator):
        coordinator.events = []
        assert alarm_switch.is_on is False

    def test_extra_state_attributes_time(self, alarm_switch, coordinator):
        coordinator.events = [
            {**MOCK_EVENT, "event_time": [7, 30]}
        ]
        attrs = alarm_switch.extra_state_attributes
        assert attrs["time"] == "07:30"

    def test_extra_state_attributes_recurrence(self, alarm_switch, coordinator):
        coordinator.events = [
            {**MOCK_EVENT, "recurrence": [False, True, True, True, True, True, False]}
        ]
        attrs = alarm_switch.extra_state_attributes
        assert attrs["recurrence"] == ["mon", "tue", "wed", "thu", "fri"]

    def test_extra_state_attributes_face(self, alarm_switch, coordinator):
        coordinator.events = [
            {**MOCK_EVENT, "face": {"objectId": "fIjF0yWRxX"}}
        ]
        attrs = alarm_switch.extra_state_attributes
        assert attrs["face"] == "Awake"

    def test_extra_state_attributes_volume(self, alarm_switch, coordinator):
        coordinator.events = [{**MOCK_EVENT, "volume": 80}]
        attrs = alarm_switch.extra_state_attributes
        assert attrs["volume"] == 80

    def test_extra_state_attributes_no_time_when_missing(self, alarm_switch, coordinator):
        coordinator.events = [{**MOCK_EVENT, "event_time": None}]
        attrs = alarm_switch.extra_state_attributes
        assert "time" not in attrs

    def test_extra_state_attributes_unknown_face_not_included(self, alarm_switch, coordinator):
        coordinator.events = [
            {**MOCK_EVENT, "face": {"objectId": "unknown_face_id"}}
        ]
        attrs = alarm_switch.extra_state_attributes
        assert "face" not in attrs

    async def test_async_turn_on(self, alarm_switch, coordinator, mock_api_client):
        await alarm_switch.async_turn_on()

        mock_api_client.update_event.assert_called_once_with(
            MOCK_EVENT["objectId"], {"enabled": True}
        )
        coordinator.async_request_refresh.assert_called_once()

    async def test_async_turn_off(self, alarm_switch, coordinator, mock_api_client):
        await alarm_switch.async_turn_off()

        mock_api_client.update_event.assert_called_once_with(
            MOCK_EVENT["objectId"], {"enabled": False}
        )
        coordinator.async_request_refresh.assert_called_once()


class TestGetEvent:
    """Tests for _get_event helper."""

    def test_returns_event_when_found(self, alarm_switch, coordinator):
        coordinator.events = [MOCK_EVENT]
        event = alarm_switch._get_event()
        assert event["objectId"] == MOCK_EVENT["objectId"]

    def test_returns_empty_dict_when_not_found(self, alarm_switch, coordinator):
        coordinator.events = []
        assert alarm_switch._get_event() == {}
