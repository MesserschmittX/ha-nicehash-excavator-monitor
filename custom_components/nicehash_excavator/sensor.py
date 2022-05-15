"""Sensor integration."""
import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, POWER_WATT, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

from .const import CONFIG_ENABLE_DEBUG_LOGGING, CONFIG_NAME, DOMAIN
from .mining_rig import MiningRig

_LOGGER = logging.getLogger(__name__)


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

    for device_id in mining_rig.devices:
        new_devices.append(GpuTempSensor(mining_rig, config_entry, device_id))
        new_devices.append(VRAMTempSensor(mining_rig, config_entry, device_id))
        new_devices.append(HotspotTempSensor(mining_rig, config_entry, device_id))
        new_devices.append(OvertempSensor(mining_rig, config_entry, device_id))
        new_devices.append(FanSensor(mining_rig, config_entry, device_id))
        new_devices.append(PowerSensor(mining_rig, config_entry, device_id))
        new_devices.append(ModelSensor(mining_rig, config_entry, device_id))
        new_devices.append(VendorSensor(mining_rig, config_entry, device_id))

    for algorithm_id in mining_rig.algorithms:
        new_devices.append(
            AlgorithmHashrateSensor(mining_rig, config_entry, algorithm_id)
        )

    for worker_id in mining_rig.workers:
        for algorithm_id in mining_rig.get_worker(worker_id).algorithms:
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
        try:
            self._enable_debug_logging = config_entry.data[CONFIG_ENABLE_DEBUG_LOGGING]
        except KeyError:
            self._enable_debug_logging = False

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

    @property
    def device_info(self) -> any:
        """Information about this entity/device."""

        info = {
            "identifiers": {
                (
                    DOMAIN,
                    f"{self._rig_name} Excavator",
                )
            },
            "name": f"{self._rig_name}",
            "manufacturer": "NiceHash",
        }
        try:
            info[
                "sw_version"
            ] = f"{self._mining_rig.info.version}, Build: {self._mining_rig.info.build_number}"

            info["uptime"] = f"{self._mining_rig.info.uptime / 60 / 60}h"

            gpu_models: dict[str, int]
            gpu_models = {}
            for device_id in self._mining_rig.devices:
                gpu_model = self._mining_rig.get_device(device_id).name
                if gpu_model in gpu_models:
                    gpu_count = gpu_models[gpu_model]
                    gpu_models[gpu_model] = gpu_count + 1
                else:
                    gpu_models[gpu_model] = 1

            model_string = ""
            for gpu_model, gpu_count in gpu_models.items():
                if model_string:
                    model_string = (
                        model_string + "; " + str(gpu_count) + "x " + gpu_model
                    )
                else:
                    model_string = str(gpu_count) + "x " + gpu_model

            info["model"] = model_string
        except (AttributeError, TypeError) as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            info["model"] = "No GPUs found"
            info["uptime"] = "Not available"
        return info


class DeviceSensorBase(SensorBase):
    """Base representation of a Graphics device Sensor."""

    def __init__(
        self,
        mining_rig: MiningRig,
        config_entry: ConfigEntry,
        device_id: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, config_entry)
        self._device_id = device_id
        self._device_name = f"GPU {device_id}"
        self._device_uuid = mining_rig.get_device(device_id).uuid

    @property
    def device_info(self) -> any:
        """Information about this entity/device."""
        try:
            return {
                "identifiers": {
                    (
                        DOMAIN,
                        self._device_uuid,
                    )
                },
                "name": self._device_name,
                "model": self._mining_rig.get_device(self._device_id).name,
                "manufacturer": self._mining_rig.get_device(self._device_id).subvendor,
                "via_device": (
                    DOMAIN,
                    f"{self._rig_name} Excavator",
                ),
            }
        except AttributeError as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"


class GpuTempSensor(DeviceSensorBase):
    """GPU temp sensor."""

    device_class = SensorDeviceClass.TEMPERATURE
    _attr_unit_of_measurement = TEMP_CELSIUS

    @property
    def name(self) -> str:
        return f"{self._rig_name} {self._device_name} GPU"

    @property
    def unique_id(self) -> str:
        return f"{self._rig_name}_{self._device_uuid}_temp"

    @property
    def state(self) -> float:
        try:
            return self._mining_rig.get_device(self._device_id).gpu_temp
        except AttributeError as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"


class VRAMTempSensor(DeviceSensorBase):
    """VRAM temp Sensor."""

    device_class = SensorDeviceClass.TEMPERATURE
    _attr_unit_of_measurement = TEMP_CELSIUS

    @property
    def name(self) -> str:
        return f"{self._rig_name} {self._device_name} VRAM"

    @property
    def unique_id(self) -> str:
        return f"{self._rig_name}_{self._device_uuid}_vram_temp"

    @property
    def state(self) -> float:
        try:
            return self._mining_rig.get_device(self._device_id).vram_temp
        except AttributeError as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"


class HotspotTempSensor(DeviceSensorBase):
    """Hotspot Sensor."""

    device_class = SensorDeviceClass.TEMPERATURE
    _attr_unit_of_measurement = TEMP_CELSIUS

    @property
    def name(self) -> str:
        return f"{self._rig_name} {self._device_name} Hotspot"

    @property
    def unique_id(self) -> str:
        return f"{self._rig_name}_{self._device_uuid}_hotspot_temp"

    @property
    def state(self) -> float:
        try:
            return self._mining_rig.get_device(self._device_id).hotspot_temp
        except AttributeError as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"


class FanSensor(DeviceSensorBase):
    """Fan Sensor."""

    _attr_unit_of_measurement = PERCENTAGE

    @property
    def name(self) -> str:
        return f"{self._rig_name} {self._device_name} Fan"

    @property
    def unique_id(self) -> str:
        return f"{self._rig_name}_{self._device_uuid}_fan"

    @property
    def state(self) -> float:
        try:
            return self._mining_rig.get_device(self._device_id).gpu_fan_speed
        except AttributeError as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"


class OvertempSensor(DeviceSensorBase):
    """Overtemp Sensor."""

    @property
    def name(self) -> str:
        return f"{self._rig_name} {self._device_name} Overtemp"

    @property
    def unique_id(self) -> str:
        return f"{self._rig_name}_{self._device_uuid}_overtemp"

    @property
    def state(self) -> bool:
        try:
            return self._mining_rig.get_device(self._device_id).too_hot
        except AttributeError as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"


class PowerSensor(DeviceSensorBase):
    """Power Sensor."""

    device_class = SensorDeviceClass.POWER
    _attr_unit_of_measurement = POWER_WATT

    @property
    def name(self) -> str:
        return f"{self._rig_name} {self._device_name} Power"

    @property
    def unique_id(self) -> str:
        return f"{self._rig_name}_{self._device_uuid}_power"

    @property
    def state(self) -> float:
        try:
            return self._mining_rig.get_device(self._device_id).gpu_power_usage
        except AttributeError as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"


class ModelSensor(DeviceSensorBase):
    """Model Sensor."""

    @property
    def name(self) -> str:
        return f"{self._rig_name} {self._device_name} GPU Model"

    @property
    def unique_id(self) -> str:
        return f"{self._rig_name}_{self._device_uuid}_gpu_model"

    @property
    def state(self) -> str:
        try:
            return self._mining_rig.get_device(self._device_id).name
        except AttributeError as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"


class VendorSensor(DeviceSensorBase):
    """Vendor Sensor."""

    @property
    def name(self) -> str:
        return f"{self._rig_name} {self._device_name} Vendor ID"

    @property
    def unique_id(self) -> str:
        return f"{self._rig_name}_{self._device_uuid}_vendor_id"

    @property
    def state(self) -> str:
        try:
            return self._mining_rig.get_device(self._device_id).subvendor
        except AttributeError as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"


class WorkerAlgorithmHashrateSensor(DeviceSensorBase):
    """Hashrate Sensor per GPU and Algorithm ."""

    _attr_unit_of_measurement = "Mh/s"

    def __init__(
        self,
        mining_rig: MiningRig,
        config_entry: ConfigEntry,
        worker_id: int,
        algorithm_id: int,
    ) -> None:
        """Initialize the sensor."""
        for device_id in mining_rig.devices:
            if device_id == mining_rig.get_worker(worker_id).device_id:
                self._device_id = device_id
                break

        super().__init__(mining_rig, config_entry, self._device_id)
        self._worker_id = worker_id
        self._algorithm_id = algorithm_id

    @property
    def name(self) -> str:
        try:
            return f"{self._rig_name} {self._device_name} {self._mining_rig.get_worker(self._worker_id).algorithms[self._algorithm_id].name}"
        except AttributeError as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"

    @property
    def unique_id(self) -> str:
        try:
            return f"{self._rig_name}_{self._device_uuid}_{self._mining_rig.get_worker(self._worker_id).algorithms[self._algorithm_id].name}"
        except AttributeError as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"

    @property
    def state(self) -> float:
        try:
            worker = self._mining_rig.get_worker(self._worker_id)
            algorithm = worker.algorithms[self._algorithm_id]
            return round(
                algorithm.speed / 1000000,
                2,
            )
        except (AttributeError, TypeError) as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"


class AlgorithmHashrateSensor(RigSensor):
    """Hashrate Sensor per Algorithm."""

    _attr_unit_of_measurement = "Mh/s"

    def __init__(
        self, mining_rig: MiningRig, config_entry: ConfigEntry, algorithm_id: int
    ) -> None:
        """Initialize the sensor."""
        super().__init__(mining_rig, config_entry)
        self._algorithm_id = algorithm_id

    @property
    def name(self) -> str:
        try:
            return f"{self._rig_name} {self._mining_rig.get_algorithm(self._algorithm_id).name}"
        except AttributeError as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"

    @property
    def unique_id(self) -> str:
        try:
            return f"{self._rig_name}_{self._mining_rig.get_algorithm(self._algorithm_id).name}_hashrate"
        except AttributeError as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"

    @property
    def state(self) -> float:
        try:
            algorithm = self._mining_rig.get_algorithm(self._algorithm_id)
            return round(
                algorithm.speed / 1000000,
                2,
            )
        except (AttributeError, TypeError) as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"


class OnlineSensor(RigSensor):
    """Online Sensor"""

    @property
    def name(self) -> str:
        return f"{self._rig_name} status"

    @property
    def unique_id(self) -> str:
        return f"{self._rig_name}_status"

    @property
    def state(self) -> str:
        return "Online" if self._mining_rig.online else "Offline"


class GpuModelsSensor(RigSensor):
    """Gpu models Sensor"""

    @property
    def name(self) -> str:
        return f"{self._rig_name} GPU models"

    @property
    def unique_id(self) -> str:
        return f"{self._rig_name}_gpu_models"

    @property
    def state(self) -> str:
        try:
            devices = ""
            for device_id in self._mining_rig.devices:
                devices += (
                    self._mining_rig.get_device(device_id).name.replace("GeForce ", "")
                    + ", "
                )
            return devices[:-2] if len(devices[:-2]) <= 255 else "value to long"
        except AttributeError as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"


class GpuCountSensor(RigSensor):
    """Gpu count Sensor"""

    @property
    def name(self) -> str:
        return f"{self._rig_name} GPU count"

    @property
    def unique_id(self) -> str:
        return f"{self._rig_name}_gpu_count"

    @property
    def state(self) -> int:
        try:
            return len(self._mining_rig.devices)
        except AttributeError as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"


class TotalPowerSensor(RigSensor):
    """Miner Power Sensor."""

    device_class = SensorDeviceClass.POWER
    _attr_unit_of_measurement = POWER_WATT

    @property
    def name(self) -> str:
        return f"{self._rig_name} Power"

    @property
    def unique_id(self) -> str:
        return f"{self._rig_name}_power"

    @property
    def state(self) -> float:
        try:
            power = 0
            for device_id in self._mining_rig.devices:
                power += self._mining_rig.get_device(device_id).gpu_power_usage
            return power
        except (AttributeError, TypeError) as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"


class CPUSensor(RigSensor):
    """CPU Sensor."""

    _attr_unit_of_measurement = PERCENTAGE

    @property
    def name(self) -> str:
        return f"{self._rig_name} CPU"

    @property
    def unique_id(self) -> str:
        return f"{self._rig_name}_cpu"

    @property
    def state(self) -> float:
        try:
            return round(self._mining_rig.info.cpu_load, 2)
        except (AttributeError, TypeError) as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"


class RAMSensor(RigSensor):
    """RAM Sensor."""

    _attr_unit_of_measurement = PERCENTAGE

    @property
    def name(self) -> str:
        return f"{self._rig_name} RAM"

    @property
    def unique_id(self) -> str:
        return f"{self._rig_name}_ram"

    @property
    def state(self) -> float:
        try:
            return round(self._mining_rig.info.ram_load)
        except (AttributeError, TypeError) as error:
            if self._enable_debug_logging:
                _LOGGER.info(error)
            return "unavailable"
