"""Constants for the Utility Meters Vision Monitor integration."""

# Integration domain
DOMAIN = "utility_meters"

# Configuration keys
CONF_INFLUXDB_URL = "influxdb_url"
CONF_INFLUXDB_TOKEN = "influxdb_token"
CONF_INFLUXDB_ORG = "influxdb_org"
CONF_INFLUXDB_BUCKET = "influxdb_bucket"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_CAMERA_TAG = "camera_tag"

# Default values
DEFAULT_INFLUXDB_URL = "http://localhost:8086"
DEFAULT_INFLUXDB_ORG = "ecoworks"
DEFAULT_INFLUXDB_BUCKET = "utility_meters"
DEFAULT_SCAN_INTERVAL = 60  # seconds
DEFAULT_CAMERA_TAG = "unknown"

# Meter types
METER_TYPE_WATER = "water"
METER_TYPE_ELECTRIC = "electric"
METER_TYPE_GAS = "gas"

METER_TYPES = [METER_TYPE_WATER, METER_TYPE_ELECTRIC, METER_TYPE_GAS]

# Meter type configuration
METER_CONFIG = {
    METER_TYPE_WATER: {
        "name": "Water Meter",
        "unit": "gal",
        "device_class": "water",
        "state_class": "total_increasing",
        "icon": "mdi:water",
    },
    METER_TYPE_ELECTRIC: {
        "name": "Electric Meter",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:flash",
    },
    METER_TYPE_GAS: {
        "name": "Gas Meter",
        "unit": "CCF",
        "device_class": "gas",
        "state_class": "total_increasing",
        "icon": "mdi:fire",
    },
}

# InfluxDB query
INFLUXDB_QUERY_TEMPLATE = """
from(bucket: "{bucket}")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "meter_reading")
  |> filter(fn: (r) => r["meter_type"] == "{meter_type}")
  |> filter(fn: (r) => r["_field"] == "value" or r["_field"] == "total_reading" or r["_field"] == "digital_reading" or r["_field"] == "dial_reading")
  |> last()
"""
