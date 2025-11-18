#!/usr/bin/env python3
"""
MQTT Publisher for Utility Meter Data

This script reads meter data from InfluxDB and publishes it to MQTT
for Home Assistant auto-discovery. This is an alternative to the
custom integration for users who prefer MQTT.

Usage:
    python mqtt_publisher.py [--interval SECONDS]

Environment Variables:
    INFLUXDB_URL: InfluxDB URL (default: http://localhost:8086)
    INFLUXDB_TOKEN: InfluxDB authentication token
    INFLUXDB_ORG: InfluxDB organization (default: ecoworks)
    INFLUXDB_BUCKET: InfluxDB bucket (default: utility_meters)
    MQTT_BROKER: MQTT broker address (default: localhost)
    MQTT_PORT: MQTT broker port (default: 1883)
    MQTT_USERNAME: MQTT username (optional)
    MQTT_PASSWORD: MQTT password (optional)
    MQTT_DISCOVERY_PREFIX: Home Assistant MQTT discovery prefix (default: homeassistant)
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)


class MQTTPublisher:
    """Publishes utility meter data to MQTT with Home Assistant discovery."""

    def __init__(self):
        """Initialize the MQTT publisher."""
        # InfluxDB configuration
        self.influxdb_url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        self.influxdb_token = os.getenv("INFLUXDB_TOKEN", "test-token")
        self.influxdb_org = os.getenv("INFLUXDB_ORG", "ecoworks")
        self.influxdb_bucket = os.getenv("INFLUXDB_BUCKET", "utility_meters")

        # MQTT configuration
        self.mqtt_broker = os.getenv("MQTT_BROKER", "localhost")
        self.mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        self.mqtt_username = os.getenv("MQTT_USERNAME")
        self.mqtt_password = os.getenv("MQTT_PASSWORD")
        self.discovery_prefix = os.getenv("MQTT_DISCOVERY_PREFIX", "homeassistant")

        # Initialize clients
        self.mqtt_client = None
        self.influxdb_client = None

        # Meter types
        self.meter_types = ["water", "electric", "gas"]

        # Meter configuration
        self.meter_config = {
            "water": {
                "name": "Water Meter",
                "unit": "gal",
                "device_class": "water",
                "icon": "mdi:water",
            },
            "electric": {
                "name": "Electric Meter",
                "unit": "kWh",
                "device_class": "energy",
                "icon": "mdi:flash",
            },
            "gas": {
                "name": "Gas Meter",
                "unit": "CCF",
                "device_class": "gas",
                "icon": "mdi:fire",
            },
        }

    def setup_mqtt(self):
        """Setup MQTT client connection."""
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            _LOGGER.error("paho-mqtt not installed. Install with: pip install paho-mqtt")
            sys.exit(1)

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                _LOGGER.info("Connected to MQTT broker at %s:%s", self.mqtt_broker, self.mqtt_port)
            else:
                _LOGGER.error("Failed to connect to MQTT broker, return code: %s", rc)

        def on_disconnect(client, userdata, rc):
            if rc != 0:
                _LOGGER.warning("Unexpected MQTT disconnection, return code: %s", rc)

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_disconnect = on_disconnect

        if self.mqtt_username and self.mqtt_password:
            self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)

        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            time.sleep(1)  # Allow connection to establish
        except Exception as e:
            _LOGGER.error("Failed to connect to MQTT broker: %s", e)
            sys.exit(1)

    def setup_influxdb(self):
        """Setup InfluxDB client connection."""
        try:
            from influxdb_client import InfluxDBClient
        except ImportError:
            _LOGGER.error("influxdb-client not installed. Install with: pip install influxdb-client")
            sys.exit(1)

        try:
            self.influxdb_client = InfluxDBClient(
                url=self.influxdb_url,
                token=self.influxdb_token,
                org=self.influxdb_org,
            )
            # Test connection
            health = self.influxdb_client.health()
            if health.status == "pass":
                _LOGGER.info("Connected to InfluxDB at %s", self.influxdb_url)
            else:
                _LOGGER.error("InfluxDB is not healthy: %s", health.status)
                sys.exit(1)
        except Exception as e:
            _LOGGER.error("Failed to connect to InfluxDB: %s", e)
            sys.exit(1)

    def publish_discovery_config(self, meter_type: str):
        """Publish MQTT discovery configuration for a meter."""
        config = self.meter_config[meter_type]

        # Device information (groups all meters together)
        device = {
            "identifiers": ["utility_meters_vision"],
            "name": "Utility Meters Vision Monitor",
            "model": "Computer Vision Monitor",
            "manufacturer": "Computer Vision Utility Monitor",
            "sw_version": "1.0.0",
        }

        # Sensor configuration
        sensor_config = {
            "name": config["name"],
            "unique_id": f"utility_meter_{meter_type}",
            "state_topic": f"{self.discovery_prefix}/sensor/utility_meters/{meter_type}/state",
            "json_attributes_topic": f"{self.discovery_prefix}/sensor/utility_meters/{meter_type}/attributes",
            "unit_of_measurement": config["unit"],
            "device_class": config["device_class"],
            "state_class": "total_increasing",
            "icon": config["icon"],
            "device": device,
        }

        # Publish discovery config
        config_topic = f"{self.discovery_prefix}/sensor/utility_meters/{meter_type}/config"
        payload = json.dumps(sensor_config)

        result = self.mqtt_client.publish(config_topic, payload, retain=True)
        if result.rc == 0:
            _LOGGER.debug("Published discovery config for %s meter", meter_type)
        else:
            _LOGGER.error("Failed to publish discovery config for %s meter", meter_type)

    def fetch_meter_data(self, meter_type: str) -> Optional[Dict]:
        """Fetch latest meter data from InfluxDB."""
        query = f"""
        from(bucket: "{self.influxdb_bucket}")
          |> range(start: -1h)
          |> filter(fn: (r) => r["_measurement"] == "meter_reading")
          |> filter(fn: (r) => r["meter_type"] == "{meter_type}")
          |> filter(fn: (r) => r["_field"] == "value" or r["_field"] == "total_reading" or r["_field"] == "digital_reading" or r["_field"] == "dial_reading")
          |> last()
        """

        try:
            query_api = self.influxdb_client.query_api()
            tables = query_api.query(query, org=self.influxdb_org)

            meter_data = {
                "total_reading": None,
                "digital_reading": None,
                "dial_reading": None,
                "confidence": None,
                "timestamp": None,
                "camera": None,
            }

            for table in tables:
                for record in table.records:
                    field = record.get_field()
                    value = record.get_value()

                    if field == "value" or field == "total_reading":
                        meter_data["total_reading"] = value
                        meter_data["timestamp"] = record.get_time()
                    elif field == "digital_reading":
                        meter_data["digital_reading"] = value
                    elif field == "dial_reading":
                        meter_data["dial_reading"] = value

                    # Get tags
                    if "confidence" in record.values:
                        meter_data["confidence"] = record.values["confidence"]
                    if "camera" in record.values:
                        meter_data["camera"] = record.values["camera"]

            if meter_data["total_reading"] is not None:
                return meter_data
            else:
                _LOGGER.warning("No data found for %s meter in the last hour", meter_type)
                return None

        except Exception as e:
            _LOGGER.error("Error fetching data for %s meter: %s", meter_type, e)
            return None

    def publish_meter_state(self, meter_type: str, meter_data: Dict):
        """Publish meter state and attributes to MQTT."""
        # Publish state (just the reading value)
        state_topic = f"{self.discovery_prefix}/sensor/utility_meters/{meter_type}/state"
        state_value = str(meter_data["total_reading"])

        result = self.mqtt_client.publish(state_topic, state_value)
        if result.rc == 0:
            _LOGGER.debug("Published state for %s meter: %s", meter_type, state_value)
        else:
            _LOGGER.error("Failed to publish state for %s meter", meter_type)

        # Publish attributes
        attributes = {
            "meter_type": meter_type,
        }

        if meter_data.get("digital_reading") is not None:
            attributes["digital_reading"] = meter_data["digital_reading"]
        if meter_data.get("dial_reading") is not None:
            attributes["dial_reading"] = round(meter_data["dial_reading"], 3)
        if meter_data.get("confidence"):
            attributes["confidence"] = meter_data["confidence"]
        if meter_data.get("camera"):
            attributes["camera"] = meter_data["camera"]
        if meter_data.get("timestamp"):
            timestamp = meter_data["timestamp"]
            if isinstance(timestamp, datetime):
                attributes["last_reading"] = timestamp.isoformat()
            else:
                attributes["last_reading"] = str(timestamp)

        attr_topic = f"{self.discovery_prefix}/sensor/utility_meters/{meter_type}/attributes"
        attr_payload = json.dumps(attributes)

        result = self.mqtt_client.publish(attr_topic, attr_payload)
        if result.rc == 0:
            _LOGGER.debug("Published attributes for %s meter", meter_type)
        else:
            _LOGGER.error("Failed to publish attributes for %s meter", meter_type)

    def publish_all_meters(self):
        """Fetch and publish data for all meter types."""
        for meter_type in self.meter_types:
            meter_data = self.fetch_meter_data(meter_type)
            if meter_data:
                self.publish_meter_state(meter_type, meter_data)
                _LOGGER.info(
                    "Published %s meter: %s %s (confidence: %s)",
                    meter_type,
                    meter_data["total_reading"],
                    self.meter_config[meter_type]["unit"],
                    meter_data.get("confidence", "unknown")
                )

    def run(self, interval: int = 60):
        """Run the publisher in a loop."""
        _LOGGER.info("Starting MQTT publisher with %s second interval", interval)

        # Setup connections
        self.setup_influxdb()
        self.setup_mqtt()

        # Publish discovery configs
        _LOGGER.info("Publishing Home Assistant discovery configurations...")
        for meter_type in self.meter_types:
            self.publish_discovery_config(meter_type)

        # Main loop
        try:
            while True:
                _LOGGER.info("Fetching and publishing meter data...")
                self.publish_all_meters()
                _LOGGER.info("Sleeping for %s seconds...", interval)
                time.sleep(interval)

        except KeyboardInterrupt:
            _LOGGER.info("Shutting down...")
        finally:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            if self.influxdb_client:
                self.influxdb_client.close()

    def publish_once(self):
        """Publish data once and exit."""
        _LOGGER.info("Publishing data once...")

        # Setup connections
        self.setup_influxdb()
        self.setup_mqtt()

        # Publish discovery configs
        for meter_type in self.meter_types:
            self.publish_discovery_config(meter_type)

        # Publish current data
        self.publish_all_meters()

        # Cleanup
        time.sleep(1)  # Allow messages to be sent
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        if self.influxdb_client:
            self.influxdb_client.close()

        _LOGGER.info("Done!")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Publish utility meter data from InfluxDB to MQTT for Home Assistant"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Update interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Publish once and exit (useful for testing or cron jobs)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    publisher = MQTTPublisher()

    if args.once:
        publisher.publish_once()
    else:
        publisher.run(interval=args.interval)


if __name__ == "__main__":
    main()
