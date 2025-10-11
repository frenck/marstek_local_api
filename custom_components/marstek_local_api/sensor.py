"""Sensor platform for Marstek integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SENSOR_CURRENT_CAPACITY,
    SENSOR_GRID_POWER,
    SENSOR_IDENTIFIER,
    SENSOR_MAX_CAPACITY,
    SENSOR_STATE_OF_CHARGE,
    SENSOR_TEMPERATURE,
    SENSOR_TOTAL_CURRENT_CAPACITY,
    SENSOR_TOTAL_GRID_OUTPUT_ENERGY,
    SENSOR_TOTAL_GRID_INPUT_ENERGY,
    SENSOR_TOTAL_GRID_POWER,
    SENSOR_TOTAL_MAX_CAPACITY,
)
from .coordinator import MarstekCoordinator

_LOGGER = logging.getLogger(__name__)


# Sensor configurations for individual devices
DEVICE_SENSORS = {
    SENSOR_IDENTIFIER: {
        "name": "Identifier",
        "icon": "mdi:identifier",
        "device_class": None,
        "state_class": None,
        "native_unit_of_measurement": None,
    },
    SENSOR_STATE_OF_CHARGE: {
        "name": "State of Charge",
        "icon": "mdi:battery",
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": PERCENTAGE,
    },
    SENSOR_CURRENT_CAPACITY: {
        "name": "Current Capacity",
        "icon": "mdi:battery-charging",
        "device_class": SensorDeviceClass.ENERGY_STORAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfEnergy.WATT_HOUR,
    },
    SENSOR_MAX_CAPACITY: {
        "name": "Max Capacity",
        "icon": "mdi:battery-outline",
        "device_class": SensorDeviceClass.ENERGY_STORAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfEnergy.WATT_HOUR,
    },
    SENSOR_TEMPERATURE: {
        "name": "Temperature",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
    },
    SENSOR_GRID_POWER: {
        "name": "Grid Power",
        "icon": "mdi:transmission-tower",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfPower.WATT,
    },
}

# Total sensors that aggregate data from all devices
TOTAL_SENSORS = {
    SENSOR_TOTAL_CURRENT_CAPACITY: {
        "name": "Total Current Capacity",
        "icon": "mdi:battery-charging",
        "device_class": SensorDeviceClass.ENERGY_STORAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfEnergy.WATT_HOUR,
    },
    SENSOR_TOTAL_MAX_CAPACITY: {
        "name": "Total Max Capacity",
        "icon": "mdi:battery-outline",
        "device_class": SensorDeviceClass.ENERGY_STORAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfEnergy.WATT_HOUR,
    },
    SENSOR_TOTAL_GRID_POWER: {
        "name": "Total Grid Power",
        "icon": "mdi:transmission-tower",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfPower.WATT,
    },
    SENSOR_TOTAL_GRID_OUTPUT_ENERGY: {
        "name": "Total Grid Output Energy",
        "icon": "mdi:transmission-tower-export",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "native_unit_of_measurement": UnitOfEnergy.WATT_HOUR,
    },
    SENSOR_TOTAL_GRID_INPUT_ENERGY: {
        "name": "Total Grid Input Energy",
        "icon": "mdi:transmission-tower-import",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "native_unit_of_measurement": UnitOfEnergy.WATT_HOUR,
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Marstek sensors from config entry."""
    coordinator: MarstekCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []

    # Add device-specific sensors
    devices_data = coordinator.data.get("devices", {}) if coordinator.data else {}
    _LOGGER.debug("Setting up sensors for %d devices: %s", len(devices_data), list(devices_data.keys()))
    
    for device_id, device_data in devices_data.items():
        if isinstance(device_data, dict) and "identifier" in device_data:
            device_name = device_data.get("device_name", device_id)
            _LOGGER.debug("Adding sensors for device: %s (%s)", device_id, device_name)
            
            for sensor_type, sensor_config in DEVICE_SENSORS.items():
                entities.append(
                    MarstekDeviceSensor(
                        coordinator,
                        device_id,
                        device_name,
                        sensor_type,
                        sensor_config,
                    )
                )

    # Add total sensors
    for sensor_type, sensor_config in TOTAL_SENSORS.items():
        entities.append(
            MarstekTotalSensor(
                coordinator,
                sensor_type,
                sensor_config,
            )
        )

    _LOGGER.debug("Created %d sensor entities total", len(entities))
    async_add_entities(entities)


class MarstekDeviceSensor(CoordinatorEntity[MarstekCoordinator], SensorEntity):
    """Representation of a Marstek device sensor."""

    def __init__(
        self,
        coordinator: MarstekCoordinator,
        device_id: str,
        device_name: str,
        sensor_type: str,
        sensor_config: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name
        self._sensor_type = sensor_type
        self._sensor_config = sensor_config

        # Generate safe entity ID
        safe_device_name = device_name.lower().replace(" ", "_").replace("-", "_")
        safe_sensor_name = sensor_config["name"].lower().replace(" ", "_").replace("-", "_")
        
        self._attr_unique_id = f"{DOMAIN}_{safe_device_name}_{safe_sensor_name}"
        self._attr_name = f"{device_name} {sensor_config['name']}"
        self._attr_icon = sensor_config["icon"]
        self._attr_device_class = sensor_config["device_class"]
        self._attr_state_class = sensor_config["state_class"]
        self._attr_native_unit_of_measurement = sensor_config["native_unit_of_measurement"]

        # Make energy storage sensors available for Energy Dashboard
        if sensor_type in [SENSOR_CURRENT_CAPACITY, SENSOR_MAX_CAPACITY]:
            self._attr_entity_category = None  # Make available for Energy Dashboard
        
        # Device information
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_name,
            "manufacturer": "Marstek",
            "model": "Battery System",
            "sw_version": "1.0",
        }

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        devices_data = self.coordinator.data.get("devices", {}) if self.coordinator.data else {}
        device_data = devices_data.get(self._device_id)
        if not device_data or not isinstance(device_data, dict):
            return None

        # Map sensor types to data keys
        data_mapping = {
            SENSOR_IDENTIFIER: "identifier",
            SENSOR_STATE_OF_CHARGE: "soc",
            SENSOR_CURRENT_CAPACITY: "bat_capacity",
            SENSOR_MAX_CAPACITY: "rated_capacity",
            SENSOR_TEMPERATURE: "bat_temp",
            SENSOR_GRID_POWER: "ongrid_power",
        }

        data_key = data_mapping.get(self._sensor_type)
        if data_key and data_key in device_data:
            return device_data[data_key]

        return None


class MarstekTotalSensor(CoordinatorEntity[MarstekCoordinator], SensorEntity):
    """Representation of a Marstek total/aggregate sensor."""

    def __init__(
        self,
        coordinator: MarstekCoordinator,
        sensor_type: str,
        sensor_config: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._sensor_config = sensor_config

        # Generate safe entity ID
        safe_sensor_name = sensor_config["name"].lower().replace(" ", "_").replace("-", "_")
        
        self._attr_unique_id = f"{DOMAIN}_system_{safe_sensor_name}"
        self._attr_name = f"Marstek {sensor_config['name']}"
        self._attr_icon = sensor_config["icon"]
        self._attr_device_class = sensor_config["device_class"]
        self._attr_state_class = sensor_config["state_class"]
        self._attr_native_unit_of_measurement = sensor_config["native_unit_of_measurement"]

        # Device information for the integration itself
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "system")},
            "name": "Marstek Battery System",
            "manufacturer": "Marstek",
            "model": "Marstek Battery System",
            "sw_version": "1.0",
        }

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            return None

        devices_data = self.coordinator.data.get("devices", {})
        total_value = 0
        device_count = 0

        for device_id, device_data in devices_data.items():
            if not isinstance(device_data, dict):
                continue

            # Map sensor types to data aggregation logic
            if self._sensor_type == SENSOR_TOTAL_CURRENT_CAPACITY:
                if "bat_capacity" in device_data and device_data["bat_capacity"] is not None:
                    total_value += device_data["bat_capacity"]
                    device_count += 1
            elif self._sensor_type == SENSOR_TOTAL_MAX_CAPACITY:
                if "rated_capacity" in device_data and device_data["rated_capacity"] is not None:
                    total_value += device_data["rated_capacity"]
                    device_count += 1
            elif self._sensor_type == SENSOR_TOTAL_GRID_POWER:
                if "ongrid_power" in device_data and device_data["ongrid_power"] is not None:
                    total_value += device_data["ongrid_power"]
                    device_count += 1
            elif self._sensor_type == SENSOR_TOTAL_GRID_OUTPUT_ENERGY:
                if "total_grid_output_energy" in device_data and device_data["total_grid_output_energy"] is not None:
                    total_value += device_data["total_grid_output_energy"]
                    device_count += 1
            elif self._sensor_type == SENSOR_TOTAL_GRID_INPUT_ENERGY:
                if "total_grid_input_energy" in device_data and device_data["total_grid_input_energy"] is not None:
                    total_value += device_data["total_grid_input_energy"]
                    device_count += 1

        return total_value if device_count > 0 else None