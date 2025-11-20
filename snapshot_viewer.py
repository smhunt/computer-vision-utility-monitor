#!/usr/bin/env python3
"""
Meter Snapshot Viewer Web UI
View archived meter snapshots and readings over time
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, send_file, jsonify, request
from dotenv import load_dotenv
import threading
import time

# Load environment
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from snapshot_manager import SnapshotManager
from influx_logger import MeterInfluxLogger

# Global variable to track capture progress
capture_status = {}

# Initialize InfluxDB logger (will gracefully handle missing credentials)
influx_logger = MeterInfluxLogger()

# Initialize Flask app
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

# Initialize snapshot manager
manager = SnapshotManager(base_dir="logs/meter_snapshots")


@app.route('/')
def index():
    """Main page - meter selection"""
    # List available meters
    meters = []
    if manager.base_dir.exists():
        for meter_dir in manager.base_dir.iterdir():
            if meter_dir.is_dir():
                snapshot_count = len(list(meter_dir.glob("*.jpg")))
                latest = manager.get_latest_snapshot(meter_dir.name)

                meters.append({
                    'name': meter_dir.name,
                    'snapshot_count': snapshot_count,
                    'latest_snapshot': latest.name if latest else None
                })

    return render_template('index.html', meters=meters)


@app.route('/meter/<meter_name>')
def meter_view(meter_name):
    """View snapshots for a specific meter"""
    # Get recent snapshots
    snapshots = manager.get_snapshots(meter_name, limit=50)

    # Build snapshot data
    snapshot_data = []
    for snapshot_path in snapshots:
        metadata = manager.get_metadata(snapshot_path)

        data = {
            'filename': snapshot_path.name,
            'path': f"/image/{meter_name}/{snapshot_path.name}",
            'timestamp': metadata['snapshot']['timestamp'] if metadata else None,
            'reading': metadata['meter_reading']['total_reading'] if metadata else None,
            'digital_reading': metadata['meter_reading'].get('digital_reading') if metadata else None,
            'dial_reading': metadata['meter_reading'].get('dial_reading') if metadata else None,
            'confidence': metadata['meter_reading']['confidence'] if metadata else None,
            'temperature': metadata.get('temperature', {}).get('celsius') if metadata else None
        }
        snapshot_data.append(data)

    return render_template('meter.html',
                         meter_name=meter_name,
                         snapshots=snapshot_data)


@app.route('/image/<meter_name>/<filename>')
def serve_image(meter_name, filename):
    """Serve snapshot image"""
    meter_dir = manager.get_meter_dir(meter_name)
    image_path = meter_dir / filename

    if image_path.exists():
        return send_file(image_path, mimetype='image/jpeg')
    else:
        return "Image not found", 404


@app.route('/api/meter/<meter_name>/history')
def api_meter_history(meter_name):
    """API endpoint for meter reading history"""
    limit = int(request.args.get('limit', 50))
    history = manager.get_reading_history(meter_name, limit=limit)
    return jsonify(history)


@app.route('/api/meter/<meter_name>/latest')
def api_meter_latest(meter_name):
    """API endpoint for latest reading"""
    latest_snapshot = manager.get_latest_snapshot(meter_name)

    if not latest_snapshot:
        return jsonify({'error': 'No snapshots found'}), 404

    metadata = manager.get_metadata(latest_snapshot)

    return jsonify({
        'snapshot': latest_snapshot.name,
        'timestamp': metadata['snapshot']['timestamp'] if metadata else None,
        'reading': metadata['meter_reading'] if metadata else None,
        'temperature': metadata.get('temperature') if metadata else None
    })


def capture_snapshot_background(meter_name, capture_id):
    """Background task to capture and process snapshot"""
    import requests
    from requests.auth import HTTPBasicAuth

    try:
        # Update status
        capture_status[capture_id] = {
            'status': 'capturing',
            'step': 1,
            'total_steps': 4,
            'message': 'Capturing snapshot from camera...'
        }

        # Import capture functions (do this inside try block)
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from snapshot_metadata_worker import process_single_snapshot

        # Get camera credentials from env
        camera_ip = os.getenv("WATER_CAM_IP", "10.10.10.207")
        camera_user = os.getenv("WATER_CAM_USER", "root")
        camera_pass = os.getenv("WATER_CAM_PASS")
        stream_url = f"http://{camera_ip}/mjpeg"

        # Capture frame
        response = requests.get(
            stream_url,
            auth=HTTPBasicAuth(camera_user, camera_pass),
            stream=True,
            timeout=10
        )

        buffer = b''
        for chunk in response.iter_content(chunk_size=1024):
            buffer += chunk
            start = buffer.find(b'\xff\xd8')
            end = buffer.find(b'\xff\xd9')
            if start != -1 and end != -1 and end > start:
                jpeg_data = buffer[start:end+2]
                temp_path = f'/tmp/meter_snapshot_{meter_name}_capture.jpg'
                with open(temp_path, 'wb') as f:
                    f.write(jpeg_data)
                break

        capture_status[capture_id] = {
            'status': 'processing',
            'step': 2,
            'total_steps': 4,
            'message': 'Analyzing meter reading with AI...'
        }

        time.sleep(0.5)  # Small delay for UI feedback

        # Process snapshot
        result = process_single_snapshot(
            temp_path,
            meter_name,
            capture_temperature=False
        )

        if result['success']:
            # Log to InfluxDB
            try:
                meter_data = result.get('meter_reading_data', {})
                if meter_data and influx_logger.write_api:
                    influx_logger.log_reading(
                        meter_name=meter_name,
                        total_reading=meter_data.get('total_reading'),
                        digital_reading=meter_data.get('digital_reading'),
                        dial_reading=meter_data.get('dial_reading'),
                        confidence=meter_data.get('confidence'),
                        temperature_c=result.get('temperature', {}).get('celsius')
                    )
                    print(f"✓ Logged reading to InfluxDB: {meter_data.get('total_reading')} m³")
            except Exception as e:
                print(f"Warning: Failed to log to InfluxDB: {e}")

            capture_status[capture_id] = {
                'status': 'complete',
                'step': 4,
                'total_steps': 4,
                'message': 'Capture complete!',
                'reading': result.get('meter_reading'),
                'confidence': result.get('confidence'),
                'archived_path': result.get('archived_path')
            }
        else:
            capture_status[capture_id] = {
                'status': 'error',
                'message': result.get('error', 'Unknown error')
            }

    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Capture error for {capture_id}: {error_msg}")
        print(traceback.format_exc())
        capture_status[capture_id] = {
            'status': 'error',
            'message': error_msg
        }


@app.route('/api/meter/<meter_name>/capture', methods=['POST'])
def api_capture_snapshot(meter_name):
    """API endpoint to trigger snapshot capture"""
    # Generate capture ID
    capture_id = f"{meter_name}_{int(time.time())}"

    # Start capture in background thread
    thread = threading.Thread(
        target=capture_snapshot_background,
        args=(meter_name, capture_id)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'capture_id': capture_id,
        'status': 'started'
    })


@app.route('/api/capture/<capture_id>/status')
def api_capture_status(capture_id):
    """API endpoint to check capture status"""
    if capture_id not in capture_status:
        return jsonify({'error': 'Capture not found'}), 404

    return jsonify(capture_status[capture_id])


@app.route('/api/camera/<meter_name>/stream')
def api_camera_stream(meter_name):
    """Proxy MJPEG stream from camera"""
    import requests
    from requests.auth import HTTPBasicAuth

    # Get camera credentials from env
    camera_ip = os.getenv("WATER_CAM_IP", "10.10.10.207")
    camera_user = os.getenv("WATER_CAM_USER", "root")
    camera_pass = os.getenv("WATER_CAM_PASS")
    stream_url = f"http://{camera_ip}/mjpeg"

    def generate():
        """Stream frames from camera"""
        try:
            response = requests.get(
                stream_url,
                auth=HTTPBasicAuth(camera_user, camera_pass),
                stream=True,
                timeout=10
            )

            for chunk in response.iter_content(chunk_size=1024):
                yield chunk

        except Exception as e:
            print(f"Stream error: {e}")

    return app.response_class(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


def create_templates():
    """Create HTML templates directory and files"""
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(exist_ok=True)

    # Create index.html
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meter Snapshot Viewer</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }
        .meter-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .meter-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-decoration: none;
            color: inherit;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .meter-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .meter-name {
            font-size: 24px;
            font-weight: 600;
            color: #007bff;
            margin-bottom: 10px;
        }
        .meter-stats {
            color: #666;
            font-size: 14px;
        }
        .meter-stats span {
            display: block;
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <h1>📊 Meter Snapshot Viewer</h1>

    {% if meters %}
        <div class="meter-grid">
            {% for meter in meters %}
            <a href="/meter/{{ meter.name }}" class="meter-card">
                <div class="meter-name">{{ meter.name }}</div>
                <div class="meter-stats">
                    <span>📸 {{ meter.snapshot_count }} snapshots</span>
                    {% if meter.latest_snapshot %}
                    <span>🕐 Latest: {{ meter.latest_snapshot }}</span>
                    {% endif %}
                </div>
            </a>
            {% endfor %}
        </div>
    {% else %}
        <p style="color: #666; font-size: 18px; text-align: center; margin-top: 50px;">
            No meters found. Capture some snapshots first using <code>/takemetersnapshot</code>
        </p>
    {% endif %}
</body>
</html>"""

    with open(templates_dir / "index.html", "w") as f:
        f.write(index_html)

    # Create meter.html
    meter_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ meter_name }} - Snapshot History</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            color: #007bff;
            text-decoration: none;
        }
        .back-link:hover {
            text-decoration: underline;
        }
        .capture-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        .capture-btn:hover {
            background: #0056b3;
        }
        .capture-btn:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        .progress-container {
            display: none;
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .progress-container.active {
            display: block;
        }
        .progress-header {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin-bottom: 15px;
        }
        .progress-bar-container {
            background: #e9ecef;
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
            margin-bottom: 15px;
        }
        .progress-bar {
            background: linear-gradient(90deg, #007bff, #0056b3);
            height: 100%;
            width: 0%;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 14px;
        }
        .progress-message {
            color: #666;
            font-size: 14px;
        }
        .progress-result {
            margin-top: 15px;
            padding: 15px;
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 6px;
            color: #155724;
        }
        .progress-result.error {
            background: #f8d7da;
            border-color: #f5c6cb;
            color: #721c24;
        }
        .progress-spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #007bff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 8px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .snapshot-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .snapshot-card {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .snapshot-image {
            width: 100%;
            height: 200px;
            object-fit: cover;
            cursor: pointer;
        }
        .snapshot-info {
            padding: 15px;
        }
        .snapshot-time {
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }
        .reading {
            font-size: 24px;
            font-weight: 600;
            color: #007bff;
            margin: 5px 0;
        }
        .confidence {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        .confidence-high { background: #d4edda; color: #155724; }
        .confidence-medium { background: #fff3cd; color: #856404; }
        .confidence-low { background: #f8d7da; color: #721c24; }
        .temperature {
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal img {
            max-width: 90%;
            max-height: 90%;
        }
        .live-preview-container {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .live-preview-header {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .live-indicator {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            color: #dc3545;
        }
        .live-dot {
            width: 8px;
            height: 8px;
            background: #dc3545;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        .stream-wrapper {
            position: relative;
            max-width: 500px;
            margin: 0 auto;
            border-radius: 8px;
            overflow: hidden;
            background: #000;
        }
        .stream-image {
            width: 100%;
            height: auto;
            display: block;
        }
        .stream-error {
            padding: 40px;
            text-align: center;
            color: #666;
            background: #f8f9fa;
        }
    </style>
</head>
<body>
    <a href="/" class="back-link">← Back to meters</a>
    <h1>📊 {{ meter_name }} - Snapshot History</h1>

    <div class="live-preview-container">
        <div class="live-preview-header">
            <span>📹 Live Camera Preview</span>
            <span class="live-indicator">
                <span class="live-dot"></span>
                LIVE
            </span>
        </div>
        <div class="stream-wrapper">
            <img src="/api/camera/{{ meter_name }}/stream"
                 alt="Live camera feed"
                 class="stream-image"
                 onerror="this.parentElement.innerHTML='<div class=\\'stream-error\\'>⚠️ Stream unavailable</div>'">
        </div>
        <div style="text-align: center; margin-top: 15px;">
            <button class="capture-btn" id="captureBtn" onclick="captureSnapshot()">
                📸 Capture Now
            </button>
        </div>
    </div>

    <div class="progress-container" id="progressContainer">
        <div class="progress-header">
            <span class="progress-spinner"></span>
            <span id="progressTitle">Capturing Snapshot...</span>
        </div>
        <div class="progress-bar-container">
            <div class="progress-bar" id="progressBar">0%</div>
        </div>
        <div class="progress-message" id="progressMessage">Initializing...</div>
        <div class="progress-result" id="progressResult" style="display: none;"></div>
    </div>

    {% if snapshots %}
        <div class="snapshot-grid">
            {% for snapshot in snapshots %}
            <div class="snapshot-card">
                <img src="{{ snapshot.path }}"
                     alt="{{ snapshot.filename }}"
                     class="snapshot-image"
                     onclick="openModal('{{ snapshot.path }}')">
                <div class="snapshot-info">
                    <div class="snapshot-time">{{ snapshot.timestamp }}</div>
                    {% if snapshot.reading %}
                        <div class="reading">{{ snapshot.reading }} m³</div>
                        <span class="confidence confidence-{{ snapshot.confidence }}">
                            {{ snapshot.confidence }}
                        </span>
                    {% endif %}
                    {% if snapshot.temperature %}
                        <div class="temperature">🌡️ {{ snapshot.temperature }}°C</div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <p style="color: #666; font-size: 18px; text-align: center; margin-top: 50px;">
            No snapshots found for this meter.
        </p>
    {% endif %}

    <div class="modal" id="imageModal" onclick="closeModal()">
        <img id="modalImage" src="">
    </div>

    <script>
        function openModal(imagePath) {
            document.getElementById('modalImage').src = imagePath;
            document.getElementById('imageModal').style.display = 'flex';
        }

        function closeModal() {
            document.getElementById('imageModal').style.display = 'none';
        }

        let checkInterval = null;

        async function captureSnapshot() {
            const btn = document.getElementById('captureBtn');
            const progressContainer = document.getElementById('progressContainer');
            const progressBar = document.getElementById('progressBar');
            const progressMessage = document.getElementById('progressMessage');
            const progressResult = document.getElementById('progressResult');

            // Disable button
            btn.disabled = true;

            // Show progress
            progressContainer.classList.add('active');
            progressResult.style.display = 'none';
            progressBar.style.width = '0%';
            progressBar.textContent = '0%';
            progressMessage.textContent = 'Starting capture...';

            try {
                // Start capture
                const response = await fetch('/api/meter/{{ meter_name }}/capture', {
                    method: 'POST'
                });

                if (!response.ok) {
                    throw new Error('Failed to start capture');
                }

                const data = await response.json();
                const captureId = data.capture_id;

                // Poll for status
                checkInterval = setInterval(async () => {
                    try {
                        const statusResponse = await fetch(`/api/capture/${captureId}/status`);
                        const status = await statusResponse.json();

                        if (status.status === 'capturing' || status.status === 'processing') {
                            const progress = (status.step / status.total_steps) * 100;
                            progressBar.style.width = progress + '%';
                            progressBar.textContent = Math.round(progress) + '%';
                            progressMessage.textContent = status.message;
                        } else if (status.status === 'complete') {
                            clearInterval(checkInterval);
                            progressBar.style.width = '100%';
                            progressBar.textContent = '100%';
                            progressMessage.textContent = status.message;

                            // Show success result
                            progressResult.className = 'progress-result';
                            progressResult.innerHTML = `
                                ✅ <strong>Success!</strong><br>
                                Reading: <strong>${status.reading} m³</strong><br>
                                Confidence: <strong>${status.confidence}</strong>
                            `;
                            progressResult.style.display = 'block';

                            // Re-enable button and reload page after 2 seconds
                            setTimeout(() => {
                                location.reload();
                            }, 2000);
                        } else if (status.status === 'error') {
                            clearInterval(checkInterval);
                            progressBar.style.width = '100%';
                            progressBar.textContent = 'Error';
                            progressMessage.textContent = 'Capture failed';

                            // Show error result
                            progressResult.className = 'progress-result error';
                            progressResult.innerHTML = `❌ <strong>Error:</strong> ${status.message}`;
                            progressResult.style.display = 'block';

                            // Re-enable button
                            btn.disabled = false;
                        }
                    } catch (e) {
                        console.error('Status check error:', e);
                    }
                }, 500);  // Check every 500ms

            } catch (error) {
                btn.disabled = false;
                progressResult.className = 'progress-result error';
                progressResult.innerHTML = `❌ <strong>Error:</strong> ${error.message}`;
                progressResult.style.display = 'block';
            }
        }
    </script>
</body>
</html>"""

    with open(templates_dir / "meter.html", "w") as f:
        f.write(meter_html)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Meter Snapshot Viewer")
    parser.add_argument('--port', '-p', type=int, default=5001,
                       help="Port to run server on (default: 5001)")
    parser.add_argument('--host', type=str, default='127.0.0.1',
                       help="Host to bind to (default: 127.0.0.1)")

    args = parser.parse_args()

    # Create templates
    create_templates()

    print(f"🚀 Starting Meter Snapshot Viewer on http://{args.host}:{args.port}")
    print(f"   Press Ctrl+C to stop\n")

    app.run(host=args.host, port=args.port, debug=True)
