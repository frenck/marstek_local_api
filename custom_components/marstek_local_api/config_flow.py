"""Config flow for Marstek integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_DESTINATION_PORT,
    CONF_DEVICES,
    CONF_IP_ADDRESS,
    CONF_POLLING_INTERVAL,
    CONF_SOURCE_PORT,
    DEFAULT_DESTINATION_PORT,
    DEFAULT_POLLING_INTERVAL,
    DEFAULT_SOURCE_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class MarstekConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Marstek."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._devices = []
            return await self.async_step_integration_config()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )

    async def async_step_integration_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle integration configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._polling_interval = user_input[CONF_POLLING_INTERVAL]
            self._source_port = user_input[CONF_SOURCE_PORT]
            return await self.async_step_add_device()

        return self.async_show_form(
            step_id="integration_config",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_POLLING_INTERVAL, default=DEFAULT_POLLING_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=3600)),
                vol.Required(
                    CONF_SOURCE_PORT, default=DEFAULT_SOURCE_PORT
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            }),
            errors=errors,
        )

    async def async_step_add_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle adding a device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input.get("add_device", False):
                device = {
                    CONF_IP_ADDRESS: user_input[CONF_IP_ADDRESS],
                    CONF_DESTINATION_PORT: user_input[CONF_DESTINATION_PORT],
                }
                self._devices.append(device)
                
                # Show form again to add more devices
                return await self.async_step_add_device()
            else:
                # Finish configuration
                if not self._devices:
                    errors["base"] = "no_devices"
                else:
                    return self.async_create_entry(
                        title="Marstek Battery System",
                        data={
                            CONF_POLLING_INTERVAL: self._polling_interval,
                            CONF_SOURCE_PORT: self._source_port,
                            CONF_DEVICES: self._devices,
                        },
                    )

        return self.async_show_form(
            step_id="add_device",
            data_schema=vol.Schema({
                vol.Required(CONF_IP_ADDRESS): cv.string,
                vol.Required(
                    CONF_DESTINATION_PORT, default=DEFAULT_DESTINATION_PORT
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
                vol.Required("add_device", default=True): cv.boolean,
            }),
            errors=errors,
            description_placeholders={
                "device_count": str(len(self._devices)),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> MarstekOptionsFlow:
        """Create the options flow."""
        return MarstekOptionsFlow(config_entry)


class MarstekOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Marstek."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry
        self._devices: list[dict[str, Any]] = list(config_entry.data.get(CONF_DEVICES, []))

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            action = user_input.get("action")
            if action == "modify_polling":
                return await self.async_step_modify_polling()
            elif action == "manage_devices":
                return await self.async_step_manage_devices()
            elif action == "add_device":
                return await self.async_step_add_device()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("action"): vol.In({
                    "modify_polling": "Modify polling interval",
                    "manage_devices": "Manage devices",
                    "add_device": "Add new device"
                }),
            }),
        )

    async def async_step_modify_polling(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Modify polling interval."""
        if user_input is not None:
            # Update only the polling interval, keep existing data
            new_data = dict(self._config_entry.data)
            new_data[CONF_POLLING_INTERVAL] = user_input[CONF_POLLING_INTERVAL]
            
            return self.async_create_entry(title="", data=new_data)

        return self.async_show_form(
            step_id="modify_polling",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_POLLING_INTERVAL,
                    default=self._config_entry.data.get(
                        CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=3600)),
            }),
        )

    async def async_step_manage_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage existing devices."""
        if user_input is not None:
            if "remove_device" in user_input:
                # Remove selected device
                device_to_remove = user_input["remove_device"]
                if device_to_remove < len(self._devices):
                    self._devices.pop(device_to_remove)
                
                # If no devices left, show error
                if not self._devices:
                    return self.async_show_form(
                        step_id="manage_devices",
                        data_schema=self._get_manage_devices_schema(),
                        errors={"base": "no_devices_remaining"},
                    )
                
                # Show updated list
                return await self.async_step_manage_devices()
            else:
                # Save changes and finish
                new_data = dict(self._config_entry.data)
                new_data[CONF_DEVICES] = self._devices
                return self.async_create_entry(title="", data=new_data)

        return self.async_show_form(
            step_id="manage_devices",
            data_schema=self._get_manage_devices_schema(),
        )

    async def async_step_add_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a new device."""
        if user_input is not None:
            # Add the new device
            device = {
                CONF_IP_ADDRESS: user_input[CONF_IP_ADDRESS],
                CONF_DESTINATION_PORT: user_input[CONF_DESTINATION_PORT],
            }
            self._devices.append(device)
            
            # Update the config entry
            new_data = dict(self._config_entry.data)
            new_data[CONF_DEVICES] = self._devices
            
            return self.async_create_entry(title="", data=new_data)

        return self.async_show_form(
            step_id="add_device",
            data_schema=vol.Schema({
                vol.Required(CONF_IP_ADDRESS): cv.string,
                vol.Required(
                    CONF_DESTINATION_PORT, default=DEFAULT_DESTINATION_PORT
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            }),
        )

    def _get_manage_devices_schema(self) -> vol.Schema:
        """Get schema for managing devices."""
        if not self._devices:
            return vol.Schema({})
        
        device_options = {}
        for i, device in enumerate(self._devices):
            device_options[i] = f"{device[CONF_IP_ADDRESS]}:{device[CONF_DESTINATION_PORT]}"
        
        return vol.Schema({
            vol.Optional("remove_device"): vol.In(device_options),
        })