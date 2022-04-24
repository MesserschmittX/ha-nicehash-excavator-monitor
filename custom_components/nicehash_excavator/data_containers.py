"""Classes that contain received data"""


class GraphicsCard:
    """contains gpu data"""

    id: int
    name: str
    subvendor: str
    uuid: str
    gpu_temp: int
    gpu_load: int
    gpu_load_memctrl: int
    gpu_power_usage: float
    gpu_fan_speed: int
    too_hot: bool
    vram_temp: int
    hotspot_temp: int

    def __init__(self, data=None) -> None:
        """Init GraphicsCard."""
        self.id = data.get("device_id") if data else "NaN"
        self.name = data.get("name") if data else "NaN"
        self.subvendor = data.get("subvendor") if data else "NaN"
        self.uuid = data.get("uuid") if data else "NaN"
        self.gpu_temp = data.get("gpu_temp") if data else "NaN"
        self.gpu_load = data.get("gpu_load") if data else "NaN"
        self.gpu_load_memctrl = data.get("gpu_load_memctrl") if data else "NaN"
        self.gpu_power_usage = data.get("gpu_power_usage") if data else "NaN"
        self.gpu_fan_speed = data.get("gpu_fan_speed") if data else "NaN"
        self.too_hot = data.get("too_hot") if data else "NaN"
        self.vram_temp = data.get("__vram_temp") if data else "NaN"
        self.hotspot_temp = data.get("__hotspot_temp") if data else "NaN"


class Algorithm:
    """contains algorithm data"""

    id: int
    name: str
    speed: float

    def __init__(self, data=None) -> None:
        """Init Algorithm."""
        self.name = data.get("name") if data else "NaN"

        if "algorithm_id" in data:
            self.id = data.get("algorithm_id")
        else:
            if "id" in data:
                self.id = data.get("id")
            else:
                self.id = "NaN"

        if "speed" in data:
            self.speed = data.get("speed")
        else:
            self.speed = "NaN"


class RigInfo:
    """contains Rig info"""

    version: str
    build_platform: str
    build_number: int
    excavator_cuda_ver: int
    driver_cuda_ver: int
    uptime: int
    cpu_load: float
    ram_load: float

    def __init__(self, data=None) -> None:
        """Init RigInfo."""
        self.version = data.get("version") if data else "NaN"
        self.build_platform = data.get("build_platform") if data else "NaN"
        self.build_number = data.get("build_number") if data else "NaN"
        self.excavator_cuda_ver = data.get("excavator_cuda_ver") if data else "NaN"
        self.driver_cuda_ver = data.get("driver_cuda_ver") if data else "NaN"
        self.uptime = data.get("uptime") if data else "NaN"
        self.cpu_load = data.get("cpu_load") if data else "NaN"
        self.ram_load = data.get("ram_load") if data else "NaN"


class Worker:
    """contains Worker data"""

    id: int
    device_id: int
    device_uuid: str
    algorithms: dict[int, Algorithm]

    def __init__(self, data=None) -> None:
        """Init Worker."""
        self.id = data.get("worker_id") if data else "NaN"
        self.device_id = data.get("device_id") if data else "NaN"
        self.device_uuid = data.get("device_uuid") if data else "NaN"
        self.algorithms = {}

        if "algorithms" in data:
            for algorithm_data in data.get("algorithms"):
                algorithm = Algorithm(algorithm_data)
                self.algorithms[algorithm.id] = algorithm
        else:
            self.algorithms = "NaN"
