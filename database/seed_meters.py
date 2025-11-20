#!/usr/bin/env python3
"""
Seed the database with example meters
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

from src.database import get_db_session, Meter


def seed_meters():
    """Seed database with example meters"""
    print("\n" + "="*60)
    print("SEEDING METERS")
    print("="*60)

    example_meters = [
        {
            'name': 'water_main',
            'type': 'water',
            'location': 'Basement',
            'unit': 'm³',
            'camera_ip': os.getenv('WATER_CAM_IP', '10.10.10.207'),
            'camera_user': os.getenv('WATER_CAM_USER', 'root'),
            'camera_preset': 'optimal_day',
            'reading_interval_minutes': 60,
            'camera_enabled': True
        },
        {
            'name': 'electric_main',
            'type': 'electric',
            'location': 'Garage',
            'unit': 'kWh',
            'camera_ip': os.getenv('ELECTRIC_CAM_IP', '10.10.10.208'),
            'camera_user': os.getenv('ELECTRIC_CAM_USER', 'root'),
            'camera_preset': 'optimal_day',
            'reading_interval_minutes': 15,
            'camera_enabled': False  # Not yet configured
        },
        {
            'name': 'gas_main',
            'type': 'gas',
            'location': 'Exterior',
            'unit': 'm³',
            'camera_ip': os.getenv('GAS_CAM_IP', '10.10.10.209'),
            'camera_user': os.getenv('GAS_CAM_USER', 'root'),
            'camera_preset': 'optimal_day',
            'reading_interval_minutes': 60,
            'camera_enabled': False  # Not yet configured
        }
    ]

    with get_db_session() as session:
        seeded = 0
        skipped = 0

        for meter_data in example_meters:
            # Check if meter already exists
            existing = session.query(Meter).filter_by(name=meter_data['name']).first()

            if existing:
                print(f"⏭️  Skipping {meter_data['name']} (already exists)")
                skipped += 1
                continue

            # Create meter
            meter = Meter(**meter_data)
            session.add(meter)
            print(f"✓ Seeded meter: {meter.name} ({meter.type}) at {meter.camera_ip}")
            seeded += 1

        session.flush()

    print(f"\nSeeded: {seeded}, Skipped: {skipped}")
    print(f"\n✓ Database now has {seeded + skipped} meter(s)")
    print("\nTo view meters:")
    print("  • Web UI: http://localhost:2500/api/db/meters")
    print("  • PostgreSQL: docker exec utility-monitor-postgres psql -U postgres -d utility_monitor -c 'SELECT * FROM meters;'")


def main():
    """Run seeding"""
    try:
        seed_meters()
    except Exception as e:
        print(f"\n❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
