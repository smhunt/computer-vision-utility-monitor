#!/usr/bin/env python3
"""
Write water meter readings to InfluxDB for Grafana visualization

Usage:
    from influxdb_writer import write_reading_to_influxdb
    write_reading_to_influxdb(reading_dict, influxdb_url="http://localhost:8086")
"""

import os
from typing import Dict
from datetime import datetime


def write_reading_to_influxdb(reading: Dict, influxdb_url: str = None):
    """Write a meter reading to InfluxDB"""

    if influxdb_url is None:
        influxdb_url = os.getenv("INFLUXDB_URL", "http://localhost:8086")

    try:
        from influxdb_client import InfluxDBClient
        from influxdb_client.client.write_api import SYNCHRONOUS
    except ImportError:
        print("Warning: influxdb-client not installed")
        print("Install with: pip install influxdb-client")
        return False

    try:
        # Initialize InfluxDB client
        client = InfluxDBClient(
            url=influxdb_url,
            org="water-meter",
            token=os.getenv("INFLUXDB_TOKEN", "test-token")
        )

        write_api = client.write_api(write_options=SYNCHRONOUS)

        # Prepare data point
        if "error" in reading:
            # Log errors separately
            point = {
                "measurement": "water_meter_error",
                "tags": {
                    "camera": os.getenv("WYZE_CAM_IP", "unknown"),
                    "error_type": reading.get("error", "unknown")
                },
                "fields": {
                    "value": 1
                },
                "time": reading.get("timestamp", datetime.now().isoformat())
            }
        else:
            # Log successful reading
            point = {
                "measurement": "water_meter",
                "tags": {
                    "camera": os.getenv("WYZE_CAM_IP", "unknown"),
                    "confidence": reading.get("confidence", "unknown")
                },
                "fields": {
                    "total_reading": float(reading.get("total_reading", 0)),
                    "digital_reading": int(reading.get("digital_reading", 0)),
                    "dial_reading": float(reading.get("dial_reading", 0)),
                    "api_input_tokens": reading.get("api_usage", {}).get("input_tokens", 0),
                    "api_output_tokens": reading.get("api_usage", {}).get("output_tokens", 0)
                },
                "time": reading.get("timestamp", datetime.now().isoformat())
            }

        # Write to InfluxDB
        write_api.write(
            bucket="water_meter",
            org="water-meter",
            record=point
        )

        client.close()
        return True

    except Exception as e:
        print(f"Warning: Failed to write to InfluxDB: {e}")
        return False


if __name__ == "__main__":
    # Test
    test_reading = {
        "digital_reading": 226,
        "dial_reading": 0.125,
        "total_reading": 226.125,
        "confidence": "high",
        "timestamp": datetime.now().isoformat(),
        "api_usage": {
            "input_tokens": 1796,
            "output_tokens": 165
        }
    }

    if write_reading_to_influxdb(test_reading):
        print("✓ Successfully wrote to InfluxDB")
    else:
        print("✗ Failed to write to InfluxDB (service may not be running)")
