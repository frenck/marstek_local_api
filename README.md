# Marstek Battery Integration for Home Assistant

A custom Home Assistant integration for monitoring Marstek battery systems via UDP communication on the device's local API.

## Features

- Monitors multiple Marstek battery devices simultaneously
- Real-time battery status including:
  - State of charge (%)
  - Current and maximum capacity (kWh)
  - Temperature (°C)
  - Grid power (W)
  - Total grid input/output energy (kWh)
- Integration-level totals across all devices
- Configurable polling intervals
- UDP communication with retry mechanism
- Device auto-discovery via UDP responses

## Installation

### HACS (Recommended)

1. Add this repository to HACS as a custom repository
2. Search for "Marstek Battery System" in HACS
3. Install the integration
4. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/marstek_local_api` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Go to Configuration > Integrations
4. Click the + button and search for "Marstek"

## Configuration

### Integration Setup

1. Go to Configuration > Integrations
2. Click the + button and search for "Marstek"
3. Configure the global settings:
   - **Polling Interval**: How often to poll devices (default: 30 seconds)
   - **Source Port**: UDP port used by Home Assistant (default: 30000)

### Adding Devices

For each Marstek battery device:
1. Enter a **Device Name** (e.g., "Main Battery", "Garage Battery")
2. Enter the **IP Address** of the device
3. Enter the **Destination Port** (default: 30000)
4. Choose whether to add another device or finish setup

### Managing Devices After Setup

To add or remove devices after initial configuration:
1. Go to **Settings → Integrations**
2. Find **Marstek Battery System** 
3. Click the **Configure** button (gear icon)
4. Choose from:
   - **Add new device**: Add another battery device
   - **Manage devices**: Remove existing devices
   - **Modify polling interval**: Change polling frequency

## Device Requirements

- Marstek battery devices must support UDP communication
- Devices must respond to `Bat.GetStatus` and `ES.GetStatus` JSON-RPC requests
- Source and destination ports should match (Marstek requirement)
- Devices should be accessible on your local network

## Sensors

### Per Device Sensors

- **Identifier**: Device identifier string
- **State of Charge**: Battery charge percentage (%)
- **Current Capacity**: Current battery capacity (kWh)
- **Max Capacity**: Maximum battery capacity (kWh)
- **Temperature**: Battery temperature (°C)
- **Grid Power**: Current grid power (W)
- **Total Grid Output Energy**: Cumulative energy sent to grid (kWh)
- **Total Grid Input Energy**: Cumulative energy received from grid (kWh)

### Integration Total Sensors

- **Total Current Capacity**: Sum of all devices' current capacity (kWh)
- **Total Max Capacity**: Sum of all devices' maximum capacity (kWh)
- **Total Grid Power**: Sum of all devices' grid power (W)

## Services

### `marstek.refresh_data`

Manually refresh data from all Marstek devices.

## UDP Communication Protocol

The integration uses JSON-RPC over UDP:

### Battery Status Request
```json
{"id": 123, "method": "Bat.GetStatus", "params": {"id": 0}}
```

### Energy System Status Request
```json
{"id": 123, "method": "ES.GetStatus", "params": {"id": 0}}
```

### Response Format
```json
{
    "id": 123,
    "src": "VenusE-24215edb2561",
    "result": {
        "id": 0,
        "soc": 85,
        "bat_capacity": 4352.0,
        "rated_capacity": 5120.0,
        "bat_temp": 23.5
    }
}
```

## Troubleshooting

### Common Issues

1. **No data from devices**: Check IP addresses and port configuration
2. **Timeout errors**: Verify network connectivity and firewall settings
3. **Port conflicts**: Ensure source port is not used by other applications

### Debugging

Enable debug logging by adding to `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.marstek_local_api: debug
```

## Support

For issues and feature requests, please use the GitHub repository:
https://github.com/DoctaShizzle/marstek_local_api

## License

This project is licensed under the MIT License.