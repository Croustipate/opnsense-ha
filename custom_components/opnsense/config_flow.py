"""Config flow for the OPNsense integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OpnsenseAuthError, OpnsenseClient, OpnsenseConnectionError
from .const import CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL, DOMAIN

CONF_API_SECRET = "api_secret"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_API_SECRET): str,
        vol.Required(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
)


class OpnsenseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for OPNsense."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(
                self.hass, verify_ssl=user_input[CONF_VERIFY_SSL]
            )
            client = OpnsenseClient(
                session,
                user_input[CONF_HOST],
                user_input[CONF_API_KEY],
                user_input[CONF_API_SECRET],
            )
            try:
                await client.async_get_status()
            except OpnsenseAuthError:
                errors["base"] = "invalid_auth"
            except OpnsenseConnectionError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_HOST], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
