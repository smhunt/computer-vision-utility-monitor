#!/usr/bin/env python3
"""
Meter Preview Web UI

Provides a web interface to preview camera captures and meter readings
in real-time. Useful for positioning cameras and debugging.

Usage:
    python meter_preview_ui.py [--port 2500]
"""

import os
import sys
import json
import argparse
import subprocess
import threading
import requests
import yaml
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, send_file, Response, request, redirect, url_for, flash
from flask_cors import CORS

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.config_loader import load_config
from camera_presets import (
    apply_preset as apply_camera_preset,
    DEFAULT_CAMERA_IP,
    DEFAULT_CAMERA_PASS,
    DEFAULT_CAMERA_USER,
)

app = Flask(__name__)
app.secret_key = 'meter-preview-secret-key-change-in-production'

# Enable CORS for React dashboard (supports both dev server ports)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173", "http://127.0.0.1:5173",
            "http://localhost:4176", "http://127.0.0.1:4176"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Global config
CONFIG = None
CONFIG_PATH = None
LOG_DIR = Path("logs")

# Track running readings (to prevent duplicate triggers)
READING_IN_PROGRESS = set()

# Track rotation settings per meter (in degrees: 0, 90, 180, 270)
ROTATION_SETTINGS = {}


def get_latest_snapshot(meter_name: str, meter_type: str):
    """Get the latest snapshot for a meter"""
    snapshot_dir = LOG_DIR / f"{meter_type}_snapshots"

    if not snapshot_dir.exists():
        return None

    # Get all snapshots, sorted by modification time
    snapshots = sorted(
        snapshot_dir.glob("*.jpg"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    return snapshots[0] if snapshots else None


def get_latest_reading(meter_type: str):
    """Get the latest reading for a meter from JSONL log"""
    log_file = LOG_DIR / f"{meter_type}_readings.jsonl"

    if not log_file.exists():
        return None

    # Read last line
    with open(log_file, 'r') as f:
        lines = f.readlines()
        if lines:
            try:
                return json.loads(lines[-1].strip())
            except json.JSONDecodeError:
                return None

    return None


def format_timestamp(iso_timestamp):
    """Format ISO timestamp to human-readable"""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_timestamp


@app.route('/')
def index():
    """Main view - show first meter's historical readings"""
    if CONFIG and CONFIG.get('meters'):
        # Auto-load first meter
        first_meter = CONFIG['meters'][0]
        meter_name = first_meter.get('name', 'unknown')
        return meter_detail(meter_name)
    else:
        return "No meters configured", 404


@app.route('/settings')
def settings():
    """Settings utility page with live preview and camera controls"""
    meters = []

    if CONFIG:
        for meter_config in CONFIG.get('meters', []):
            meter_name = meter_config.get('name', 'unknown')
            meter_type = meter_config.get('type', 'unknown')

            latest_snapshot = get_latest_snapshot(meter_name, meter_type)
            latest_reading = get_latest_reading(meter_type)

            meter_info = {
                'name': meter_name,
                'type': meter_type,
                'camera_ip': meter_config.get('camera_ip', 'N/A'),
                'reading_interval': meter_config.get('reading_interval', 'N/A'),
                'has_snapshot': latest_snapshot is not None,
                'has_reading': latest_reading is not None,
                'snapshot_path': f'/snapshot/{meter_type}' if latest_snapshot else None,
                'reading': latest_reading
            }

            meters.append(meter_info)

    return render_template('settings.html', meters=meters, format_timestamp=format_timestamp)


@app.route('/snapshot/<meter_type>')
def snapshot(meter_type):
    """Serve the latest snapshot for a meter type"""
    # Find meter config
    meter_config = None
    if CONFIG:
        for m in CONFIG.get('meters', []):
            if m.get('type') == meter_type:
                meter_config = m
                break

    if not meter_config:
        return "Meter not found", 404

    meter_name = meter_config.get('name', 'unknown')
    latest_snapshot = get_latest_snapshot(meter_name, meter_type)

    if not latest_snapshot:
        return "No snapshot available", 404

    return send_file(latest_snapshot, mimetype='image/jpeg')


@app.route('/meter/<meter_name>')
def meter_detail(meter_name):
    """Show detailed reading history for a specific meter"""
    # Find meter config
    meter_config = None
    if CONFIG:
        for m in CONFIG.get('meters', []):
            if m.get('name') == meter_name:
                meter_config = m
                break

    if not meter_config:
        return f"Meter '{meter_name}' not found", 404

    meter_type = meter_config.get('type', 'unknown')

    # Get all readings from JSONL
    readings = []
    log_file = LOG_DIR / f"{meter_type}_readings.jsonl"

    if log_file.exists():
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    reading = json.loads(line.strip())
                    readings.append(reading)
                except json.JSONDecodeError:
                    continue

    # Reverse to show newest first
    readings.reverse()

    # Get all snapshots with metadata
    snapshots = []
    snapshot_dir = LOG_DIR / "meter_snapshots" / meter_name

    if snapshot_dir.exists():
        # Get all JSON metadata files
        json_files = sorted(
            snapshot_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True  # Newest first
        )

        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    metadata = json.load(f)
                    # Add the relative path for web serving
                    image_filename = json_file.stem + '.jpg'
                    metadata['image_url'] = f'/static/snapshots/{meter_name}/{image_filename}'
                    snapshots.append(metadata)
            except (json.JSONDecodeError, FileNotFoundError):
                continue

    return render_template('meter.html',
                         meter_name=meter_name,
                         meter_type=meter_type,
                         readings=readings,
                         snapshots=snapshots,
                         format_timestamp=format_timestamp)


@app.route('/static/snapshots/<meter_name>/<filename>')
def serve_snapshot(meter_name, filename):
    """Serve snapshot images from logs directory"""
    snapshot_path = LOG_DIR / "meter_snapshots" / meter_name / filename
    if snapshot_path.exists():
        return send_file(snapshot_path, mimetype='image/jpeg')
    return "Snapshot not found", 404


@app.route('/api/meters')
def api_meters():
    """API endpoint returning meter data as JSON"""
    meters = []

    if CONFIG:
        for meter_config in CONFIG.get('meters', []):
            meter_name = meter_config.get('name', 'unknown')
            meter_type = meter_config.get('type', 'unknown')

            latest_snapshot = get_latest_snapshot(meter_name, meter_type)
            latest_reading = get_latest_reading(meter_type)

            meter_info = {
                'name': meter_name,
                'type': meter_type,
                'camera_ip': meter_config.get('camera_ip', 'N/A'),
                'reading_interval': meter_config.get('reading_interval', 'N/A'),
                'has_snapshot': latest_snapshot is not None,
                'has_reading': latest_reading is not None,
                'snapshot_url': f'/snapshot/{meter_type}' if latest_snapshot else None,
                'snapshot_timestamp': latest_snapshot.stat().st_mtime if latest_snapshot else None,
                'reading': latest_reading
            }

            meters.append(meter_info)

    return jsonify(meters)


def trigger_reading_async(meter_type):
    """Trigger a reading in the background"""
    try:
        # Build environment from config
        env = os.environ.copy()

        # Find meter config
        if CONFIG:
            for meter_config in CONFIG.get('meters', []):
                if meter_config.get('type') == meter_type:
                    # Add meter-specific env vars
                    cam_ip = meter_config.get('camera_ip', '')
                    cam_user = meter_config.get('camera_user', '')
                    cam_pass = meter_config.get('camera_pass', '')

                    # Set env vars (handle ${VAR:default} format)
                    if cam_ip.startswith('${') and cam_ip.endswith('}'):
                        var_part = cam_ip[2:-1]
                        if ':' in var_part:
                            var_name, default = var_part.split(':', 1)
                            env[var_name] = env.get(var_name, default)

                    break

        # Create a temporary config file with just this meter
        temp_config_path = Path(f"/tmp/meter_config_{meter_type}.yaml")

        # Run multi_meter_monitor.py --run-once
        result = subprocess.run(
            [sys.executable, 'multi_meter_monitor.py', '--run-once', str(temp_config_path)],
            env=env,
            capture_output=True,
            text=True,
            timeout=90
        )

        print(f"[{meter_type}] Reading completed with exit code: {result.returncode}")
        if result.returncode != 0:
            print(f"[{meter_type}] Error output: {result.stderr}")

    except Exception as e:
        print(f"[{meter_type}] Error triggering reading: {e}")
    finally:
        READING_IN_PROGRESS.discard(meter_type)


@app.route('/api/trigger/<meter_type>', methods=['POST'])
def api_trigger_reading(meter_type):
    """Trigger a new reading for a specific meter"""

    # Check if already in progress
    if meter_type in READING_IN_PROGRESS:
        return jsonify({
            'status': 'in_progress',
            'message': f'Reading already in progress for {meter_type} meter'
        })

    # Mark as in progress
    READING_IN_PROGRESS.add(meter_type)

    # Start reading in background thread
    thread = threading.Thread(target=trigger_reading_async, args=(meter_type,))
    thread.daemon = True
    thread.start()

    return jsonify({
        'status': 'triggered',
        'message': f'Reading triggered for {meter_type} meter. Check back in 15-30 seconds.'
    })


@app.route('/api/status/<meter_type>')
def api_status(meter_type):
    """Check if a reading is in progress"""
    return jsonify({
        'in_progress': meter_type in READING_IN_PROGRESS
    })


@app.route('/api/stream/<meter_type>')
def api_stream(meter_type):
    """Proxy MJPEG stream from camera"""
    try:
        # Find meter config
        meter_config = None
        if CONFIG:
            for m in CONFIG.get('meters', []):
                if m.get('type') == meter_type:
                    meter_config = m
                    break

        if not meter_config:
            return "Meter not found", 404

        camera_ip = meter_config.get('camera_ip', '').replace('${WATER_CAM_IP:', '').replace('}', '').split(':')[-1] or '10.10.10.207'
        camera_user = meter_config.get('camera_user', '').replace('${WATER_CAM_USER:', '').replace('}', '').split(':')[-1] or 'root'
        camera_pass = meter_config.get('camera_pass', '').replace('${WATER_CAM_PASS:', '').replace('}', '').split(':')[-1] or '***REMOVED***'

        # Stream MJPEG from camera
        mjpeg_url = f"http://{camera_user}:{camera_pass}@{camera_ip}/mjpeg"

        def generate():
            """Stream MJPEG frames from camera"""
            response = requests.get(mjpeg_url, stream=True, timeout=30)
            for chunk in response.iter_content(chunk_size=1024):
                yield chunk

        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

    except Exception as e:
        return f"Stream error: {str(e)}", 500


@app.route('/api/preset/<meter_type>/<preset_name>', methods=['POST'])
def api_apply_preset(meter_type, preset_name):
    """Apply a camera preset"""
    try:
        if not CONFIG:
            return jsonify({
                'status': 'error',
                'message': 'Configuration not loaded'
            }), 500

        meter_config = next(
            (m for m in CONFIG.get('meters', []) if m.get('type') == meter_type),
            None
        )

        if not meter_config:
            return jsonify({
                'status': 'error',
                'message': f'Meter type {meter_type} not found'
            }), 404

        camera_ip = meter_config.get('camera_ip') or DEFAULT_CAMERA_IP
        camera_user = meter_config.get('camera_user') or DEFAULT_CAMERA_USER
        camera_pass = meter_config.get('camera_pass') or DEFAULT_CAMERA_PASS

        # Debug logging
        print(f"🔧 Applying preset '{preset_name}' to {meter_type}")
        print(f"   Camera: {camera_ip}, User: {camera_user}")

        result = apply_camera_preset(
            preset_name,
            camera_ip=camera_ip,
            camera_user=camera_user,
            camera_pass=camera_pass
        )

        if result.get('success'):
            return jsonify({
                'status': 'success',
                'message': f'Applied {preset_name} preset to {camera_ip}',
                'details': result
            })

        return jsonify({
            'status': 'error',
            'message': f"Failed to apply preset {preset_name}",
            'details': result
        }), 500

    except Exception as e:
        import traceback
        print(f"❌ Error applying preset: {e}")
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/rotation/<meter_type>', methods=['GET', 'POST'])
def api_rotation(meter_type):
    """Get or set image rotation for a meter"""
    if request.method == 'GET':
        # Get current rotation setting
        rotation = ROTATION_SETTINGS.get(meter_type, 0)
        return jsonify({
            'status': 'success',
            'rotation': rotation
        })

    elif request.method == 'POST':
        # Set rotation
        try:
            data = request.get_json() or {}
            rotation = data.get('rotation', 0)

            # Validate rotation value
            if rotation not in [0, 90, 180, 270]:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid rotation: {rotation}. Must be 0, 90, 180, or 270'
                }), 400

            # Store rotation setting
            ROTATION_SETTINGS[meter_type] = rotation

            return jsonify({
                'status': 'success',
                'rotation': rotation,
                'message': f'Rotation set to {rotation}°'
            })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500


@app.route('/api/optimize/<meter_type>', methods=['POST'])
def api_run_optimization(meter_type):
    """Run camera optimization experiment"""
    try:
        # Run optimization in background
        def run_optimization():
            subprocess.run(
                [sys.executable, 'optimize_camera_settings.py'],
                capture_output=True,
                text=True,
                timeout=900
            )

        thread = threading.Thread(target=run_optimization)
        thread.daemon = True
        thread.start()

        return jsonify({
            'status': 'started',
            'message': 'Optimization started. Results in ~12 minutes.'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/presets')
def api_list_presets():
    """List available camera presets"""
    presets = {
        "night_vision": {"name": "🌙 Night Vision", "desc": "IR LED + High Contrast"},
        "day_clear": {"name": "☀️ Day Mode", "desc": "Natural Light Optimized"},
        "low_noise": {"name": "🔇 Low Noise", "desc": "Smoother Image"},
        "high_detail": {"name": "🔍 High Detail", "desc": "Max Sharpness"},
        "balanced": {"name": "⚖️ Balanced", "desc": "All-Around Good"},
        "auto_adaptive": {"name": "🤖 Auto", "desc": "Camera Decides"}
    }
    return jsonify(presets)


@app.route('/api/reprocess/<meter_type>', methods=['POST'])
def api_reprocess_snapshot(meter_type):
    """Reprocess an existing snapshot image"""
    try:
        data = request.get_json()
        filename = data.get('filename')

        if not filename:
            return jsonify({'status': 'error', 'error': 'No filename provided'})

        # Find the meter config
        if not CONFIG or 'meters' not in CONFIG:
            return jsonify({'status': 'error', 'error': 'No meters configured'})

        meter = CONFIG['meters'][0]
        meter_name = meter.get('name', 'unknown')

        # Get the image path
        image_path = LOG_DIR / 'meter_snapshots' / meter_name / filename

        if not image_path.exists():
            return jsonify({'status': 'error', 'error': f'Image not found: {filename}'})

        # Import and run analysis
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from gemini_reader import read_meter

        # Use Gemini (free) with Claude fallback
        reading = read_meter(str(image_path), fallback_to_claude=True)

        if 'error' in reading:
            return jsonify({'status': 'error', 'error': reading['error']})

        # Update the metadata JSON file
        metadata_path = image_path.with_suffix('.json')
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            metadata['meter_reading'] = reading

            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

        # Log to JSONL
        log_file = LOG_DIR / f"{meter_type}_readings.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(reading) + '\n')

        # Try InfluxDB (optional)
        try:
            from influx_logger import MeterInfluxLogger
            logger = MeterInfluxLogger()
            logger.log_reading(meter_name, meter_type, reading)
        except Exception:
            pass

        return jsonify({
            'status': 'success',
            'reading': reading.get('total_reading'),
            'confidence': reading.get('confidence'),
            'dial_angle_degrees': reading.get('dial_angle_degrees')
        })

    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/api/snapshot/<meter_type>', methods=['POST'])
def api_capture_snapshot(meter_type):
    """Capture snapshot and run full analysis/logging workflow"""
    try:
        # Run the complete workflow script
        result = subprocess.run(
            ['python3', 'run_meter_reading.py'],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=Path(__file__).parent
        )

        if result.returncode == 0:
            # Parse JSON output
            try:
                data = json.loads(result.stdout)
                return jsonify(data)
            except json.JSONDecodeError:
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to parse output: {result.stdout}'
                }), 500
        else:
            return jsonify({
                'status': 'error',
                'message': f'Workflow failed: {result.stderr}'
            }), 500

    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': 'Analysis timed out (60s)'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/snapshot/delete/<meter_type>', methods=['POST'])
def api_delete_snapshot(meter_type):
    """Delete the latest snapshot"""
    try:
        # Find meter config
        meter_config = None
        if CONFIG:
            for m in CONFIG.get('meters', []):
                if m.get('type') == meter_type:
                    meter_config = m
                    break

        if not meter_config:
            return jsonify({'status': 'error', 'message': 'Meter not found'}), 404

        meter_name = meter_config.get('name', 'unknown')
        latest_snapshot = get_latest_snapshot(meter_name, meter_type)

        if not latest_snapshot:
            return jsonify({'status': 'error', 'message': 'No snapshot to delete'}), 404

        # Delete the snapshot file
        snapshot_path = Path(latest_snapshot)
        metadata_path = snapshot_path.with_suffix('.json')

        # Delete snapshot
        if snapshot_path.exists():
            snapshot_path.unlink()

        # Delete associated metadata if exists
        if metadata_path.exists():
            metadata_path.unlink()

        return jsonify({
            'status': 'success',
            'message': 'Snapshot deleted',
            'deleted_file': snapshot_path.name
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/snapshot/reanalyze/<meter_type>', methods=['POST'])
def api_reanalyze_snapshot(meter_type):
    """Reanalyze the latest snapshot"""
    try:
        # Find meter config
        meter_config = None
        if CONFIG:
            for m in CONFIG.get('meters', []):
                if m.get('type') == meter_type:
                    meter_config = m
                    break

        if not meter_config:
            return jsonify({'status': 'error', 'message': 'Meter not found'}), 404

        meter_name = meter_config.get('name', 'unknown')
        latest_snapshot = get_latest_snapshot(meter_name, meter_type)

        if not latest_snapshot:
            return jsonify({'status': 'error', 'message': 'No snapshot to analyze'}), 404

        # Import and use llm_reader
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from llm_reader import read_meter_with_claude

        # Analyze the existing snapshot
        result = read_meter_with_claude(str(latest_snapshot))

        if 'error' in result:
            return jsonify({
                'status': 'error',
                'message': f"Analysis failed: {result['error']}",
                'details': result
            }), 500

        # Update metadata file
        snapshot_path = Path(latest_snapshot)
        metadata_path = snapshot_path.with_suffix('.json')

        metadata = {
            "snapshot": {
                "filename": snapshot_path.name,
                "timestamp": datetime.now().isoformat(),
                "path": str(snapshot_path)
            },
            "meter_reading": {
                "digital_reading": result.get('digital_reading'),
                "black_digit": result.get('black_digit'),
                "dial_reading": result.get('dial_reading'),
                "total_reading": result.get('total_reading'),
                "confidence": result.get('confidence'),
                "notes": result.get('notes')
            },
            "api_usage": result.get('api_usage', {}),
            "camera": {
                "source_file": snapshot_path.name,
                "model": "Wyze Cam V2 (Thingino)",
                "ip": meter_config.get('camera_ip', 'N/A')
            },
            "reanalyzed": True,
            "reanalyzed_at": datetime.now().isoformat()
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Also update the readings JSONL file
        log_file = LOG_DIR / f"{meter_type}_readings.jsonl"
        reading_entry = {
            **result,
            "meter_type": meter_type,
            "reanalyzed": True,
            "timestamp": datetime.now().isoformat()
        }

        with open(log_file, 'a') as f:
            f.write(json.dumps(reading_entry) + '\n')

        return jsonify({
            'status': 'success',
            'message': 'Snapshot reanalyzed',
            'reading': result
        })

    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/snapshots/<meter_name>', methods=['GET'])
def api_get_snapshots(meter_name):
    """Get list of snapshots for a meter as JSON"""
    try:
        snapshots = []
        snapshot_dir = LOG_DIR / "meter_snapshots" / meter_name

        if snapshot_dir.exists():
            # Get all JSON metadata files
            json_files = sorted(
                snapshot_dir.glob("*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True  # Newest first
            )

            for json_file in json_files:
                try:
                    with open(json_file, 'r') as f:
                        metadata = json.load(f)
                        # Add the relative path for web serving
                        image_filename = json_file.stem + '.jpg'
                        metadata['image_url'] = f'/static/snapshots/{meter_name}/{image_filename}'
                        snapshots.append(metadata)
                except (json.JSONDecodeError, FileNotFoundError):
                    continue

        return jsonify({
            'status': 'success',
            'snapshots': snapshots,
            'count': len(snapshots)
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/consumption/<meter_type>', methods=['GET'])
def api_get_consumption(meter_type):
    """Get consumption data for graphing with flexible time periods and intervals"""
    try:
        from datetime import datetime, timedelta
        from collections import defaultdict

        # Get query parameters
        period = request.args.get('period', '24h')
        interval = request.args.get('interval', 'hour')

        log_file = LOG_DIR / f"{meter_type}_readings.jsonl"
        if not log_file.exists():
            return jsonify({
                'status': 'success',
                'hours': [],
                'consumption': [],
                'unit': 'm³'
            })

        # Parse period to determine cutoff time
        now = datetime.now()
        period_map = {
            '24h': timedelta(hours=24),
            '7d': timedelta(days=7),
            '10d': timedelta(days=10),
            '30d': timedelta(days=30),
            '90d': timedelta(days=90)
        }
        cutoff_time = now - period_map.get(period, timedelta(hours=24))

        # Read all valid readings from JSONL within time period
        readings = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if 'total_reading' in data and data.get('total_reading') is not None:
                        timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                        if timestamp >= cutoff_time:
                            readings.append({
                                'timestamp': timestamp,
                                'total': float(data['total_reading'])
                            })
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue

        if not readings:
            return jsonify({
                'status': 'success',
                'hours': [],
                'consumption': [],
                'unit': 'm³'
            })

        # Sort by timestamp
        readings.sort(key=lambda x: x['timestamp'])

        # Group by interval
        interval_data = defaultdict(lambda: {'readings': [], 'timestamps': []})

        for reading in readings:
            if interval == '5min':
                # Round to nearest 5-minute interval
                minute = (reading['timestamp'].minute // 5) * 5
                rounded_time = reading['timestamp'].replace(minute=minute, second=0, microsecond=0)
                key = rounded_time.strftime('%Y-%m-%d %H:%M')
                label = rounded_time.strftime('%H:%M')
            elif interval == '15min':
                # Round to nearest 15-minute interval
                minute = (reading['timestamp'].minute // 15) * 15
                rounded_time = reading['timestamp'].replace(minute=minute, second=0, microsecond=0)
                key = rounded_time.strftime('%Y-%m-%d %H:%M')
                label = rounded_time.strftime('%H:%M')
            elif interval == '30min':
                # Round to nearest 30-minute interval
                minute = (reading['timestamp'].minute // 30) * 30
                rounded_time = reading['timestamp'].replace(minute=minute, second=0, microsecond=0)
                key = rounded_time.strftime('%Y-%m-%d %H:%M')
                label = rounded_time.strftime('%H:%M')
            elif interval == 'hour':
                key = reading['timestamp'].strftime('%Y-%m-%d %H:00')
                label = reading['timestamp'].strftime('%H:00')
            elif interval == 'day':
                key = reading['timestamp'].strftime('%Y-%m-%d')
                label = reading['timestamp'].strftime('%b %d')
            elif interval == 'week':
                # Week starting on Monday
                week_start = reading['timestamp'] - timedelta(days=reading['timestamp'].weekday())
                key = week_start.strftime('%Y-W%U')
                label = week_start.strftime('%b %d')
            else:
                key = reading['timestamp'].strftime('%Y-%m-%d %H:00')
                label = reading['timestamp'].strftime('%H:00')

            interval_data[key]['readings'].append(reading['total'])
            interval_data[key]['timestamps'].append(reading['timestamp'])
            interval_data[key]['label'] = label

        # Calculate consumption (max - min) for each interval
        labels = []
        consumption = []

        sorted_keys = sorted(interval_data.keys())
        for key in sorted_keys:
            data = interval_data[key]
            if len(data['readings']) >= 2:
                interval_consumption = max(data['readings']) - min(data['readings'])
                labels.append(data['label'])
                consumption.append(round(interval_consumption, 3))

        return jsonify({
            'status': 'success',
            'hours': labels,
            'consumption': consumption,
            'unit': 'm³'
        })

    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/config/meters', methods=['GET'])
def api_config_meters():
    """Get meter configuration with display metadata"""
    try:
        meters_config = []

        if CONFIG and 'meters' in CONFIG:
            # Meter display configuration (icons, colors, labels)
            meter_display = {
                'water': {
                    'icon': 'droplets',
                    'label': 'Water Meter',
                    'color': '#3b82f6',  # blue
                    'lightColor': '#eff6ff',
                    'darkColor': '#1e3a8a',
                    'unit': 'm³'
                },
                'electric': {
                    'icon': 'zap',
                    'label': 'Electric Meter',
                    'color': '#eab308',  # yellow
                    'lightColor': '#fefce8',
                    'darkColor': '#713f12',
                    'unit': 'kWh'
                },
                'gas': {
                    'icon': 'flame',
                    'label': 'Gas Meter',
                    'color': '#f97316',  # orange
                    'lightColor': '#fff7ed',
                    'darkColor': '#7c2d12',
                    'unit': 'm³'
                }
            }

            for meter in CONFIG['meters']:
                meter_type = meter.get('type', 'unknown')
                display = meter_display.get(meter_type, {})

                meters_config.append({
                    'name': meter.get('name'),
                    'type': meter_type,
                    'display': display,
                    'reading_interval': meter.get('reading_interval'),
                    'camera_ip': meter.get('camera_ip')
                })

        return jsonify({
            'status': 'success',
            'meters': meters_config
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/config/pricing', methods=['GET'])
def api_config_pricing():
    """Get pricing configuration from pricing.json"""
    try:
        pricing_file = Path('config/pricing.json')

        if not pricing_file.exists():
            return jsonify({
                'status': 'error',
                'message': 'Pricing configuration not found'
            }), 404

        with open(pricing_file, 'r') as f:
            pricing_data = json.load(f)

        return jsonify({
            'status': 'success',
            'pricing': pricing_data.get('utility_rates', {}),
            'household': pricing_data.get('household', {}),
            'metadata': pricing_data.get('utility_rates', {}).get('metadata', {})
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/config/edit', methods=['GET'])
def config_edit():
    """Configuration editor page"""
    # Load current meter configuration
    meters_config_raw = ""
    if CONFIG_PATH and Path(CONFIG_PATH).exists():
        with open(CONFIG_PATH, 'r') as f:
            meters_config_raw = f.read()

    # Load current pricing configuration
    pricing_config_raw = ""
    pricing_file = Path('config/pricing.json')
    if pricing_file.exists():
        with open(pricing_file, 'r') as f:
            pricing_config_raw = json.dumps(json.load(f), indent=2)

    return render_template('config_edit.html',
                         meters_config=meters_config_raw,
                         pricing_config=pricing_config_raw)


@app.route('/config/save/meters', methods=['POST'])
def config_save_meters():
    """Save meter configuration"""
    try:
        meters_config = request.form.get('meters_config', '')

        if not CONFIG_PATH:
            flash('Error: Config path not set', 'error')
            return redirect(url_for('config_edit'))

        # Validate YAML syntax
        try:
            yaml.safe_load(meters_config)
        except yaml.YAMLError as e:
            flash(f'Invalid YAML syntax: {str(e)}', 'error')
            return redirect(url_for('config_edit'))

        # Save to file
        with open(CONFIG_PATH, 'w') as f:
            f.write(meters_config)

        # Reload configuration
        global CONFIG
        CONFIG = load_config(CONFIG_PATH)

        flash('✅ Meter configuration saved successfully!', 'success')
        return redirect(url_for('config_edit'))

    except Exception as e:
        flash(f'Error saving meter configuration: {str(e)}', 'error')
        return redirect(url_for('config_edit'))


@app.route('/config/save/pricing', methods=['POST'])
def config_save_pricing():
    """Save pricing configuration"""
    try:
        pricing_config = request.form.get('pricing_config', '')

        # Validate JSON syntax
        try:
            pricing_data = json.loads(pricing_config)
        except json.JSONDecodeError as e:
            flash(f'Invalid JSON syntax: {str(e)}', 'error')
            return redirect(url_for('config_edit'))

        # Save to file
        pricing_file = Path('config/pricing.json')
        with open(pricing_file, 'w') as f:
            json.dump(pricing_data, f, indent=2)

        flash('✅ Pricing configuration saved successfully!', 'success')
        return redirect(url_for('config_edit'))

    except Exception as e:
        flash(f'Error saving pricing configuration: {str(e)}', 'error')
        return redirect(url_for('config_edit'))


@app.route('/api/bill/upload', methods=['POST'])
def api_bill_upload():
    """Handle bill upload and parse with LLM"""
    try:
        from datetime import datetime
        from werkzeug.utils import secure_filename
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from bill_parser import parse_bill_with_gemini, save_bill_data

        # Get uploaded file
        if 'bill' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400

        file = request.files['bill']
        utility_type = request.form.get('utility_type', 'water')

        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        upload_dir = LOG_DIR / 'bill_uploads' / utility_type
        upload_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_path = upload_dir / f"{timestamp}_{filename}"

        file.save(str(save_path))

        # Parse bill with Gemini
        result = parse_bill_with_gemini(str(save_path), utility_type)

        if 'error' in result:
            return jsonify({
                'status': 'error',
                'message': result['error']
            }), 500

        # Add upload metadata
        result['uploaded_at'] = datetime.now().isoformat()
        result['original_filename'] = filename

        # Save to config
        save_bill_data(result, config_path='config/pricing.json')

        return jsonify({
            'status': 'success',
            'extracted': result.get('extracted', {}),
            'api_usage': result.get('api_usage', {}),
            'message': 'Bill parsed successfully'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.template_filter('timestamp')
def timestamp_filter(iso_timestamp):
    """Template filter for formatting timestamps"""
    return format_timestamp(iso_timestamp)


def create_templates():
    """Create HTML templates if they don't exist"""
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)

    # Create index.html template
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meter Preview Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 15px;
            font-size: 14px;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }

        .header h1 {
            font-size: 1.4em;
            margin-bottom: 5px;
        }

        .header p {
            opacity: 0.9;
            font-size: 0.9em;
        }

        .controls {
            background: #1e293b;
            padding: 12px 15px;
            border-radius: 6px;
            margin-bottom: 12px;
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .btn {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.2s;
        }

        .btn:hover {
            background: #2563eb;
        }

        .btn.secondary {
            background: #6b7280;
        }

        .btn.secondary:hover {
            background: #4b5563;
        }

        .auto-refresh-label {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }

        .meters-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 15px;
        }

        .meter-card {
            background: #1e293b;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            border: 1px solid #334155;
        }

        .meter-header {
            background: #334155;
            padding: 12px 15px;
            border-bottom: 1px solid #475569;
        }

        .meter-name {
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 5px;
            text-transform: capitalize;
        }

        .meter-meta {
            display: flex;
            gap: 20px;
            font-size: 0.9em;
            color: #94a3b8;
        }

        .meter-meta span {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 600;
        }

        .status-success {
            background: #10b981;
            color: white;
        }

        .status-error {
            background: #ef4444;
            color: white;
        }

        .status-warning {
            background: #f59e0b;
            color: white;
        }

        .meter-body {
            padding: 12px;
        }

        .snapshot-container {
            background: #0f172a;
            border-radius: 6px;
            padding: 8px;
            margin-bottom: 12px;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }

        .snapshot-image {
            width: 100%;
            max-height: 400px;
            object-fit: contain;
            border-radius: 6px;
            display: block;
        }

        .snapshot-actions {
            display: flex;
            gap: 8px;
            justify-content: center;
            margin-top: 8px;
        }

        .btn-snapshot-action {
            background: #334155;
            color: #e2e8f0;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .btn-snapshot-action:hover {
            background: #475569;
            transform: translateY(-1px);
        }

        .btn-snapshot-action:active {
            transform: translateY(0);
        }

        .btn-snapshot-action.btn-reanalyze:hover {
            background: #3b82f6;
        }

        .btn-snapshot-action.btn-delete:hover {
            background: #dc2626;
        }

        .btn-snapshot-action:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .no-snapshot {
            text-align: center;
            padding: 60px 20px;
            color: #64748b;
            font-size: 1.1em;
        }

        .reading-data {
            background: #0f172a;
            border-radius: 6px;
            padding: 12px;
        }

        .reading-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #334155;
        }

        .reading-row:last-child {
            border-bottom: none;
        }

        .reading-label {
            color: #94a3b8;
            font-weight: 500;
        }

        .reading-value {
            font-weight: 600;
            color: #e2e8f0;
        }

        .reading-value.large {
            font-size: 1.3em;
            color: #3b82f6;
        }

        .confidence-high { color: #10b981; }
        .confidence-medium { color: #f59e0b; }
        .confidence-low { color: #ef4444; }

        .error-message {
            background: #7f1d1d;
            color: #fecaca;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #ef4444;
        }

        .timestamp {
            color: #64748b;
            font-size: 0.85em;
            margin-top: 10px;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #64748b;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #334155;
            border-top-color: #3b82f6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        .camera-controls {
            background: #0f172a;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 12px;
        }

        .control-section {
            margin-bottom: 12px;
        }

        .control-section:last-child {
            margin-bottom: 0;
        }

        .control-section h3 {
            font-size: 0.85em;
            margin-bottom: 8px;
            color: #94a3b8;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .preset-buttons {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 6px;
        }

        .btn-preset {
            background: #334155;
            color: #e2e8f0;
            border: 1px solid #475569;
            padding: 8px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
            white-space: nowrap;
        }

        .btn-preset:hover {
            background: #475569;
            border-color: #64748b;
            transform: translateY(-1px);
        }

        .btn-preset:active {
            transform: translateY(0);
        }

        .btn-preset.active {
            background: #3b82f6;
            border-color: #2563eb;
        }

        .action-buttons {
            display: flex;
            gap: 10px;
        }

        .btn-action {
            flex: 1;
            background: #3b82f6;
            color: white;
            border: none;
            padding: 10px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
        }

        .btn-action:hover {
            background: #2563eb;
            transform: translateY(-1px);
        }

        .btn-action:active {
            transform: translateY(0);
        }

        .btn-optimize {
            background: #8b5cf6;
        }

        .btn-optimize:hover {
            background: #7c3aed;
        }

        .btn-reading {
            background: #10b981;
        }

        .btn-reading:hover {
            background: #059669;
        }

        .status-message {
            margin-top: 10px;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .status-message.info {
            background: #1e3a8a;
            color: #93c5fd;
            border-left: 4px solid #3b82f6;
        }

        .status-message.success {
            background: #064e3b;
            color: #6ee7b7;
            border-left: 4px solid #10b981;
        }

        .status-message.error {
            background: #7f1d1d;
            color: #fecaca;
            border-left: 4px solid #ef4444;
        }

        .status-message.processing {
            background: #4c1d95;
            color: #ddd6fe;
            border-left: 4px solid #8b5cf6;
        }

        .activity-log {
            background: #0f172a;
            border-radius: 6px;
            padding: 12px;
            margin-top: 12px;
            max-height: 200px;
            overflow-y: auto;
        }

        .activity-log h3 {
            font-size: 0.85em;
            margin-bottom: 8px;
            color: #94a3b8;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .log-entry {
            font-size: 11px;
            padding: 4px 8px;
            margin-bottom: 4px;
            border-left: 2px solid #334155;
            color: #cbd5e1;
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
        }

        .log-entry:last-child {
            margin-bottom: 0;
        }

        .log-timestamp {
            color: #64748b;
            margin-right: 8px;
        }

        .log-action {
            color: #3b82f6;
        }

        .log-success {
            border-left-color: #10b981;
        }

        .log-error {
            border-left-color: #ef4444;
        }

        .snapshot-loading {
            position: relative;
        }

        .snapshot-loading::after {
            content: 'Loading...';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(15, 23, 42, 0.9);
            color: #3b82f6;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Meter Preview Dashboard</h1>
        <p>Real-time camera captures and meter readings</p>
    </div>

    <div class="controls">
        <button class="btn" onclick="refreshAll()">🔄 Refresh All</button>
        <label class="auto-refresh-label">
            <input type="checkbox" id="autoRefresh" onchange="toggleAutoRefresh()">
            Auto-refresh every 5 seconds
        </label>
        <div style="flex: 1;"></div>
        <span id="lastUpdate" style="color: #64748b; font-size: 14px;"></span>
    </div>

    <div class="meters-grid">
        {% if meters %}
            {% for meter in meters %}
            <div class="meter-card">
                <div class="meter-header">
                    <div class="meter-name">
                        {{ meter.name }}
                        {% if meter.has_reading and not meter.reading.get('error') %}
                            <span class="status-badge status-success">Online</span>
                        {% elif meter.reading and meter.reading.get('error') %}
                            <span class="status-badge status-error">Error</span>
                        {% else %}
                            <span class="status-badge status-warning">No Data</span>
                        {% endif %}
                    </div>
                    <div class="meter-meta">
                        <span>📹 {{ meter.camera_ip }}</span>
                        <span>🔄 {{ meter.reading_interval }}s</span>
                        <span>{{ meter.type|upper }}</span>
                    </div>
                </div>

                <div class="meter-body">
                    <div class="snapshot-container">
                        <img src="/api/stream/{{ meter.type }}"
                             alt="{{ meter.name }} live stream"
                             class="snapshot-image">

                        <!-- Snapshot Actions -->
                        <div class="snapshot-actions">
                            <button class="btn-snapshot-action btn-reanalyze"
                                    onclick="reanalyzeSnapshot('{{ meter.type }}')"
                                    title="Reanalyze this snapshot with Claude">
                                🔄 Reanalyze
                            </button>
                            <button class="btn-snapshot-action btn-delete"
                                    onclick="deleteSnapshot('{{ meter.type }}')"
                                    title="Delete this snapshot">
                                🗑️ Delete
                            </button>
                        </div>
                    </div>

                    <!-- Camera Controls -->
                    <div class="camera-controls">
                        <!-- Camera Presets: Temporarily disabled - Thingino firmware uses different API endpoints -->
                        <!--
                        <div class="control-section">
                            <h3>📹 Camera Presets</h3>
                            <div class="preset-buttons">
                                <button class="btn-preset" onclick="applyPreset(this, '{{ meter.type }}', 'night_vision')">🌙 Night Vision</button>
                                <button class="btn-preset" onclick="applyPreset(this, '{{ meter.type }}', 'day_clear')">☀️ Day Mode</button>
                                <button class="btn-preset" onclick="applyPreset(this, '{{ meter.type }}', 'low_noise')">🔇 Low Noise</button>
                                <button class="btn-preset" onclick="applyPreset(this, '{{ meter.type }}', 'high_detail')">🔍 High Detail</button>
                                <button class="btn-preset" onclick="applyPreset(this, '{{ meter.type }}', 'balanced')">⚖️ Balanced</button>
                                <button class="btn-preset" onclick="applyPreset(this, '{{ meter.type }}', 'auto_adaptive')">🤖 Auto</button>
                            </div>
                        </div>
                        -->

                        <div class="control-section">
                            <h3>🔄 Image Rotation</h3>
                            <div class="preset-buttons">
                                <button class="btn-preset" onclick="setRotation(this, '{{ meter.type }}', 0)">0° Normal</button>
                                <button class="btn-preset" onclick="setRotation(this, '{{ meter.type }}', 90)">⤴️ 90° CW</button>
                                <button class="btn-preset" onclick="setRotation(this, '{{ meter.type }}', 180)">⤵️ 180° Flip</button>
                                <button class="btn-preset" onclick="setRotation(this, '{{ meter.type }}', 270)">⤵️ 270° CW</button>
                            </div>
                            <div style="margin-top: 8px; font-size: 11px; color: #94a3b8; text-align: center;">
                                <span id="rotation-status-{{ meter.type }}">Current: 0°</span>
                            </div>
                        </div>

                        <div class="control-section">
                            <h3>🔬 Actions</h3>
                            <div class="action-buttons">
                                <button class="btn-action btn-optimize" onclick="runOptimization(this, '{{ meter.type }}')">
                                    🔬 Auto-Optimize (~12 min)
                                </button>
                                <button class="btn-action btn-reading" onclick="triggerReading(this, '{{ meter.type }}')">
                                    📸 Take Reading Now
                                </button>
                            </div>
                        </div>

                        <div id="status-{{ meter.type }}" class="status-message" style="display: none;"></div>
                    </div>

                    <!-- Activity Log -->
                    <div class="activity-log">
                        <h3>📋 Activity Log</h3>
                        <div id="log-{{ meter.type }}" class="log-content">
                            <div class="log-entry">
                                <span class="log-timestamp">[--:--:--]</span>
                                <span>Waiting for action...</span>
                            </div>
                        </div>
                    </div>

                    {% if meter.reading %}
                        {% if meter.reading.get('error') %}
                            <div class="error-message">
                                <strong>❌ Error:</strong> {{ meter.reading.error }}
                                {% if meter.reading.raw_reading and meter.reading.raw_reading.get('notes') %}
                                    <br><br>
                                    <strong>Details:</strong> {{ meter.reading.raw_reading.notes }}
                                {% endif %}
                            </div>
                        {% else %}
                            <div class="reading-data">
                                <div class="reading-row">
                                    <span class="reading-label">Total Reading</span>
                                    <span class="reading-value large">
                                        {{ "%.3f"|format(meter.reading.total_reading) }}
                                        {% if meter.type == 'water' %}m³{% elif meter.type == 'electric' %}kWh{% else %}{{ meter.reading.get('unit', 'CCF') }}{% endif %}
                                    </span>
                                </div>

                                {% if meter.reading.get('digital_reading') is not none %}
                                <div class="reading-row">
                                    <span class="reading-label">Digital Display</span>
                                    <span class="reading-value">{{ meter.reading.digital_reading }}</span>
                                </div>
                                {% endif %}

                                {% if meter.reading.get('dial_reading') is not none %}
                                <div class="reading-row">
                                    <span class="reading-label">Dial Reading</span>
                                    <span class="reading-value">{{ "%.3f"|format(meter.reading.dial_reading) }}</span>
                                </div>
                                {% endif %}

                                <div class="reading-row">
                                    <span class="reading-label">Confidence</span>
                                    <span class="reading-value confidence-{{ meter.reading.confidence }}">
                                        {{ meter.reading.confidence|upper }}
                                    </span>
                                </div>

                                {% if meter.reading.get('notes') %}
                                <div class="reading-row">
                                    <span class="reading-label">Notes</span>
                                    <span class="reading-value">{{ meter.reading.notes }}</span>
                                </div>
                                {% endif %}
                            </div>
                        {% endif %}

                        <div class="timestamp">
                            Last updated: {{ format_timestamp(meter.reading.timestamp) }}
                        </div>
                    {% else %}
                        <div class="no-snapshot">
                            No reading data available
                        </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        {% else %}
            <div class="loading">
                <div class="spinner"></div>
                <p>No meters configured</p>
            </div>
        {% endif %}
    </div>

    <script>
        let autoRefreshInterval = null;

        function refreshAll() {
            console.log('Refreshing...');
            location.reload();
        }

        function toggleAutoRefresh() {
            const checkbox = document.getElementById('autoRefresh');
            if (checkbox.checked) {
                autoRefreshInterval = setInterval(refreshAll, 5000);
                updateTimestamp();
            } else {
                if (autoRefreshInterval) {
                    clearInterval(autoRefreshInterval);
                    autoRefreshInterval = null;
                }
            }
        }

        function updateTimestamp() {
            const now = new Date().toLocaleTimeString();
            document.getElementById('lastUpdate').textContent = 'Last update: ' + now;
        }

        function addLogEntry(meterType, message, type = 'info') {
            const logEl = document.getElementById('log-' + meterType);
            const now = new Date();
            const timestamp = now.toLocaleTimeString('en-US', { hour12: false });

            const entry = document.createElement('div');
            entry.className = 'log-entry';
            if (type === 'success') entry.classList.add('log-success');
            if (type === 'error') entry.classList.add('log-error');

            entry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span><span>${message}</span>`;

            logEl.appendChild(entry);

            // Auto-scroll to bottom
            logEl.parentElement.scrollTop = logEl.parentElement.scrollHeight;

            // Keep only last 20 entries
            while (logEl.children.length > 20) {
                logEl.removeChild(logEl.firstChild);
            }
        }

        function showStatus(meterType, message, type) {
            const statusEl = document.getElementById('status-' + meterType);
            statusEl.textContent = message;
            statusEl.className = 'status-message ' + type;
            statusEl.style.display = 'block';

            // Auto-hide after 5 seconds for success messages
            if (type === 'success') {
                setTimeout(() => {
                    statusEl.style.display = 'none';
                }, 5000);
            }
        }

        async function applyPreset(buttonEl, meterType, presetName) {
            // Disable all preset buttons during operation
            const buttons = document.querySelectorAll('.btn-preset');
            buttons.forEach(btn => btn.disabled = true);

            addLogEntry(meterType, `📹 Applying ${presetName} preset to camera...`);
            showStatus(meterType, 'Applying ' + presetName + ' preset...', 'info');

            try {
                const response = await fetch(`/api/preset/${meterType}/${presetName}`, {
                    method: 'POST'
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();

                if (data.status === 'success') {
                    addLogEntry(meterType, `✓ ${presetName} mode applied to live stream`, 'success');

                    // Highlight the active preset button
                    buttons.forEach(btn => {
                        btn.classList.remove('active');
                    });
                    buttonEl.classList.add('active');

                    showStatus(meterType, `✓ ${presetName} mode active! Watch the live stream update.`, 'success');
                } else {
                    addLogEntry(meterType, `✗ Failed to apply preset: ${data.message}`, 'error');
                    showStatus(meterType, '✗ Failed: ' + (data.message || 'Unknown error'), 'error');
                }
            } catch (error) {
                addLogEntry(meterType, `✗ Error: ${error.message}`, 'error');
                showStatus(meterType, '✗ Error: ' + error.message, 'error');
            } finally {
                // Re-enable all buttons
                buttons.forEach(btn => btn.disabled = false);
            }
        }

        async function setRotation(buttonEl, meterType, degrees) {
            // Disable all rotation buttons during operation
            const rotationButtons = buttonEl.parentElement.querySelectorAll('.btn-preset');
            rotationButtons.forEach(btn => btn.disabled = true);

            addLogEntry(meterType, `🔄 Setting rotation to ${degrees}°...`);

            try {
                const response = await fetch(`/api/rotation/${meterType}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ rotation: degrees })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();

                if (data.status === 'success') {
                    addLogEntry(meterType, `✓ Rotation set to ${degrees}° (applied on next reading)`, 'success');

                    // Update status display
                    const statusEl = document.getElementById('rotation-status-' + meterType);
                    if (statusEl) {
                        statusEl.textContent = `Current: ${degrees}°`;
                    }

                    // Highlight the active rotation button
                    rotationButtons.forEach(btn => {
                        btn.classList.remove('active');
                    });
                    buttonEl.classList.add('active');

                    showStatus(meterType, `✓ Rotation set to ${degrees}°. Will apply on next reading.`, 'success');
                } else {
                    addLogEntry(meterType, `✗ Failed to set rotation: ${data.message}`, 'error');
                    showStatus(meterType, '✗ Failed: ' + (data.message || 'Unknown error'), 'error');
                }
            } catch (error) {
                addLogEntry(meterType, `✗ Error: ${error.message}`, 'error');
                showStatus(meterType, '✗ Error: ' + error.message, 'error');
            } finally {
                // Re-enable all buttons
                rotationButtons.forEach(btn => btn.disabled = false);
            }
        }

        let optimizationRunning = false;

        async function runOptimization(buttonEl, meterType) {
            if (optimizationRunning) {
                alert('Optimization already running. Please wait for it to complete.');
                return;
            }

            const confirmed = confirm(
                'This will test 6 different camera configurations and take about 12 minutes.\\n\\n' +
                'The optimization will run in the background. Results will be saved to logs/optimization_results.json.\\n\\n' +
                'Continue?'
            );

            if (!confirmed) return;

            optimizationRunning = true;
            const originalText = buttonEl.textContent;
            buttonEl.disabled = true;
            buttonEl.textContent = '🔬 Running... (~12 min)';

            showStatus(meterType, '🔬 Starting optimization experiment... (~12 minutes)', 'processing');

            try {
                const response = await fetch(`/api/optimize/${meterType}`, {
                    method: 'POST'
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();

                if (data.status === 'started') {
                    showStatus(meterType,
                        '🔬 Optimization running in background. Check logs/optimization_results.json in ~12 minutes. You can close this page safely.',
                        'processing'
                    );

                    // Keep button disabled for 5 minutes to prevent accidental re-runs
                    setTimeout(() => {
                        optimizationRunning = false;
                        buttonEl.disabled = false;
                        buttonEl.textContent = originalText;
                    }, 300000);
                } else {
                    throw new Error(data.message || 'Failed to start optimization');
                }
            } catch (error) {
                showStatus(meterType, '✗ Error: ' + error.message, 'error');
                optimizationRunning = false;
                buttonEl.disabled = false;
                buttonEl.textContent = originalText;
            }
        }

        async function triggerReading(buttonEl, meterType) {
            const originalText = buttonEl.textContent;
            buttonEl.disabled = true;
            buttonEl.textContent = '⏳ Processing...';

            // Clear any previous error messages
            const statusEl = document.getElementById('status-' + meterType);
            statusEl.style.display = 'none';

            addLogEntry(meterType, '📸 Capturing snapshot with current camera settings...');
            showStatus(meterType, '📸 Capturing image with current mode...', 'info');

            try {
                // First, capture a snapshot with current camera settings
                const snapResponse = await fetch(`/api/snapshot/${meterType}`, {
                    method: 'POST'
                });

                if (!snapResponse.ok) {
                    throw new Error(`Snapshot failed: HTTP ${snapResponse.status}`);
                }

                const snapData = await snapResponse.json();

                if (snapData.status !== 'success') {
                    throw new Error(snapData.message || 'Failed to capture snapshot');
                }

                addLogEntry(meterType, '✓ Snapshot captured, analyzing with Claude Vision API...', 'success');
                showStatus(meterType, '🤖 Analyzing image with Claude Vision API... (15-30 seconds)', 'info');

                // Now trigger the reading analysis
                const response = await fetch(`/api/trigger/${meterType}`, {
                    method: 'POST'
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();

                if (data.status === 'triggered') {
                    addLogEntry(meterType, '✓ Analysis in progress, refreshing page with results...', 'success');
                    showStatus(meterType, '✓ Analysis complete! Refreshing page...', 'success');

                    // Auto-refresh after 30 seconds to show results
                    setTimeout(() => {
                        location.reload();
                    }, 30000);
                } else if (data.status === 'in_progress') {
                    addLogEntry(meterType, '⏳ Reading already in progress, waiting...');
                    showStatus(meterType, '⏳ Reading already in progress...', 'info');
                    buttonEl.disabled = false;
                    buttonEl.textContent = originalText;
                } else {
                    throw new Error(data.message || 'Failed to trigger reading');
                }
            } catch (error) {
                addLogEntry(meterType, `✗ Error: ${error.message}`, 'error');
                showStatus(meterType, '✗ Error: ' + error.message, 'error');
                buttonEl.disabled = false;
                buttonEl.textContent = originalText;
            }
        }

        async function reanalyzeSnapshot(meterType) {
            if (!confirm('Reanalyze this snapshot? This will use Claude API credits.')) {
                return;
            }

            addLogEntry(meterType, '🔄 Reanalyzing snapshot...');
            showStatus(meterType, '🔄 Reanalyzing snapshot...', 'info');

            try {
                const response = await fetch(`/api/snapshot/reanalyze/${meterType}`, {
                    method: 'POST'
                });

                const data = await response.json();

                if (data.status === 'success') {
                    addLogEntry(meterType, '✓ Snapshot reanalyzed successfully!', 'success');
                    showStatus(meterType, '✓ Reanalysis complete! Refreshing...', 'success');

                    // Refresh page to show new results
                    setTimeout(() => {
                        location.reload();
                    }, 1500);
                } else {
                    throw new Error(data.message || 'Reanalysis failed');
                }
            } catch (error) {
                addLogEntry(meterType, `✗ Reanalysis error: ${error.message}`, 'error');
                showStatus(meterType, '✗ Error: ' + error.message, 'error');
            }
        }

        async function deleteSnapshot(meterType) {
            if (!confirm('Delete this snapshot? This action cannot be undone.')) {
                return;
            }

            addLogEntry(meterType, '🗑️ Deleting snapshot...');
            showStatus(meterType, '🗑️ Deleting snapshot...', 'info');

            try {
                const response = await fetch(`/api/snapshot/delete/${meterType}`, {
                    method: 'POST'
                });

                const data = await response.json();

                if (data.status === 'success') {
                    addLogEntry(meterType, '✓ Snapshot deleted successfully!', 'success');
                    showStatus(meterType, '✓ Deleted! Refreshing...', 'success');

                    // Refresh page to show updated state
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                } else {
                    throw new Error(data.message || 'Delete failed');
                }
            } catch (error) {
                addLogEntry(meterType, `✗ Delete error: ${error.message}`, 'error');
                showStatus(meterType, '✗ Error: ' + error.message, 'error');
            }
        }

        // Initial timestamp
        updateTimestamp();
    </script>
</body>
</html>
"""

    with open(templates_dir / "index.html", "w") as f:
        f.write(index_html)

    # Create config_edit.html template
    config_edit_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Configuration Editor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 20px;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }

        .header h1 {
            font-size: 2em;
            margin-bottom: 8px;
        }

        .header p {
            opacity: 0.9;
            font-size: 1em;
        }

        .nav-links {
            margin-bottom: 20px;
        }

        .nav-links a {
            display: inline-block;
            background: #334155;
            color: #e2e8f0;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            margin-right: 10px;
            transition: background 0.2s;
        }

        .nav-links a:hover {
            background: #475569;
        }

        .flash-messages {
            margin-bottom: 20px;
        }

        .flash {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 4px solid;
            animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        .flash.success {
            background: #064e3b;
            color: #6ee7b7;
            border-left-color: #10b981;
        }

        .flash.error {
            background: #7f1d1d;
            color: #fecaca;
            border-left-color: #ef4444;
        }

        .config-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }

        @media (max-width: 1200px) {
            .config-grid {
                grid-template-columns: 1fr;
            }
        }

        .config-section {
            background: #1e293b;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #334155;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        }

        .section-header {
            background: #334155;
            padding: 20px;
            border-bottom: 1px solid #475569;
        }

        .section-header h2 {
            font-size: 1.5em;
            margin-bottom: 5px;
        }

        .section-header p {
            color: #94a3b8;
            font-size: 0.95em;
        }

        .section-body {
            padding: 20px;
        }

        label {
            display: block;
            margin-bottom: 10px;
            font-weight: 600;
            color: #cbd5e1;
        }

        textarea {
            width: 100%;
            min-height: 500px;
            background: #0f172a;
            color: #e2e8f0;
            border: 2px solid #334155;
            border-radius: 8px;
            padding: 15px;
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.6;
            resize: vertical;
            transition: border-color 0.2s;
        }

        textarea:focus {
            outline: none;
            border-color: #3b82f6;
        }

        .button-group {
            display: flex;
            gap: 15px;
            margin-top: 20px;
        }

        button {
            flex: 1;
            background: #3b82f6;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.2s;
        }

        button:hover {
            background: #2563eb;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }

        button:active {
            transform: translateY(0);
        }

        button.secondary {
            background: #6b7280;
        }

        button.secondary:hover {
            background: #4b5563;
            box-shadow: 0 4px 12px rgba(107, 114, 128, 0.4);
        }

        .help-text {
            background: #1e3a8a;
            color: #93c5fd;
            padding: 15px 20px;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
            margin-top: 20px;
            font-size: 0.9em;
            line-height: 1.6;
        }

        .help-text strong {
            color: #dbeafe;
        }

        .help-text code {
            background: #0f172a;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
        }

        .warning-box {
            background: #7f1d1d;
            color: #fecaca;
            padding: 15px 20px;
            border-radius: 8px;
            border-left: 4px solid #ef4444;
            margin-bottom: 20px;
        }

        .warning-box strong {
            color: #fee2e2;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚙️ Configuration Editor</h1>
        <p>Edit meter hardware settings and utility pricing rates</p>
    </div>

    <div class="nav-links">
        <a href="/">← Back to Dashboard</a>
        <a href="/settings">View Live Meters</a>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            <div class="flash-messages">
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            </div>
        {% endif %}
    {% endwith %}

    <div class="warning-box">
        <strong>⚠️ Warning:</strong> Changes to configuration files will reload the system. Make sure your YAML and JSON syntax is correct before saving.
    </div>

    <div class="config-grid">
        <!-- Meter Configuration -->
        <div class="config-section">
            <div class="section-header">
                <h2>📹 Meter Configuration</h2>
                <p>Camera IPs, reading intervals, and meter hardware setup</p>
            </div>
            <div class="section-body">
                <form method="POST" action="/config/save/meters">
                    <label for="meters_config">meters.yaml</label>
                    <textarea id="meters_config" name="meters_config" spellcheck="false">{{ meters_config }}</textarea>

                    <div class="button-group">
                        <button type="submit">💾 Save Meter Config</button>
                        <button type="button" class="secondary" onclick="location.reload()">🔄 Reset</button>
                    </div>

                    <div class="help-text">
                        <strong>Format:</strong> YAML<br>
                        <strong>Example:</strong><br>
                        <code>meters:</code><br>
                        <code>  - name: "water_main"</code><br>
                        <code>    type: "water"</code><br>
                        <code>    camera_ip: "10.10.10.207"</code><br>
                        <code>    reading_interval: 600</code>
                    </div>
                </form>
            </div>
        </div>

        <!-- Pricing Configuration -->
        <div class="config-section">
            <div class="section-header">
                <h2>💰 Pricing Configuration</h2>
                <p>Utility rates, household info, and cost calculations</p>
            </div>
            <div class="section-body">
                <form method="POST" action="/config/save/pricing">
                    <label for="pricing_config">pricing.json</label>
                    <textarea id="pricing_config" name="pricing_config" spellcheck="false">{{ pricing_config }}</textarea>

                    <div class="button-group">
                        <button type="submit">💾 Save Pricing Config</button>
                        <button type="button" class="secondary" onclick="location.reload()">🔄 Reset</button>
                    </div>

                    <div class="help-text">
                        <strong>Format:</strong> JSON<br>
                        <strong>Contains:</strong><br>
                        • Household address and timezone<br>
                        • Utility account numbers<br>
                        • Water, electricity, and gas rates<br>
                        • Bill upload history
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
        // Auto-grow textareas
        document.querySelectorAll('textarea').forEach(textarea => {
            textarea.style.height = textarea.scrollHeight + 'px';
        });

        // Confirm before leaving with unsaved changes
        let formChanged = false;
        document.querySelectorAll('textarea').forEach(textarea => {
            textarea.addEventListener('input', () => {
                formChanged = true;
            });
        });

        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', () => {
                formChanged = false;
            });
        });

        window.addEventListener('beforeunload', (e) => {
            if (formChanged) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            }
        });
    </script>
</body>
</html>
"""

    with open(templates_dir / "config_edit.html", "w") as f:
        f.write(config_edit_html)


def main():
    parser = argparse.ArgumentParser(description='Meter Preview Web UI')
    parser.add_argument('--port', type=int, default=2500, help='Port to run server on')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--config', default='config/meters.yaml', help='Config file path')
    args = parser.parse_args()

    # Load configuration
    global CONFIG, CONFIG_PATH
    CONFIG_PATH = args.config
    try:
        CONFIG = load_config(args.config)
        print(f"✅ Loaded config with {len(CONFIG.get('meters', []))} meter(s)")
    except Exception as e:
        print(f"⚠️  Warning: Could not load config: {e}")
        print("   Preview UI will run with limited functionality")

    # Register database API routes
    try:
        from src.api_routes import register_api_routes
        register_api_routes(app)
        print("✅ Database API routes registered")
    except Exception as e:
        print(f"⚠️  Warning: Could not register database routes: {e}")

    # Create templates
    create_templates()

    print("\n" + "=" * 60)
    print("🌐 Meter Preview Dashboard")
    print("=" * 60)
    print(f"\n📍 Server running at: http://{args.host}:{args.port}")
    print(f"📁 Watching logs in: {LOG_DIR.absolute()}")
    print(f"📊 Database API available at: http://{args.host}:{args.port}/api/db/*")
    print("\n💡 Tips:")
    print("   - Use 'Auto-refresh' to see updates in real-time")
    print("   - Run 'python multi_meter_monitor.py --run-once' to capture new readings")
    print("   - Access /api/db/meters to see meters in PostgreSQL")
    print("   - Press Ctrl+C to stop the server")
    print("\n" + "=" * 60 + "\n")

    # Run Flask app
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
