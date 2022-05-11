"""Constants for the Nicehash Excavator integration."""

DOMAIN = "nicehash_excavator"


DEFAULT_HOST_PORT = 18000
DEFAULT_UPDATE_INTERVAL = 60
DEFAULT_UPDATE_INTERVAL_FAST = 1

MAX_UPDATE_INTERVAL = 3600
MIN_UPDATE_INTERVAL = 1

CONFIG_NAME = "name"
CONFIG_HOST_ADDRESS = "host_address"
CONFIG_HOST_PORT = "host_port"
CONFIG_UPDATE_INTERVAL = "update_interval"
CONFIG_UPDATE_INTERVAL_FAST = "update_interval_fast"

API = "api"
MINING_RIG = "mining_rig"

ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_NO_RESPONSE = "no_response"
ERROR_INVALID_PORT = "invalid_port"
ERROR_INVALID_UPDATE_INTERVAL = "invalid_update_interval"
ERROR_UNKNOWN = "unknown"
