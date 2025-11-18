"""
Base Meter Class - Abstract base for all meter types

This module provides an abstract base class that defines the interface
for all meter implementations (water, electric, gas, etc.).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import os
import sys
import json
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_reader import read_meter_with_claude
from influxdb_writer import write_reading_to_influxdb


class BaseMeter(ABC):
    """
    Abstract base class for utility meter monitoring

    All meter implementations (water, electric, gas) should inherit from this
    and implement the abstract methods for meter-specific behavior.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize base meter with configuration

        Args:
            config: Dictionary containing meter configuration
                Required keys:
                    - meter_type: Type of meter (water, electric, gas)
                    - camera_ip: IP address of camera
                    - camera_user: Camera username
                    - camera_pass: Camera password
                Optional keys:
                    - reading_interval: Seconds between readings (default: 600)
                    - stream_url: MJPEG stream URL (if available)
                    - snapshot_url: Static snapshot URL (fallback)
                    - log_dir: Directory for logs (default: logs/)
                    - mqtt_enabled: Enable MQTT publishing (default: False)
        """
        self.config = config
        self.meter_type = config.get("meter_type")
        self.camera_ip = config.get("camera_ip")
        self.camera_user = config.get("camera_user")
        self.camera_pass = config.get("camera_pass")
        self.reading_interval = config.get("reading_interval", 600)
        self.stream_url = config.get("stream_url")

        # Determine snapshot mode
        if self.stream_url:
            self.snapshot_mode = "mjpeg"
            self.snapshot_url = self.stream_url
        else:
            self.snapshot_mode = "static"
            self.snapshot_url = config.get("snapshot_url") or \
                f"http://{self.camera_user}:{self.camera_pass}@{self.camera_ip}/cgi-bin/currentpic.cgi"

        # Logging configuration
        self.log_dir = Path(config.get("log_dir", "logs"))
        self.log_file = self.log_dir / f"{self.meter_type}_readings.jsonl"
        self.snapshot_dir = self.log_dir / f"{self.meter_type}_snapshots"

        # Create directories
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        # Temp image path
        self.temp_image = f"/tmp/{self.meter_type}_snapshot.jpg"

        # Statistics
        self.readings = []
        self.consecutive_errors = 0

    @abstractmethod
    def get_claude_prompt(self) -> str:
        """
        Get the Claude API prompt for this meter type

        Returns:
            Prompt string customized for this meter type
        """
        pass

    @abstractmethod
    def parse_reading(self, claude_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the Claude API response into standardized reading format

        Args:
            claude_response: Raw response from Claude API

        Returns:
            Standardized reading dictionary with meter-specific fields
        """
        pass

    @abstractmethod
    def validate_reading(self, reading: Dict[str, Any]) -> bool:
        """
        Validate a meter reading for plausibility

        Args:
            reading: Parsed meter reading

        Returns:
            True if reading is valid, False otherwise
        """
        pass

    def get_meter_type(self) -> str:
        """Get the meter type"""
        return self.meter_type

    def get_reading_interval(self) -> int:
        """Get the reading interval in seconds"""
        return self.reading_interval

    def capture_snapshot(self) -> bool:
        """
        Capture snapshot from camera

        Returns:
            True if successful, False otherwise
        """
        # This will be delegated to the camera_capture module
        from core.camera_capture import CameraCapture

        capture = CameraCapture(self.config)
        return capture.capture_snapshot(self.temp_image)

    def test_connection(self) -> bool:
        """
        Test camera connection

        Returns:
            True if camera is accessible, False otherwise
        """
        from core.camera_capture import CameraCapture

        capture = CameraCapture(self.config)
        return capture.test_connection()

    def read_meter(self) -> Dict[str, Any]:
        """
        Capture image and read meter using Claude API

        Returns:
            Dictionary containing reading data or error
        """
        # Capture snapshot
        if not self.capture_snapshot():
            return {
                "error": "Failed to capture snapshot",
                "meter_type": self.meter_type,
                "timestamp": datetime.now().isoformat()
            }

        # Get meter-specific prompt
        prompt = self.get_claude_prompt()

        # Read meter with Claude
        result = read_meter_with_claude(self.temp_image, custom_prompt=prompt)

        # Add meter type to result
        if "error" not in result:
            result["meter_type"] = self.meter_type

            # Parse and validate reading
            parsed = self.parse_reading(result)

            if not self.validate_reading(parsed):
                return {
                    "error": "Invalid reading - failed validation",
                    "meter_type": self.meter_type,
                    "timestamp": datetime.now().isoformat(),
                    "raw_reading": parsed
                }

            return parsed
        else:
            result["meter_type"] = self.meter_type
            return result

    def log_reading(self, reading: Dict[str, Any]) -> None:
        """
        Log reading to JSON lines file and save snapshot

        Args:
            reading: Reading dictionary to log
        """
        # Log to JSONL file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(reading) + "\n")

        # Save snapshot image with timestamp
        if os.path.exists(self.temp_image):
            timestamp = reading.get('timestamp', datetime.now().isoformat()).replace(':', '-')

            # Create descriptive filename
            if "error" not in reading:
                reading_val = reading.get('total_reading', 'unknown')
                image_filename = self.snapshot_dir / f"{timestamp}_{reading_val}.jpg"
            else:
                image_filename = self.snapshot_dir / f"{timestamp}_error.jpg"

            try:
                shutil.copy(self.temp_image, image_filename)
            except Exception as e:
                print(f"  Warning: Could not save snapshot: {e}")

    def store_reading(self, reading: Dict[str, Any]) -> bool:
        """
        Store reading in InfluxDB

        Args:
            reading: Reading dictionary to store

        Returns:
            True if successful, False otherwise
        """
        return write_reading_to_influxdb(reading)

    def publish_mqtt(self, reading: Dict[str, Any]) -> bool:
        """
        Publish reading to MQTT (optional)

        Args:
            reading: Reading dictionary to publish

        Returns:
            True if successful, False otherwise
        """
        if not self.config.get("mqtt_enabled", False):
            return False

        try:
            import paho.mqtt.client as mqtt

            mqtt_broker = os.getenv("MQTT_BROKER", "localhost")
            mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
            mqtt_topic = os.getenv("MQTT_TOPIC", f"home/{self.meter_type}/meter")

            client = mqtt.Client()
            client.connect(mqtt_broker, mqtt_port, 60)

            payload = json.dumps({
                "meter_type": self.meter_type,
                "value": reading.get("total_reading"),
                "timestamp": reading.get("timestamp"),
                "confidence": reading.get("confidence", "unknown")
            })

            client.publish(mqtt_topic, payload, qos=1, retain=True)
            client.disconnect()

            return True
        except ImportError:
            return False
        except Exception as e:
            print(f"  MQTT publish error: {e}")
            return False

    def process_reading(self) -> Dict[str, Any]:
        """
        Complete reading workflow: capture, read, log, store

        Returns:
            Reading dictionary
        """
        # Read meter
        reading = self.read_meter()

        # Log reading
        self.log_reading(reading)

        # Store in InfluxDB
        if "error" not in reading:
            self.store_reading(reading)
            self.readings.append(reading)
            self.consecutive_errors = 0
        else:
            self.consecutive_errors += 1

        # Publish to MQTT if configured
        if "error" not in reading and self.config.get("mqtt_enabled", False):
            self.publish_mqtt(reading)

        return reading

    def calculate_statistics(self) -> Optional[Dict[str, Any]]:
        """
        Calculate usage statistics from readings

        Returns:
            Dictionary with statistics or None if insufficient data
        """
        if len(self.readings) < 2:
            return None

        start_time = datetime.fromisoformat(self.readings[0]['timestamp'])
        end_time = datetime.fromisoformat(self.readings[-1]['timestamp'])
        duration_hours = (end_time - start_time).total_seconds() / 3600

        start_reading = self.readings[0]['total_reading']
        end_reading = self.readings[-1]['total_reading']
        total_usage = end_reading - start_reading

        avg_rate = total_usage / duration_hours if duration_hours > 0 else 0

        return {
            "meter_type": self.meter_type,
            "num_readings": len(self.readings),
            "duration_hours": duration_hours,
            "total_usage": total_usage,
            "average_rate": avg_rate,
            "start_reading": start_reading,
            "end_reading": end_reading,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }

    def __str__(self) -> str:
        """String representation of meter"""
        return f"{self.meter_type.capitalize()} Meter @ {self.camera_ip}"
