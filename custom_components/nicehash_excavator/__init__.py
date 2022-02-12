"""Nicehash Excavator integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONFIG_UPDATE_INTERVAL, DOMAIN
from .mining_rig import MiningRig

_LOGGER = logging.getLogger(__name__)


PLATFORMS = [Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up from a config entry."""

    mining_rig = MiningRig(hass, config_entry)
    await mining_rig.update()

    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = mining_rig

    config_entry.async_on_unload(config_entry.add_update_listener(update_config))

    hass.config_entries.async_setup_platforms(config_entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)
    return unload_ok


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:

        new = {**config_entry.data}
        # TODO_: modify Config Entry data

        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True


async def update_config(hass, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    mining_rig: MiningRig = hass.data[DOMAIN][config_entry.entry_id]
    update_interval = config_entry.data.get(CONFIG_UPDATE_INTERVAL)
    mining_rig.set_update_interval(hass, update_interval)
