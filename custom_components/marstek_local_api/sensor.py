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
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
    },
    SENSOR_MAX_CAPACITY: {
        "name": "Max Capacity",
        "icon": "mdi:battery-plus",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": None,
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
    SENSOR_TOTAL_GRID_OUTPUT_ENERGY: {
        "name": "Total Grid Output Energy",
        "icon": "mdi:transmission-tower-export",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "native_unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
    },
    SENSOR_TOTAL_GRID_INPUT_ENERGY: {
        "name": "Total Grid Input Energy",
        "icon": "mdi:transmission-tower-import",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "native_unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
    },
}

# Sensor configurations for integration totals
TOTAL_SENSORS = {
    SENSOR_TOTAL_CURRENT_CAPACITY: {
        "name": "Total Current Capacity",
        "icon": "mdi:battery-charging",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
    },
    SENSOR_TOTAL_MAX_CAPACITY: {
        "name": "Total Max Capacity",
        "icon": "mdi:battery-plus",
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": None,
        "native_unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
    },
    SENSOR_TOTAL_GRID_POWER: {
        "name": "Total Grid Power",
        "icon": "mdi:transmission-tower",
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfPower.WATT,
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Marstek sensors."""
    coordinator: MarstekCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities: list[SensorEntity] = []
    
    # Wait for first data fetch to know available devices
    if coordinator.data:
        # Add device sensors
        for device_id in coordinator.data.get("devices", {}):
            for sensor_type in DEVICE_SENSORS:
                entities.append(
                    MarstekDeviceSensor(
                        coordinator, device_id, sensor_type
                    )
                )
        
        # Add total sensors
        for sensor_type in TOTAL_SENSORS:
            entities.append(
                MarstekTotalSensor(coordinator, sensor_type)
            )
    
    async_add_entities(entities)


class MarstekDeviceSensor(CoordinatorEntity[MarstekCoordinator], SensorEntity):
    """Sensor for individual Marstek device."""

    def __init__(
        self,
        coordinator: MarstekCoordinator,
        device_id: str,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._sensor_type = sensor_type
        self._config = DEVICE_SENSORS[sensor_type]
        
        # Entity configuration
        self._attr_name = f"{device_id} {self._config['name']}"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{sensor_type}"
        self._attr_icon = self._config["icon"]
        self._attr_device_class = self._config["device_class"]
        self._attr_state_class = self._config["state_class"]
        self._attr_native_unit_of_measurement = self._config["native_unit_of_measurement"]
        
        # Device information
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": f"Marstek Battery {device_id}",
            "manufacturer": "Marstek",
            "model": "Battery System",
            "sw_version": "1.0",
        }

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        device_data = self.coordinator.data.get("devices", {}).get(self._device_id)
        if not device_data:
            return None
        
        return device_data.get(self._sensor_type)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._device_id in self.coordinator.data.get("devices", {})
        )


class MarstekTotalSensor(CoordinatorEntity[MarstekCoordinator], SensorEntity):
    """Sensor for Marstek integration totals."""

    def __init__(
        self,
        coordinator: MarstekCoordinator,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._config = TOTAL_SENSORS[sensor_type]
        
        # Entity configuration
        self._attr_name = f"Marstek {self._config['name']}"
        self._attr_unique_id = f"{DOMAIN}_total_{sensor_type}"
        self._attr_icon = self._config["icon"]
        self._attr_device_class = self._config["device_class"]
        self._attr_state_class = self._config["state_class"]
        self._attr_native_unit_of_measurement = self._config["native_unit_of_measurement"]
        
        # Device information for integration
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "marstek_system")},
            "name": "Marstek Battery System",
            "manufacturer": "Marstek",
            "model": "Integration",
            "sw_version": "1.0",
        }

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        totals_data = self.coordinator.data.get("totals", {})
        return totals_data.get(self._sensor_type)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "totals" in self.coordinator.data
        )