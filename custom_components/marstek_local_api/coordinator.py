"""Data update coordinator for Marstek integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import MarstekDevice, MarstekUDPClient
from .const import (
    CONF_DESTINATION_PORT,
    CONF_DEVICE_NAME,
    CONF_DEVICES,
    CONF_IP_ADDRESS,
    CONF_POLLING_INTERVAL,
    CONF_SOURCE_PORT,
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

_LOGGER = logging.getLogger(__name__)


class MarstekCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from Marstek devices."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.client = MarstekUDPClient(entry.data[CONF_SOURCE_PORT])
        self.devices: list[MarstekDevice] = []
        
        # Add devices from config
        self._update_devices_from_config()

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=entry.data[CONF_POLLING_INTERVAL]),
        )

    def _update_devices_from_config(self) -> None:
        """Update device list from configuration."""
        # Clear existing devices
        self.devices.clear()
        self.client._devices.clear()
        
        # Add configured devices
        for i, device_config in enumerate(self.entry.data[CONF_DEVICES]):
            device_name = device_config.get(CONF_DEVICE_NAME, f"Device {len(self.devices)+1}")
            device = self.client.add_device(
                device_name,
                device_config[CONF_IP_ADDRESS],
                device_config[CONF_DESTINATION_PORT]
            )
            self.devices.append(device)

    async def async_config_entry_updated(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Handle config entry updates."""
        self.entry = entry
        
        # Update polling interval
        self.update_interval = timedelta(seconds=entry.data[CONF_POLLING_INTERVAL])
        
        # Update device configuration
        self._update_devices_from_config()
        
        # Refresh data with updated devices
        await self.async_refresh()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from all devices."""
        if not self.client._transport:
            await self.client.start()

        data: dict[str, Any] = {"devices": {}, "totals": {}}
        
        # Fetch data from all devices concurrently
        tasks = []
        for device in self.devices:
            tasks.append(self._get_device_data(device))
        
        try:
            device_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process device data results
            for device, result in zip(self.devices, device_results):
                if isinstance(result, Exception):
                    _LOGGER.error("Error fetching data from %s: %s", device, result)
                    continue
                
                if result:
                    # Use device name as key for user-friendly identification
                    device_key = device.name
                    data["devices"][device_key] = result
            
            # Calculate aggregate totals
            self._calculate_totals(data)
            
            return data
            
        except Exception as e:
            _LOGGER.error("Error fetching data: %s", e)
            raise UpdateFailed(f"Error fetching data: {e}")

    async def _get_device_data(self, device: MarstekDevice) -> dict[str, Any] | None:
        """Retrieve and process data from a single device."""
        try:
            # Request battery status
            bat_status = await self.client.get_battery_status(device)
            if not bat_status or "result" not in bat_status:
                _LOGGER.warning("No battery status received from %s", device)
                return None
            
            # Request energy system status
            es_status = await self.client.get_energy_system_status(device)
            if not es_status or "result" not in es_status:
                _LOGGER.warning("No energy system status received from %s", device)
                return None
            
            # Process response data
            bat_result = bat_status["result"]
            es_result = es_status["result"]
            
            # Log any device error codes
            bat_error_code = bat_result.get("error_code", "0")
            if bat_error_code != "0" and bat_error_code != 0:
                _LOGGER.warning("Battery error code %s from device %s: %s", bat_error_code, device, bat_result)
            
            # Check for energy system error codes
            es_error_code = es_result.get("error_code")
            if es_error_code is not None and es_error_code != "0" and es_error_code != 0:
                _LOGGER.warning("Energy system error code %s from device %s: %s", es_error_code, device, es_result)
            
            # Build device data with unit conversions
            device_data = {
                "device_name": device.name,
                "ip_address": device.ip_address,
                SENSOR_IDENTIFIER: bat_status.get("src", f"{device.ip_address}_{device.destination_port}"),
                SENSOR_STATE_OF_CHARGE: bat_result.get("soc", 0),
                SENSOR_CURRENT_CAPACITY: bat_result.get("bat_capacity", 0) / 1000,  # Wh to kWh
                SENSOR_MAX_CAPACITY: bat_result.get("rated_capacity", 0) / 1000,  # Wh to kWh
                SENSOR_TEMPERATURE: bat_result.get("bat_temp", 0),
                SENSOR_GRID_POWER: es_result.get("ongrid_power", 0),
                SENSOR_TOTAL_GRID_OUTPUT_ENERGY: es_result.get("total_grid_output_energy", 0) / 1000,  # Wh to kWh
                SENSOR_TOTAL_GRID_INPUT_ENERGY: es_result.get("total_grid_input_energy", 0) / 1000,  # Wh to kWh
            }
            
            # Store device identifier for future reference
            if "src" in bat_status and device.identifier is None:
                device.identifier = bat_status["src"]
            
            return device_data
            
        except Exception as e:
            _LOGGER.error("Error getting data from %s: %s", device, e)
            return None

    def _calculate_totals(self, data: dict[str, Any]) -> None:
        """Calculate aggregate totals across all devices."""
        total_current_capacity = 0
        total_max_capacity = 0
        total_grid_power = 0
        
        for device_data in data["devices"].values():
            total_current_capacity += device_data.get(SENSOR_CURRENT_CAPACITY, 0)
            total_max_capacity += device_data.get(SENSOR_MAX_CAPACITY, 0)
            total_grid_power += device_data.get(SENSOR_GRID_POWER, 0)
        
        data["totals"] = {
            SENSOR_TOTAL_CURRENT_CAPACITY: total_current_capacity,
            SENSOR_TOTAL_MAX_CAPACITY: total_max_capacity,
            SENSOR_TOTAL_GRID_POWER: total_grid_power,
        }

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        await self.client.stop()