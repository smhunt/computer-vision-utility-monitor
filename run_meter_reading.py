#!/usr/bin/env python3
"""
Run complete meter reading workflow
Capture -> Analyze -> Validate -> Archive -> Log
"""
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.config_loader import load_config
from llm_reader import read_meter_with_claude

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
    import requests
    camera_user = meter.get('camera_user', '').replace('${WATER_CAM_USER:', '').replace('}', '').split(':')[-1] or 'root'
    camera_pass = meter.get('camera_pass', '').replace('${WATER_CAM_PASS:', '').replace('}', '').split(':')[-1] or '***REMOVED***'
    mjpeg_url = f"http://{camera_user}:{camera_pass}@{camera_ip}/mjpeg"

    try:
        response = requests.get(mjpeg_url, stream=True, timeout=10)
        if response.status_code != 200:
            print(json.dumps({'error': f'Camera returned HTTP {response.status_code}'}))
            sys.exit(1)

        # Read stream until we get a complete JPEG frame
        jpeg_data = b''
        found_start = False

        for chunk in response.iter_content(chunk_size=1024):
            jpeg_data += chunk

            if not found_start and b'\xff\xd8' in jpeg_data:
                start_idx = jpeg_data.find(b'\xff\xd8')
                jpeg_data = jpeg_data[start_idx:]
                found_start = True

            if found_start and b'\xff\xd9' in jpeg_data:
                end_idx = jpeg_data.find(b'\xff\xd9') + 2
                jpeg_data = jpeg_data[:end_idx]
                break

            if len(jpeg_data) > 500000:
                break

    except Exception as e:
        print(json.dumps({'error': f'Failed to capture image: {str(e)}'}))
        sys.exit(1)

    # Save temp image
    temp_path = Path(f'/tmp/meter_capture_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg')
    with open(temp_path, 'wb') as f:
        f.write(jpeg_data)

    print(f"✅ Captured {len(jpeg_data)} bytes", file=sys.stderr)

    # Step 2: Analyze with LLM
    print(f"🤖 Analyzing image...", file=sys.stderr)
    reading = read_meter_with_claude(str(temp_path))

    if 'error' in reading:
        print(json.dumps(reading))
        sys.exit(1)

    print(f"✅ Reading: {reading.get('total_reading')} m³", file=sys.stderr)

    # Step 3: Archive snapshot with metadata
    print(f"📦 Archiving snapshot...", file=sys.stderr)
    archive_dir = Path('logs/meter_snapshots') / meter_name
    archive_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = reading.get('timestamp', datetime.now().isoformat())
    snapshot_filename = f"{meter_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    snapshot_path = archive_dir / snapshot_filename
    metadata_path = archive_dir / f"{snapshot_filename.replace('.jpg', '.json')}"

    # Copy image to archive
    shutil.copy2(temp_path, snapshot_path)

    # Save metadata
    metadata = {
        'snapshot': {
            'filename': snapshot_filename,
            'timestamp': timestamp_str,
            'size': snapshot_path.stat().st_size
        },
        'meter_reading': reading
    }
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    # Step 4: Log to JSONL
    print(f"📝 Logging to JSONL...", file=sys.stderr)
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{meter_type}_readings.jsonl"

    with open(log_file, 'a') as f:
        f.write(json.dumps(reading) + '\n')

    # Step 5: Try InfluxDB (optional)
    try:
        import sys as _sys
        import io
        # Suppress InfluxDB output
        old_stdout = _sys.stdout
        old_stderr = _sys.stderr
        _sys.stdout = io.StringIO()
        _sys.stderr = io.StringIO()

        from influx_logger import MeterInfluxLogger
        logger = MeterInfluxLogger()
        logger.log_reading(meter_name, meter_type, reading)

        _sys.stdout = old_stdout
        _sys.stderr = old_stderr
        print(f"✅ Logged to InfluxDB", file=sys.stderr)
    except Exception as e:
        if 'old_stdout' in locals():
            _sys.stdout = old_stdout
            _sys.stderr = old_stderr
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
