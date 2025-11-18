#!/usr/bin/env python3
"""
Generate realistic mock meter readings to populate the dashboard

This generates believable data based on typical household usage patterns:
- Water: Peak usage during morning (7-9am) and evening (6-9pm) for showers, cooking, cleaning
- Electric: Variable usage with higher consumption during day, peaks during morning/evening
- Gas: Heating patterns with higher usage in cold months and during morning/evening
"""

import os
import sys
from datetime import datetime, timedelta
import random
import math

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from influxdb_writer import write_reading_to_influxdb

def get_time_of_day_multiplier(hour):
    """
    Get usage multiplier based on time of day
    Returns multiplier for typical household activity:
    - Night (12am-6am): 0.1-0.3 (minimal usage)
    - Morning (6am-9am): 1.5-2.0 (shower, breakfast, getting ready)
    - Day (9am-5pm): 0.5-0.8 (work hours, some at home)
    - Evening (5pm-10pm): 1.2-1.8 (dinner, activities, peak usage)
    - Late evening (10pm-12am): 0.4-0.7 (winding down)
    """
    if 0 <= hour < 6:  # Night
        return random.uniform(0.1, 0.3)
    elif 6 <= hour < 9:  # Morning peak
        return random.uniform(1.5, 2.0)
    elif 9 <= hour < 17:  # Day
        return random.uniform(0.5, 0.8)
    elif 17 <= hour < 22:  # Evening peak
        return random.uniform(1.2, 1.8)
    else:  # Late evening
        return random.uniform(0.4, 0.7)

def get_day_of_week_multiplier(day_of_week):
    """
    Get usage multiplier based on day of week
    0 = Monday, 6 = Sunday
    Weekends have slightly higher usage (people home more)
    """
    if day_of_week >= 5:  # Weekend
        return random.uniform(1.1, 1.3)
    else:  # Weekday
        return random.uniform(0.9, 1.1)

def generate_mock_readings(days=30):
    """Generate realistic mock readings for water, electric, and gas meters"""

    # Starting values (cumulative meter readings)
    water_base = 1250000  # gallons (typical residential meter after several years)
    electric_base = 45000  # kWh (typical after several years of service)
    gas_base = 12000  # CCF (hundred cubic feet, typical after several years)

    # Base consumption rates per 10 minutes (will be modified by time/day multipliers)
    water_base_rate = 1.5  # gallons per 10 min (avg ~216 gal/day = typical household)
    electric_base_rate = 2.0  # kWh per 10 min (avg ~28.8 kWh/day = ~865 kWh/month)
    gas_base_rate = 0.6  # CCF per 10 min (avg ~86 CCF/day, varies greatly by season)

    # Current month for seasonal adjustment (November = 11)
    current_month = datetime.now().month

    # Seasonal multiplier for gas (heating) - higher in winter months
    if current_month in [12, 1, 2]:  # Winter
        gas_seasonal = random.uniform(1.8, 2.2)
    elif current_month in [3, 4, 10, 11]:  # Spring/Fall
        gas_seasonal = random.uniform(1.0, 1.4)
    else:  # Summer
        gas_seasonal = random.uniform(0.3, 0.6)

    # Generate data going back in time
    now = datetime.now()
    total_readings = days * 24 * 6  # readings per day (every 10 minutes)

    print(f"Generating {days} days of realistic meter data...")
    print(f"Total readings per meter: {total_readings}")
    print(f"Seasonal gas multiplier (month {current_month}): {gas_seasonal:.2f}x")
    print()

    # Cumulative readings
    water_cumulative = water_base
    electric_cumulative = electric_base
    gas_cumulative = gas_base

    for i in range(total_readings):
        # Calculate timestamp (going backwards from now)
        minutes_ago = 10 * (total_readings - 1 - i)
        timestamp = now - timedelta(minutes=minutes_ago)

        # Get time-based multipliers
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        time_mult = get_time_of_day_multiplier(hour)
        day_mult = get_day_of_week_multiplier(day_of_week)

        # Add some random variation (simulates variable usage)
        random_var = random.uniform(0.8, 1.2)

        # Calculate incremental usage for this 10-minute period
        water_increment = water_base_rate * time_mult * day_mult * random_var
        electric_increment = electric_base_rate * time_mult * day_mult * random_var
        gas_increment = gas_base_rate * time_mult * day_mult * gas_seasonal * random_var

        # Add occasional spikes (simulates specific activities)
        if random.random() < 0.05:  # 5% chance of spike
            water_increment *= random.uniform(2, 4)  # Washing machine, shower, etc.
        if random.random() < 0.08:  # 8% chance of spike
            electric_increment *= random.uniform(1.5, 3)  # Dryer, AC, oven, etc.
        if random.random() < 0.04 and gas_seasonal > 1.0:  # 4% chance of spike in heating season
            gas_increment *= random.uniform(1.5, 2.5)  # Furnace cycling

        # Update cumulative readings
        water_cumulative += water_increment
        electric_cumulative += electric_increment
        gas_cumulative += gas_increment

        # Water meter data
        water_data = {
            "meter_type": "water",
            "total_reading": water_cumulative,
            "digital_reading": int(water_cumulative),
            "dial_reading": water_cumulative - int(water_cumulative),
            "confidence": random.choices(
                ["high", "medium", "low"],
                weights=[70, 25, 5]  # 70% high, 25% medium, 5% low confidence
            )[0],
            "timestamp": timestamp.isoformat(),
            "api_usage": {
                "input_tokens": random.randint(1500, 2000),
                "output_tokens": random.randint(150, 200)
            }
        }

        # Electric meter data
        electric_data = {
            "meter_type": "electric",
            "total_reading": electric_cumulative,
            "digital_reading": int(electric_cumulative),
            "dial_reading": electric_cumulative - int(electric_cumulative),
            "confidence": random.choices(
                ["high", "medium", "low"],
                weights=[75, 20, 5]
            )[0],
            "timestamp": timestamp.isoformat(),
            "api_usage": {
                "input_tokens": random.randint(1500, 2000),
                "output_tokens": random.randint(150, 200)
            }
        }

        # Gas meter data
        gas_data = {
            "meter_type": "gas",
            "total_reading": gas_cumulative,
            "digital_reading": int(gas_cumulative),
            "dial_reading": gas_cumulative - int(gas_cumulative),
            "confidence": random.choices(
                ["high", "medium", "low"],
                weights=[80, 15, 5]
            )[0],
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

        # Progress indicator
        if (i + 1) % (total_readings // 20) == 0:
            percent = ((i + 1) / total_readings) * 100
            days_done = (i + 1) / (24 * 6)
            print(f"  {percent:.0f}% - Generated {days_done:.1f} days of data...")

    # Print summary statistics
    print()
    print("=" * 70)
    print("Generation Complete - Summary Statistics")
    print("=" * 70)
    total_water = water_cumulative - water_base
    total_electric = electric_cumulative - electric_base
    total_gas = gas_cumulative - gas_base

    print(f"Water Usage:    {total_water:,.1f} gallons over {days} days ({total_water/days:.1f} gal/day avg)")
    print(f"Electric Usage: {total_electric:,.1f} kWh over {days} days ({total_electric/days:.1f} kWh/day avg)")
    print(f"Gas Usage:      {total_gas:,.1f} CCF over {days} days ({total_gas/days:.1f} CCF/day avg)")
    print()

if __name__ == "__main__":
    print("=" * 70)
    print("Realistic Utility Meter Data Generator")
    print("=" * 70)
    print()

    # Allow customization via command line
    days = 30
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
            if days < 1 or days > 365:
                print("Error: Days must be between 1 and 365")
                sys.exit(1)
        except ValueError:
            print("Error: Invalid number of days")
            print("Usage: python generate_mock_data.py [days]")
            print("Example: python generate_mock_data.py 30")
            sys.exit(1)

    try:
        generate_mock_readings(days)
        print("✓ Successfully generated all mock data!")
        print()
        print("Next steps:")
        print("  1. Access Grafana at http://localhost:3000 (admin/admin123456)")
        print("  2. View the Utility Meters Dashboard")
        print("  3. Explore usage patterns and trends")
        print()
    except Exception as e:
        print(f"\n✗ Error generating data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
