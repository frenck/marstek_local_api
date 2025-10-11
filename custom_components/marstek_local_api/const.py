"""Constants for the Marstek integration."""
from typing import Final

DOMAIN: Final = "marstek_local_api"

# Configuration keys
CONF_POLLING_INTERVAL: Final = "polling_interval"
CONF_SOURCE_PORT: Final = "source_port"
CONF_DEVICES: Final = "devices"
CONF_IP_ADDRESS: Final = "ip_address"
CONF_DESTINATION_PORT: Final = "destination_port"
CONF_DEVICE_NAME: Final = "device_name"

# Default values
DEFAULT_POLLING_INTERVAL: Final = 30  # seconds
DEFAULT_SOURCE_PORT: Final = 30000
DEFAULT_DESTINATION_PORT: Final = 30000

# UDP communication
UDP_TIMEOUT: Final = 5  # seconds
MAX_RETRIES: Final = 3

# API methods
METHOD_BAT_STATUS: Final = "Bat.GetStatus"
METHOD_ES_STATUS: Final = "ES.GetStatus"

# Sensor types
SENSOR_IDENTIFIER: Final = "identifier"
SENSOR_STATE_OF_CHARGE: Final = "state_of_charge"
SENSOR_CURRENT_CAPACITY: Final = "current_capacity"
SENSOR_MAX_CAPACITY: Final = "max_capacity"
SENSOR_TEMPERATURE: Final = "temperature"
SENSOR_GRID_POWER: Final = "grid_power"
SENSOR_TOTAL_GRID_OUTPUT_ENERGY: Final = "total_grid_output_energy"
SENSOR_TOTAL_GRID_INPUT_ENERGY: Final = "total_grid_input_energy"

# Integration level sensors
SENSOR_TOTAL_CURRENT_CAPACITY: Final = "total_current_capacity"
SENSOR_TOTAL_MAX_CAPACITY: Final = "total_max_capacity"
SENSOR_TOTAL_GRID_POWER: Final = "total_grid_power"