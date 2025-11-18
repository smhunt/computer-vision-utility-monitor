# Home Assistant Integration for Computer Vision Utility Monitor

This is a custom Home Assistant integration that reads utility meter data from InfluxDB and exposes it as Home Assistant sensors. The integration supports water, electric, and gas meters with full support for the Home Assistant Energy Dashboard.

## Features

- **Three Meter Types**: Support for water, electric, and gas meters
- **InfluxDB Data Source**: Reads real-time meter data from your InfluxDB instance
- **Energy Dashboard Compatible**: Full support for Home Assistant's Energy Dashboard with proper state classes
- **Rich Attributes**: Each sensor includes confidence levels, digital/dial readings, and timestamps
- **UI Configuration**: Easy setup through Home Assistant's UI (no YAML required)
- **Device Registry**: Proper device grouping for all meter sensors
- **Automatic Updates**: Configurable polling interval (default: 60 seconds)
- **Async/Await**: Non-blocking implementation following Home Assistant best practices

## Supported Sensors

Each meter type is exposed as a separate sensor with the following properties:

### Water Meter
- **Device Class**: `water`
- **Unit**: Gallons (gal)
- **State Class**: `total_increasing` (for statistics)
- **Icon**: `mdi:water`

### Electric Meter
- **Device Class**: `energy`
- **Unit**: Kilowatt-hours (kWh)
- **State Class**: `total_increasing` (for Energy Dashboard)
- **Icon**: `mdi:flash`

### Gas Meter
- **Device Class**: `gas`
- **Unit**: CCF (hundred cubic feet)
- **State Class**: `total_increasing` (for statistics)
- **Icon**: `mdi:fire`

## Installation

### Method 1: Manual Installation

1. Copy the entire `custom_components/utility_meters` directory to your Home Assistant's `config/custom_components/` directory:

```bash
# From the project root
cp -r home_assistant/custom_components/utility_meters /path/to/homeassistant/config/custom_components/
```

2. Restart Home Assistant

3. Go to **Settings** > **Devices & Services** > **Add Integration**

4. Search for "Utility Meters Vision Monitor" and click to add it

### Method 2: Using HACS (Home Assistant Community Store)

Currently, this integration is not in the HACS default repository. To add it as a custom repository:

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Install the "Utility Meters Vision Monitor" integration
7. Restart Home Assistant
8. Add the integration through the UI

## Configuration

### Initial Setup

1. Navigate to **Settings** > **Devices & Services**
2. Click **Add Integration**
3. Search for "Utility Meters Vision Monitor"
4. Enter your configuration:

| Field | Description | Default | Required |
|-------|-------------|---------|----------|
| InfluxDB URL | The URL of your InfluxDB instance | `http://localhost:8086` | Yes |
| InfluxDB Token | Your InfluxDB authentication token | - | Yes |
| InfluxDB Organization | The organization name in InfluxDB | `ecoworks` | Yes |
| InfluxDB Bucket | The bucket where meter data is stored | `utility_meters` | Yes |
| Scan Interval | How often to poll for updates (seconds) | `60` | No |
| Camera Tag | Optional tag to identify the camera source | `unknown` | No |

### InfluxDB Token

To get your InfluxDB token:

1. Open InfluxDB UI (usually at `http://localhost:8086`)
2. Go to **Data** > **API Tokens**
3. Copy an existing token or create a new one with read access to the `utility_meters` bucket

For the default setup in this project, you can use the token from `grafana-provisioning/datasources/influxdb.yml`.

### Configuration Options

After initial setup, you can modify the following options:

- **Scan Interval**: Adjust polling frequency (10-3600 seconds)
- **Camera Tag**: Update the camera identifier

To modify options:
1. Go to **Settings** > **Devices & Services**
2. Find "Utility Meters Vision Monitor"
3. Click **Configure**

## Usage

### Viewing Sensors

After configuration, three sensors will be created:

- `sensor.water_meter` - Current water meter reading in gallons
- `sensor.electric_meter` - Current electric meter reading in kWh
- `sensor.gas_meter` - Current gas meter reading in CCF

Each sensor includes the following attributes:

- `digital_reading` - The integer portion of the meter reading
- `dial_reading` - The fractional portion from analog dials
- `confidence` - Reading confidence level (high/medium/low)
- `camera` - Camera tag identifier
- `last_reading` - ISO timestamp of the last reading
- `meter_type` - Type of meter (water/electric/gas)

### Energy Dashboard Integration

The electric sensor is automatically compatible with Home Assistant's Energy Dashboard:

1. Go to **Settings** > **Dashboards** > **Energy**
2. Click **Add Consumption**
3. Select `sensor.electric_meter` from the list
4. Configure the pricing if desired

The sensor uses the `total_increasing` state class, which allows Home Assistant to calculate usage over time and display statistics properly.

### Creating Dashboard Cards

#### Simple Entity Card

```yaml
type: entities
title: Utility Meters
entities:
  - entity: sensor.water_meter
    name: Water Usage
    icon: mdi:water
  - entity: sensor.electric_meter
    name: Electric Usage
    icon: mdi:flash
  - entity: sensor.gas_meter
    name: Gas Usage
    icon: mdi:fire
```

#### Gauge Card

```yaml
type: gauge
entity: sensor.water_meter
name: Water Meter
unit: gallons
min: 0
max: 2000000
severity:
  green: 0
  yellow: 1500000
  red: 1800000
```

#### Statistics Graph Card

```yaml
type: statistics-graph
entities:
  - sensor.electric_meter
title: Electric Usage
stat_types:
  - change
period: day
days_to_show: 7
```

### Automation Examples

#### Alert on Low Confidence Reading

```yaml
automation:
  - alias: "Low Confidence Meter Reading Alert"
    trigger:
      - platform: state
        entity_id:
          - sensor.water_meter
          - sensor.electric_meter
          - sensor.gas_meter
    condition:
      - condition: template
        value_template: "{{ state_attr(trigger.entity_id, 'confidence') == 'low' }}"
    action:
      - service: notify.mobile_app
        data:
          title: "Meter Reading Issue"
          message: "{{ state_attr(trigger.entity_id, 'friendly_name') }} has low confidence reading"
```

#### Track Daily Usage

```yaml
sensor:
  - platform: template
    sensors:
      daily_water_usage:
        friendly_name: "Daily Water Usage"
        unit_of_measurement: "gal"
        value_template: >
          {% set start = states('sensor.water_meter') | float %}
          {% set end = state_attr('sensor.water_meter', 'last_reading') | float %}
          {{ (end - start) | round(2) }}
```

## Data Model

The integration expects meter data in InfluxDB with the following structure:

### Measurement: `meter_reading`

**Tags:**
- `meter_type`: water, electric, or gas
- `confidence`: high, medium, or low
- `camera`: Camera identifier

**Fields:**
- `value` or `total_reading`: Total cumulative reading (float)
- `digital_reading`: Integer portion of reading (int)
- `dial_reading`: Fractional portion of reading (float)
- `api_input_tokens`: API tokens used for reading (int, optional)
- `api_output_tokens`: API tokens output (int, optional)

**Example InfluxDB Line Protocol:**
```
meter_reading,meter_type=water,confidence=high,camera=wyze_cam_1 value=1250347.256,digital_reading=1250347,dial_reading=0.256 1634567890000000000
```

## Troubleshooting

### Integration Not Appearing

1. Ensure the `custom_components/utility_meters` directory is in the correct location
2. Restart Home Assistant completely (not just reload)
3. Check Home Assistant logs for any errors: **Settings** > **System** > **Logs**

### Cannot Connect to InfluxDB

1. Verify InfluxDB is running: `curl http://localhost:8086/health`
2. Check that the InfluxDB URL is correct (use `http://localhost:8086` for local installations)
3. Verify the token has read permissions for the bucket
4. Ensure the organization and bucket names match your InfluxDB configuration

### Sensors Show "Unavailable"

1. Check that data exists in InfluxDB for all three meter types
2. Verify the query is returning data (use InfluxDB UI Data Explorer)
3. Check the logs for specific error messages
4. Ensure the scan interval isn't too short (minimum 10 seconds)

### No Data in Sensors

1. Verify the `generate_mock_data.py` script has been run to populate InfluxDB
2. Check that data is being written to the correct bucket
3. Ensure at least one reading exists for each meter type in the last hour
4. Use InfluxDB UI to manually query and verify data exists

### Debugging

Enable debug logging for the integration by adding this to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.utility_meters: debug
    influxdb_client: debug
```

Then restart Home Assistant and check the logs under **Settings** > **System** > **Logs**.

## Architecture

### Component Structure

```
custom_components/utility_meters/
├── __init__.py          # Main integration setup and coordinator
├── manifest.json        # Integration metadata and requirements
├── config_flow.py       # UI configuration flow
├── const.py            # Constants and configuration
├── sensor.py           # Sensor platform implementation
└── strings.json        # UI translations
```

### Data Flow

1. **Coordinator** (`__init__.py`): Manages data updates on a schedule
2. **Query** (`__init__.py`): Fetches latest meter readings from InfluxDB using Flux queries
3. **Sensors** (`sensor.py`): Subscribe to coordinator updates and expose data to Home Assistant
4. **Attributes**: Rich metadata attached to each sensor state

### Update Cycle

1. Every `scan_interval` seconds (default: 60)
2. Coordinator executes Flux query for each meter type
3. Latest reading (from last hour) is retrieved
4. Data is parsed and stored in coordinator
5. All sensors are notified of update
6. Home Assistant updates sensor states and attributes

## Advanced Configuration

### Custom InfluxDB Queries

The integration uses the following Flux query template (defined in `const.py`):

```flux
from(bucket: "{bucket}")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "meter_reading")
  |> filter(fn: (r) => r["meter_type"] == "{meter_type}")
  |> filter(fn: (r) => r["_field"] == "value" or r["_field"] == "total_reading" or r["_field"] == "digital_reading" or r["_field"] == "dial_reading")
  |> last()
```

This query looks for the most recent reading in the last hour. If your data retention or structure is different, you can modify the query in `const.py`.

### Multiple Cameras

To monitor multiple cameras with different meter sets:

1. Add the integration multiple times with different camera tags
2. Each instance will create separate sensors
3. Use camera tag to identify which physical meters are being read

### MQTT Alternative

While this integration uses InfluxDB, you can also publish meter readings to MQTT for Home Assistant discovery:

```python
import json
import paho.mqtt.client as mqtt

# MQTT configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT)

# Publish discovery config for Home Assistant
config = {
    "name": "Water Meter",
    "state_topic": "homeassistant/sensor/water_meter/state",
    "unit_of_measurement": "gal",
    "device_class": "water",
    "state_class": "total_increasing",
    "unique_id": "water_meter_001",
    "device": {
        "identifiers": ["utility_meters"],
        "name": "Utility Meters",
        "model": "Vision Monitor",
        "manufacturer": "Computer Vision Utility Monitor"
    }
}

client.publish(
    "homeassistant/sensor/water_meter/config",
    json.dumps(config),
    retain=True
)

# Publish state
client.publish(
    "homeassistant/sensor/water_meter/state",
    "1250347.256"
)
```

## Requirements

- Home Assistant 2023.1.0 or newer
- InfluxDB 2.x with Flux query language support
- Python 3.11+ (Home Assistant requirement)
- `influxdb-client` Python package (automatically installed)

## Development

### Project Structure

This integration follows Home Assistant's official integration standards:

- Async/await patterns for non-blocking I/O
- DataUpdateCoordinator for efficient polling
- Config flow for UI-based configuration
- Proper device and entity registry integration
- Type hints throughout
- Comprehensive error handling and logging

### Testing Locally

1. Copy the integration to your Home Assistant test instance
2. Use the `generate_mock_data.py` script to populate InfluxDB with test data
3. Add the integration through the UI
4. Monitor logs for any errors
5. Verify sensors appear and update correctly

### Contributing

Contributions are welcome! Please:

1. Follow Home Assistant's code style guidelines
2. Add appropriate logging
3. Update documentation for any new features
4. Test thoroughly with real and mock data

## License

This integration is part of the computer-vision-utility-monitor project. See the main project repository for license information.

## Support

For issues, questions, or feature requests:

1. Check the Troubleshooting section above
2. Review Home Assistant logs for error messages
3. Open an issue in the project repository
4. Include relevant log excerpts and configuration details

## Changelog

### Version 1.0.0 (Initial Release)

- Support for water, electric, and gas meters
- InfluxDB data source integration
- Home Assistant Energy Dashboard compatibility
- UI-based configuration flow
- Rich sensor attributes (confidence, digital/dial readings, timestamps)
- Device registry integration
- Configurable polling interval
- Comprehensive error handling and logging

## Acknowledgments

- Built for the [Computer Vision Utility Monitor](https://github.com/seanhunt/computer-vision-utility-monitor) project
- Follows [Home Assistant Integration Guidelines](https://developers.home-assistant.io/)
- Uses [InfluxDB Python Client](https://github.com/influxdata/influxdb-client-python)
