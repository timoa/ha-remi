"""Tests for the Remi sensor platform."""
from __future__ import annotations

import pytest

from custom_components.urbanhello_remi_unofficial.sensor import SENSOR_DESCRIPTIONS

from .conftest import MOCK_REMI_DATA


def _get_description(key: str):
    """Return the sensor description for the given key."""
    return next(d for d in SENSOR_DESCRIPTIONS if d.key == key)


class TestTemperatureSensor:
    """Tests for the temperature sensor value function."""

    def test_temperature_formula(self):
        desc = _get_description("temperature")
        assert desc.value_fn({"temp": 157}) == pytest.approx(21.0)

    def test_temperature_formula_zero(self):
        desc = _get_description("temperature")
        assert desc.value_fn({"temp": 115}) == pytest.approx(0.0)

    def test_temperature_formula_negative(self):
        desc = _get_description("temperature")
        assert desc.value_fn({"temp": 105}) == pytest.approx(-5.0)

    def test_temperature_missing_field_defaults_to_zero(self):
        desc = _get_description("temperature")
        assert desc.value_fn({}) == pytest.approx(-57.5)

    def test_temperature_from_mock_data(self):
        desc = _get_description("temperature")
        assert desc.value_fn(MOCK_REMI_DATA) == pytest.approx(21.0)


class TestLuminositySensor:
    """Tests for the luminosity sensor value function."""

    def test_luminosity_returns_value(self):
        desc = _get_description("luminosity")
        assert desc.value_fn({"luminosity": 42}) == 42

    def test_luminosity_returns_none_when_missing(self):
        desc = _get_description("luminosity")
        assert desc.value_fn({}) is None

    def test_luminosity_from_mock_data(self):
        desc = _get_description("luminosity")
        assert desc.value_fn(MOCK_REMI_DATA) == 42


class TestRssiSensor:
    """Tests for the WiFi signal sensor value function."""

    def test_rssi_returns_value(self):
        desc = _get_description("rssi")
        assert desc.value_fn({"rssi": -65}) == -65

    def test_rssi_returns_none_when_missing(self):
        desc = _get_description("rssi")
        assert desc.value_fn({}) is None

    def test_rssi_disabled_by_default(self):
        desc = _get_description("rssi")
        assert desc.entity_registry_enabled_default is False


class TestFirmwareVersionSensor:
    """Tests for the firmware version sensor value function."""

    def test_firmware_version_returns_value(self):
        desc = _get_description("firmware_version")
        assert desc.value_fn({"current_firmware_version": 100}) == 100

    def test_firmware_version_returns_none_when_missing(self):
        desc = _get_description("firmware_version")
        assert desc.value_fn({}) is None


class TestIpAddressSensor:
    """Tests for the IP address sensor value function."""

    def test_ip_address_returns_value(self):
        desc = _get_description("ip_address")
        assert desc.value_fn({"ipv4Address": "192.168.1.50"}) == "192.168.1.50"

    def test_ip_address_returns_none_when_missing(self):
        desc = _get_description("ip_address")
        assert desc.value_fn({}) is None

    def test_ip_address_disabled_by_default(self):
        desc = _get_description("ip_address")
        assert desc.entity_registry_enabled_default is False


class TestCurrentFaceSensor:
    """Tests for the current face sensor value function."""

    def test_face_awake(self):
        desc = _get_description("current_face")
        remi = {"face": {"objectId": "fIjF0yWRxX"}}
        assert desc.value_fn(remi) == "Awake"

    def test_face_sleepy(self):
        desc = _get_description("current_face")
        remi = {"face": {"objectId": "rnAltoFwYC"}}
        assert desc.value_fn(remi) == "Sleepy"

    def test_face_off(self):
        desc = _get_description("current_face")
        remi = {"face": {"objectId": "GDaZOVdRqj"}}
        assert desc.value_fn(remi) == "Off"

    def test_face_semi_awake(self):
        desc = _get_description("current_face")
        remi = {"face": {"objectId": "9faiiPGBVv"}}
        assert desc.value_fn(remi) == "Semi-Awake"

    def test_face_smiley(self):
        desc = _get_description("current_face")
        remi = {"face": {"objectId": "d712mdpZ0v"}}
        assert desc.value_fn(remi) == "Smiley"

    def test_face_unknown_object_id(self):
        desc = _get_description("current_face")
        remi = {"face": {"objectId": "unknown_id"}}
        assert desc.value_fn(remi) == "Unknown"

    def test_face_missing_field(self):
        desc = _get_description("current_face")
        assert desc.value_fn({}) == "Unknown"

    def test_face_none_value(self):
        desc = _get_description("current_face")
        assert desc.value_fn({"face": None}) == "Unknown"

    def test_face_from_mock_data(self):
        desc = _get_description("current_face")
        assert desc.value_fn(MOCK_REMI_DATA) == "Awake"
