"""Marstek integration services."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import MarstekCoordinator

_LOGGER = logging.getLogger(__name__)

# Service schema
REFRESH_DATA_SCHEMA = vol.Schema({})


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Marstek integration."""
    
    async def refresh_data(call: ServiceCall) -> None:
        """Refresh data from all Marstek devices."""
        for entry_id in hass.data.get(DOMAIN, {}):
            coordinator: MarstekCoordinator = hass.data[DOMAIN][entry_id]
            await coordinator.async_refresh()
        
        _LOGGER.info("Refreshed data for all Marstek devices")
    
    hass.services.async_register(
        DOMAIN,
        "refresh_data",
        refresh_data,
        schema=REFRESH_DATA_SCHEMA,
    )


async def async_remove_services(hass: HomeAssistant) -> None:
    """Remove services for Marstek integration."""
    hass.services.async_remove(DOMAIN, "refresh_data")