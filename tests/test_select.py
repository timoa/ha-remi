"""Tests for the Remi select platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.urbanhello_remi_unofficial.const import (
    DOMAIN,
    FACE_DEFINE_TO_NAME,
    FACE_DEFINE_TO_OBJECT_ID,
    MUSIC_MODE_OPTIONS,
)
from custom_components.urbanhello_remi_unofficial.coordinator import (
    RemiDataUpdateCoordinator,
)
from custom_components.urbanhello_remi_unofficial.select import (
    RemiClockFormatSelectEntity,
    RemiFaceSelectEntity,
    RemiMusicModeSelectEntity,
    async_setup_entry,
)

from .conftest import MOCK_REMI_ID


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests in this module."""
    yield


@pytest.fixture
def mock_coordinator():
    """Return a mock coordinator with select data."""
    coordinator = MagicMock(spec=RemiDataUpdateCoordinator)
    coordinator.remi = {
        "objectId": MOCK_REMI_ID,
        "face": {"__type": "Pointer", "className": "Face", "objectId": "fIjF0yWRxX"},
        "hourFormat24": True,
        "musicMode": 1,
    }
    coordinator.client = MagicMock()
    coordinator.client.update_remi = AsyncMock(return_value={})
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    @pytest.mark.skip(reason="Requires full HA platform setup - covered by other tests")
    async def test_adds_all_select_entities(self, hass: HomeAssistant, mock_coordinator):
        added_entities = []

        async def mock_add_entities(entities):
            added_entities.extend(entities)

        hass.data = {DOMAIN: {"entry_1": mock_coordinator}}

        entry = MagicMock()
        entry.entry_id = "entry_1"

        await async_setup_entry(hass, entry, mock_add_entities)

        assert len(added_entities) == 3
        assert isinstance(added_entities[0], RemiFaceSelectEntity)
        assert isinstance(added_entities[1], RemiClockFormatSelectEntity)
        assert isinstance(added_entities[2], RemiMusicModeSelectEntity)


class TestRemiFaceSelectEntity:
    """Tests for RemiFaceSelectEntity."""

    def test_unique_id(self, mock_coordinator):
        entity = RemiFaceSelectEntity(mock_coordinator)
        assert entity.unique_id == f"{MOCK_REMI_ID}_face"

    def test_name_attr(self, mock_coordinator):
        entity = RemiFaceSelectEntity(mock_coordinator)
        assert entity._attr_name == "Clock Face"

    def test_icon(self, mock_coordinator):
        entity = RemiFaceSelectEntity(mock_coordinator)
        assert entity.icon == "mdi:emoticon-outline"

    def test_options(self, mock_coordinator):
        entity = RemiFaceSelectEntity(mock_coordinator)
        assert set(entity.options) == set(FACE_DEFINE_TO_NAME.values())

    def test_current_option_returns_face_name(self, mock_coordinator):
        entity = RemiFaceSelectEntity(mock_coordinator)
        assert entity.current_option == "Awake"

    def test_current_option_returns_none_for_unknown_face(self, mock_coordinator):
        mock_coordinator.remi["face"] = {"objectId": "unknown_id"}
        entity = RemiFaceSelectEntity(mock_coordinator)
        assert entity.current_option is None

    def test_current_option_handles_none_face(self, mock_coordinator):
        mock_coordinator.remi["face"] = None
        entity = RemiFaceSelectEntity(mock_coordinator)
        assert entity.current_option is None

    async def test_select_option_updates_face(self, mock_coordinator):
        entity = RemiFaceSelectEntity(mock_coordinator)
        await entity.async_select_option("Sleepy")

        mock_coordinator.client.update_remi.assert_awaited_once_with(
            {
                "face": {
                    "__type": "Pointer",
                    "className": "Face",
                    "objectId": FACE_DEFINE_TO_OBJECT_ID["FACE_NIGHT"],
                }
            }
        )
        mock_coordinator.async_request_refresh.assert_awaited_once()

    async def test_select_option_ignores_invalid_option(self, mock_coordinator):
        entity = RemiFaceSelectEntity(mock_coordinator)
        await entity.async_select_option("InvalidFace")

        mock_coordinator.client.update_remi.assert_not_called()


class TestRemiClockFormatSelectEntity:
    """Tests for RemiClockFormatSelectEntity."""

    def test_unique_id(self, mock_coordinator):
        entity = RemiClockFormatSelectEntity(mock_coordinator)
        assert entity.unique_id == f"{MOCK_REMI_ID}_clock_format"

    def test_name_attr(self, mock_coordinator):
        entity = RemiClockFormatSelectEntity(mock_coordinator)
        assert entity._attr_name == "Clock Format"

    def test_icon(self, mock_coordinator):
        entity = RemiClockFormatSelectEntity(mock_coordinator)
        assert entity.icon == "mdi:clock-outline"

    def test_options(self, mock_coordinator):
        entity = RemiClockFormatSelectEntity(mock_coordinator)
        assert entity.options == ["12h", "24h"]

    def test_current_option_returns_24h_when_true(self, mock_coordinator):
        entity = RemiClockFormatSelectEntity(mock_coordinator)
        assert entity.current_option == "24h"

    def test_current_option_returns_12h_when_false(self, mock_coordinator):
        mock_coordinator.remi["hourFormat24"] = False
        entity = RemiClockFormatSelectEntity(mock_coordinator)
        assert entity.current_option == "12h"

    async def test_select_24h_updates_format(self, mock_coordinator):
        entity = RemiClockFormatSelectEntity(mock_coordinator)
        await entity.async_select_option("24h")

        mock_coordinator.client.update_remi.assert_awaited_once_with(
            {"hourFormat24": True}
        )
        mock_coordinator.async_request_refresh.assert_awaited_once()

    async def test_select_12h_updates_format(self, mock_coordinator):
        entity = RemiClockFormatSelectEntity(mock_coordinator)
        await entity.async_select_option("12h")

        mock_coordinator.client.update_remi.assert_awaited_once_with(
            {"hourFormat24": False}
        )


class TestRemiMusicModeSelectEntity:
    """Tests for RemiMusicModeSelectEntity."""

    def test_unique_id(self, mock_coordinator):
        entity = RemiMusicModeSelectEntity(mock_coordinator)
        assert entity.unique_id == f"{MOCK_REMI_ID}_music_mode"

    def test_name_attr(self, mock_coordinator):
        entity = RemiMusicModeSelectEntity(mock_coordinator)
        assert entity._attr_name == "Music Mode"

    def test_icon(self, mock_coordinator):
        entity = RemiMusicModeSelectEntity(mock_coordinator)
        assert entity.icon == "mdi:music"

    def test_options(self, mock_coordinator):
        entity = RemiMusicModeSelectEntity(mock_coordinator)
        assert set(entity.options) == set(MUSIC_MODE_OPTIONS.values())

    def test_current_option_returns_music_mode(self, mock_coordinator):
        entity = RemiMusicModeSelectEntity(mock_coordinator)
        assert entity.current_option == MUSIC_MODE_OPTIONS[1]

    def test_current_option_handles_unknown_mode(self, mock_coordinator):
        mock_coordinator.remi["musicMode"] = 99
        entity = RemiMusicModeSelectEntity(mock_coordinator)
        assert entity.current_option is None

    async def test_select_option_updates_music_mode(self, mock_coordinator):
        entity = RemiMusicModeSelectEntity(mock_coordinator)
        target_mode = next(k for k, v in MUSIC_MODE_OPTIONS.items() if v != MUSIC_MODE_OPTIONS[1])
        target_name = MUSIC_MODE_OPTIONS[target_mode]

        await entity.async_select_option(target_name)

        mock_coordinator.client.update_remi.assert_awaited_once_with(
            {"musicMode": target_mode}
        )
        mock_coordinator.async_request_refresh.assert_awaited_once()
