"""Nicehash Excavator API"""
from __future__ import annotations

import logging

import aiohttp
from aiohttp.client_reqrep import ClientResponse

_LOGGER = logging.getLogger(__name__)


class ExcavatorAPI:
    """Excavator API Implementation."""

    def __init__(self, host_adress: str, host_port: int) -> None:
        """Init ExcavatorAPI."""
        self._host_adress = self.format_host_adress(host_adress)
        self._host_port = host_port
        self._enable_loggigng = False

    async def request(self, querry: str) -> ClientResponse | None:
        """Excavator API Request"""

        url = f"{self._host_adress}:{self._host_port}/api?command={querry}"

        if self._enable_loggigng:
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
                _LOGGER.warning("Error while getting data from %s", url)

    async def test_connection(self) -> bool:
        """Test connectivity"""
        querry = '{"id":1,"method":"info","params":[]}'
        response = await self.request(querry)
        if response is not None:
            return True
        return False

    async def get_rig_info(self) -> ClientResponse | None:
        """Get Rig Information"""
        querry = '{"id":1,"method":"info","params":[]}'
        response = await self.request(querry)
        if response is not None:
            return response
        return None

    async def get_devices(self) -> ClientResponse | None:
        """Get the devices"""
        querry = '{"id":1,"method":"devices.get","params":[]}'
        response = await self.request(querry)
        if response is not None:
            devices = {}
            for device in response.get("devices"):
                devices[device.get("device_id")] = device
            return devices

    async def get_algorithms(self) -> ClientResponse | None:
        """Get the Algorithms"""
        querry = '{"id":1,"method":"algorithm.list","params":[]}'
        response = await self.request(querry)
        if response is not None:
            algorithms = {}
            for algorithm in response.get("algorithms"):
                algorithms[algorithm.get("algorithm_id")] = algorithm
            return algorithms

    async def get_workers(self) -> ClientResponse | None:
        """Get the workers"""
        querry = '{"id":1,"method":"worker.list","params":[]}'
        response = await self.request(querry)
        if response is not None:
            workers = {}
            for worker in response.get("workers"):
                algorithms = {}
                for algorithm in worker.get("algorithms"):
                    algorithms[algorithm.get("id")] = algorithm
                worker["algorithms"] = algorithms
                workers[worker.get("worker_id")] = worker
            return workers

    @staticmethod
    def format_host_adress(host_adress: str) -> str:
        """Add http if missing"""
        if not host_adress.startswith("http://") and not host_adress.startswith(
            "https://"
        ):
            host_adress = "http://" + host_adress
        return host_adress

    def set_logging(self, enable: bool) -> None:
        """Enable or disable logging of the made requests"""
        self._enable_loggigng = enable
