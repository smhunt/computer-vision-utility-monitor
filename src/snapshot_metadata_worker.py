#!/usr/bin/env python3
"""
Snapshot Metadata Worker
Processes snapshots and adds metadata after meter reading analysis
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from snapshot_manager import SnapshotManager
from llm_reader import read_meter_with_claude
from temperature_reader import get_temperature


class SnapshotMetadataWorker:
    """Worker that processes snapshots and adds metadata"""

    def __init__(self,
                 watch_dir: str = "/tmp",
                 archive_dir: str = "logs/meter_snapshots"):
        """
        Initialize the worker

        Args:
            watch_dir: Directory to watch for new snapshots
            archive_dir: Directory for archived snapshots
        """
        self.watch_dir = Path(watch_dir)
        self.manager = SnapshotManager(base_dir=archive_dir)
        self.processed = set()

    def process_snapshot(self,
                        snapshot_path: Path,
                        meter_name: str,
                        capture_temperature: bool = True) -> Dict:
        """
        Process a snapshot: analyze, archive, and add metadata

        Args:
            snapshot_path: Path to the snapshot file
            meter_name: Name of the meter
            capture_temperature: Whether to attempt temperature capture

        Returns:
            Processing result dictionary
        """
        result = {
            'success': False,
            'meter_name': meter_name,
            'snapshot_path': str(snapshot_path),
            'timestamp': datetime.now().isoformat()
        }

        try:
            print(f"\n{'='*60}")
            print(f"Processing snapshot: {snapshot_path.name}")
            print(f"Meter: {meter_name}")
            print(f"{'='*60}")

            # 1. Analyze meter reading
            print("\n[1/4] Analyzing meter reading...")
            meter_reading = read_meter_with_claude(str(snapshot_path))

            if 'error' in meter_reading:
                result['error'] = f"Meter reading failed: {meter_reading['error']}"
                return result

            current_reading = meter_reading.get('total_reading')
            print(f"  ✓ Reading: {current_reading} m³")
            print(f"  ✓ Confidence: {meter_reading.get('confidence')}")

            # Validate against previous readings (water meters should only increase)
            print("\n[1.5/4] Validating against previous readings...")
            recent_readings = self.manager.get_reading_history(meter_name, limit=5)

            if recent_readings:
                last_reading = recent_readings[0]['total_reading']
                print(f"  Last reading: {last_reading} m³")

                # Check if reading is lower than last reading
                if current_reading < last_reading:
                    warning_msg = f"⚠️  WARNING: Reading ({current_reading} m³) is LOWER than last reading ({last_reading} m³)"
                    print(f"  {warning_msg}")
                    meter_reading['validation_warning'] = warning_msg
                    meter_reading['confidence'] = 'low'  # Downgrade confidence

                # Check if reading is suspiciously high (jumped by more than 100 m³ in one reading)
                elif current_reading > last_reading + 100:
                    warning_msg = f"⚠️  WARNING: Reading jumped by {current_reading - last_reading:.2f} m³ (possible error)"
                    print(f"  {warning_msg}")
                    meter_reading['validation_warning'] = warning_msg
                    meter_reading['confidence'] = 'low'  # Downgrade confidence
                else:
                    print(f"  ✓ Reading is valid (increased by {current_reading - last_reading:.3f} m³)")
            else:
                print(f"  ℹ  No previous readings to validate against")

            # 2. Capture temperature (optional)
            temperature_data = None
            if capture_temperature:
                print("\n[2/4] Capturing temperature...")
                temperature_data = get_temperature(source="camera")
                if temperature_data.get('available'):
                    print(f"  ✓ Temperature: {temperature_data['temperature_c']}°C")
                else:
                    print(f"  ⚠️  Temperature unavailable")
            else:
                print("\n[2/4] Skipping temperature capture")

            # 3. Archive snapshot with timestamp
            print("\n[3/4] Archiving snapshot...")
            timestamp = datetime.fromisoformat(meter_reading['timestamp'])
            archived_path = self.manager.save_snapshot(
                str(snapshot_path),
                meter_name,
                timestamp=timestamp
            )
            print(f"  ✓ Archived to: {archived_path}")

            # 4. Create metadata file
            print("\n[4/4] Creating metadata...")
            camera_info = {
                'source_file': snapshot_path.name,
                'model': 'Wyze Cam V2 (Thingino)',
                'ip': os.getenv('WATER_CAM_IP', '10.10.10.207')
            }

            metadata_path = self.manager.create_metadata_file(
                archived_path,
                meter_reading,
                temperature_data=temperature_data,
                camera_info=camera_info
            )
            print(f"  ✓ Metadata saved: {metadata_path.name}")

            # Success!
            result['success'] = True
            result['archived_path'] = str(archived_path)
            result['metadata_path'] = str(metadata_path)
            result['meter_reading'] = meter_reading.get('total_reading')
            result['confidence'] = meter_reading.get('confidence')
            result['meter_reading_data'] = meter_reading  # Full meter reading data for InfluxDB
            result['temperature'] = temperature_data  # Temperature data for InfluxDB

            print(f"\n{'='*60}")
            print("✅ Processing complete!")
            print(f"{'='*60}\n")

        except Exception as e:
            result['error'] = f"Processing error: {str(e)}"
            print(f"\n❌ Error: {str(e)}\n")

        return result

    def watch_and_process(self,
                         meter_name: str = "water_main",
                         pattern: str = "meter_snapshot_*.jpg",
                         interval: int = 5):
        """
        Watch directory for new snapshots and process them

        Args:
            meter_name: Name of the meter
            pattern: File pattern to watch for
            interval: Check interval in seconds
        """
        print(f"👀 Watching {self.watch_dir} for {pattern}")
        print(f"   Checking every {interval} seconds")
        print(f"   Press Ctrl+C to stop\n")

        try:
            while True:
                # Find matching snapshots
                snapshots = list(self.watch_dir.glob(pattern))

                for snapshot in snapshots:
                    # Skip if already processed
                    if snapshot in self.processed:
                        continue

                    # Process the snapshot
                    result = self.process_snapshot(snapshot, meter_name)

                    # Mark as processed
                    self.processed.add(snapshot)

                    # Log result
                    if result['success']:
                        print(f"✓ Processed: {snapshot.name}")
                    else:
                        print(f"✗ Failed: {snapshot.name} - {result.get('error')}")

                # Wait before next check
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n⏹  Worker stopped by user")


def process_single_snapshot(snapshot_path: str,
                            meter_name: str,
                            capture_temperature: bool = True) -> Dict:
    """
    Process a single snapshot (convenience function)

    Args:
        snapshot_path: Path to snapshot file
        meter_name: Name of the meter
        capture_temperature: Whether to capture temperature

    Returns:
        Processing result dictionary
    """
    worker = SnapshotMetadataWorker()
    return worker.process_snapshot(
        Path(snapshot_path),
        meter_name,
        capture_temperature=capture_temperature
    )


# Command-line interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Snapshot Metadata Worker")
    parser.add_argument('mode', choices=['watch', 'process'],
                       help="Mode: watch directory or process single file")
    parser.add_argument('--snapshot', '-s', type=str,
                       help="Snapshot file to process (process mode)")
    parser.add_argument('--meter', '-m', type=str, default="water_main",
                       help="Meter name (default: water_main)")
    parser.add_argument('--watch-dir', '-w', type=str, default="/tmp",
                       help="Directory to watch (watch mode)")
    parser.add_argument('--interval', '-i', type=int, default=5,
                       help="Check interval in seconds (watch mode)")
    parser.add_argument('--no-temperature', action='store_true',
                       help="Skip temperature capture")

    args = parser.parse_args()

    if args.mode == 'process':
        # Process single snapshot
        if not args.snapshot:
            print("Error: --snapshot required for process mode")
            sys.exit(1)

        result = process_single_snapshot(
            args.snapshot,
            args.meter,
            capture_temperature=not args.no_temperature
        )

        # Print result
        print("\nResult:")
        print(json.dumps(result, indent=2))

        sys.exit(0 if result['success'] else 1)

    elif args.mode == 'watch':
        # Watch mode
        worker = SnapshotMetadataWorker(watch_dir=args.watch_dir)
        worker.watch_and_process(
            meter_name=args.meter,
            interval=args.interval
        )
