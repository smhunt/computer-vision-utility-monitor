#!/usr/bin/env python3
"""
Water Meter Monitoring with Wyze Cam V2 (Thingino or Dafang Hacks)

Quick start:
1. Flash Wyze Cam V2 with Thingino or Dafang Hacks firmware
2. Configure WiFi and get camera IP from web interface
3. Set environment variables or edit config below
4. Run: python wyze_cam_monitor.py

Requirements:
- Wyze Cam V2 with Thingino (recommended) or Dafang Hacks firmware
- ANTHROPIC_API_KEY environment variable
- Camera accessible via HTTP snapshot URL

Thingino: Check web interface after setup for snapshot URL
Dafang: Default URL is http://root:ismart12@IP/cgi-bin/currentpic.cgi
"""

import os
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from llm_reader import read_meter_with_claude
    from influxdb_writer import write_reading_to_influxdb
except ImportError as e:
    print(f"Error: Cannot import required module: {e}")
    print("Make sure you're running from the project root")
    sys.exit(1)

# ============================================================================
# CONFIGURATION - Edit these values or set as environment variables
# ============================================================================

CAMERA_IP = os.getenv("WYZE_CAM_IP", "192.168.1.100")
CAMERA_USER = os.getenv("WYZE_CAM_USER", "root")
CAMERA_PASS = os.getenv("WYZE_CAM_PASS", "ismart12")  # For Dafang Hacks; check Thingino web interface
INTERVAL = int(os.getenv("READING_INTERVAL", "600"))  # 10 minutes

# ============================================================================
# Snapshot URL Configuration
# ============================================================================
# Check for Thingino MJPEG stream first (newer firmware)
STREAM_URL = os.getenv("WYZE_CAM_STREAM_URL", None)

if STREAM_URL:
    # Thingino MJPEG stream - we'll extract frames from it
    SNAPSHOT_MODE = "mjpeg"
    SNAPSHOT_URL = STREAM_URL
else:
    # Fall back to Dafang Hacks or static snapshot URL
    SNAPSHOT_MODE = "static"
    SNAPSHOT_URL = f"http://{CAMERA_USER}:{CAMERA_PASS}@{CAMERA_IP}/cgi-bin/currentpic.cgi"

# Alternative: RTSP stream (requires ffmpeg)
# RTSP_URL = f"rtsp://{CAMERA_USER}:{CAMERA_PASS}@{CAMERA_IP}:554/live/ch00_0"
# Use: capture_from_rtsp(RTSP_URL, temp_file)

TEMP_IMAGE = "/tmp/meter_snapshot.jpg"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_mjpeg_frame(stream_url, output_path):
    """Extract a single JPEG frame from an MJPEG stream"""
    try:
        import base64
        import urllib.request

        # Create authorization header if credentials are provided
        req = urllib.request.Request(stream_url)
        if CAMERA_USER and CAMERA_PASS:
            credentials = base64.b64encode(f"{CAMERA_USER}:{CAMERA_PASS}".encode()).decode()
            req.add_header('Authorization', f'Basic {credentials}')

        response = urllib.request.urlopen(req, timeout=10)

        # Read MJPEG stream and extract first JPEG frame
        data = b''
        while len(data) < 600000:  # Read up to 600KB
            chunk = response.read(4096)
            if not chunk:
                break
            data += chunk

        # Find JPEG frame boundaries (FFD8 = start, FFD9 = end)
        start = data.find(b'\xff\xd8')
        end = data.find(b'\xff\xd9', start) + 2

        if start >= 0 and end > start:
            jpeg_data = data[start:end]
            with open(output_path, 'wb') as f:
                f.write(jpeg_data)
            return True
        return False
    except Exception as e:
        print(f"  MJPEG extraction error: {e}")
        return False


def test_camera_connection():
    """Test if camera is accessible"""
    print(f"Testing connection to {CAMERA_IP}...", end=" ")
    try:
        if SNAPSHOT_MODE == "mjpeg":
            # Test MJPEG stream
            success = extract_mjpeg_frame(SNAPSHOT_URL, TEMP_IMAGE)
            if success:
                print("✓ Connected")
            else:
                print("✗ Failed to extract frame")
            return success
        else:
            # Test static snapshot URL
            response = requests.get(SNAPSHOT_URL, timeout=5)
            if response.status_code == 200:
                print("✓ Connected")
                return True
            else:
                print(f"✗ HTTP {response.status_code}")
                return False
    except requests.exceptions.Timeout:
        print("✗ Timeout")
        return False
    except requests.exceptions.ConnectionError:
        print("✗ Connection refused")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def capture_snapshot():
    """Capture snapshot from Wyze Cam (supports MJPEG and static snapshots)"""
    try:
        if SNAPSHOT_MODE == "mjpeg":
            # Extract frame from MJPEG stream
            return extract_mjpeg_frame(SNAPSHOT_URL, TEMP_IMAGE)
        else:
            # Static snapshot URL (Dafang Hacks)
            response = requests.get(SNAPSHOT_URL, timeout=10)
            if response.status_code == 200:
                with open(TEMP_IMAGE, 'wb') as f:
                    f.write(response.content)
                return True
            return False
    except Exception as e:
        print(f"  Capture error: {e}")
        return False


def capture_from_rtsp(rtsp_url, output_path):
    """
    Alternative: Capture from RTSP stream using ffmpeg
    Requires: pip install ffmpeg-python
    """
    import subprocess
    try:
        cmd = [
            'ffmpeg',
            '-i', rtsp_url,
            '-frames:v', '1',
            '-q:v', '2',
            '-y',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=15)
        return result.returncode == 0
    except Exception as e:
        print(f"  RTSP capture error: {e}")
        return False


def publish_to_mqtt(reading):
    """Publish reading to MQTT (optional)"""
    try:
        import paho.mqtt.client as mqtt
        import json
        
        mqtt_broker = os.getenv("MQTT_BROKER", "localhost")
        mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        mqtt_topic = os.getenv("MQTT_TOPIC", "home/water/meter")
        
        client = mqtt.Client()
        client.connect(mqtt_broker, mqtt_port, 60)
        
        payload = json.dumps({
            "value": reading["total_reading"],
            "timestamp": reading["timestamp"],
            "confidence": reading.get("confidence", "unknown")
        })
        
        client.publish(mqtt_topic, payload, qos=1, retain=True)
        client.disconnect()
        
        return True
    except ImportError:
        # MQTT not installed
        return False
    except Exception as e:
        print(f"  MQTT publish error: {e}")
        return False


def log_reading(reading, log_file="logs/readings.jsonl"):
    """Append reading to JSON lines log"""
    import json
    import shutil

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Log to JSONL file
    with open(log_file, "a") as f:
        f.write(json.dumps(reading) + "\n")

    # Also save the snapshot image with timestamp
    if os.path.exists(TEMP_IMAGE):
        timestamp = reading.get('timestamp', datetime.now().isoformat()).replace(':', '-')
        image_dir = "logs/snapshots"
        os.makedirs(image_dir, exist_ok=True)

        # Create a descriptive filename with the reading
        if "error" not in reading:
            reading_val = reading.get('total_reading', 'unknown')
            image_filename = f"{image_dir}/meter_{timestamp}_{reading_val:.3f}.jpg"
        else:
            image_filename = f"{image_dir}/meter_{timestamp}_error.jpg"

        try:
            shutil.copy(TEMP_IMAGE, image_filename)
        except Exception as e:
            print(f"  Warning: Could not save snapshot: {e}")


# ============================================================================
# MAIN MONITORING LOOP
# ============================================================================

def main():
    print("=" * 70)
    print("Water Meter Monitor - Wyze Cam V2")
    print("(Thingino or Dafang Hacks firmware)")
    print("=" * 70)
    print()
    
    # Display configuration
    print("Configuration:")
    print(f"  Camera IP: {CAMERA_IP}")
    print(f"  Snapshot Mode: {SNAPSHOT_MODE.upper()}")
    print(f"  Interval: {INTERVAL} seconds ({INTERVAL/60:.1f} minutes)")
    if CAMERA_PASS:
        print(f"  Stream URL: {SNAPSHOT_URL.replace(CAMERA_PASS, '***')}")
    else:
        print(f"  Stream URL: {SNAPSHOT_URL}")
    print()
    
    # Verify API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print()
        print("Set it with:")
        print("  export ANTHROPIC_API_KEY=sk-ant-...")
        print()
        return
    
    # Test camera connection
    if not test_camera_connection():
        print()
        print("Cannot connect to camera. Please check:")
        print("  1. Camera is powered on and connected to network")
        print("  2. IP address is correct (current: {})".format(CAMERA_IP))
        print("  3. Snapshot URL is correct")
        print("  4. Username/password are correct (if required)")
        print("  5. Thingino or Dafang Hacks firmware is installed")
        print()
        print("For Thingino: Check web interface at http://{} for snapshot URL".format(CAMERA_IP))
        print("For Dafang: Default URL uses root/ismart12")
        print()
        print("To change camera IP, set WYZE_CAM_IP environment variable:")
        print("  export WYZE_CAM_IP=192.168.1.XXX")
        print()
        return
    
    print()
    print("Starting monitoring... (Press Ctrl+C to stop)")
    print()
    
    readings = []
    consecutive_errors = 0
    
    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Capture snapshot
            print(f"[{timestamp}] Capturing snapshot...", end=" ")
            if not capture_snapshot():
                print("✗ Failed")
                consecutive_errors += 1
                
                if consecutive_errors >= 3:
                    print("  ⚠️  Multiple capture failures. Waiting 5 minutes...")
                    time.sleep(300)
                    consecutive_errors = 0
                else:
                    time.sleep(30)
                continue
            
            print("✓", end=" ")
            consecutive_errors = 0
            
            # Read meter with LLM
            print("Reading meter...", end=" ")
            result = read_meter_with_claude(TEMP_IMAGE)
            
            if "error" not in result:
                readings.append(result)
                
                print(f"✓")
                print(f"  Reading: {result['total_reading']:.3f} m³")
                print(f"  Digital: {result['digital_reading']}, Dial: {result['dial_reading']:.3f}")
                print(f"  Confidence: {result['confidence']}")
                
                # Calculate flow rate
                if len(readings) >= 2:
                    prev = readings[-2]
                    time_diff = (datetime.fromisoformat(result['timestamp']) -
                               datetime.fromisoformat(prev['timestamp'])).seconds / 60
                    
                    if time_diff > 0:
                        volume_diff = result['total_reading'] - prev['total_reading']
                        flow_rate = (volume_diff * 1000) / time_diff  # L/min
                        
                        if flow_rate > 0.01:
                            print(f"  Flow Rate: {flow_rate:.2f} L/min")
                            
                            # Alert if high flow
                            if flow_rate > 10:
                                print(f"  ⚠️  HIGH FLOW DETECTED!")
                
                # Log reading
                log_reading(result)

                # Write to InfluxDB for Grafana
                if write_reading_to_influxdb(result):
                    print(f"  📊 Logged to InfluxDB")

                # Publish to MQTT (if configured)
                if publish_to_mqtt(result):
                    print(f"  📤 Published to MQTT")
                
            else:
                print(f"✗")
                print(f"  Error: {result.get('error', 'Unknown error')}")
            
            print()
            
            # Wait for next reading
            time.sleep(INTERVAL)
    
    except KeyboardInterrupt:
        print("\n")
        print("=" * 70)
        print("Monitoring stopped by user")
        print("=" * 70)
        
        if len(readings) >= 2:
            # Calculate session statistics
            start_time = datetime.fromisoformat(readings[0]['timestamp'])
            end_time = datetime.fromisoformat(readings[-1]['timestamp'])
            duration = (end_time - start_time).seconds / 3600
            
            total_usage = (readings[-1]['total_reading'] - 
                          readings[0]['total_reading']) * 1000  # liters
            
            avg_flow = total_usage / duration if duration > 0 else 0
            
            print()
            print("Session Summary:")
            print(f"  Readings: {len(readings)}")
            print(f"  Duration: {duration:.2f} hours")
            print(f"  Total Usage: {total_usage:.1f} liters")
            print(f"  Average Flow: {avg_flow:.1f} L/hour")
            print(f"  Start: {readings[0]['total_reading']:.3f} m³")
            print(f"  End: {readings[-1]['total_reading']:.3f} m³")
            print()
    
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
