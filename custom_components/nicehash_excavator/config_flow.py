"""Config flow for Nicehash Excavator integration."""
from __future__ import annotations

import logging
from typing import Any

from aiohttp.client_exceptions import ClientConnectorError
import voluptuous as vol
from voluptuous.validators import All, Range

from homeassistant import exceptions
from homeassistant.config_entries import (
    CONN_CLASS_LOCAL_PUSH,
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONFIG_HOST_ADRESS,
    CONFIG_HOST_PORT,
    CONFIG_NAME,
    CONFIG_UPDATE_INTERVAL,
    DEFAULT_HOST_PORT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_PORT,
    ERROR_NO_RESPONSE,
    ERROR_UNKNOWN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)
from .excavator import ExcavatorAPI

_LOGGER = logging.getLogger(__name__)

MAIN_DATA_SCHEMA = {
    vol.Required(CONFIG_NAME): str,
    vol.Required(CONFIG_HOST_ADRESS): str,
    vol.Required(CONFIG_HOST_PORT, default=DEFAULT_HOST_PORT): int,
    vol.Required(CONFIG_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): All(
        int, Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL)
    ),
}


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input"""

    if data[CONFIG_HOST_PORT] < 1 or data[CONFIG_HOST_PORT] > 65535:
        raise InvalidPort

    excavator = ExcavatorAPI(data[CONFIG_HOST_ADRESS], data[CONFIG_HOST_PORT])

    result = await excavator.test_connection()
    if not result:
        raise NoResponse

    return {
        "title": data[CONFIG_NAME],
        CONFIG_NAME: data[CONFIG_NAME],
        CONFIG_HOST_ADRESS: data[CONFIG_HOST_ADRESS],
        CONFIG_HOST_PORT: data[CONFIG_HOST_PORT],
        CONFIG_UPDATE_INTERVAL: data[CONFIG_UPDATE_INTERVAL],
    }


class MainConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nicehash Excavator Integration."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""

        errors = {}
        if user_input is not None:
            try:
                validated_input = await validate_input(self.hass, user_input)
                return self.async_create_entry(
                    title=validated_input["title"], data=user_input
                )

            except NoResponse as err:
                _LOGGER.error(err)
                errors["base"] = ERROR_NO_RESPONSE
            except InvalidPort as err:
                _LOGGER.error(err)
                errors[CONFIG_HOST_PORT] = ERROR_INVALID_PORT
            except ClientConnectorError as err:
                _LOGGER.error(err)
                errors[CONFIG_HOST_ADRESS] = ERROR_CANNOT_CONNECT
                errors[CONFIG_HOST_PORT] = ERROR_CANNOT_CONNECT
            except Exception as err:
                _LOGGER.error(err)
                errors["base"] = ERROR_UNKNOWN

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
        if user_input is not None:
            new = {**self.config_entry.data}
            new[CONFIG_UPDATE_INTERVAL] = user_input[CONFIG_UPDATE_INTERVAL]
            self.hass.config_entries.async_update_entry(self.config_entry, data=new)
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONFIG_UPDATE_INTERVAL,
                        default=self.config_entry.data.get(CONFIG_UPDATE_INTERVAL),
                    ): All(int, Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL))
                }
            ),
        )


class NoResponse(exceptions.HomeAssistantError):
    """Error to indicate no response was received."""


class InvalidPort(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid port."""
