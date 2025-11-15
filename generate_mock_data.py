#!/usr/bin/env python3
"""
Generate mock meter readings to populate the dashboard
"""

import os
import sys
from datetime import datetime, timedelta
import random

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from influxdb_writer import write_reading_to_influxdb

def generate_mock_readings():
    """Generate mock readings for water, electric, and gas meters"""

    # Starting values
    water_base = 1250000  # gallons
    electric_base = 45000  # kWh
    gas_base = 12000  # CCF

    # Generate 24 hours of data (every 10 minutes)
    now = datetime.now()

    for i in range(144):  # 24 hours * 6 readings per hour
        timestamp = now - timedelta(minutes=10 * (143 - i))

        # Water meter (slow increase)
        water_reading = water_base + (i * random.uniform(0.5, 2.0))
        water_data = {
            "meter_type": "water",
            "total_reading": water_reading,
            "digital_reading": int(water_reading),
            "dial_reading": water_reading - int(water_reading),
            "confidence": random.choice(["high", "high", "high", "medium", "medium", "low"]),
            "timestamp": timestamp.isoformat(),
            "api_usage": {
                "input_tokens": random.randint(1500, 2000),
                "output_tokens": random.randint(150, 200)
            }
        }

        # Electric meter (medium increase)
        electric_reading = electric_base + (i * random.uniform(1.0, 3.0))
        electric_data = {
            "meter_type": "electric",
            "total_reading": electric_reading,
            "digital_reading": int(electric_reading),
            "dial_reading": electric_reading - int(electric_reading),
            "confidence": random.choice(["high", "high", "medium", "medium", "low"]),
            "timestamp": timestamp.isoformat(),
            "api_usage": {
                "input_tokens": random.randint(1500, 2000),
                "output_tokens": random.randint(150, 200)
            }
        }

        # Gas meter (slow increase)
        gas_reading = gas_base + (i * random.uniform(0.2, 1.0))
        gas_data = {
            "meter_type": "gas",
            "total_reading": gas_reading,
            "digital_reading": int(gas_reading),
            "dial_reading": gas_reading - int(gas_reading),
            "confidence": random.choice(["high", "high", "high", "medium", "low"]),
            "timestamp": timestamp.isoformat(),
            "api_usage": {
                "input_tokens": random.randint(1500, 2000),
                "output_tokens": random.randint(150, 200)
            }
        }

        # Write to InfluxDB
        write_reading_to_influxdb(water_data)
        write_reading_to_influxdb(electric_data)
        write_reading_to_influxdb(gas_data)

        if (i + 1) % 24 == 0:
            print(f"✓ Generated {i + 1} readings per meter ({(i+1)//6} hours of data)")

if __name__ == "__main__":
    print("Generating mock meter data...")
    print("This will create 24 hours of data for water, electric, and gas meters")

    try:
        generate_mock_readings()
        print("\n✓ Successfully generated all mock data!")
        print("Dashboard should now show data at http://localhost:5173")
    except Exception as e:
        print(f"\n✗ Error generating data: {e}")
        sys.exit(1)
