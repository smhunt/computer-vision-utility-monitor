#!/usr/bin/env python3
"""
Quick integration test for PostgreSQL database
"""

import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

from src.database import (
    get_db_session,
    Meter,
    Snapshot,
    Bill,
    UserSettings
)


def test_meter_crud():
    """Test meter create/read operations"""
    print("\n" + "="*60)
    print("TESTING METER CRUD")
    print("="*60)

    with get_db_session() as session:
        # Create meter
        meter = Meter(
            name='test_water_main',
            type='water',
            unit='m³',
            location='Test Basement',
            camera_ip='10.10.10.207',
            reading_interval_minutes=60
        )

        session.add(meter)
        session.flush()

        print(f"✓ Created meter: {meter.name} (ID: {meter.id})")

        # Read meter back
        retrieved = session.query(Meter).filter_by(name='test_water_main').first()
        assert retrieved is not None
        assert retrieved.type == 'water'

        print(f"✓ Retrieved meter: {retrieved.name}")

        # Update meter
        retrieved.location = 'Updated Location'
        session.flush()

        print(f"✓ Updated meter location to: {retrieved.location}")

        # Count meters
        count = session.query(Meter).count()
        print(f"✓ Total meters in database: {count}")

        return retrieved.id


def test_snapshot_crud(meter_id):
    """Test snapshot create/read operations"""
    print("\n" + "="*60)
    print("TESTING SNAPSHOT CRUD")
    print("="*60)

    with get_db_session() as session:
        # Create snapshot
        snapshot = Snapshot(
            meter_id=meter_id,
            timestamp=datetime.utcnow(),
            file_path='logs/test_snapshot.jpg',
            total_reading=22.712,
            digital_reading=22.0,
            dial_reading=0.712,
            confidence='high',
            temperature_c=18.5,
            processed=True
        )

        session.add(snapshot)
        session.flush()

        print(f"✓ Created snapshot (ID: {snapshot.id})")
        print(f"  Reading: {snapshot.total_reading} m³")
        print(f"  Confidence: {snapshot.confidence}")

        # Query snapshots for meter
        snapshots = session.query(Snapshot).filter_by(meter_id=meter_id).all()
        print(f"✓ Total snapshots for meter: {len(snapshots)}")


def test_user_settings():
    """Test user settings"""
    print("\n" + "="*60)
    print("TESTING USER SETTINGS")
    print("="*60)

    with get_db_session() as session:
        # Create settings
        settings = UserSettings(
            user_id='test_user',
            theme='dark',
            timezone='America/Toronto',
            preferences={'auto_refresh': True, 'refresh_interval': 30}
        )

        session.add(settings)
        session.flush()

        print(f"✓ Created user settings for: {settings.user_id}")
        print(f"  Theme: {settings.theme}")
        print(f"  Timezone: {settings.timezone}")
        print(f"  Preferences: {settings.preferences}")

        # Retrieve settings
        retrieved = session.query(UserSettings).filter_by(user_id='test_user').first()
        assert retrieved.theme == 'dark'

        print(f"✓ Retrieved settings successfully")


def test_to_dict():
    """Test model to_dict conversion"""
    print("\n" + "="*60)
    print("TESTING MODEL SERIALIZATION")
    print("="*60)

    with get_db_session() as session:
        meter = session.query(Meter).filter_by(name='test_water_main').first()

        if meter:
            meter_dict = meter.to_dict()
            print(f"✓ Converted meter to dict:")
            print(f"  Name: {meter_dict['name']}")
            print(f"  Type: {meter_dict['type']}")
            print(f"  Location: {meter_dict['location']}")


def cleanup():
    """Clean up test data"""
    print("\n" + "="*60)
    print("CLEANING UP TEST DATA")
    print("="*60)

    with get_db_session() as session:
        # Delete test meter (will cascade delete snapshots)
        meter = session.query(Meter).filter_by(name='test_water_main').first()
        if meter:
            session.delete(meter)
            print(f"✓ Deleted test meter")

        # Delete test user settings
        settings = session.query(UserSettings).filter_by(user_id='test_user').first()
        if settings:
            session.delete(settings)
            print(f"✓ Deleted test user settings")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("POSTGRESQL INTEGRATION TEST")
    print("="*60)

    try:
        # Test meter operations
        meter_id = test_meter_crud()

        # Test snapshot operations
        test_snapshot_crud(meter_id)

        # Test user settings
        test_user_settings()

        # Test serialization
        test_to_dict()

        # Clean up
        cleanup()

        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        print("\nPostgreSQL integration is working correctly.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
