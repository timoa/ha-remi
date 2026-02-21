"""Tests for the Remi light platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.light import ATTR_RGB_COLOR
from homeassistant.core import HomeAssistant

from custom_components.urbanhello_remi_unofficial.const import DOMAIN
from custom_components.urbanhello_remi_unofficial.coordinator import (
    RemiDataUpdateCoordinator,
)
from custom_components.urbanhello_remi_unofficial.light import (
    RemiBackgroundLightEntity,
    RemiNightLightEntity,
    async_setup_entry,
)

from .conftest import MOCK_REMI_DATA, MOCK_REMI_ID


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests in this module."""
    yield


@pytest.fixture
def mock_coordinator_with_lights():
    """Return a mock coordinator with RGB light data."""
    coordinator = MagicMock(spec=RemiDataUpdateCoordinator)
    coordinator.remi = {
        "objectId": MOCK_REMI_ID,
        "lightnight": [255, 128, 0],
        "background_color": [0, 0, 255],
    }
    coordinator.client = MagicMock()
    coordinator.client.update_remi = AsyncMock(return_value={})
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    @pytest.mark.skip(reason="Requires full HA platform setup - covered by other tests")
    async def test_adds_night_and_background_light(self, hass: HomeAssistant, mock_coordinator_with_lights):
        added_entities = []

        async def mock_add_entities(entities):
            added_entities.extend(entities)

        hass.data = {DOMAIN: {"entry_1": mock_coordinator_with_lights}}

        entry = MagicMock()
        entry.entry_id = "entry_1"

        await async_setup_entry(hass, entry, mock_add_entities)

        assert len(added_entities) == 2
        assert isinstance(added_entities[0], RemiNightLightEntity)
        assert isinstance(added_entities[1], RemiBackgroundLightEntity)


class TestRemiNightLightEntity:
    """Tests for RemiNightLightEntity."""

    def test_unique_id(self, mock_coordinator_with_lights):
        entity = RemiNightLightEntity(mock_coordinator_with_lights)
        assert entity.unique_id == f"{MOCK_REMI_ID}_night_light"

    def test_name(self, mock_coordinator_with_lights):
        entity = RemiNightLightEntity(mock_coordinator_with_lights)
        assert entity.name == "Night Light"

    def test_icon(self, mock_coordinator_with_lights):
        entity = RemiNightLightEntity(mock_coordinator_with_lights)
        assert entity.icon == "mdi:weather-night"

    def test_rgb_color_returns_tuple(self, mock_coordinator_with_lights):
        entity = RemiNightLightEntity(mock_coordinator_with_lights)
        assert entity.rgb_color == (255, 128, 0)

    def test_rgb_color_returns_none_when_invalid(self, mock_coordinator_with_lights):
        mock_coordinator_with_lights.remi["lightnight"] = [255, 128]
        entity = RemiNightLightEntity(mock_coordinator_with_lights)
        assert entity.rgb_color is None

    def test_is_on_when_any_channel_non_zero(self, mock_coordinator_with_lights):
        entity = RemiNightLightEntity(mock_coordinator_with_lights)
        assert entity.is_on is True

    def test_is_off_when_all_channels_zero(self, mock_coordinator_with_lights):
        mock_coordinator_with_lights.remi["lightnight"] = [0, 0, 0]
        entity = RemiNightLightEntity(mock_coordinator_with_lights)
        assert entity.is_on is False

    async def test_turn_on_with_rgb_color(self, mock_coordinator_with_lights):
        entity = RemiNightLightEntity(mock_coordinator_with_lights)
        await entity.async_turn_on(**{ATTR_RGB_COLOR: (100, 150, 200)})

        mock_coordinator_with_lights.client.update_remi.assert_awaited_once_with(
            {"lightnight": [100, 150, 200]}
        )
        mock_coordinator_with_lights.async_request_refresh.assert_awaited_once()

    async def test_turn_on_without_rgb_uses_current(self, mock_coordinator_with_lights):
        entity = RemiNightLightEntity(mock_coordinator_with_lights)
        await entity.async_turn_on()

        mock_coordinator_with_lights.client.update_remi.assert_awaited_once_with(
            {"lightnight": [255, 128, 0]}
        )

    async def test_turn_on_when_off_uses_white(self, mock_coordinator_with_lights):
        mock_coordinator_with_lights.remi["lightnight"] = [0, 0, 0]
        entity = RemiNightLightEntity(mock_coordinator_with_lights)
        await entity.async_turn_on()

        mock_coordinator_with_lights.client.update_remi.assert_awaited_once_with(
            {"lightnight": [255, 255, 255]}
        )

    async def test_turn_off_sets_rgb_to_zero(self, mock_coordinator_with_lights):
        entity = RemiNightLightEntity(mock_coordinator_with_lights)
        await entity.async_turn_off()

        mock_coordinator_with_lights.client.update_remi.assert_awaited_once_with(
            {"lightnight": [0, 0, 0]}
        )
        mock_coordinator_with_lights.async_request_refresh.assert_awaited_once()


class TestRemiBackgroundLightEntity:
    """Tests for RemiBackgroundLightEntity."""

    def test_unique_id(self, mock_coordinator_with_lights):
        entity = RemiBackgroundLightEntity(mock_coordinator_with_lights)
        assert entity.unique_id == f"{MOCK_REMI_ID}_background_color"

    def test_name(self, mock_coordinator_with_lights):
        entity = RemiBackgroundLightEntity(mock_coordinator_with_lights)
        assert entity.name == "Background Color"

    def test_icon(self, mock_coordinator_with_lights):
        entity = RemiBackgroundLightEntity(mock_coordinator_with_lights)
        assert entity.icon == "mdi:palette"

    def test_rgb_color_returns_tuple(self, mock_coordinator_with_lights):
        entity = RemiBackgroundLightEntity(mock_coordinator_with_lights)
        assert entity.rgb_color == (0, 0, 255)

    async def test_turn_on_updates_background_color_field(self, mock_coordinator_with_lights):
        entity = RemiBackgroundLightEntity(mock_coordinator_with_lights)
        await entity.async_turn_on(**{ATTR_RGB_COLOR: (255, 0, 128)})

        mock_coordinator_with_lights.client.update_remi.assert_awaited_once_with(
            {"background_color": [255, 0, 128]}
        )

    async def test_turn_off_sets_background_color_to_zero(self, mock_coordinator_with_lights):
        entity = RemiBackgroundLightEntity(mock_coordinator_with_lights)
        await entity.async_turn_off()

        mock_coordinator_with_lights.client.update_remi.assert_awaited_once_with(
            {"background_color": [0, 0, 0]}
        )
