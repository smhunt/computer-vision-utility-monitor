#!/usr/bin/env python3
"""
Compare dial readings before and after the prompt improvements

This script helps evaluate the effectiveness of the new prompt by comparing
readings from the same images processed at different times.
"""
import json
import sys
from pathlib import Path
from datetime import datetime

def load_reading_from_json(json_path):
    """Load a reading from a metadata JSON file"""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        # Extract meter_reading section
        if 'meter_reading' in data:
            return data['meter_reading']
        return data
    except Exception as e:
        print(f"Error loading {json_path}: {e}")
        return None

def load_readings_from_jsonl(jsonl_path):
    """Load all readings from a JSONL log file"""
    readings = []
    try:
        with open(jsonl_path, 'r') as f:
            for line in f:
                if line.strip():
                    reading = json.loads(line.strip())
                    readings.append(reading)
    except Exception as e:
        print(f"Error loading {jsonl_path}: {e}")

    return readings

def analyze_dial_accuracy(readings):
    """Analyze dial angle consistency and detect potential errors"""

    if not readings:
        print("No readings to analyze")
        return

    print("\n" + "="*80)
    print("DIAL READING ANALYSIS")
    print("="*80)

    # Extract dial angles
    dial_angles = []
    for r in readings:
        if 'dial_angle_degrees' in r:
            dial_angles.append({
                'timestamp': r.get('timestamp', 'unknown'),
                'angle': r['dial_angle_degrees'],
                'reading': r.get('dial_reading', 0),
                'confidence': r.get('confidence', 'unknown'),
                'warnings': r.get('dial_angle_warnings', []),
                'notes': r.get('notes', '')[:100] + '...' if len(r.get('notes', '')) > 100 else r.get('notes', '')
            })

    if not dial_angles:
        print("\n❌ No dial angle data found in readings")
        return

    print(f"\n📊 Total readings with dial angles: {len(dial_angles)}")
    print(f"\n{'─'*80}")
    print(f"{'Timestamp':<20} {'Angle':>8} {'Reading':>10} {'Conf':>8} {'Warnings':>10}")
    print(f"{'─'*80}")

    for entry in dial_angles[-10:]:  # Show last 10
        ts = entry['timestamp'].split('T')[1][:8] if 'T' in entry['timestamp'] else entry['timestamp'][:20]
        warnings_count = len(entry['warnings'])
        warnings_indicator = f"⚠️  {warnings_count}" if warnings_count > 0 else "✓"

        print(f"{ts:<20} {entry['angle']:>6}° {entry['reading']:>10.4f} {entry['confidence']:>8} {warnings_indicator:>10}")

    # Statistical analysis
    angles = [e['angle'] for e in dial_angles]

    print(f"\n{'─'*80}")
    print("STATISTICS:")
    print(f"{'─'*80}")
    print(f"  Min angle:     {min(angles):>6}°")
    print(f"  Max angle:     {max(angles):>6}°")
    print(f"  Mean angle:    {sum(angles)/len(angles):>6.1f}°")
    print(f"  Range:         {max(angles)-min(angles):>6}°")

    # Detect potential issues
    print(f"\n{'─'*80}")
    print("POTENTIAL ISSUES:")
    print(f"{'─'*80}")

    # Check for readings with warnings
    with_warnings = [e for e in dial_angles if e['warnings']]
    if with_warnings:
        print(f"\n⚠️  {len(with_warnings)} reading(s) with validation warnings:")
        for entry in with_warnings[-5:]:  # Show last 5
            print(f"\n  Timestamp: {entry['timestamp']}")
            print(f"  Angle: {entry['angle']}°")
            print(f"  Warnings:")
            for warning in entry['warnings']:
                print(f"    - {warning}")
    else:
        print("\n✅ No validation warnings found")

    # Check for suspicious angle changes
    print(f"\n{'─'*80}")
    print("ANGLE CONSISTENCY:")
    print(f"{'─'*80}")

    if len(dial_angles) > 1:
        large_jumps = []
        for i in range(1, len(dial_angles)):
            angle_diff = abs(dial_angles[i]['angle'] - dial_angles[i-1]['angle'])
            # Account for wraparound (359° -> 1°)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff

            if angle_diff > 45:  # Flag changes >45° between consecutive readings
                large_jumps.append({
                    'from': dial_angles[i-1],
                    'to': dial_angles[i],
                    'diff': angle_diff
                })

        if large_jumps:
            print(f"\n⚠️  Found {len(large_jumps)} large angle jump(s) (>45° between consecutive readings):")
            for jump in large_jumps[-5:]:
                print(f"\n  {jump['from']['angle']:>3}° → {jump['to']['angle']:>3}°  (Δ{jump['diff']:.0f}°)")
                print(f"  Time: {jump['from']['timestamp']} → {jump['to']['timestamp']}")
        else:
            print("\n✅ No large angle jumps detected (all changes <45°)")

    # Direction analysis
    print(f"\n{'─'*80}")
    print("DIRECTION DISTRIBUTION:")
    print(f"{'─'*80}")

    directions = {
        'UP (0-45°)': 0,
        'RIGHT (45-135°)': 0,
        'DOWN (135-225°)': 0,
        'LEFT (225-315°)': 0,
        'UP (315-360°)': 0
    }

    for entry in dial_angles:
        angle = entry['angle']
        if 0 <= angle < 45:
            directions['UP (0-45°)'] += 1
        elif 45 <= angle < 135:
            directions['RIGHT (45-135°)'] += 1
        elif 135 <= angle < 225:
            directions['DOWN (135-225°)'] += 1
        elif 225 <= angle < 315:
            directions['LEFT (225-315°)'] += 1
        else:
            directions['UP (315-360°)'] += 1

    for direction, count in directions.items():
        pct = (count / len(dial_angles)) * 100 if dial_angles else 0
        bar = '█' * int(pct / 2)
        print(f"  {direction:<20} {count:>3} ({pct:>5.1f}%) {bar}")

def main():
    """Main entry point"""

    print("\n" + "="*80)
    print("DIAL READING COMPARISON TOOL")
    print("="*80)

    # Check for JSONL log files
    log_dir = Path("logs")

    if not log_dir.exists():
        print(f"\n❌ Error: logs directory not found at {log_dir.absolute()}")
        sys.exit(1)

    jsonl_files = list(log_dir.glob("*_readings.jsonl"))

    if not jsonl_files:
        print(f"\n❌ Error: No *_readings.jsonl files found in {log_dir.absolute()}")
        sys.exit(1)

    print(f"\nFound {len(jsonl_files)} reading log file(s):")
    for f in jsonl_files:
        print(f"  - {f.name}")

    # Analyze each log file
    for jsonl_file in jsonl_files:
        print(f"\n{'='*80}")
        print(f"ANALYZING: {jsonl_file.name}")
        print(f"{'='*80}")

        readings = load_readings_from_jsonl(jsonl_file)

        if not readings:
            print(f"\n❌ No readings found in {jsonl_file.name}")
            continue

        print(f"\n📈 Total readings in log: {len(readings)}")

        # Show date range
        timestamps = [r.get('timestamp', '') for r in readings if r.get('timestamp')]
        if timestamps:
            print(f"   Oldest: {timestamps[0]}")
            print(f"   Newest: {timestamps[-1]}")

        # Analyze dial accuracy
        analyze_dial_accuracy(readings)

    print(f"\n{'='*80}")
    print("RECOMMENDATIONS:")
    print(f"{'='*80}")
    print("""
    1. Review readings with validation warnings - these may have angle errors
    2. Large angle jumps (>45°) between consecutive readings are suspicious
    3. If most readings cluster in one direction, verify physical dial position
    4. Compare notes field to ensure step-by-step analysis is being performed
    5. If accuracy is still poor, consider hybrid OpenCV approach
    """)
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
