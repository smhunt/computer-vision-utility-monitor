#!/usr/bin/env python3
"""
Clean up wrong meter readings from the archive
Removes readings that are clearly incorrect (not in expected range)
"""

import json
import os
from pathlib import Path
from datetime import datetime

# Expected range for water meter readings (2000-3000 m³)
MIN_VALID_READING = 2000
MAX_VALID_READING = 3000

def cleanup_wrong_readings(meter_name="water_main", dry_run=True):
    """
    Clean up wrong readings from the archive

    Args:
        meter_name: Name of the meter
        dry_run: If True, only report what would be deleted (don't actually delete)
    """
    base_dir = Path("logs/meter_snapshots") / meter_name

    if not base_dir.exists():
        print(f"Error: Directory not found: {base_dir}")
        return

    # Find all JSON metadata files
    json_files = sorted(base_dir.glob("*.json"))

    print(f"Found {len(json_files)} readings to check")
    print(f"Valid reading range: {MIN_VALID_READING} - {MAX_VALID_READING} m³")
    print(f"Mode: {'DRY RUN (no files will be deleted)' if dry_run else 'LIVE (files will be deleted)'}")
    print("=" * 60)

    wrong_readings = []
    valid_readings = []

    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            reading = data.get('meter_reading', {}).get('total_reading')
            timestamp = data.get('snapshot', {}).get('timestamp', 'unknown')

            if reading is None:
                print(f"⚠️  {json_file.name}: No reading found")
                continue

            # Check if reading is in valid range
            if reading < MIN_VALID_READING or reading > MAX_VALID_READING:
                wrong_readings.append({
                    'file': json_file,
                    'reading': reading,
                    'timestamp': timestamp
                })
                print(f"❌ WRONG: {json_file.name} - {reading:.3f} m³ at {timestamp}")
            else:
                valid_readings.append({
                    'file': json_file,
                    'reading': reading,
                    'timestamp': timestamp
                })
                print(f"✓ Valid: {json_file.name} - {reading:.3f} m³")

        except Exception as e:
            print(f"⚠️  Error reading {json_file.name}: {e}")

    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  Valid readings: {len(valid_readings)}")
    print(f"  Wrong readings: {len(wrong_readings)}")

    if wrong_readings:
        print("\n" + "=" * 60)
        print("Wrong readings to be deleted:")
        for item in wrong_readings:
            print(f"  - {item['file'].name}: {item['reading']:.3f} m³")

        if not dry_run:
            print("\n" + "=" * 60)
            print("Deleting wrong readings...")

            for item in wrong_readings:
                json_file = item['file']
                jpg_file = json_file.with_suffix('.jpg')

                # Delete JSON file
                if json_file.exists():
                    json_file.unlink()
                    print(f"  ✓ Deleted: {json_file.name}")

                # Delete corresponding JPG file
                if jpg_file.exists():
                    jpg_file.unlink()
                    print(f"  ✓ Deleted: {jpg_file.name}")

            print(f"\n✅ Cleanup complete! Deleted {len(wrong_readings)} wrong readings.")
        else:
            print(f"\n⚠️  DRY RUN - No files were deleted. Run with dry_run=False to delete.")
    else:
        print("\n✅ No wrong readings found!")

    return wrong_readings, valid_readings


if __name__ == "__main__":
    import sys

    # Check command line argument
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == "--delete":
        dry_run = False
        print("⚠️  WARNING: Running in DELETE mode!\n")

    wrong, valid = cleanup_wrong_readings(dry_run=dry_run)

    if dry_run and wrong:
        print("\n" + "=" * 60)
        print("To actually delete these files, run:")
        print("  python3 cleanup_wrong_readings.py --delete")
