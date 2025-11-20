#!/usr/bin/env python3
"""
InfluxDB Logger for Meter Readings
Logs meter readings to InfluxDB for graphing and analysis
"""

import os
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path

try:
    from influxdb_client import InfluxDBClient, Point
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUX_AVAILABLE = True
except ImportError:
    INFLUX_AVAILABLE = False
    print("Warning: influxdb-client not installed. Install with: pip install influxdb-client")


class MeterInfluxLogger:
    """Logs meter readings to InfluxDB"""

    def __init__(self,
                 url: str = None,
                 token: str = None,
                 org: str = None,
                 bucket: str = None):
        """
        Initialize InfluxDB logger

        Args:
            url: InfluxDB URL (default: from env INFLUXDB_URL)
            token: InfluxDB token (default: from env INFLUXDB_TOKEN)
            org: InfluxDB organization (default: from env INFLUXDB_ORG)
            bucket: InfluxDB bucket (default: from env INFLUXDB_BUCKET)
        """
        if not INFLUX_AVAILABLE:
            self.client = None
            self.write_api = None
            return

        self.url = url or os.getenv('INFLUXDB_URL', 'http://localhost:8086')
        self.token = token or os.getenv('INFLUXDB_TOKEN')
        self.org = org or os.getenv('INFLUXDB_ORG', 'ecoworks')
        self.bucket = bucket or os.getenv('INFLUXDB_BUCKET', 'utility_meters')

        if not self.token:
            print("Warning: INFLUXDB_TOKEN not set. Logging disabled.")
            self.client = None
            self.write_api = None
            return

        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            print(f"✓ Connected to InfluxDB: {self.url}")
        except Exception as e:
            print(f"Warning: Could not connect to InfluxDB: {e}")
            self.client = None
            self.write_api = None

    def log_reading(self,
                   meter_name: str,
                   total_reading: float,
                   digital_reading: float = None,
                   dial_reading: float = None,
                   confidence: str = None,
                   temperature_c: float = None,
                   timestamp: datetime = None) -> bool:
        """
        Log a meter reading to InfluxDB

        Args:
            meter_name: Name of the meter (e.g., 'water_main')
            total_reading: Total reading in cubic meters
            digital_reading: Digital display reading
            dial_reading: Dial reading
            confidence: Confidence level (high/medium/low)
            temperature_c: Temperature in Celsius (optional)
            timestamp: Reading timestamp (default: now)

        Returns:
            True if logged successfully, False otherwise
        """
        if not self.write_api:
            return False

        try:
            if timestamp is None:
                timestamp = datetime.utcnow()

            # Create point
            point = Point("meter_reading") \
                .tag("meter", meter_name) \
                .field("total_reading", float(total_reading))

            # Add optional fields
            if digital_reading is not None:
                point = point.field("digital_reading", float(digital_reading))

            if dial_reading is not None:
                point = point.field("dial_reading", float(dial_reading))

            if confidence:
                point = point.tag("confidence", confidence)

            if temperature_c is not None:
                point = point.field("temperature_c", float(temperature_c))

            # Set timestamp
            point = point.time(timestamp)

            # Write to InfluxDB
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True

        except Exception as e:
            print(f"Error logging to InfluxDB: {e}")
            return False

    def get_recent_readings(self,
                           meter_name: str,
                           hours: int = 24,
                           limit: int = 100) -> List[Dict]:
        """
        Get recent readings from InfluxDB

        Args:
            meter_name: Name of the meter
            hours: Number of hours to look back
            limit: Maximum number of readings to return

        Returns:
            List of reading dictionaries
        """
        if not self.client:
            return []

        try:
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -{hours}h)
              |> filter(fn: (r) => r["_measurement"] == "meter_reading")
              |> filter(fn: (r) => r["meter"] == "{meter_name}")
              |> filter(fn: (r) => r["_field"] == "total_reading")
              |> sort(columns: ["_time"], desc: true)
              |> limit(n: {limit})
            '''

            query_api = self.client.query_api()
            result = query_api.query(org=self.org, query=query)

            readings = []
            for table in result:
                for record in table.records:
                    readings.append({
                        'timestamp': record.get_time(),
                        'total_reading': record.get_value(),
                        'meter': record.values.get('meter')
                    })

            return readings

        except Exception as e:
            print(f"Error querying InfluxDB: {e}")
            return []

    def delete_reading(self,
                      meter_name: str,
                      start_time: datetime,
                      end_time: datetime) -> bool:
        """
        Delete readings from InfluxDB within a time range

        Args:
            meter_name: Name of the meter
            start_time: Start of time range
            end_time: End of time range

        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.client:
            return False

        try:
            delete_api = self.client.delete_api()

            predicate = f'_measurement="meter_reading" AND meter="{meter_name}"'

            delete_api.delete(
                start=start_time,
                stop=end_time,
                predicate=predicate,
                bucket=self.bucket,
                org=self.org
            )

            print(f"✓ Deleted readings for {meter_name} between {start_time} and {end_time}")
            return True

        except Exception as e:
            print(f"Error deleting from InfluxDB: {e}")
            return False

    def close(self):
        """Close InfluxDB client connection"""
        if self.client:
            self.client.close()


# Command-line interface for testing
if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    print("InfluxDB Logger Test")
    print("=" * 60)

    logger = MeterInfluxLogger()

    if logger.write_api:
        # Test logging
        print("\nTest: Logging a reading...")
        success = logger.log_reading(
            meter_name="water_main",
            total_reading=22.712,
            digital_reading=22,
            dial_reading=0.712,
            confidence="high"
        )

        if success:
            print("✓ Successfully logged test reading")
        else:
            print("✗ Failed to log test reading")

        # Test querying
        print("\nTest: Querying recent readings...")
        readings = logger.get_recent_readings("water_main", hours=24, limit=10)

        if readings:
            print(f"✓ Found {len(readings)} recent readings:")
            for reading in readings[:5]:
                print(f"  {reading['timestamp']}: {reading['total_reading']} m³")
        else:
            print("  No readings found")

        logger.close()
    else:
        print("\n✗ InfluxDB not available")
        print("\nTo enable InfluxDB logging:")
        print("  1. Install: pip install influxdb-client")
        print("  2. Set INFLUXDB_TOKEN in .env file")
        print("  3. Ensure InfluxDB is running")
