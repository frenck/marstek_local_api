# Marstek Integration Example Configuration

## Home Assistant Configuration

Add to your `configuration.yaml` for logging (optional):

```yaml
logger:
  logs:
    custom_components.marstek_local_api: info  # Change to 'debug' for troubleshooting
```

## Integration Configuration Examples

### Single Device Setup
- IP Address: `192.168.1.100`
- Destination Port: `30000`
- Polling Interval: `30` seconds
- Source Port: `30000`

### Multiple Device Setup
Device 1:
- IP Address: `192.168.1.100`
- Destination Port: `30000`

Device 2:
- IP Address: `192.168.1.101`
- Destination Port: `30000`

Device 3:
- IP Address: `192.168.1.102`
- Destination Port: `30000`

Common Settings:
- Polling Interval: `30` seconds
- Source Port: `30000`

## Network Requirements

1. Ensure your Home Assistant server can reach the Marstek devices
2. Check firewall settings allow UDP traffic on the configured ports
3. Verify devices are powered on and connected to the network
4. Test connectivity with ping before configuring the integration

## Automation Examples

### Low Battery Alert
```yaml
automation:
  - alias: "Marstek Low Battery Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.marstek_local_api_total_current_capacity
        below: 5  # kWh threshold
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "Battery capacity is low: {{ states('sensor.marstek_local_api_total_current_capacity') }} kWh"
```

### Grid Power Monitoring
```yaml
automation:
  - alias: "Marstek High Grid Usage"
    trigger:
      - platform: numeric_state
        entity_id: sensor.marstek_local_api_total_grid_power
        above: 2000  # Watts threshold
        for:
          minutes: 5
    action:
      - service: notify.home_assistant
        data:
          message: "High grid power usage detected: {{ states('sensor.marstek_local_api_total_grid_power') }} W"
```

## Dashboard Cards

### Battery Status Card
```yaml
type: entities
title: Marstek Battery Status
entities:
  - entity: sensor.marstek_local_api_total_current_capacity
    name: Current Capacity
  - entity: sensor.marstek_local_api_total_max_capacity
    name: Maximum Capacity
  - entity: sensor.marstek_local_api_total_grid_power
    name: Grid Power
```

### Individual Device Card
```yaml
type: vertical-stack
title: Battery Device Details
cards:
  - type: entities
    entities:
      - entity: sensor.venus_e_24215edb2561_state_of_charge
        name: State of Charge
      - entity: sensor.venus_e_24215edb2561_temperature
        name: Temperature
      - entity: sensor.venus_e_24215edb2561_grid_power
        name: Grid Power