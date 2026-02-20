"""Config flow for the UrbanHello Remi integration."""
from __future__ import annotations

import logging
from typing import Any
import uuid

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RemiApiClient, RemiAuthError, RemiApiError
from .const import CONF_INSTALLATION_ID, CONF_REMI_ID, CONF_SESSION_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class RemiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UrbanHello Remi."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._username: str = ""
        self._password: str = ""
        self._session_token: str = ""
        self._installation_id: str = ""
        self._all_remi_ids: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            installation_id = str(uuid.uuid4())
            client = RemiApiClient(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                session,
                installation_id,
            )
            try:
                session_token, current_remi_id, all_remi_ids = await client.login()
            except RemiAuthError:
                errors["base"] = "invalid_auth"
            except RemiApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during Remi login")
                errors["base"] = "unknown"
            else:
                self._username = user_input[CONF_USERNAME]
                self._password = user_input[CONF_PASSWORD]
                self._session_token = session_token
                self._installation_id = installation_id
                self._all_remi_ids = all_remi_ids

                if len(all_remi_ids) == 1:
                    return await self._async_create_entry(all_remi_ids[0])

                return await self.async_step_device()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle device selection when multiple Remis are on the account."""
        if user_input is not None:
            return await self._async_create_entry(user_input[CONF_REMI_ID])

        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_REMI_ID): vol.In(self._all_remi_ids),
                }
            ),
        )

    async def _async_create_entry(self, remi_id: str) -> ConfigFlowResult:
        """Create the config entry for the selected Remi device."""
        await self.async_set_unique_id(remi_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"Remi ({self._username})"
            if len(self._all_remi_ids) == 1
            else f"Remi {remi_id} ({self._username})",
            data={
                CONF_USERNAME: self._username,
                CONF_PASSWORD: self._password,
                CONF_REMI_ID: remi_id,
                CONF_SESSION_TOKEN: self._session_token,
                CONF_INSTALLATION_ID: self._installation_id,
            },
        )
