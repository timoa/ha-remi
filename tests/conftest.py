"""Shared fixtures for the UrbanHello Remi integration tests."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.urbanhello_remi_unofficial.api import RemiApiClient
from custom_components.urbanhello_remi_unofficial.const import (
    CONF_INSTALLATION_ID,
    CONF_REMI_ID,
    CONF_SESSION_TOKEN,
    DOMAIN,
)
from custom_components.urbanhello_remi_unofficial.coordinator import (
    RemiDataUpdateCoordinator,
)

MOCK_REMI_ID = "remi_object_id_1"
MOCK_SESSION_TOKEN = "mock_session_token"
MOCK_USERNAME = "test@example.com"
MOCK_PASSWORD = "test_password"
MOCK_INSTALLATION_ID = "mock-installation-uuid"

MOCK_REMI_DATA: dict[str, Any] = {
    "objectId": MOCK_REMI_ID,
    "name": "Remi Bedroom",
    "online": True,
    "alive": True,
    "temp": 157,
    "luminosity": 42,
    "rssi": -65,
    "current_firmware_version": 100,
    "ipv4Address": "192.168.1.50",
    "uniqueID": "AABBCCDDEEFF",
    "face": {"__type": "Pointer", "className": "Face", "objectId": "fIjF0yWRxX"},
    "lightnight": [0, 0, 0],
    "background_color": [255, 128, 0],
    "volume": 50,
    "noiseThreshold": 30,
    "clockFormat": 0,
    "musicMode": 1,
}

MOCK_EVENT_DATA: list[dict[str, Any]] = [
    {
        "objectId": "event_id_1",
        "name": "Morning Alarm",
        "enabled": True,
        "event_time": [7, 30],
        "recurrence": [False, True, True, True, True, True, False],
        "volume": 80,
        "face": {"__type": "Pointer", "className": "Face", "objectId": "fIjF0yWRxX"},
    }
]

MOCK_FACES_DATA: list[dict[str, Any]] = [
    {"objectId": "GDaZOVdRqj", "define": "FACE_OFF", "index": 0},
    {"objectId": "fIjF0yWRxX", "define": "FACE_DAY", "index": 1},
    {"objectId": "rnAltoFwYC", "define": "FACE_NIGHT", "index": 2},
    {"objectId": "9faiiPGBVv", "define": "FACE_SEMI_AWAKE", "index": 3},
    {"objectId": "d712mdpZ0v", "define": "FACE_SMILY", "index": 4},
]

MOCK_CONFIG_DATA: dict[str, Any] = {
    "params": {"default_firmware_update_version": 110}
}

MOCK_LOGIN_RESPONSE: dict[str, Any] = {
    "sessionToken": MOCK_SESSION_TOKEN,
    "currentRemi": {"objectId": MOCK_REMI_ID},
    "remis": [MOCK_REMI_ID],
}


@pytest.fixture
def mock_api_client() -> MagicMock:
    """Return a mock RemiApiClient."""
    client = MagicMock(spec=RemiApiClient)
    client.remi_id = MOCK_REMI_ID
    client.session_token = MOCK_SESSION_TOKEN
    client._remi_id = MOCK_REMI_ID
    client._session_token = MOCK_SESSION_TOKEN
    client.login = AsyncMock(
        return_value=(MOCK_SESSION_TOKEN, MOCK_REMI_ID, [MOCK_REMI_ID])
    )
    client.get_remi = AsyncMock(return_value=MOCK_REMI_DATA)
    client.get_events = AsyncMock(return_value=MOCK_EVENT_DATA)
    client.get_faces = AsyncMock(return_value=MOCK_FACES_DATA)
    client.get_config = AsyncMock(return_value=MOCK_CONFIG_DATA)
    client.update_remi = AsyncMock(return_value={})
    client.create_event = AsyncMock(return_value={"objectId": "new_event_id"})
    client.update_event = AsyncMock(return_value={})
    client.delete_event = AsyncMock(return_value=None)
    return client


@pytest.fixture
def mock_config_entry_data() -> dict[str, Any]:
    """Return mock config entry data."""
    return {
        "username": MOCK_USERNAME,
        "password": MOCK_PASSWORD,
        CONF_REMI_ID: MOCK_REMI_ID,
        CONF_SESSION_TOKEN: MOCK_SESSION_TOKEN,
        CONF_INSTALLATION_ID: MOCK_INSTALLATION_ID,
    }
