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
    CONF_DEVICES,
    CONF_DESTINATION_PORT,
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
        for device_config in entry.data[CONF_DEVICES]:
            device = self.client.add_device(
                device_config[CONF_IP_ADDRESS],
                device_config[CONF_DESTINATION_PORT]
            )
            self.devices.append(device)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=entry.data[CONF_POLLING_INTERVAL]),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from all devices."""
        if not self.client._transport:
            await self.client.start()

        data: dict[str, Any] = {"devices": {}, "totals": {}}
        
        # Collect data from all devices
        tasks = []
        for device in self.devices:
            tasks.append(self._get_device_data(device))
        
        try:
            device_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for device, result in zip(self.devices, device_results):
                if isinstance(result, Exception):
                    _LOGGER.error("Error fetching data from %s: %s", device, result)
                    continue
                
                if result:
                    device_key = device.identifier or f"{device.ip_address}_{device.destination_port}"
                    data["devices"][device_key] = result
            
            # Calculate totals
            self._calculate_totals(data)
            
            return data
            
        except Exception as e:
            _LOGGER.error("Error fetching data: %s", e)
            raise UpdateFailed(f"Error fetching data: {e}")

    async def _get_device_data(self, device: MarstekDevice) -> dict[str, Any] | None:
        """Get data from a single device."""
        try:
            # Get battery status
            bat_status = await self.client.get_battery_status(device)
            if not bat_status or "result" not in bat_status:
                _LOGGER.warning("No battery status received from %s", device)
                return None
            
            # Get energy system status
            es_status = await self.client.get_energy_system_status(device)
            if not es_status or "result" not in es_status:
                _LOGGER.warning("No energy system status received from %s", device)
                return None
            
            # Extract and convert data
            bat_result = bat_status["result"]
            es_result = es_status["result"]
            
            device_data = {
                SENSOR_IDENTIFIER: bat_status.get("src", f"{device.ip_address}_{device.destination_port}"),
                SENSOR_STATE_OF_CHARGE: bat_result.get("soc", 0),
                SENSOR_CURRENT_CAPACITY: bat_result.get("bat_capacity", 0) / 1000,  # Convert Wh to kWh
                SENSOR_MAX_CAPACITY: bat_result.get("rated_capacity", 0) / 1000,  # Convert Wh to kWh
                SENSOR_TEMPERATURE: bat_result.get("bat_temp", 0),
                SENSOR_GRID_POWER: es_result.get("ongrid_power", 0),
                SENSOR_TOTAL_GRID_OUTPUT_ENERGY: es_result.get("total_grid_output_energy", 0) / 1000,  # Convert Wh to kWh
                SENSOR_TOTAL_GRID_INPUT_ENERGY: es_result.get("total_grid_input_energy", 0) / 1000,  # Convert Wh to kWh
            }
            
            # Update device identifier if we got it
            if "src" in bat_status and device.identifier is None:
                device.identifier = bat_status["src"]
            
            return device_data
            
        except Exception as e:
            _LOGGER.error("Error getting data from %s: %s", device, e)
            return None

    def _calculate_totals(self, data: dict[str, Any]) -> None:
        """Calculate total values across all devices."""
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