"""Tests for the Remi binary sensor platform."""
from __future__ import annotations

import pytest

from custom_components.urbanhello_remi_unofficial.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS,
)

from .conftest import MOCK_REMI_DATA


def _get_description(key: str):
    """Return the binary sensor description for the given key."""
    return next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == key)


class TestOnlineBinarySensor:
    """Tests for the online binary sensor."""

    def test_online_true(self):
        desc = _get_description("online")
        assert desc.value_fn({"online": True}) is True

    def test_online_false(self):
        desc = _get_description("online")
        assert desc.value_fn({"online": False}) is False

    def test_online_missing_defaults_false(self):
        desc = _get_description("online")
        assert desc.value_fn({}) is False

    def test_online_from_mock_data(self):
        desc = _get_description("online")
        assert desc.value_fn(MOCK_REMI_DATA) is True


class TestAliveBinarySensor:
    """Tests for the alive binary sensor."""

    def test_alive_true(self):
        desc = _get_description("alive")
        assert desc.value_fn({"alive": True}) is True

    def test_alive_false(self):
        desc = _get_description("alive")
        assert desc.value_fn({"alive": False}) is False

    def test_alive_missing_defaults_false(self):
        desc = _get_description("alive")
        assert desc.value_fn({}) is False

    def test_alive_disabled_by_default(self):
        desc = _get_description("alive")
        assert desc.entity_registry_enabled_default is False

    def test_alive_from_mock_data(self):
        desc = _get_description("alive")
        assert desc.value_fn(MOCK_REMI_DATA) is True


class TestFirmwareUpdateBinarySensor:
    """Tests for the firmware update binary sensor."""

    def test_update_available_when_newer_version_exists(self):
        desc = _get_description("firmware_update")
        remi = {"current_firmware_version": 100}
        assert desc.value_fn(remi, 110) is True

    def test_no_update_when_on_latest(self):
        desc = _get_description("firmware_update")
        remi = {"current_firmware_version": 110}
        assert desc.value_fn(remi, 110) is False

    def test_no_update_when_latest_is_none(self):
        desc = _get_description("firmware_update")
        remi = {"current_firmware_version": 100}
        assert desc.value_fn(remi, None) is False

    def test_no_update_when_firmware_missing(self):
        desc = _get_description("firmware_update")
        assert desc.value_fn({}, 110) is True

    def test_no_update_when_both_missing(self):
        desc = _get_description("firmware_update")
        assert desc.value_fn({}, None) is False

    def test_firmware_update_from_mock_data(self):
        desc = _get_description("firmware_update")
        assert desc.value_fn(MOCK_REMI_DATA, 110) is True

    def test_no_firmware_update_from_mock_data_same_version(self):
        desc = _get_description("firmware_update")
        assert desc.value_fn(MOCK_REMI_DATA, 100) is False
