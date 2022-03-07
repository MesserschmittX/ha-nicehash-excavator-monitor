"""A MiningRig that connects several devices."""
from __future__ import annotations

import datetime

import homeassistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Callable, HomeAssistant

from .const import (
    CONFIG_HOST_ADDRESS,
    CONFIG_HOST_PORT,
    CONFIG_NAME,
    CONFIG_UPDATE_INTERVAL,
)
from .data_containers import Algorithm, GraphicsCard, Worker
from .excavator import ExcavatorAPI


class MiningRig:
    """The Rig containing devices"""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Init MiningRig."""
        self._hass = hass
        self._name = config_entry.data[CONFIG_NAME]
        self._id = config_entry.data[CONFIG_NAME].lower()
        self._api = ExcavatorAPI(
            config_entry.data[CONFIG_HOST_ADDRESS], config_entry.data[CONFIG_HOST_PORT]
        )
        self.algorithms = {}
        self.devices = {}
        self.workers = {}
        self.online = True
        self.info = None

        self._callbacks = set()

        self._remove_update_listener = None
        update_interval = config_entry.data.get(CONFIG_UPDATE_INTERVAL)
        self.set_update_interval(hass, update_interval)

    @property
    def mining_rig_id(self) -> str:
        """ID for MiningRig."""
        return self._id

    async def test_connection(self) -> bool:
        """Test connectivity to the MiningRig."""
        self.online = await self._api.test_connection()
        return self.online

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register callback, called when MiningRig updates."""
        self._callbacks.add(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

    async def update(self, event=None) -> None:
        """Update MiningRig via Excavator API."""
        self.algorithms = await self._api.get_algorithms()
        self.devices = await self._api.get_devices()
        self.workers = await self._api.get_workers()
        self.info = await self._api.get_rig_info()
        if self.info is None:
            self.online = False
        else:
            self.online = True
        await self.publish_updates()

    async def publish_updates(self) -> None:
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()

    def set_update_interval(self, hass: HomeAssistant, update_interval: int) -> None:
        """Set new update interval."""
        if self._remove_update_listener:
            self._remove_update_listener()
        self._remove_update_listener = (
            homeassistant.helpers.event.async_track_time_interval(
                hass, self.update, datetime.timedelta(seconds=update_interval)
            )
        )

    def get_algorithm(self, algorithm_id) -> Algorithm | None:
        """Get algorithm by id."""
        if algorithm_id in self.algorithms:
            return self.algorithms[algorithm_id]
        return None

    def get_device(self, device_id) -> GraphicsCard | None:
        """Get device by id."""
        if device_id in self.devices:
            return self.devices[device_id]
        return None

    def get_worker(self, worker_id) -> Worker | None:
        """Get worker by id."""
        if worker_id in self.workers:
            return self.workers[worker_id]
        return None
