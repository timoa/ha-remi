"""Regressions for real firmware metadata, cloud outages and integration reloads."""


import asyncio


from time import monotonic
from unittest.mock import AsyncMock, MagicMock, patch


import aiohttp


import pytest


from homeassistant.exceptions import HomeAssistantError


from custom_components.urbanhello_remi_unofficial import _register_services, async_unload_entry


from custom_components.urbanhello_remi_unofficial.api import RemiApiClient, RemiApiError


from custom_components.urbanhello_remi_unofficial.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS, RemiBinarySensorEntity,
)


from custom_components.urbanhello_remi_unofficial.button import RemiCheckFirmwareButton


from custom_components.urbanhello_remi_unofficial.const import DOMAIN


from custom_components.urbanhello_remi_unofficial.coordinator import RemiDataUpdateCoordinator


from custom_components.urbanhello_remi_unofficial.firmware import firmware_update_available


from .conftest import (
    MOCK_CONFIG_DATA,
    MOCK_LOGIN_RESPONSE,
    MOCK_REMI_DATA,
    MOCK_REMI_ID,
)


from .test_api import _make_response


@pytest.mark.parametrize("device,expected", [
    ({"current_firmware_version": 332, "update_firmware_version": 332, "firmware_need_update": 0}, False),
    ({"current_firmware_version": 332, "update_firmware_version": 332}, False),
    ({"current_firmware_version": 332, "update_firmware_version": 333, "firmware_need_update": 1}, True),
    ({"current_firmware_version": 332, "update_firmware_version": 333}, True),
    ({"current_firmware_version": "332", "update_firmware_version": "333"}, True),
    ({"current_firmware_version": 332, "update_firmware_version": 332, "firmware_need_update": "1"}, True),
    ({"current_firmware_version": None}, None),
    ({"current_firmware_version": 332}, None),
    ({"current_firmware_version": True, "update_firmware_version": 333}, None),
    ({"current_firmware_version": "bad", "update_firmware_version": 333}, None),
    ({"current_firmware_version": 332, "update_firmware_version": 0}, None),
    ({"firmware_need_update": "0"}, False),
    ({"firmware_need_update": "unknown"}, None),
])
def test_firmware_uses_device_assignment(device, expected):
    assert firmware_update_available(device, 333) is expected


async def test_firmware_attributes_explain_global_default(hass, mock_api_client):
    """Explain the device target next to the server-wide default version."""
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    coordinator.data = {"remi": {**MOCK_REMI_DATA, "current_firmware_version": 332,
                                 "update_firmware_version": 332, "firmware_need_update": 0}}
    coordinator.config_params = {"default_firmware_update_version": 333}
    desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "firmware_update")
    entity = RemiBinarySensorEntity(coordinator, desc)
    assert entity.is_on is False
    assert entity.extra_state_attributes == {"installed_version": 332, "target_version": 332,
        "server_default_version": 333, "update_requested": False, "update_method": "automatic_wifi"}


async def test_firmware_button_performs_reads_only(hass, mock_api_client):
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    coordinator.data = {"remi": MOCK_REMI_DATA, "events": []}
    await RemiCheckFirmwareButton(coordinator).async_press()
    mock_api_client.get_config.assert_awaited_once()
    mock_api_client.get_remi.assert_awaited_once()
    mock_api_client.update_remi.assert_not_awaited()
    mock_api_client.create_event.assert_not_awaited()
    mock_api_client.update_event.assert_not_awaited()


async def test_firmware_button_reports_failed_read(hass, mock_api_client):
    """Report a failed metadata read instead of silently succeeding."""
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    coordinator.data = {"remi": MOCK_REMI_DATA, "events": []}
    mock_api_client.get_config.side_effect = RemiApiError("unreachable")
    with pytest.raises(HomeAssistantError):
        await RemiCheckFirmwareButton(coordinator).async_press()


async def test_metadata_failure_does_not_discard_device_state(hass, mock_api_client):
    """Keep the device and alarm data when the metadata read fails."""
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    mock_api_client.get_config.side_effect = RemiApiError("502")
    result = await coordinator._async_update_data()
    assert result["remi"] == MOCK_REMI_DATA


async def test_failed_metadata_read_waits_before_retrying(hass, mock_api_client):
    """Do not retry a failed firmware metadata read on every poll."""
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    mock_api_client.get_config.side_effect = RemiApiError("502")
    await coordinator._async_update_data()
    await coordinator._async_update_data()
    assert mock_api_client.get_config.await_count == 1

    # The cool-down expires, so the next poll reads the metadata again.
    coordinator._config_retry_at = monotonic() - 1
    await coordinator._async_update_data()
    assert mock_api_client.get_config.await_count == 2


async def test_firmware_button_checks_metadata_during_the_cooldown(hass, mock_api_client):
    """Let the manual firmware check read the metadata despite the cool-down."""
    coordinator = RemiDataUpdateCoordinator(hass, mock_api_client)
    mock_api_client.get_config.side_effect = RemiApiError("502")
    await coordinator._async_update_data()
    assert mock_api_client.get_config.await_count == 1

    mock_api_client.get_config.side_effect = None
    mock_api_client.get_config.return_value = MOCK_CONFIG_DATA
    await RemiCheckFirmwareButton(coordinator).async_press()
    assert mock_api_client.get_config.await_count == 2
    assert coordinator.latest_firmware_version == 110


@pytest.fixture
def api_pair():
    """Return an API client bound to a mocked HTTP session."""
    session = MagicMock(spec=aiohttp.ClientSession)
    client = RemiApiClient("test@example.com", "test", session)
    client.set_remi_id(MOCK_REMI_ID)
    client._session_token = "old_token"
    return client, session


async def test_502_read_is_retried(api_pair):
    """Retry a read that failed with a transient server error."""
    client, session = api_pair
    session.request.side_effect = [_make_response(502, {}), _make_response(200, {"results": []})]
    with patch("custom_components.urbanhello_remi_unofficial.api.asyncio.sleep", new=AsyncMock()):
        assert await client.get_events() == []
    assert session.request.call_count == 2


async def test_reads_stop_after_three_attempts(api_pair):
    """Give up after three attempts instead of retrying forever."""
    client, session = api_pair
    session.request.return_value = _make_response(503, {})
    with patch("custom_components.urbanhello_remi_unofficial.api.asyncio.sleep", new=AsyncMock()):
        with pytest.raises(RemiApiError):
            await client.get_events()
    assert session.request.call_count == 3


@pytest.mark.parametrize("error", [TimeoutError(), aiohttp.ClientConnectionError()])
async def test_transport_read_recovers(api_pair, error):
    """Recover a read that failed with a transport error."""
    client, session = api_pair
    session.request.side_effect = [error, _make_response(200, {"results": []})]
    with patch("custom_components.urbanhello_remi_unofficial.api.asyncio.sleep", new=AsyncMock()):
        assert await client.get_events() == []
    assert session.request.call_args.kwargs["timeout"].total == 15


@pytest.mark.parametrize("operation", ["create", "update", "delete", "device"])
async def test_writes_are_not_replayed_after_502(api_pair, operation):
    """Never replay a device command that failed with a server error."""
    client, session = api_pair
    session.request.return_value = _make_response(502, {})
    with pytest.raises(RemiApiError):
        if operation == "create":
            await client.create_event({"name": "Test"})
        elif operation == "update":
            await client.update_event("event", {"enabled": True})
        elif operation == "delete":
            await client.delete_event("event")
        else:
            await client.update_remi({"volume": 50})
    session.request.assert_called_once()


async def test_relogin_preserves_selected_device(api_pair):
    """Keep the selected device across a re-login."""
    client, session = api_pair
    selected = "second_remi"
    client.set_remi_id(selected)
    session.post.return_value = _make_response(200, MOCK_LOGIN_RESPONSE)
    session.request.side_effect = [_make_response(401, {}), _make_response(200, {"results": []})]
    await client.get_events()
    assert client.remi_id == selected
    session.request.return_value = _make_response(200, {})
    session.request.side_effect = None
    await client.update_remi({"volume": 10})
    assert session.request.call_args.args[1].endswith("/Remi/second_remi")


async def test_wrong_device_response_is_rejected(api_pair):
    """Reject a response describing another device."""
    client, session = api_pair
    session.request.return_value = _make_response(200, {"results": [{"objectId": "wrong"}]})
    with pytest.raises(RemiApiError, match="selected device"):
        await client.get_remi()


async def test_simultaneous_expired_reads_share_one_login(api_pair):
    """Share a single re-login between concurrent expired reads."""
    client, session = api_pair
    both_started = asyncio.Event()
    expired_count = 0

    def response_for_request(*args, **kwargs):
        """Answer expired tokens with a 401 and fresh tokens with data."""
        nonlocal expired_count
        if kwargs["headers"]["X-Parse-Session-Token"] == "old_token":
            expired_count += 1
            if expired_count == 2:
                both_started.set()
            response = _make_response(401, {})

            async def enter():
                """Wait for the second request before answering the 401."""
                await both_started.wait()
                return response

            response.__aenter__ = AsyncMock(side_effect=enter)
            return response
        return _make_response(200, {"results": []})

    session.request.side_effect = response_for_request
    session.post.return_value = _make_response(200, MOCK_LOGIN_RESPONSE)
    await asyncio.wait_for(asyncio.gather(client.get_events(), client.get_events()), timeout=2)
    session.post.assert_called_once()
    assert session.request.call_count == 4


async def test_services_use_current_coordinator_after_reload(hass):
    old = MagicMock()
    current = MagicMock()
    current.events = [{"objectId": "event1"}]
    current.client.update_event = AsyncMock()
    current.async_request_refresh = AsyncMock()
    hass.data[DOMAIN] = {"entry": old}
    _register_services(hass)
    hass.data[DOMAIN]["entry"] = current
    await hass.services.async_call(DOMAIN, "update_alarm", {"event_id": "event1", "enabled": False}, blocking=True)
    current.client.update_event.assert_awaited_once_with("event1", {"enabled": False})
    old.client.update_event.assert_not_called()


async def test_services_refuse_missing_alarm(hass):
    """Refuse an alarm action that targets an unknown alarm."""
    coordinator = MagicMock()
    coordinator.events = []
    hass.data[DOMAIN] = {"entry": coordinator}
    _register_services(hass)
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN, "delete_alarm", {"event_id": "stale"}, blocking=True)
    coordinator.client.delete_event.assert_not_called()


async def test_last_unload_removes_services(hass):
    """Remove the alarm services when the last entry is unloaded."""
    entry = MagicMock(entry_id="entry")
    hass.data[DOMAIN] = {"entry": MagicMock()}
    _register_services(hass)
    with patch.object(hass.config_entries, "async_unload_platforms", return_value=True):
        assert await async_unload_entry(hass, entry)
    assert not hass.services.has_service(DOMAIN, "create_alarm")
