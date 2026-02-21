"""Tests for the Remi number platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.urbanhello_remi_unofficial.const import DOMAIN
from custom_components.urbanhello_remi_unofficial.coordinator import (
    RemiDataUpdateCoordinator,
)
from custom_components.urbanhello_remi_unofficial.number import (
    NUMBER_DESCRIPTIONS,
    RemiNumberEntity,
    async_setup_entry,
)

from .conftest import MOCK_REMI_DATA, MOCK_REMI_ID


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests in this module."""
    yield


@pytest.fixture
def mock_coordinator():
    """Return a mock coordinator with number data."""
    coordinator = MagicMock(spec=RemiDataUpdateCoordinator)
    coordinator.remi = {
        "objectId": MOCK_REMI_ID,
        "volume": 75,
        "luminosity": 60,
        "noise_notification_threshold": 30,
    }
    coordinator.client = MagicMock()
    coordinator.client.update_remi = AsyncMock(return_value={})
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    @pytest.mark.skip(reason="Requires full HA platform setup - covered by other tests")
    async def test_adds_all_number_entities(self, hass: HomeAssistant, mock_coordinator):
        added_entities = []

        async def mock_add_entities(entities):
            added_entities.extend(entities)

        hass.data = {DOMAIN: {"entry_1": mock_coordinator}}

        entry = MagicMock()
        entry.entry_id = "entry_1"

        await async_setup_entry(hass, entry, mock_add_entities)

        assert len(added_entities) == 3
        for entity in added_entities:
            assert isinstance(entity, RemiNumberEntity)


class TestRemiNumberEntity:
    """Tests for RemiNumberEntity."""

    def test_volume_entity_unique_id(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[0])
        assert entity.unique_id == f"{MOCK_REMI_ID}_volume"

    def test_volume_entity_properties(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[0])
        assert entity.entity_description.name == "Volume"
        assert entity.icon == "mdi:volume-high"
        assert entity.native_min_value == 0
        assert entity.native_max_value == 100
        assert entity.native_step == 1

    def test_volume_native_value(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[0])
        assert entity.native_value == 75

    def test_volume_default_value_when_missing(self, mock_coordinator):
        mock_coordinator.remi.pop("volume")
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[0])
        assert entity.native_value == 50

    async def test_volume_set_value(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[0])
        await entity.async_set_native_value(80)

        mock_coordinator.client.update_remi.assert_awaited_once_with({"volume": 80})
        mock_coordinator.async_request_refresh.assert_awaited_once()

    def test_luminosity_entity_properties(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[1])
        assert entity.entity_description.name == "Screen Brightness"
        assert entity.icon == "mdi:brightness-6"

    def test_luminosity_native_value(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[1])
        assert entity.native_value == 60

    def test_luminosity_default_value_when_missing(self, mock_coordinator):
        mock_coordinator.remi.pop("luminosity")
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[1])
        assert entity.native_value == 50

    async def test_luminosity_set_value(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[1])
        await entity.async_set_native_value(90)

        mock_coordinator.client.update_remi.assert_awaited_once_with({"luminosity": 90})

    def test_noise_threshold_entity_properties(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[2])
        assert entity.entity_description.name == "Noise Alert Threshold"
        assert entity.icon == "mdi:microphone"

    def test_noise_threshold_native_value(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[2])
        assert entity.native_value == 30

    def test_noise_threshold_default_value_when_missing(self, mock_coordinator):
        mock_coordinator.remi.pop("noise_notification_threshold")
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[2])
        assert entity.native_value == 0

    async def test_noise_threshold_set_value(self, mock_coordinator):
        entity = RemiNumberEntity(mock_coordinator, NUMBER_DESCRIPTIONS[2])
        await entity.async_set_native_value(45)

        mock_coordinator.client.update_remi.assert_awaited_once_with(
            {"noise_notification_threshold": 45}
        )
