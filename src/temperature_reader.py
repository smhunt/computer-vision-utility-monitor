#!/usr/bin/env python3
"""
Temperature Reader Module
Captures temperature data from camera or alternative sources
"""

import os
import subprocess
from typing import Optional, Dict
from datetime import datetime

def get_camera_temperature_ssh(camera_ip: str, user: str, password: str) -> Optional[float]:
    """
    Get temperature from camera via SSH

    Args:
        camera_ip: Camera IP address
        user: SSH username
        password: SSH password

    Returns:
        Temperature in Celsius, or None if unavailable
    """
    # Try different temperature sources in order of preference
    commands = [
        # Linux thermal zone (most reliable)
        "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null",
        # Thingino built-in command
        "temperature 2>/dev/null",
        # Hardware monitoring
        "cat /sys/class/hwmon/hwmon0/temp1_input 2>/dev/null",
        # Ingenic-specific
        "cat /proc/jz/temperature 2>/dev/null",
    ]

    for cmd in commands:
        try:
            # Try with sshpass if available
            ssh_cmd = f'sshpass -p "{password}" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=3 {user}@{camera_ip} "{cmd}"'
            result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=5)

            if result.returncode == 127:  # sshpass not found
                # Try without sshpass (requires SSH key setup)
                ssh_cmd = f'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=3 {user}@{camera_ip} "{cmd}"'
                result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=5)

            if result.returncode == 0 and result.stdout.strip():
                # Parse temperature value
                temp_str = result.stdout.strip()

                # If value is in millidegrees (like 45000 for 45°C)
                if temp_str.isdigit() and int(temp_str) > 200:
                    return float(temp_str) / 1000.0

                # Try to parse as float directly
                try:
                    temp = float(temp_str)
                    # Sanity check: temperature should be between -40 and 85°C for electronics
                    if -40 <= temp <= 85:
                        return temp
                except ValueError:
                    continue

        except Exception:
            continue

    return None


def get_temperature(camera_ip: str = None, user: str = None, password: str = None,
                   source: str = "camera") -> Dict:
    """
    Get temperature from configured source

    Args:
        camera_ip: Camera IP address (default: from env WATER_CAM_IP)
        user: SSH username (default: from env WATER_CAM_USER)
        password: SSH password (default: from env WATER_CAM_PASS)
        source: Temperature source - "camera", "weather_api", "external", etc.

    Returns:
        Dictionary with temperature data:
        {
            'temperature_c': float or None,
            'temperature_f': float or None,
            'source': str,
            'timestamp': str,
            'available': bool
        }
    """
    # Get credentials from environment if not provided
    camera_ip = camera_ip or os.getenv("WATER_CAM_IP")
    user = user or os.getenv("WATER_CAM_USER")
    password = password or os.getenv("WATER_CAM_PASS")

    result = {
        'temperature_c': None,
        'temperature_f': None,
        'source': source,
        'timestamp': datetime.now().isoformat(),
        'available': False
    }

    if source == "camera":
        if not all([camera_ip, user, password]):
            result['error'] = "Camera credentials not configured"
            return result

        temp_c = get_camera_temperature_ssh(camera_ip, user, password)

        if temp_c is not None:
            result['temperature_c'] = round(temp_c, 1)
            result['temperature_f'] = round((temp_c * 9/5) + 32, 1)
            result['available'] = True
        else:
            result['error'] = "SSH not available or no temperature sensor found"

    elif source == "weather_api":
        # TODO: Implement weather API integration
        result['error'] = "Weather API integration not implemented"

    elif source == "external":
        # TODO: Implement external sensor integration (e.g., MQTT, Home Assistant)
        result['error'] = "External sensor integration not implemented"

    else:
        result['error'] = f"Unknown temperature source: {source}"

    return result


def format_temperature(temp_data: Dict) -> str:
    """
    Format temperature data for display

    Args:
        temp_data: Temperature data dictionary from get_temperature()

    Returns:
        Formatted temperature string
    """
    if not temp_data.get('available'):
        return f"N/A ({temp_data.get('error', 'unavailable')})"

    temp_c = temp_data.get('temperature_c')
    temp_f = temp_data.get('temperature_f')
    source = temp_data.get('source', 'unknown')

    return f"{temp_c}°C / {temp_f}°F (from {source})"


# Command-line interface for testing
if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing temperature capture...")
    print()

    # Test camera temperature
    print("[1] Camera temperature (SSH):")
    temp_data = get_temperature(source="camera")
    print(f"    {format_temperature(temp_data)}")
    print(f"    Raw data: {temp_data}")
    print()

    # Instructions
    if not temp_data.get('available'):
        print("⚠️  Temperature not available")
        print()
        print("To enable camera temperature:")
        print("  1. Configure SSH access on the camera")
        print("  2. Ensure WATER_CAM_* variables are set in .env")
        print("  3. Install sshpass: brew install sshpass (macOS) or apt install sshpass (Linux)")
        print()
        print("Alternative sources:")
        print("  - Integrate with weather API")
        print("  - Use external temperature sensor")
        print("  - Connect to Home Assistant")
