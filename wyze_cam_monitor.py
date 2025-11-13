#!/usr/bin/env python3
"""
Water Meter Monitoring with Wyze Cam V2 (Dafang Hacks)

Quick start:
1. Flash Wyze Cam V2 with Dafang Hacks firmware
2. Configure WiFi and get camera IP
3. Set environment variables or edit config below
4. Run: python examples/wyze_cam_monitor.py

Requirements:
- Wyze Cam V2 with Dafang Hacks firmware
- ANTHROPIC_API_KEY environment variable
"""

import os
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from llm_reader import read_meter_with_claude
except ImportError:
    print("Error: Cannot import llm_reader")
    print("Make sure you're running from the project root")
    sys.exit(1)

# ============================================================================
# CONFIGURATION - Edit these values or set as environment variables
# ============================================================================

CAMERA_IP = os.getenv("WYZE_CAM_IP", "192.168.1.100")
CAMERA_USER = os.getenv("WYZE_CAM_USER", "root")
CAMERA_PASS = os.getenv("WYZE_CAM_PASS", "ismart12")  # Change this!
INTERVAL = int(os.getenv("READING_INTERVAL", "600"))  # 10 minutes

# Snapshot URL (Dafang Hacks)
SNAPSHOT_URL = f"http://{CAMERA_USER}:{CAMERA_PASS}@{CAMERA_IP}/cgi-bin/currentpic.cgi"

# Alternative: RTSP stream (requires ffmpeg)
# RTSP_URL = f"rtsp://{CAMERA_USER}:{CAMERA_PASS}@{CAMERA_IP}:554/live/ch00_0"
# Use: capture_from_rtsp(RTSP_URL, temp_file)

TEMP_IMAGE = "/tmp/meter_snapshot.jpg"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def test_camera_connection():
    """Test if camera is accessible"""
    print(f"Testing connection to {CAMERA_IP}...", end=" ")
    try:
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
    """Capture snapshot from Wyze Cam"""
    try:
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
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a") as f:
        f.write(json.dumps(reading) + "\n")


# ============================================================================
# MAIN MONITORING LOOP
# ============================================================================

def main():
    print("=" * 70)
    print("Water Meter Monitor - Wyze Cam V2 with Dafang Hacks")
    print("=" * 70)
    print()
    
    # Display configuration
    print("Configuration:")
    print(f"  Camera IP: {CAMERA_IP}")
    print(f"  Interval: {INTERVAL} seconds ({INTERVAL/60:.1f} minutes)")
    print(f"  Snapshot URL: {SNAPSHOT_URL.replace(CAMERA_PASS, '***')}")
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
        print("  3. Username/password are correct")
        print("  4. Dafang Hacks firmware is installed")
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
