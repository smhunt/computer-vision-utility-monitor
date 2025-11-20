#!/usr/bin/env python3
"""
Snapshot Manager Module
Manages meter snapshot archiving with timestamps and metadata
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class SnapshotManager:
    """Manages meter snapshot archiving and metadata"""

    def __init__(self, base_dir: str = "logs/meter_snapshots"):
        """
        Initialize snapshot manager

        Args:
            base_dir: Base directory for snapshot archives
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_meter_dir(self, meter_name: str) -> Path:
        """Get the directory for a specific meter"""
        meter_dir = self.base_dir / meter_name
        meter_dir.mkdir(parents=True, exist_ok=True)
        return meter_dir

    def generate_snapshot_filename(self, meter_name: str, timestamp: datetime = None) -> str:
        """
        Generate timestamped filename for snapshot

        Args:
            meter_name: Name of the meter
            timestamp: Timestamp for the snapshot (default: now)

        Returns:
            Filename string (e.g., "water_main_20251119_120530.jpg")
        """
        if timestamp is None:
            timestamp = datetime.now()

        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"{meter_name}_{timestamp_str}.jpg"

    def save_snapshot(self,
                     source_path: str,
                     meter_name: str,
                     timestamp: datetime = None) -> Path:
        """
        Save snapshot to archive with timestamp

        Args:
            source_path: Path to source image file
            meter_name: Name of the meter
            timestamp: Timestamp for the snapshot (default: now)

        Returns:
            Path to archived snapshot
        """
        if timestamp is None:
            timestamp = datetime.now()

        meter_dir = self.get_meter_dir(meter_name)
        filename = self.generate_snapshot_filename(meter_name, timestamp)
        dest_path = meter_dir / filename

        # Copy file to archive
        shutil.copy2(source_path, dest_path)

        return dest_path

    def create_metadata_file(self,
                            snapshot_path: Path,
                            meter_reading: Dict,
                            temperature_data: Optional[Dict] = None,
                            camera_info: Optional[Dict] = None) -> Path:
        """
        Create metadata JSON file for a snapshot

        Args:
            snapshot_path: Path to the snapshot image
            meter_reading: Meter reading data from llm_reader
            temperature_data: Temperature data (optional)
            camera_info: Camera information (optional)

        Returns:
            Path to metadata file
        """
        metadata_path = snapshot_path.with_suffix('.json')

        metadata = {
            'snapshot': {
                'filename': snapshot_path.name,
                'timestamp': meter_reading.get('timestamp', datetime.now().isoformat()),
                'path': str(snapshot_path)
            },
            'meter_reading': {
                'digital_reading': meter_reading.get('digital_reading'),
                'dial_reading': meter_reading.get('dial_reading'),
                'total_reading': meter_reading.get('total_reading'),
                'confidence': meter_reading.get('confidence'),
                'notes': meter_reading.get('notes')
            },
            'api_usage': meter_reading.get('api_usage', {}),
        }

        # Add temperature if available
        if temperature_data:
            metadata['temperature'] = {
                'celsius': temperature_data.get('temperature_c'),
                'fahrenheit': temperature_data.get('temperature_f'),
                'source': temperature_data.get('source'),
                'available': temperature_data.get('available', False)
            }

        # Add camera info if available
        if camera_info:
            metadata['camera'] = camera_info

        # Write metadata file
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        return metadata_path

    def get_latest_snapshot(self, meter_name: str) -> Optional[Path]:
        """
        Get the most recent snapshot for a meter

        Args:
            meter_name: Name of the meter

        Returns:
            Path to latest snapshot or None
        """
        meter_dir = self.get_meter_dir(meter_name)
        snapshots = sorted(meter_dir.glob(f"{meter_name}_*.jpg"), reverse=True)

        return snapshots[0] if snapshots else None

    def get_snapshots(self,
                     meter_name: str,
                     limit: Optional[int] = None) -> list:
        """
        Get list of snapshots for a meter

        Args:
            meter_name: Name of the meter
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshot paths (newest first)
        """
        meter_dir = self.get_meter_dir(meter_name)
        snapshots = sorted(meter_dir.glob(f"{meter_name}_*.jpg"), reverse=True)

        if limit:
            snapshots = snapshots[:limit]

        return snapshots

    def get_metadata(self, snapshot_path: Path) -> Optional[Dict]:
        """
        Load metadata for a snapshot

        Args:
            snapshot_path: Path to snapshot image

        Returns:
            Metadata dictionary or None
        """
        metadata_path = snapshot_path.with_suffix('.json')

        if not metadata_path.exists():
            return None

        with open(metadata_path, 'r') as f:
            return json.load(f)

    def get_reading_history(self, meter_name: str, limit: int = 10) -> list:
        """
        Get reading history for a meter

        Args:
            meter_name: Name of the meter
            limit: Maximum number of readings to return

        Returns:
            List of reading data with metadata
        """
        snapshots = self.get_snapshots(meter_name, limit=limit)
        history = []

        for snapshot_path in snapshots:
            metadata = self.get_metadata(snapshot_path)
            if metadata:
                history.append({
                    'snapshot_path': str(snapshot_path),
                    'timestamp': metadata['snapshot']['timestamp'],
                    'total_reading': metadata['meter_reading']['total_reading'],
                    'confidence': metadata['meter_reading']['confidence'],
                    'temperature': metadata.get('temperature', {}).get('celsius')
                })

        return history


# Command-line interface for testing
if __name__ == "__main__":
    import sys

    # Example usage
    manager = SnapshotManager()

    print("Snapshot Manager Test")
    print("=" * 60)
    print()

    # Show snapshots for water_main
    meter_name = "water_main"
    print(f"Recent snapshots for {meter_name}:")

    snapshots = manager.get_snapshots(meter_name, limit=5)
    if snapshots:
        for snapshot in snapshots:
            print(f"  {snapshot.name}")

            # Show metadata if available
            metadata = manager.get_metadata(snapshot)
            if metadata:
                reading = metadata['meter_reading']['total_reading']
                confidence = metadata['meter_reading']['confidence']
                print(f"    Reading: {reading} m³ (confidence: {confidence})")
    else:
        print("  No snapshots found")

    print()
    print(f"Latest snapshot: {manager.get_latest_snapshot(meter_name)}")
