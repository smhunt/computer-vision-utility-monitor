#!/usr/bin/env python3
"""
Meter Preview Web UI

Provides a web interface to preview camera captures and meter readings
in real-time. Useful for positioning cameras and debugging.

Usage:
    python meter_preview_ui.py [--port 5000]
"""

import os
import sys
import json
import argparse
import subprocess
import threading
import requests
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, send_file, Response

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.config_loader import load_config

app = Flask(__name__)

# Global config
CONFIG = None
LOG_DIR = Path("logs")

# Track running readings (to prevent duplicate triggers)
READING_IN_PROGRESS = set()


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
    """Main dashboard showing all meters"""
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

    return render_template('index.html', meters=meters, format_timestamp=format_timestamp)


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
        result = subprocess.run(
            [sys.executable, 'camera_presets.py', preset_name],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0:
            return jsonify({
                'status': 'success',
                'message': f'Applied {preset_name} preset',
                'output': result.stdout
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to apply preset',
                'error': result.stderr
            }), 500

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


@app.route('/api/snapshot/<meter_type>', methods=['POST'])
def api_capture_snapshot(meter_type):
    """Capture a fresh snapshot from camera"""
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

        camera_ip = meter_config.get('camera_ip', '').replace('${WATER_CAM_IP:', '').replace('}', '').split(':')[-1] or '10.10.10.207'
        camera_user = meter_config.get('camera_user', '').replace('${WATER_CAM_USER:', '').replace('}', '').split(':')[-1] or 'root'
        camera_pass = meter_config.get('camera_pass', '').replace('${WATER_CAM_PASS:', '').replace('}', '').split(':')[-1] or '***REMOVED***'

        # Capture from MJPEG stream (extract one frame)
        mjpeg_url = f"http://{camera_user}:{camera_pass}@{camera_ip}/mjpeg"

        # Read MJPEG stream and extract first JPEG frame
        response = requests.get(mjpeg_url, stream=True, timeout=10)

        if response.status_code != 200:
            return jsonify({
                'status': 'error',
                'message': f'Camera returned HTTP {response.status_code}'
            }), 500

        # Read stream until we get a complete JPEG frame
        jpeg_data = b''
        found_start = False

        for chunk in response.iter_content(chunk_size=1024):
            jpeg_data += chunk

            # Look for JPEG start marker (FFD8) and end marker (FFD9)
            if not found_start and b'\xff\xd8' in jpeg_data:
                # Found JPEG start, trim everything before it
                start_idx = jpeg_data.find(b'\xff\xd8')
                jpeg_data = jpeg_data[start_idx:]
                found_start = True

            if found_start and b'\xff\xd9' in jpeg_data:
                # Found JPEG end, extract complete frame
                end_idx = jpeg_data.find(b'\xff\xd9') + 2
                jpeg_data = jpeg_data[:end_idx]
                break

            # Safety: don't read more than 500KB
            if len(jpeg_data) > 500000:
                break

        if len(jpeg_data) > 1000 and jpeg_data.startswith(b'\xff\xd8'):
            # Save to snapshot directory
            snapshot_dir = LOG_DIR / f"{meter_type}_snapshots"
            snapshot_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            meter_name = meter_config.get('name', 'unknown')
            snapshot_path = snapshot_dir / f"{meter_name}_{timestamp}.jpg"

            with open(snapshot_path, 'wb') as f:
                f.write(jpeg_data)

            return jsonify({
                'status': 'success',
                'message': 'Snapshot captured',
                'timestamp': timestamp,
                'size': len(jpeg_data)
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to extract JPEG frame from stream'
            }), 500

    except Exception as e:
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
                    </div>

                    <!-- Camera Controls -->
                    <div class="camera-controls">
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

            addLogEntry(meterType, '🔬 Starting meter reading analysis...');
            showStatus(meterType, '📸 Capturing image and analyzing... (15-30 seconds)', 'info');

            try {
                const response = await fetch(`/api/trigger/${meterType}`, {
                    method: 'POST'
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();

                if (data.status === 'triggered') {
                    addLogEntry(meterType, '✓ Reading triggered, processing with Claude Vision API...', 'success');
                    showStatus(meterType, '📸 Reading in progress... Auto-refreshing in 30 seconds.', 'info');

                    // Auto-refresh after 30 seconds
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

        // Initial timestamp
        updateTimestamp();
    </script>
</body>
</html>
"""

    with open(templates_dir / "index.html", "w") as f:
        f.write(index_html)


def main():
    parser = argparse.ArgumentParser(description='Meter Preview Web UI')
    parser.add_argument('--port', type=int, default=5000, help='Port to run server on')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--config', default='config/meters.yaml', help='Config file path')
    args = parser.parse_args()

    # Load configuration
    global CONFIG
    try:
        CONFIG = load_config(args.config)
        print(f"✅ Loaded config with {len(CONFIG.get('meters', []))} meter(s)")
    except Exception as e:
        print(f"⚠️  Warning: Could not load config: {e}")
        print("   Preview UI will run with limited functionality")

    # Create templates
    create_templates()

    print("\n" + "=" * 60)
    print("🌐 Meter Preview Dashboard")
    print("=" * 60)
    print(f"\n📍 Server running at: http://{args.host}:{args.port}")
    print(f"📁 Watching logs in: {LOG_DIR.absolute()}")
    print("\n💡 Tips:")
    print("   - Use 'Auto-refresh' to see updates in real-time")
    print("   - Run 'python multi_meter_monitor.py --run-once' to capture new readings")
    print("   - Press Ctrl+C to stop the server")
    print("\n" + "=" * 60 + "\n")

    # Run Flask app
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
