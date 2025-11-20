#!/usr/bin/env python3
"""
Camera Capability Discovery Script for Thingino Firmware
Discovers available APIs, sensors, and system information including temperature
"""

import os
import subprocess
import json
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Camera connection details from environment
CAMERA_IP = os.getenv("WATER_CAM_IP", "10.10.10.207")
CAMERA_USER = os.getenv("WATER_CAM_USER", "root")
CAMERA_PASS = os.getenv("WATER_CAM_PASS")

def run_ssh_command(command: str) -> Optional[str]:
    """Execute a command on the camera via SSH"""
    try:
        # Try using ssh with password (requires sshpass)
        cmd = f'sshpass -p "{CAMERA_PASS}" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {CAMERA_USER}@{CAMERA_IP} "{command}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)

        if result.returncode == 127:  # sshpass not found
            # Try without sshpass (assumes SSH key is set up)
            cmd = f'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {CAMERA_USER}@{CAMERA_IP} "{command}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception as e:
        print(f"SSH error: {e}")
        return None

def test_http_endpoint(path: str) -> Optional[str]:
    """Test an HTTP endpoint on the camera"""
    try:
        url = f"http://{CAMERA_IP}{path}"
        response = requests.get(url, auth=HTTPBasicAuth(CAMERA_USER, CAMERA_PASS), timeout=5)
        if response.status_code == 200:
            return response.text
        return None
    except:
        return None

def discover_temperature_sources() -> Dict:
    """Discover all available temperature sources"""
    sources = {}

    # Test 1: Linux thermal zones
    print("  [1] Testing thermal zones...")
    temp = run_ssh_command("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null")
    if temp:
        sources['thermal_zone0'] = {
            'raw_value': temp,
            'celsius': float(temp) / 1000 if temp.isdigit() else None,
            'method': 'sysfs'
        }

    # Test 2: ISP temperature (Ingenic specific)
    print("  [2] Testing ISP temperature...")
    isp_temp = run_ssh_command("cat /proc/jz/isp/isp-fs 2>/dev/null | grep -i temp")
    if isp_temp:
        sources['isp_temperature'] = {
            'raw_value': isp_temp,
            'method': 'proc_jz'
        }

    # Test 3: SoC temperature
    print("  [3] Testing SoC temperature...")
    soc_temp = run_ssh_command("cat /proc/jz/temperature 2>/dev/null")
    if soc_temp:
        sources['soc_temperature'] = {
            'raw_value': soc_temp,
            'method': 'proc_jz'
        }

    # Test 4: Hardware monitoring
    print("  [4] Testing hwmon...")
    hwmon = run_ssh_command("cat /sys/class/hwmon/hwmon0/temp1_input 2>/dev/null")
    if hwmon:
        sources['hwmon'] = {
            'raw_value': hwmon,
            'celsius': float(hwmon) / 1000 if hwmon.isdigit() else None,
            'method': 'hwmon'
        }

    # Test 5: Custom Thingino command
    print("  [5] Testing Thingino commands...")
    thingino_temp = run_ssh_command("temperature 2>/dev/null")
    if thingino_temp:
        sources['thingino_cmd'] = {
            'raw_value': thingino_temp,
            'method': 'thingino_binary'
        }

    return sources

def discover_http_endpoints() -> List[str]:
    """Discover available HTTP/CGI endpoints"""
    print("  Testing HTTP endpoints...")
    available = []

    # Common CGI endpoints to test
    test_endpoints = [
        '/x/json-isp',
        '/x/json-system',
        '/x/json-network',
        '/x/json-sensors',
        '/cgi-bin/status',
        '/api/system',
        '/api/sensors',
        '/status.json',
        '/x/preview.cgi',
    ]

    for endpoint in test_endpoints:
        result = test_http_endpoint(endpoint)
        if result and 'Not Found' not in result and 'Forbidden' not in result:
            available.append(endpoint)
            print(f"    ✓ {endpoint}")

    return available

def discover_cgi_scripts() -> List[str]:
    """List available CGI scripts"""
    print("  Listing CGI scripts...")
    scripts = run_ssh_command("ls /var/www/x/*.cgi 2>/dev/null")
    if scripts:
        return scripts.split('\n')
    return []

def get_system_info() -> Dict:
    """Get basic system information"""
    print("  Getting system info...")
    info = {}

    # Kernel version
    kernel = run_ssh_command("uname -a")
    if kernel:
        info['kernel'] = kernel

    # Thingino version
    version = run_ssh_command("cat /etc/os-release 2>/dev/null")
    if version:
        info['os_release'] = version

    # SoC model
    soc = run_ssh_command("cat /proc/cpuinfo | grep 'system type'")
    if soc:
        info['soc'] = soc

    # Memory
    mem = run_ssh_command("free -m")
    if mem:
        info['memory'] = mem

    return info

def main():
    """Main discovery routine"""
    print("=" * 60)
    print("THINGINO CAMERA CAPABILITY DISCOVERY")
    print(f"Camera: {CAMERA_IP}")
    print("=" * 60)
    print()

    results = {
        'camera_ip': CAMERA_IP,
        'timestamp': datetime.now().isoformat()
    }

    # 1. Discover temperature sources
    print("[1/4] Discovering temperature sources...")
    results['temperature_sources'] = discover_temperature_sources()
    print(f"      Found {len(results['temperature_sources'])} temperature source(s)")
    print()

    # 2. Discover HTTP endpoints
    print("[2/4] Discovering HTTP endpoints...")
    results['http_endpoints'] = discover_http_endpoints()
    print(f"      Found {len(results['http_endpoints'])} endpoint(s)")
    print()

    # 3. Discover CGI scripts
    print("[3/4] Discovering CGI scripts...")
    results['cgi_scripts'] = discover_cgi_scripts()
    print(f"      Found {len(results['cgi_scripts'])} script(s)")
    print()

    # 4. Get system info
    print("[4/4] Getting system information...")
    results['system_info'] = get_system_info()
    print()

    # Save results
    output_file = 'camera_capabilities.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print("=" * 60)
    print("DISCOVERY COMPLETE")
    print("=" * 60)
    print()
    print(f"Results saved to: {output_file}")
    print()

    # Print summary
    if results['temperature_sources']:
        print("Temperature Sources Found:")
        for name, data in results['temperature_sources'].items():
            print(f"  - {name}: {data.get('raw_value', 'N/A')}")
            if 'celsius' in data and data['celsius']:
                print(f"    {data['celsius']:.1f}°C")
    else:
        print("⚠️  No temperature sources found")
        print("    This camera may not have temperature sensors accessible")
        print("    or SSH access may not be configured.")

    print()
    print("Next steps:")
    print("  1. Review camera_capabilities.json for full details")
    print("  2. If SSH failed, you may need to configure SSH access")
    print("  3. Check available HTTP endpoints for alternative data sources")

if __name__ == "__main__":
    main()
