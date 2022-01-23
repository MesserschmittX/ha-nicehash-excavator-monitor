"""Platform for sensor integration."""
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

from .const import CONFIG_NAME, DOMAIN
from .mining_rig import MiningRig


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Add sensors for passed config_entry in HA."""

    mining_rig: MiningRig = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []

    for card_id in mining_rig.cards.keys():
        new_devices.append(GpuTempSensor(config_entry, mining_rig, card_id))
        new_devices.append(VRAMTempSensor(config_entry, mining_rig, card_id))
        new_devices.append(HotspotTempSensor(config_entry, mining_rig, card_id))
        new_devices.append(OvertemperatureSensor(config_entry, mining_rig, card_id))
    for algorithm_id in mining_rig.algorithms.keys():
        new_devices.append(
            AlgorithmHashrateSensor(config_entry, mining_rig, algorithm_id)
        )
    for worker_id in mining_rig.workers.keys():
        for algorithm_id in mining_rig.workers[worker_id].get("algorithms").keys():
            new_devices.append(
                WorkerAlgorithmHashrateSensor(
                    config_entry, mining_rig, worker_id, algorithm_id
                )
            )
    if new_devices:
        async_add_entities(new_devices)


class SensorBase(Entity):
    """Base representation of a Sensor."""

    should_poll = False

    def __init__(self, mining_rig: MiningRig, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._rig_name = config_entry.data.get(CONFIG_NAME)
        self._mining_rig = mining_rig

    @property
    def available(self) -> bool:
        """Return True if mining rig is available."""
        return self._mining_rig.online

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._mining_rig.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        self._mining_rig.remove_callback(self.async_write_ha_state)


class RigSensor(SensorBase):
    """Base representation of a Graphics card Sensor."""

    def __init__(self, mining_rig: MiningRig, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, config_entry)

    @property
    def device_info(self) -> any:
        """Information about this entity/device."""
        gpu_types = {}
        for card_id in self._mining_rig.cards.keys():
            gpy_type = self._mining_rig.cards.get(card_id).get("name")
            if gpy_type in gpu_types:
                gpu_count = gpu_types[gpy_type]
                gpu_types[gpy_type] = gpu_count + 1
            else:
                gpu_types[gpy_type] = 1

        model_string = ""
        for card in gpu_types.keys():
            if model_string:
                model_string = model_string + "; " + str(gpu_types[card]) + "x " + card
            else:
                model_string = str(gpu_types[card]) + "x " + card

        return {
            "identifiers": {
                (
                    DOMAIN,
                    f"{self._rig_name} Excavator",
                )
            },
            "name": f"{self._rig_name}",
            "sw_version": f"{self._mining_rig.info.get('version')}, Build: {self._mining_rig.info.get('build_number')}",
            "uptime": f"{self._mining_rig.info.get('uptime') / 60 / 60}h",
            "model": model_string,
            "manufacturer": "NiceHash",
        }


class CardSensorBase(SensorBase):
    """Base representation of a Graphics card Sensor."""

    def __init__(
        self, mining_rig: MiningRig, card_id: any, config_entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, config_entry)
        self._card_id = card_id
        self._card_name = (
            f"GPU {self._mining_rig.cards.get(self._card_id).get('device_id')}"
        )
        self._card_uuid = self._mining_rig.cards.get(self._card_id).get("uuid")

    @property
    def device_info(self) -> any:
        """Information about this entity/device."""

        return {
            "identifiers": {
                (
                    DOMAIN,
                    self._card_uuid,
                )
            },
            "name": self._card_name,
            "model": self._mining_rig.cards.get(self._card_id).get("name"),
            "manufacturer": self._mining_rig.cards.get(self._card_id).get("subvendor"),
            "via_device": (
                DOMAIN,
                f"{self._rig_name} Excavator",
            ),
        }


class GpuTempSensor(CardSensorBase):
    """GPU temp sensor."""

    device_class = SensorDeviceClass.TEMPERATURE
    _attr_unit_of_measurement = TEMP_CELSIUS

    def __init__(
        self, config_entry: ConfigEntry, mining_rig: MiningRig, card_id: any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, card_id, config_entry)
        self._attr_unique_id = f"{self._card_uuid}_temp"
        self._attr_name = f"{self._rig_name} {self._card_name} GPU"

    @property
    def state(self) -> float:
        """Return the state of the sensor."""
        return self._mining_rig.cards.get(self._card_id).get("gpu_temp")


class VRAMTempSensor(CardSensorBase):
    """VRAM temp Sensor."""

    device_class = SensorDeviceClass.TEMPERATURE
    _attr_unit_of_measurement = TEMP_CELSIUS

    def __init__(
        self, config_entry: ConfigEntry, mining_rig: MiningRig, _card_id: any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, _card_id, config_entry)
        self._attr_unique_id = f"{self._card_uuid}_vram_temp"
        self._attr_name = f"{self._rig_name} {self._card_name} VRAM"

    @property
    def state(self) -> float:
        """Return the state of the sensor."""
        return self._mining_rig.cards.get(self._card_id).get("__vram_temp")


class HotspotTempSensor(CardSensorBase):
    """Hotspot Sensor."""

    device_class = SensorDeviceClass.TEMPERATURE
    _attr_unit_of_measurement = TEMP_CELSIUS

    def __init__(
        self, config_entry: ConfigEntry, mining_rig: MiningRig, _card_id: any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, _card_id, config_entry)
        self._attr_unique_id = f"{self._card_uuid}_Hotspot_Temp"
        self._attr_name = f"{self._rig_name} {self._card_name} Hotspot"

    @property
    def state(self) -> float:
        """Return the state of the sensor."""
        return self._mining_rig.cards.get(self._card_id).get("__hotspot_temp")


class OvertemperatureSensor(CardSensorBase):
    """Overtemp Sensor."""

    def __init__(
        self, config_entry: ConfigEntry, mining_rig: MiningRig, _card_id: any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, _card_id, config_entry)
        self._attr_unique_id = f"{self._card_uuid}_overtemp"
        self._attr_name = f"{self._rig_name} {self._card_name} Overtemp"

    @property
    def state(self) -> bool:
        """Return the state of the sensor."""
        return self._mining_rig.cards.get(self._card_id).get("too_hot")


class WorkerAlgorithmHashrateSensor(CardSensorBase):
    """Hashrate Sensor per GPU and Algorithm ."""

    _attr_unit_of_measurement = "Mh/s"

    def __init__(
        self,
        config_entry: ConfigEntry,
        mining_rig: MiningRig,
        worker_id: any,
        algorithm_id: any,
    ) -> None:
        """Initialize the sensor."""
        for card_id in mining_rig.cards.keys():
            if mining_rig.cards.get(card_id).get("device_id") == mining_rig.workers.get(
                worker_id
            ).get("device_id"):
                self._card_id = card_id
                break

        super().__init__(mining_rig, self._card_id, config_entry)
        self._worker_id = worker_id
        self._algorithm_id = algorithm_id
        self._attr_unique_id = f'{self._card_uuid}_{self._mining_rig.workers.get(self._card_id).get("algorithms").get(self._algorithm_id).get("name")}'
        self._attr_name = f'{self._rig_name} {self._card_name} {self._mining_rig.workers.get(self._card_id).get("algorithms").get(self._algorithm_id).get("name")}'

    @property
    def state(self) -> float:
        """Return the state of the sensor."""

        return round(
            self._mining_rig.workers.get(self._card_id)
            .get("algorithms")
            .get(self._algorithm_id)
            .get("speed")
            / 1000000,
            2,
        )


class AlgorithmHashrateSensor(RigSensor):
    """Hashrate Sensor per Algorithm."""

    _attr_unit_of_measurement = "Mh/s"

    def __init__(
        self, config_entry: ConfigEntry, mining_rig: MiningRig, algorithm_id: any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, config_entry)
        self._algorithm_id = algorithm_id
        self._attr_unique_id = f'{self._rig_name}_{self._mining_rig.algorithms.get(self._algorithm_id).get("name")}_hashrate'
        self._attr_name = f'{self._rig_name} {self._mining_rig.algorithms.get(self._algorithm_id).get("name")}'

    @property
    def state(self) -> float:
        """Return the state of the sensor."""
        return round(
            self._mining_rig.algorithms.get(self._algorithm_id).get("speed") / 1000000,
            2,
        )


class OnlineSensor(RigSensor):
    """Online Sensor"""

    def __init__(self, config_entry: ConfigEntry, mining_rig: MiningRig) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, config_entry)
        self._attr_unique_id = f"{self._rig_name}_status"
        self._attr_name = f"{self._rig_name} status"

    @property
    def state(self) -> float:
        """Return the state of the sensor."""
        return "Online" if self._mining_rig.online else "Offline"
