"""Switch integration."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONFIG_NAME,
    CONFIG_UPDATE_INTERVAL,
    CONFIG_UPDATE_INTERVAL_FAST,
    DOMAIN,
)
from .mining_rig import MiningRig


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the switch."""

    mining_rig: MiningRig = hass.data[DOMAIN][config_entry.entry_id]

    switch = RequestRateSwitch(hass, mining_rig, config_entry)

    async_add_entities([switch])


class RequestRateSwitch(SwitchEntity):
    """Representation of a switch that can be toggled."""

    def __init__(
        self, hass: HomeAssistant, mining_rig: MiningRig, config_entry: ConfigEntry
    ) -> None:
        """Initialize the switch."""
        self._hass = hass
        self._mining_rig = mining_rig
        self._config_entry = config_entry
        self._rig_name = config_entry.data.get(CONFIG_NAME)
        self._state = False

    @property
    def name(self):
        """Return the name of the switch."""
        return self._rig_name + " fast update"

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    async def async_turn_on(self, **args):
        """Turn the device on."""
        update_interval = self._config_entry.data.get(CONFIG_UPDATE_INTERVAL_FAST)
        self._mining_rig.set_update_interval(self._hass, update_interval)
        self._state = True

    async def async_turn_off(self, **args):
        """Turn the device off."""
        update_interval = self._config_entry.data.get(CONFIG_UPDATE_INTERVAL)
        self._mining_rig.set_update_interval(self._hass, update_interval)
        self._state = False
