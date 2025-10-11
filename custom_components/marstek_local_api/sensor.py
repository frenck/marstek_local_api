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
from homeassistant.core import HomeAssistant, callback
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


# Sensor configuration for individual device sensors
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
        "native_unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
    },
    SENSOR_MAX_CAPACITY: {
        "name": "Max Capacity",
        "icon": "mdi:battery-outline",
        "device_class": SensorDeviceClass.ENERGY_STORAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
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

# Total sensors aggregating data from all devices
TOTAL_SENSORS = {
    SENSOR_TOTAL_CURRENT_CAPACITY: {
        "name": "Total Current Capacity",
        "icon": "mdi:battery-charging",
        "device_class": SensorDeviceClass.ENERGY_STORAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
    },
    SENSOR_TOTAL_MAX_CAPACITY: {
        "name": "Total Max Capacity",
        "icon": "mdi:battery-outline",
        "device_class": SensorDeviceClass.ENERGY_STORAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
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
    
    # Store the async_add_entities callback for later use
    coordinator._async_add_entities = async_add_entities
    coordinator._existing_device_sensors = set()
    
    # Set up initial entities
    await _async_setup_sensors(coordinator, async_add_entities)
    
    # Listen for coordinator updates to add new device sensors
    @callback
    def _async_add_new_sensors():
        """Add sensors for new devices."""
        hass.async_create_task(_async_setup_sensors(coordinator, async_add_entities))
    
    coordinator.async_add_listener(_async_add_new_sensors)


async def _async_setup_sensors(
    coordinator: MarstekCoordinator,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for all devices."""
    entities = []

    # Create device-specific sensors
    devices_data = coordinator.data.get("devices", {}) if coordinator.data else {}
    
    for device_id, device_data in devices_data.items():
        if isinstance(device_data, dict) and SENSOR_IDENTIFIER in device_data:
            device_name = device_data.get("device_name", device_id)
            
            # Check if we already have sensors for this device
            device_key = f"{device_id}_{device_name}"
            if device_key in coordinator._existing_device_sensors:
                continue
                
            coordinator._existing_device_sensors.add(device_key)
            
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

    # Create total aggregate sensors (only once)
    if not hasattr(coordinator, '_total_sensors_created'):
        coordinator._total_sensors_created = True
        for sensor_type, sensor_config in TOTAL_SENSORS.items():
            entities.append(
                MarstekTotalSensor(
                    coordinator,
                    sensor_type,
                    sensor_config,
                )
            )

    if entities:
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

        # Create unique entity ID from device and sensor names
        safe_device_name = device_name.lower().replace(" ", "_").replace("-", "_")
        safe_sensor_name = sensor_config["name"].lower().replace(" ", "_").replace("-", "_")
        
        self._attr_unique_id = f"{DOMAIN}_{safe_device_name}_{safe_sensor_name}"
        self._attr_name = f"{device_name} {sensor_config['name']}"
        self._attr_icon = sensor_config["icon"]
        self._attr_device_class = sensor_config["device_class"]
        self._attr_state_class = sensor_config["state_class"]
        self._attr_native_unit_of_measurement = sensor_config["native_unit_of_measurement"]

        # Enable energy storage sensors for Energy Dashboard
        if sensor_type in [SENSOR_CURRENT_CAPACITY, SENSOR_MAX_CAPACITY]:
            self._attr_entity_category = None
        
        # Device information for Home Assistant
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_name,
            "manufacturer": "Marstek",
            "model": "Marstek Battery Device",
            "sw_version": "1.0",
        }

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        devices_data = self.coordinator.data.get("devices", {}) if self.coordinator.data else {}
        device_data = devices_data.get(self._device_id)
        if not device_data or not isinstance(device_data, dict):
            return None

        # Access sensor data using the SENSOR_* constant keys
        if self._sensor_type in device_data:
            return device_data[self._sensor_type]

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

        # Create unique entity ID for total sensor
        safe_sensor_name = sensor_config["name"].lower().replace(" ", "_").replace("-", "_")
        
        self._attr_unique_id = f"{DOMAIN}_system_{safe_sensor_name}"
        self._attr_name = f"Marstek {sensor_config['name']}"
        self._attr_icon = sensor_config["icon"]
        self._attr_device_class = sensor_config["device_class"]
        self._attr_state_class = sensor_config["state_class"]
        self._attr_native_unit_of_measurement = sensor_config["native_unit_of_measurement"]

        # Device information for the system integration
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "system")},
            "name": "Marstek Battery Integration",
            "manufacturer": "Marstek",
            "model": "Marstek Battery Array",
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

            # Aggregate sensor data based on sensor type
            if self._sensor_type == SENSOR_TOTAL_CURRENT_CAPACITY:
                if SENSOR_CURRENT_CAPACITY in device_data and device_data[SENSOR_CURRENT_CAPACITY] is not None:
                    total_value += device_data[SENSOR_CURRENT_CAPACITY]
                    device_count += 1
            elif self._sensor_type == SENSOR_TOTAL_MAX_CAPACITY:
                if SENSOR_MAX_CAPACITY in device_data and device_data[SENSOR_MAX_CAPACITY] is not None:
                    total_value += device_data[SENSOR_MAX_CAPACITY]
                    device_count += 1
            elif self._sensor_type == SENSOR_TOTAL_GRID_POWER:
                if SENSOR_GRID_POWER in device_data and device_data[SENSOR_GRID_POWER] is not None:
                    total_value += device_data[SENSOR_GRID_POWER]
                    device_count += 1
            elif self._sensor_type == SENSOR_TOTAL_GRID_OUTPUT_ENERGY:
                if SENSOR_TOTAL_GRID_OUTPUT_ENERGY in device_data and device_data[SENSOR_TOTAL_GRID_OUTPUT_ENERGY] is not None:
                    total_value += device_data[SENSOR_TOTAL_GRID_OUTPUT_ENERGY]
                    device_count += 1
            elif self._sensor_type == SENSOR_TOTAL_GRID_INPUT_ENERGY:
                if SENSOR_TOTAL_GRID_INPUT_ENERGY in device_data and device_data[SENSOR_TOTAL_GRID_INPUT_ENERGY] is not None:
                    total_value += device_data[SENSOR_TOTAL_GRID_INPUT_ENERGY]
                    device_count += 1

        return total_value if device_count > 0 else None