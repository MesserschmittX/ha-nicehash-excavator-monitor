"""Nicehash Excavator API"""
from __future__ import annotations

import logging

import aiohttp
from aiohttp.client_reqrep import ClientResponse

from .data_containers import Algorithm, GraphicsCard, RigInfo, Worker

_LOGGER = logging.getLogger(__name__)


class ExcavatorAPI:
    """Excavator API Implementation."""

    def __init__(self, host_address: str, host_port: int) -> None:
        """Init ExcavatorAPI."""
        self.host_address = self.format_host_address(host_address)
        self._host_port = host_port
        self._enable_debug_logging = False

    async def request(self, query: str) -> ClientResponse | None:
        """Excavator API Request"""

        url = f"{self.host_address}:{self._host_port}/api?command={query}"

        if self._enable_debug_logging:
            _LOGGER.info("GET %s", url)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    if response.content:
                        raise Exception(
                            str(response.status)
                            + ": "
                            + response.reason
                            + ": "
                            + str(await response.text())
                        )
                    raise Exception(str(response.status) + ": " + response.reason)
            except Exception:
                if self._enable_debug_logging:
                    _LOGGER.warning("Error while getting data from %s", url)
                return None

    async def test_connection(self) -> bool:
        """Test connectivity"""
        query = '{"id":1,"method":"info","params":[]}'
        response = await self.request(query)
        if response is not None:
            return True
        return False

    async def get_rig_info(self) -> RigInfo | None:
        """Get Rig Information"""
        query = '{"id":1,"method":"info","params":[]}'
        response = await self.request(query)
        if response is not None:
            return RigInfo(response)
        return RigInfo()

    async def get_devices(self) -> dict[int, GraphicsCard] | None:
        """Get the devices"""
        query = '{"id":1,"method":"devices.get","params":[]}'
        response = await self.request(query)
        if response is not None:
            devices = {}
            for device_data in response.get("devices"):
                card = GraphicsCard(device_data)
                devices[card.id] = card
            return devices

    async def get_algorithms(self) -> dict[int, Algorithm] | None:
        """Get the Algorithms"""
        query = '{"id":1,"method":"algorithm.list","params":[]}'
        response = await self.request(query)
        if response is not None:
            algorithms = {}
            for algorithm_data in response.get("algorithms"):
                algorithm = Algorithm(algorithm_data)
                algorithms[algorithm.id] = algorithm
            return algorithms
        return None

    async def get_workers(self) -> dict[int, Worker] | None:
        """Get the workers"""
        query = '{"id":1,"method":"worker.list","params":[]}'
        response = await self.request(query)
        if response is not None:
            workers = {}
            for worker_data in response.get("workers"):
                worker = Worker(worker_data)
                workers[worker.id] = worker
            return workers
        return None

    @staticmethod
    def format_host_address(host_address: str) -> str:
        """Add http if missing"""
        if not host_address.startswith("http://") and not host_address.startswith(
            "https://"
        ):
            host_address = "http://" + host_address
        return host_address

    def set_logging(self, enable: bool) -> None:
        """Enable or disable logging of the made requests"""
        self._enable_debug_logging = enable
