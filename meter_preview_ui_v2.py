#!/usr/bin/env python3
"""
Meter Preview Web UI v2

Enhanced version with camera controls and reading triggers
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
from flask import Flask, render_template, jsonify, send_file

sys.path.insert(0, str(Path(__file__).parent / "src"))
from utils.config_loader import load_config

app = Flask(__name__)

CONFIG = None
LOG_DIR = Path("logs")
READING_IN_PROGRESS = set()


def get_latest_snapshot(meter_name, meter_type):
    snapshot_dir = LOG_DIR / f"{meter_type}_snapshots"
    if not snapshot_dir.exists():
        return None
    snapshots = sorted(snapshot_dir.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    return snapshots[0] if snapshots else None


def get_latest_reading(meter_type):
    log_file = LOG_DIR / f"{meter_type}_readings.jsonl"
    if not log_file.exists():
        return None
    with open(log_file, 'r') as f:
        lines = f.readlines()
        if lines:
            try:
                return json.loads(lines[-1].strip())
            except:
                return None
    return None


def format_timestamp(iso_timestamp):
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_timestamp


def get_meter_config(meter_type):
    """Get configuration for a specific meter type"""
    if CONFIG:
        for meter_config in CONFIG.get('meters', []):
            if meter_config.get('type') == meter_type:
                return meter_config
    return None


def trigger_reading_async(meter_type):
    """Trigger a reading in the background"""
    try:
        env = os.environ.copy()
        
        # Run using existing config
        result = subprocess.run(
            [sys.executable, 'multi_meter_monitor.py', '--run-once'],
            env=env,
            capture_output=True,
            text=True,
            timeout=90,
            cwd=str(Path(__file__).parent)
        )
        
        print(f"[{meter_type}] Reading completed: exit={result.returncode}")
        
    except Exception as e:
        print(f"[{meter_type}] Error: {e}")
    finally:
        READING_IN_PROGRESS.discard(meter_type)


@app.route('/')
def index():
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
    meter_config = get_meter_config(meter_type)
    if not meter_config:
        return "Meter not found", 404
    
    meter_name = meter_config.get('name', 'unknown')
    latest_snapshot = get_latest_snapshot(meter_name, meter_type)
    
    if not latest_snapshot:
        return "No snapshot available", 404
    
    return send_file(latest_snapshot, mimetype='image/jpeg')


@app.route('/api/trigger/<meter_type>', methods=['POST'])
def api_trigger_reading(meter_type):
    if meter_type in READING_IN_PROGRESS:
        return jsonify({'status': 'in_progress', 'message': 'Reading already in progress'})
    
    READING_IN_PROGRESS.add(meter_type)
    thread = threading.Thread(target=trigger_reading_async, args=(meter_type,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'triggered', 'message': 'Reading started. Refresh in 20 seconds.'})


@app.route('/api/camera/<meter_type>/ir', methods=['POST'])
def api_toggle_ir(meter_type):
    """Toggle IR mode on camera"""
    meter_config = get_meter_config(meter_type)
    if not meter_config:
        return jsonify({'error': 'Meter not found'}), 404
    
    camera_ip = meter_config.get('camera_ip', '').replace('${WATER_CAM_IP:', '').replace('}', '')
    camera_user = meter_config.get('camera_user', 'root').replace('${WATER_CAM_USER:', '').replace('}', '')
    camera_pass = meter_config.get('camera_pass', '').replace('${WATER_CAM_PASS:', '').replace('}', '')
    
    try:
        # Thingino API call to toggle IR
        response = requests.get(
            f'http://{camera_ip}/api/v1/night',
            auth=(camera_user, camera_pass),
            timeout=5
        )
        return jsonify({'status': 'success', 'message': 'IR toggled'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/status/<meter_type>')
def api_status(meter_type):
    return jsonify({'in_progress': meter_type in READING_IN_PROGRESS})


@app.template_filter('timestamp')
def timestamp_filter(iso_timestamp):
    return format_timestamp(iso_timestamp)


def create_templates():
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    
    # Enhanced template with controls
    html = open('templates/index_template.html', 'w')
    html.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meter Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui; background: #0f172a; color: #e2e8f0; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px; margin-bottom: 30px; }
        .header h1 { font-size: 2em; margin-bottom: 10px; }
        .meters-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(600px, 1fr)); gap: 30px; }
        .meter-card { background: #1e293b; border-radius: 12px; overflow: hidden; border: 1px solid #334155; }
        .meter-header { background: #334155; padding: 20px; }
        .meter-name { font-size: 1.5em; margin-bottom: 8px; text-transform: capitalize; }
        .meter-body { padding: 20px; }
        .snapshot-container { background: #0f172a; border-radius: 8px; padding: 10px; margin-bottom: 20px; }
        .snapshot-image { width: 100%; border-radius: 6px; }
        .meter-actions { margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap; }
        .btn { background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 14px; transition: all 0.2s; }
        .btn:hover { background: #2563eb; }
        .btn:disabled { background: #4b5563; cursor: not-allowed; }
        .btn.secondary { background: #6b7280; }
        .btn.secondary:hover { background: #4b5563; }
        .status-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 0.8em; font-weight: 600; }
        .status-success { background: #10b981; }
        .status-error { background: #ef4444; }
        .reading-data { background: #0f172a; border-radius: 8px; padding: 20px; }
        .reading-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #334155; }
        .reading-label { color: #94a3b8; }
        .reading-value { font-weight: 600; }
        .error-message { background: #7f1d1d; color: #fecaca; padding: 15px; border-radius: 6px; border-left: 4px solid #ef4444; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Meter Dashboard</h1>
        <p>Real-time camera controls and readings</p>
    </div>

    <div class="meters-grid">
        {% for meter in meters %}
        <div class="meter-card">
            <div class="meter-header">
                <div class="meter-name">
                    {{ meter.name }}
                    {% if meter.has_reading and not meter.reading.get('error') %}
                        <span class="status-badge status-success">Online</span>
                    {% else %}
                        <span class="status-badge status-error">Error</span>
                    {% endif %}
                </div>
            </div>

            <div class="meter-body">
                <div class="snapshot-container">
                    {% if meter.has_snapshot %}
                        <img src="{{ meter.snapshot_path }}?t={{ meter.reading.timestamp if meter.reading else '' }}"
                             class="snapshot-image" id="snapshot_{{ meter.type }}">
                    {% else %}
                        <div style="text-align: center; padding: 60px; color: #64748b;">📷 No snapshot</div>
                    {% endif %}
                </div>

                {% if meter.reading %}
                    {% if meter.reading.get('error') %}
                        <div class="error-message">
                            <strong>❌ Error:</strong> {{ meter.reading.error }}
                            {% if meter.reading.raw_reading and meter.reading.raw_reading.get('notes') %}
                                <br><br><strong>Notes:</strong> {{ meter.reading.raw_reading.notes }}
                            {% endif %}
                        </div>
                    {% else %}
                        <div class="reading-data">
                            <div class="reading-row">
                                <span class="reading-label">Total Reading</span>
                                <span class="reading-value">{{ "%.3f"|format(meter.reading.total_reading) }} m³</span>
                            </div>
                            <div class="reading-row">
                                <span class="reading-label">Confidence</span>
                                <span class="reading-value">{{ meter.reading.confidence|upper }}</span>
                            </div>
                        </div>
                    {% endif %}
                {% endif %}

                <div class="meter-actions">
                    <button class="btn" onclick="takeReading('{{ meter.type }}')" id="takeBtn_{{ meter.type }}">
                        📸 Take Reading
                    </button>
                    <button class="btn secondary" onclick="toggleIR('{{ meter.type }}')">
                        🔦 Toggle IR
                    </button>
                    <button class="btn secondary" onclick="location.reload()">
                        🔄 Refresh
                    </button>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    <script>
        async function takeReading(meterType) {
            const btn = document.getElementById(`takeBtn_${meterType}`);
            btn.disabled = true;
            btn.textContent = '⏳ Reading...';
            
            try {
                const response = await fetch(`/api/trigger/${meterType}`, { method: 'POST' });
                const data = await response.json();
                
                if (data.status === 'triggered') {
                    btn.textContent = '✓ Started!';
                    setTimeout(() => {
                        btn.textContent = '🔄 Refreshing...';
                        location.reload();
                    }, 20000);
                }
            } catch (e) {
                btn.textContent = '❌ Error';
                btn.disabled = false;
            }
        }

        async function toggleIR(meterType) {
            try {
                const response = await fetch(`/api/camera/${meterType}/ir`, { method: 'POST' });
                const data = await response.json();
                alert(data.message || 'IR toggled');
            } catch (e) {
                alert('Error toggling IR: ' + e.message);
            }
        }
    </script>
</body>
</html>
""")
    html.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5001)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--config', default='config/meters.yaml')
    args = parser.parse_args()

    global CONFIG
    try:
        CONFIG = load_config(args.config)
        print(f"✅ Loaded {len(CONFIG.get('meters', []))} meter(s)")
    except Exception as e:
        print(f"⚠️  Warning: {e}")

    create_templates()
    
    # Move template to correct location
    Path('templates/index.html').write_text(Path('templates/index_template.html').read_text())

    print(f"\n🌐 Dashboard: http://{args.host}:{args.port}\n")
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
