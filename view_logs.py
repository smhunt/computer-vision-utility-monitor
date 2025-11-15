#!/usr/bin/env python3
"""
View water meter reading logs and snapshots

Usage:
    python3 view_logs.py                    # Show all readings
    python3 view_logs.py --latest 5         # Show last 5 readings
    python3 view_logs.py --stats            # Show statistics
    python3 view_logs.py --images           # Show list of images
    python3 view_logs.py --tail             # Follow log in real-time
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict

LOG_FILE = "logs/readings.jsonl"
IMAGE_DIR = "logs/snapshots"


def load_readings(limit=None) -> List[Dict]:
    """Load all readings from JSONL file"""
    readings = []
    if not os.path.exists(LOG_FILE):
        return readings

    with open(LOG_FILE, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    readings.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if limit:
        readings = readings[-limit:]
    return readings


def show_all_readings(readings):
    """Display all readings in table format"""
    if not readings:
        print("No readings found.")
        return

    print()
    print("=" * 100)
    print("WATER METER READINGS LOG")
    print("=" * 100)
    print()
    print(f"{'Timestamp':<26} {'Reading (m³)':<15} {'Digital':<10} {'Dial':<10} {'Confidence':<12} {'Status'}")
    print("-" * 100)

    for reading in readings:
        if "error" in reading:
            status = f"ERROR: {reading['error']}"
            print(f"{reading.get('timestamp', 'N/A'):<26} {'N/A':<15} {'N/A':<10} {'N/A':<10} {'N/A':<12} {status}")
        else:
            timestamp = reading.get('timestamp', 'N/A')
            total = f"{reading.get('total_reading', 0):.3f}"
            digital = reading.get('digital_reading', 'N/A')
            dial = f"{reading.get('dial_reading', 0):.3f}"
            confidence = reading.get('confidence', 'unknown')
            status = "✓ OK"

            print(f"{timestamp:<26} {total:<15} {digital:<10} {dial:<10} {confidence:<12} {status}")

    print()


def show_statistics(readings):
    """Show statistics about readings"""
    if not readings:
        print("No readings found.")
        return

    valid_readings = [r for r in readings if "error" not in r]

    if not valid_readings:
        print("No valid readings found.")
        return

    values = [r['total_reading'] for r in valid_readings]
    min_val = min(values)
    max_val = max(values)
    total_usage = max_val - min_val if len(values) > 1 else 0

    print()
    print("=" * 60)
    print("STATISTICS")
    print("=" * 60)
    print()
    print(f"Total Readings:        {len(readings)}")
    print(f"Valid Readings:        {len(valid_readings)}")
    print(f"Failed Readings:       {len(readings) - len(valid_readings)}")
    print()
    print(f"Latest Reading:        {valid_readings[-1]['total_reading']:.3f} m³")
    print(f"First Reading:         {valid_readings[0]['total_reading']:.3f} m³")
    print(f"Total Usage:           {total_usage:.3f} m³ ({total_usage * 1000:.1f} liters)")
    print(f"Min Reading:           {min_val:.3f} m³")
    print(f"Max Reading:           {max_val:.3f} m³")
    print()

    # Calculate time span
    first_time = datetime.fromisoformat(valid_readings[0]['timestamp'])
    last_time = datetime.fromisoformat(valid_readings[-1]['timestamp'])
    duration = (last_time - first_time).total_seconds() / 3600
    if duration > 0:
        flow_rate = (total_usage * 1000) / duration
        print(f"Monitoring Duration:   {duration:.1f} hours")
        print(f"Average Flow Rate:     {flow_rate:.2f} L/hour")
    print()


def show_images():
    """List all saved snapshot images"""
    if not os.path.exists(IMAGE_DIR):
        print(f"No snapshots directory found at {IMAGE_DIR}")
        return

    images = sorted(Path(IMAGE_DIR).glob("*.jpg"))
    if not images:
        print("No snapshot images found.")
        return

    print()
    print("=" * 100)
    print("SNAPSHOT IMAGES")
    print("=" * 100)
    print()
    print(f"{'Filename':<70} {'Size':<15} {'Date Modified'}")
    print("-" * 100)

    for img in images:
        stat = img.stat()
        size_mb = stat.st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{img.name:<70} {size_mb:>6.2f} MB       {mtime}")

    print()
    print(f"Total images: {len(images)}")
    total_size = sum(img.stat().st_size for img in images) / (1024 * 1024)
    print(f"Total size: {total_size:.2f} MB")
    print()
    print(f"View images: open {IMAGE_DIR}")
    print()


def tail_log():
    """Follow log file in real-time"""
    if not os.path.exists(LOG_FILE):
        print(f"Log file not found: {LOG_FILE}")
        return

    print("Monitoring log file (Ctrl+C to stop)...")
    print()

    # Get initial line count
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()

    # Show existing readings
    show_all_readings([json.loads(line) for line in lines if line.strip()])

    # Now tail for new lines
    try:
        with open(LOG_FILE, 'r') as f:
            f.seek(0, 2)  # Go to end of file
            while True:
                line = f.readline()
                if line:
                    try:
                        reading = json.loads(line)
                        if "error" in reading:
                            status = f"✗ ERROR: {reading['error']}"
                        else:
                            status = f"✓ {reading['total_reading']:.3f} m³"
                        print(f"[{reading.get('timestamp', 'N/A')}] {status}")
                    except json.JSONDecodeError:
                        pass
                else:
                    import time
                    time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


def main():
    parser = argparse.ArgumentParser(description="View water meter reading logs")
    parser.add_argument("--latest", type=int, help="Show latest N readings")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--images", action="store_true", help="Show list of images")
    parser.add_argument("--tail", action="store_true", help="Follow log in real-time")

    args = parser.parse_args()

    if args.tail:
        tail_log()
    elif args.images:
        show_images()
    elif args.stats:
        readings = load_readings()
        show_statistics(readings)
    else:
        readings = load_readings(limit=args.latest)
        show_all_readings(readings)


if __name__ == "__main__":
    main()
