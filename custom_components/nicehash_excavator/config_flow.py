"""Config flow for Nicehash Excavator integration."""
from __future__ import annotations

import logging

from aiohttp.client_exceptions import ClientConnectorError
import voluptuous as vol

from homeassistant.config_entries import (
    CONN_CLASS_LOCAL_PUSH,
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONFIG_HOST_ADDRESS,
    CONFIG_HOST_PORT,
    CONFIG_NAME,
    CONFIG_UPDATE_INTERVAL,
    CONFIG_UPDATE_INTERVAL_FAST,
    DEFAULT_HOST_PORT,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL_FAST,
    DOMAIN,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_PORT,
    ERROR_INVALID_UPDATE_INTERVAL,
    ERROR_NO_RESPONSE,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)
from .excavator import ExcavatorAPI

_LOGGER = logging.getLogger(__name__)

MAIN_DATA_SCHEMA = {
    vol.Required(CONFIG_NAME): str,
    vol.Required(CONFIG_HOST_ADDRESS): str,
    vol.Required(CONFIG_HOST_PORT, default=DEFAULT_HOST_PORT): int,
    vol.Required(CONFIG_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): int,
    vol.Required(
        CONFIG_UPDATE_INTERVAL_FAST, default=DEFAULT_UPDATE_INTERVAL_FAST
    ): int,
}


async def get_errors(data: dict) -> dict[str, any]:
    """Validate the user input"""
    errors = await validate_update_intervals(data)

    if data[CONFIG_HOST_PORT] < 1 or data[CONFIG_HOST_PORT] > 65535:
        _LOGGER.error(ERROR_INVALID_PORT)
        errors[CONFIG_HOST_PORT] = ERROR_INVALID_PORT

    try:
        excavator = ExcavatorAPI(data[CONFIG_HOST_ADDRESS], data[CONFIG_HOST_PORT])
        result = await excavator.test_connection()
        if not result:
            _LOGGER.error(ERROR_NO_RESPONSE)
            errors["base"] = ERROR_NO_RESPONSE
    except ClientConnectorError as err:
        _LOGGER.error(err)
        errors[CONFIG_HOST_ADDRESS] = ERROR_CANNOT_CONNECT
        errors[CONFIG_HOST_PORT] = ERROR_CANNOT_CONNECT

    return errors


async def validate_update_intervals(data: dict) -> dict[str, any]:
    """Validate the user input"""
    errors = {}
    if (
        data[CONFIG_UPDATE_INTERVAL] < MIN_UPDATE_INTERVAL
        or data[CONFIG_UPDATE_INTERVAL] > MAX_UPDATE_INTERVAL
    ):
        _LOGGER.error(ERROR_INVALID_UPDATE_INTERVAL)
        errors[CONFIG_UPDATE_INTERVAL] = ERROR_INVALID_UPDATE_INTERVAL

    if (
        data[CONFIG_UPDATE_INTERVAL_FAST] < MIN_UPDATE_INTERVAL
        or data[CONFIG_UPDATE_INTERVAL_FAST] > MAX_UPDATE_INTERVAL
    ):
        _LOGGER.error(ERROR_INVALID_UPDATE_INTERVAL)
        errors[CONFIG_UPDATE_INTERVAL_FAST] = ERROR_INVALID_UPDATE_INTERVAL

    return errors


class MainConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nicehash Excavator Integration."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""

        errors = {}
        if user_input is not None:
            errors = await get_errors(user_input)
            if not errors:
                return self.async_create_entry(
                    title=user_input[CONFIG_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(MAIN_DATA_SCHEMA), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowHandler:
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    """Class for the Options Handler"""

    def __init__(self, config_entry: ConfigEntry) -> None:
        super().__init__()
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""
        errors = {}
        if user_input is not None:
            errors = await get_errors(user_input)
            if not errors:
                new = {**self.config_entry.data}
                new[CONFIG_HOST_ADDRESS] = user_input[CONFIG_HOST_ADDRESS]
                new[CONFIG_HOST_PORT] = user_input[CONFIG_HOST_PORT]
                new[CONFIG_UPDATE_INTERVAL] = user_input[CONFIG_UPDATE_INTERVAL]
                new[CONFIG_UPDATE_INTERVAL_FAST] = user_input[
                    CONFIG_UPDATE_INTERVAL_FAST
                ]
                self.hass.config_entries.async_update_entry(self.config_entry, data=new)
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONFIG_HOST_ADDRESS,
                        default=self.config_entry.data.get(CONFIG_HOST_ADDRESS),
                    ): str,
                    vol.Required(
                        CONFIG_HOST_PORT,
                        default=self.config_entry.data.get(CONFIG_HOST_PORT),
                    ): int,
                    vol.Required(
                        CONFIG_UPDATE_INTERVAL,
                        default=self.config_entry.data.get(CONFIG_UPDATE_INTERVAL),
                    ): int,
                    vol.Required(
                        CONFIG_UPDATE_INTERVAL_FAST,
                        default=self.config_entry.data.get(CONFIG_UPDATE_INTERVAL_FAST),
                    ): int,
                }
            ),
            errors=errors,
        )
