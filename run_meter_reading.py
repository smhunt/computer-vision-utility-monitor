#!/usr/bin/env python3
"""
Run complete meter reading workflow
Capture -> Analyze -> Validate -> Archive -> Log
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.config_loader import load_config
from llm_reader import read_meter_with_claude
from snapshot_manager import archive_snapshot_with_metadata
from influx_logger import MeterInfluxLogger

def main():
    # Load config
    config = load_config('config/meters.yaml')

    if not config or 'meters' not in config or not config['meters']:
        print(json.dumps({'error': 'No meters configured'}))
        sys.exit(1)

    # Auto-select first meter
    meter = config['meters'][0]
    meter_name = meter.get('name', 'unknown')
    meter_type = meter.get('type', 'unknown')
    camera_ip = meter.get('camera_ip', '').replace('${WATER_CAM_IP:', '').replace('}', '').split(':')[-1] or '10.10.10.207'

    print(f"📸 Capturing from {meter_name}...", file=sys.stderr)

    # Step 1: Capture image
    import subprocess
    mjpeg_url = f"http://root:***REMOVED***@{camera_ip}/mjpeg"

    result = subprocess.run(
        ['curl', '-s', '--max-time', '10', mjpeg_url],
        capture_output=True
    )

    if result.returncode != 0:
        print(json.dumps({'error': 'Failed to capture image'}))
        sys.exit(1)

    jpeg_data = result.stdout

    # Extract first JPEG frame
    if b'\xff\xd8' in jpeg_data and b'\xff\xd9' in jpeg_data:
        start_idx = jpeg_data.find(b'\xff\xd8')
        end_idx = jpeg_data.find(b'\xff\xd9', start_idx) + 2
        jpeg_data = jpeg_data[start_idx:end_idx]

    # Save temp image
    temp_path = Path(f'/tmp/meter_capture_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg')
    with open(temp_path, 'wb') as f:
        f.write(jpeg_data)

    print(f"✅ Captured {len(jpeg_data)} bytes", file=sys.stderr)

    # Step 2: Analyze with LLM
    print(f"🤖 Analyzing image...", file=sys.stderr)
    reading = read_meter_with_claude(str(temp_path), meter_type=meter_type)

    if 'error' in reading:
        print(json.dumps(reading))
        sys.exit(1)

    print(f"✅ Reading: {reading.get('total_reading')} m³", file=sys.stderr)

    # Step 3: Archive snapshot with metadata
    print(f"📦 Archiving snapshot...", file=sys.stderr)
    archive_result = archive_snapshot_with_metadata(
        temp_path,
        meter_name,
        reading
    )

    # Step 4: Log to JSONL
    print(f"📝 Logging to JSONL...", file=sys.stderr)
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{meter_type}_readings.jsonl"

    with open(log_file, 'a') as f:
        f.write(json.dumps(reading) + '\n')

    # Step 5: Try InfluxDB (optional)
    try:
        logger = MeterInfluxLogger()
        logger.log_reading(meter_name, meter_type, reading)
        print(f"✅ Logged to InfluxDB", file=sys.stderr)
    except Exception as e:
        print(f"⚠️  InfluxDB logging failed: {e}", file=sys.stderr)

    # Output final result as JSON
    print(json.dumps({
        'status': 'success',
        'reading': reading.get('total_reading'),
        'confidence': reading.get('confidence'),
        'timestamp': reading.get('timestamp')
    }))

if __name__ == '__main__':
    main()
