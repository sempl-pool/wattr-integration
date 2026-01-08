"""Config flow for the wattr integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import selector

from .api import WattrApi
from .const import CONF_LINKED_SENSOR, DOMAIN

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_DEVICE_ID): str,
        vol.Optional("add_linked_sensor", default=False): bool,
    }
)
STEP_SENSOR_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_LINKED_SENSOR): selector({"entity": {"domain": "sensor"}}),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Create API client with the provided credentials
    api = WattrApi(hass, data)

    try:
        # Validate the API key and device ID combination
        if not await api.check_token():
            raise InvalidAuth
    except (aiohttp.ClientError, ConnectionError) as err:
        _LOGGER.error("Connection error during token validation: %s", err)
        raise CannotConnect from err

    # Return info that you want to store in the config entry.
    return {"title": "Wattr Pool Controller"}


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for wattr."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        _LOGGER.debug(
            "STEP_USER_DATA_SCHEMA keys: %s", list(STEP_USER_DATA_SCHEMA.schema.keys())
        )

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                self._user_data = user_input
                # Check if user wants to add a linked sensor
                if user_input.get("add_linked_sensor", False):
                    return await self.async_step_linked_sensor()
                # Skip sensor step and create entry directly
                # Filter out UI-only fields
                clean_data = {k: v for k, v in user_input.items()
                             if k not in ("add_linked_sensor",)}
                return self.async_create_entry(title="Wattr Pool Controller", data=clean_data)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_linked_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the linked sensor step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # merge step 1 data with step 2 data, but exclude UI-only fields
            step1_data = {k: v for k, v in self._user_data.items()
                         if k not in ("add_linked_sensor",)}
            data = {**step1_data, **user_input}
            return self.async_create_entry(title="Wattr Pool Controller", data=data)

        return self.async_show_form(
            step_id="linked_sensor",
            data_schema=STEP_SENSOR_DATA_SCHEMA,
            errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
