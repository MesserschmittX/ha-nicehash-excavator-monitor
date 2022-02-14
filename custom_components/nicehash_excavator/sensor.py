"""Sensor integration."""
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, POWER_WATT, TEMP_CELSIUS
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

    new_devices.append(OnlineSensor(mining_rig, config_entry))
    new_devices.append(GpuModelsSensor(mining_rig, config_entry))
    new_devices.append(GpuCountSensor(mining_rig, config_entry))
    new_devices.append(TotalPowerSensor(mining_rig, config_entry))
    new_devices.append(CPUSensor(mining_rig, config_entry))
    new_devices.append(RAMSensor(mining_rig, config_entry))

    for card_id in mining_rig.cards.keys():
        new_devices.append(GpuTempSensor(mining_rig, config_entry, card_id))
        new_devices.append(VRAMTempSensor(mining_rig, config_entry, card_id))
        new_devices.append(HotspotTempSensor(mining_rig, config_entry, card_id))
        new_devices.append(OvertemperatureSensor(mining_rig, config_entry, card_id))
        new_devices.append(FanSensor(mining_rig, config_entry, card_id))
        new_devices.append(PowerSensor(mining_rig, config_entry, card_id))
        new_devices.append(ModelSensor(mining_rig, config_entry, card_id))
        new_devices.append(VendorSensor(mining_rig, config_entry, card_id))
    for algorithm_id in mining_rig.algorithms.keys():
        new_devices.append(
            AlgorithmHashrateSensor(mining_rig, config_entry, algorithm_id)
        )
    for worker_id in mining_rig.workers.keys():
        for algorithm_id in mining_rig.workers[worker_id].get("algorithms").keys():
            new_devices.append(
                WorkerAlgorithmHashrateSensor(
                    mining_rig, config_entry, worker_id, algorithm_id
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
    """Base representation of a Rig Sensor."""

    def __init__(self, mining_rig: MiningRig, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, config_entry)

    @property
    def device_info(self) -> any:
        """Information about this entity/device."""
        gpu_models = {}
        for card_id in self._mining_rig.cards.keys():
            gpy_model = self._mining_rig.cards.get(card_id).get("name")
            if gpy_model in gpu_models:
                gpu_count = gpu_models[gpy_model]
                gpu_models[gpy_model] = gpu_count + 1
            else:
                gpu_models[gpy_model] = 1

        model_string = ""
        for card in gpu_models.keys():
            if model_string:
                model_string = model_string + "; " + str(gpu_models[card]) + "x " + card
            else:
                model_string = str(gpu_models[card]) + "x " + card

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
        self, mining_rig: MiningRig, config_entry: ConfigEntry, card_id: any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, card_id, config_entry)
        self._attr_unique_id = f"{self._rig_name}_{self._card_uuid}_temp"
        self._attr_name = f"{self._rig_name} {self._card_name} GPU"

    @property
    def state(self) -> float:
        return self._mining_rig.cards.get(self._card_id).get("gpu_temp")


class VRAMTempSensor(CardSensorBase):
    """VRAM temp Sensor."""

    device_class = SensorDeviceClass.TEMPERATURE
    _attr_unit_of_measurement = TEMP_CELSIUS

    def __init__(
        self, mining_rig: MiningRig, config_entry: ConfigEntry, _card_id: any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, _card_id, config_entry)
        self._attr_unique_id = f"{self._rig_name}_{self._card_uuid}_vram_temp"
        self._attr_name = f"{self._rig_name} {self._card_name} VRAM"

    @property
    def state(self) -> float:
        return self._mining_rig.cards.get(self._card_id).get("__vram_temp")


class HotspotTempSensor(CardSensorBase):
    """Hotspot Sensor."""

    device_class = SensorDeviceClass.TEMPERATURE
    _attr_unit_of_measurement = TEMP_CELSIUS

    def __init__(
        self, mining_rig: MiningRig, config_entry: ConfigEntry, _card_id: any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, _card_id, config_entry)
        self._attr_unique_id = f"{self._rig_name}_{self._card_uuid}_hotspot_temp"
        self._attr_name = f"{self._rig_name} {self._card_name} Hotspot"

    @property
    def state(self) -> float:
        return self._mining_rig.cards.get(self._card_id).get("__hotspot_temp")


class FanSensor(CardSensorBase):
    """Fan Sensor."""

    _attr_unit_of_measurement = PERCENTAGE

    def __init__(
        self, mining_rig: MiningRig, config_entry: ConfigEntry, _card_id: any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, _card_id, config_entry)
        self._attr_unique_id = f"{self._rig_name}_{self._card_uuid}_fan"
        self._attr_name = f"{self._rig_name} {self._card_name} Fan"

    @property
    def state(self) -> float:
        return self._mining_rig.cards.get(self._card_id).get("gpu_fan_speed")


class OvertemperatureSensor(CardSensorBase):
    """Overtemp Sensor."""

    def __init__(
        self, mining_rig: MiningRig, config_entry: ConfigEntry, _card_id: any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, _card_id, config_entry)
        self._attr_unique_id = f"{self._rig_name}_{self._card_uuid}_overtemp"
        self._attr_name = f"{self._rig_name} {self._card_name} Overtemp"

    @property
    def state(self) -> bool:
        return self._mining_rig.cards.get(self._card_id).get("too_hot")


class PowerSensor(CardSensorBase):
    """Power Sensor."""

    device_class = SensorDeviceClass.POWER
    _attr_unit_of_measurement = POWER_WATT

    def __init__(
        self, mining_rig: MiningRig, config_entry: ConfigEntry, _card_id: any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, _card_id, config_entry)
        self._attr_unique_id = f"{self._rig_name}_{self._card_uuid}_power"
        self._attr_name = f"{self._rig_name} {self._card_name} Power"

    @property
    def state(self) -> float:
        return self._mining_rig.cards.get(self._card_id).get("gpu_power_usage")


class ModelSensor(CardSensorBase):
    """Model Sensor."""

    def __init__(
        self, mining_rig: MiningRig, config_entry: ConfigEntry, _card_id: any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, _card_id, config_entry)
        self._attr_unique_id = f"{self._rig_name}_{self._card_uuid}_gpu_model"
        self._attr_name = f"{self._rig_name} {self._card_name} GPU Model"

    @property
    def state(self) -> str:
        return self._mining_rig.cards.get(self._card_id).get("name")


class VendorSensor(CardSensorBase):
    """Vendor Sensor."""

    def __init__(
        self, mining_rig: MiningRig, config_entry: ConfigEntry, _card_id: any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, _card_id, config_entry)
        self._attr_unique_id = f"{self._rig_name}_{self._card_uuid}_vendor_id"
        self._attr_name = f"{self._rig_name} {self._card_name} Vendor ID"

    @property
    def state(self) -> str:
        return self._mining_rig.cards.get(self._card_id).get("subvendor")


class WorkerAlgorithmHashrateSensor(CardSensorBase):
    """Hashrate Sensor per GPU and Algorithm ."""

    _attr_unit_of_measurement = "Mh/s"

    def __init__(
        self,
        mining_rig: MiningRig,
        config_entry: ConfigEntry,
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
        self._attr_unique_id = f'{self._rig_name}_{self._card_uuid}_{self._mining_rig.workers.get(self._card_id).get("algorithms").get(self._algorithm_id).get("name")}'
        self._attr_name = f'{self._rig_name} {self._card_name} {self._mining_rig.workers.get(self._card_id).get("algorithms").get(self._algorithm_id).get("name")}'

    @property
    def state(self) -> float:
        if self._mining_rig.workers.get(self._card_id, None):
            return round(
                self._mining_rig.workers.get(self._card_id)
                .get("algorithms")
                .get(self._algorithm_id)
                .get("speed")
                / 1000000,
                2,
            )
        return "Unavailable"


class AlgorithmHashrateSensor(RigSensor):
    """Hashrate Sensor per Algorithm."""

    _attr_unit_of_measurement = "Mh/s"

    def __init__(
        self, mining_rig: MiningRig, config_entry: ConfigEntry, algorithm_id: any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, config_entry)
        self._algorithm_id = algorithm_id
        self._attr_unique_id = f'{self._rig_name}_{self._mining_rig.algorithms.get(self._algorithm_id).get("name")}_hashrate'
        self._attr_name = f'{self._rig_name} {self._mining_rig.algorithms.get(self._algorithm_id).get("name")}'

    @property
    def state(self) -> float:
        if self._mining_rig.algorithms.get(self._algorithm_id, None):
            return round(
                self._mining_rig.algorithms.get(self._algorithm_id).get("speed")
                / 1000000,
                2,
            )
        return "Unavailable"


class OnlineSensor(RigSensor):
    """Online Sensor"""

    def __init__(self, mining_rig: MiningRig, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, config_entry)
        self._attr_unique_id = f"{self._rig_name}_status"
        self._attr_name = f"{self._rig_name} status"

    @property
    def state(self) -> str:
        return "Online" if self._mining_rig.online else "Offline"


class GpuModelsSensor(RigSensor):
    """Gpu models Sensor"""

    def __init__(self, mining_rig: MiningRig, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, config_entry)
        self._attr_unique_id = f"{self._rig_name}_gpu_models"
        self._attr_name = f"{self._rig_name} GPU models"

    @property
    def state(self) -> str:
        cards = ""
        for card_id in self._mining_rig.cards.keys():
            cards += (
                self._mining_rig.cards.get(card_id).get("name").replace("GeForce ", "")
                + ", "
            )
        return cards[:-2] if len(cards[:-2]) <= 255 else "value to long"


class GpuCountSensor(RigSensor):
    """Gpu count Sensor"""

    def __init__(self, mining_rig: MiningRig, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, config_entry)
        self._attr_unique_id = f"{self._rig_name}_gpu_count"
        self._attr_name = f"{self._rig_name} GPU count"

    @property
    def state(self) -> int:
        return len(self._mining_rig.cards)


class TotalPowerSensor(RigSensor):
    """Miner Power Sensor."""

    device_class = SensorDeviceClass.POWER
    _attr_unit_of_measurement = POWER_WATT

    def __init__(self, mining_rig: MiningRig, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, config_entry)
        self._attr_unique_id = f"{self._rig_name}_power"
        self._attr_name = f"{self._rig_name} Power"

    @property
    def state(self) -> float:
        power = 0
        for card_id in self._mining_rig.cards.keys():
            power += self._mining_rig.cards.get(card_id).get("gpu_power_usage")
        return power


class CPUSensor(RigSensor):
    """CPU Sensor."""

    _attr_unit_of_measurement = PERCENTAGE

    def __init__(self, mining_rig: MiningRig, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, config_entry)
        self._attr_unique_id = f"{self._rig_name}_cpu"
        self._attr_name = f"{self._rig_name} CPU"

    @property
    def state(self) -> float:
        return round(self._mining_rig.info.get("cpu_load"), 2)


class RAMSensor(RigSensor):
    """RAM Sensor."""

    _attr_unit_of_measurement = PERCENTAGE

    def __init__(self, mining_rig: MiningRig, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, config_entry)
        self._attr_unique_id = f"{self._rig_name}_ram"
        self._attr_name = f"{self._rig_name} RAM"

    @property
    def state(self) -> float:
        return round(self._mining_rig.info.get("ram_load"))
