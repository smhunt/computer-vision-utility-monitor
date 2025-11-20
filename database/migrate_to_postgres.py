#!/usr/bin/env python3
"""
Migration script to move existing data to PostgreSQL
Migrates data from JSON/JSONL files to PostgreSQL database
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

from src.database import (
    get_db_session,
    init_database,
    Meter,
    Snapshot,
    Bill
)


def migrate_meters(config_path: str = 'config/meters.yaml'):
    """Migrate meter configuration from YAML/JSON to PostgreSQL"""
    print("\n" + "="*60)
    print("MIGRATING METERS")
    print("="*60)

    # Try to load existing config
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"⚠️  No meter config found at {config_path}")
        print("Creating example meters...")

        # Create example meters
        example_meters = [
            {
                'name': 'water_main',
                'type': 'water',
                'location': 'Basement',
                'unit': 'm³',
                'camera_ip': os.getenv('WATER_CAM_IP', '10.10.10.207'),
                'camera_user': os.getenv('WATER_CAM_USER', 'root'),
                'camera_preset': 'optimal_day',
                'reading_interval_minutes': 60
            },
            {
                'name': 'electric_main',
                'type': 'electric',
                'location': 'Garage',
                'unit': 'kWh',
                'camera_ip': os.getenv('ELECTRIC_CAM_IP', '10.10.10.208'),
                'camera_user': os.getenv('ELECTRIC_CAM_USER', 'root'),
                'camera_preset': 'optimal_day',
                'reading_interval_minutes': 15
            },
            {
                'name': 'gas_main',
                'type': 'gas',
                'location': 'Exterior',
                'unit': 'm³',
                'camera_ip': os.getenv('GAS_CAM_IP', '10.10.10.209'),
                'camera_user': os.getenv('GAS_CAM_USER', 'root'),
                'camera_preset': 'optimal_day',
                'reading_interval_minutes': 60
            }
        ]

        meters_to_migrate = example_meters
    else:
        # Load from config file
        import yaml
        with open(config_file) as f:
            config = yaml.safe_load(f)
        meters_to_migrate = config.get('meters', [])

    # Migrate to database
    with get_db_session() as session:
        migrated = 0
        skipped = 0

        for meter_data in meters_to_migrate:
            # Check if meter already exists
            existing = session.query(Meter).filter_by(name=meter_data['name']).first()

            if existing:
                print(f"⏭️  Skipping {meter_data['name']} (already exists)")
                skipped += 1
                continue

            # Create meter
            meter = Meter(
                name=meter_data['name'],
                type=meter_data['type'],
                location=meter_data.get('location'),
                unit=meter_data['unit'],
                camera_ip=meter_data.get('camera_ip'),
                camera_user=meter_data.get('camera_user'),
                camera_preset=meter_data.get('camera_preset'),
                reading_interval_minutes=meter_data.get('reading_interval_minutes', 60)
            )

            session.add(meter)
            print(f"✓ Migrated meter: {meter.name} ({meter.type})")
            migrated += 1

        session.flush()

    print(f"\nMigrated: {migrated}, Skipped: {skipped}")


def migrate_snapshots(logs_dir: str = 'logs'):
    """Migrate snapshot data from JSONL files to PostgreSQL"""
    print("\n" + "="*60)
    print("MIGRATING SNAPSHOTS")
    print("="*60)

    logs_path = Path(logs_dir)
    if not logs_path.exists():
        print(f"⚠️  Logs directory not found: {logs_dir}")
        return

    # Find all JSONL reading files
    jsonl_files = list(logs_path.glob('*_readings.jsonl'))

    if not jsonl_files:
        print("⚠️  No JSONL files found")
        return

    with get_db_session() as session:
        total_migrated = 0
        total_skipped = 0

        for jsonl_file in jsonl_files:
            # Determine meter name from filename
            meter_name = jsonl_file.stem.replace('_readings', '')

            # Look up meter in database
            meter = session.query(Meter).filter_by(name=meter_name).first()

            if not meter:
                print(f"⚠️  Meter not found for {meter_name}, skipping snapshots")
                continue

            print(f"\nProcessing {jsonl_file.name}...")

            migrated = 0
            skipped = 0

            # Read JSONL file
            with open(jsonl_file) as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())

                        # Parse timestamp
                        timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))

                        # Check if snapshot already exists
                        existing = session.query(Snapshot).filter_by(
                            meter_id=meter.id,
                            timestamp=timestamp
                        ).first()

                        if existing:
                            skipped += 1
                            continue

                        # Create snapshot
                        snapshot = Snapshot(
                            meter_id=meter.id,
                            timestamp=timestamp,
                            file_path=data.get('snapshot_path', ''),
                            total_reading=data.get('total_reading'),
                            digital_reading=data.get('digital_reading'),
                            dial_reading=data.get('dial_reading'),
                            confidence=data.get('confidence'),
                            temperature_c=data.get('temperature', {}).get('celsius'),
                            processed=True,
                            api_model=data.get('api_usage', {}).get('model')
                        )

                        session.add(snapshot)
                        migrated += 1

                        # Commit in batches
                        if migrated % 100 == 0:
                            session.flush()
                            print(f"  Progress: {migrated} snapshots migrated...")

                    except Exception as e:
                        print(f"  ⚠️  Error processing line: {e}")
                        continue

            session.flush()
            print(f"  ✓ Migrated: {migrated}, Skipped: {skipped}")
            total_migrated += migrated
            total_skipped += skipped

        print(f"\nTotal migrated: {total_migrated}, Total skipped: {total_skipped}")


def migrate_bills(config_path: str = 'config/pricing.json'):
    """Migrate bill data from pricing.json to PostgreSQL"""
    print("\n" + "="*60)
    print("MIGRATING BILLS")
    print("="*60)

    config_file = Path(config_path)
    if not config_file.exists():
        print(f"⚠️  No pricing config found at {config_path}")
        return

    with open(config_file) as f:
        config = json.load(f)

    bill_uploads = config.get('bill_uploads', {})

    if not bill_uploads:
        print("⚠️  No bill uploads found")
        return

    with get_db_session() as session:
        total_migrated = 0

        for meter_type, bills_list in bill_uploads.items():
            # Look up meter
            meter = session.query(Meter).filter_by(type=meter_type).first()

            if not meter:
                print(f"⚠️  No meter found for type {meter_type}, skipping bills")
                continue

            print(f"\nProcessing bills for {meter_type}...")

            for bill_data in bills_list:
                # Check if bill already exists
                existing = session.query(Bill).filter_by(
                    meter_id=meter.id,
                    source_file=bill_data.get('source_file')
                ).first()

                if existing:
                    print(f"  ⏭️  Skipping {bill_data.get('source_file')} (already exists)")
                    continue

                # Parse billing period
                period = bill_data.get('billing_period', '')
                period_parts = period.split(' to ')

                # Create bill
                bill = Bill(
                    meter_id=meter.id,
                    source_file=bill_data.get('source_file'),
                    billing_period_start=datetime.fromisoformat(period_parts[0]).date() if len(period_parts) > 0 else None,
                    billing_period_end=datetime.fromisoformat(period_parts[1]).date() if len(period_parts) > 1 else None,
                    total_amount=bill_data.get('total_amount'),
                    usage=bill_data.get('usage'),
                    uploaded_at=datetime.fromisoformat(bill_data.get('uploaded_at')) if bill_data.get('uploaded_at') else None,
                    parsed_data=bill_data
                )

                session.add(bill)
                print(f"  ✓ Migrated bill: {bill.source_file}")
                total_migrated += 1

        session.flush()
        print(f"\nTotal migrated: {total_migrated}")


def main():
    """Run all migrations"""
    print("\n" + "="*60)
    print("DATABASE MIGRATION TOOL")
    print("="*60)
    print("This will migrate data from files to PostgreSQL")
    print()

    # Check database connection
    from src.database.connection import test_connection

    if not test_connection():
        print("\n❌ Database connection failed!")
        print("Please ensure:")
        print("  1. PostgreSQL is running (docker-compose up -d)")
        print("  2. Environment variables are set (POSTGRES_HOST, POSTGRES_PASSWORD, etc.)")
        sys.exit(1)

    print()

    # Initialize database schema
    print("Initializing database schema...")
    init_database()

    # Run migrations
    try:
        migrate_meters()
        migrate_snapshots()
        migrate_bills()

        print("\n" + "="*60)
        print("✓ MIGRATION COMPLETE!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
