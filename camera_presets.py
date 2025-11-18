#!/usr/bin/env python3
"""
Camera Preset Modes

Pre-configured camera settings optimized for different conditions.
Use these as quick-apply presets in the dashboard.
"""

import os
from typing import Dict, List

import requests

DEFAULT_CAMERA_IP = os.getenv("WATER_CAM_IP", "10.10.10.207")
DEFAULT_CAMERA_USER = os.getenv("WATER_CAM_USER", "root")
DEFAULT_CAMERA_PASS = os.getenv("WATER_CAM_PASS", "***REMOVED***")

# Preset modes
PRESETS = {
    "night_vision": {
        "name": "🌙 Night Vision (IR LED)",
        "description": "Best for dark environments - uses IR LED",
        "settings": {
            "irled": "on",
            "nightmode": "on",
            "contrast": "200",
            "sharpness": "150"
        }
    },

    "day_clear": {
        "name": "☀️ Day Mode (Clear)",
        "description": "For well-lit conditions with natural light",
        "settings": {
            "irled": "off",
            "nightmode": "off",
            "contrast": "180",
            "sharpness": "180",
            "brightness": "150"
        }
    },

    "low_noise": {
        "name": "🔇 Low Noise (IR + Reduced)",
        "description": "Reduce grain in low light - smoother image",
        "settings": {
            "irled": "on",
            "nightmode": "on",
            "contrast": "100",
            "sharpness": "100"
        }
    },

    "high_detail": {
        "name": "🔍 High Detail (Max Sharpness)",
        "description": "Maximum sharpness for reading small digits",
        "settings": {
            "irled": "on",
            "nightmode": "on",
            "contrast": "150",
            "sharpness": "255",
            "brightness": "128"
        }
    },

    "balanced": {
        "name": "⚖️ Balanced (Medium)",
        "description": "Balanced settings for most conditions",
        "settings": {
            "irled": "on",
            "nightmode": "on",
            "contrast": "128",
            "sharpness": "128"
        }
    },

    "auto_adaptive": {
        "name": "🤖 Auto Adaptive",
        "description": "Let camera automatically adjust",
        "settings": {
            "irled": "auto",
            "nightmode": "auto",
            "contrast": "128",
            "sharpness": "128"
        }
    }
}


def apply_preset(
    preset_name: str,
    camera_ip: str = None,
    camera_user: str = None,
    camera_pass: str = None,
    timeout: int = 5
) -> Dict[str, object]:
    """
    Apply a camera preset to a specific camera.

    Args:
        preset_name: Name of preset to apply (from PRESETS dict)
        camera_ip: Override camera IP address (defaults to env)
        camera_user: Override camera username (defaults to env)
        camera_pass: Override camera password (defaults to env)
        timeout: HTTP request timeout in seconds

    Returns:
        Dictionary with success flag, errors list, and metadata
    """
    if preset_name not in PRESETS:
        msg = f"Unknown preset: {preset_name}"
        print(f"❌ {msg}")
        return {"success": False, "errors": [msg], "applied": []}

    preset = PRESETS[preset_name]
    print(f"\n{preset['name']}")
    print(f"{preset['description']}")
    print(f"\nApplying settings...")

    ip = camera_ip or DEFAULT_CAMERA_IP
    user = camera_user or DEFAULT_CAMERA_USER
    password = camera_pass or DEFAULT_CAMERA_PASS
    base_url = f"http://{user}:{password}@{ip}"

    errors: List[str] = []
    applied: List[str] = []

    for setting, value in preset['settings'].items():
        try:
            url = f"{base_url}/cgi-bin/configManager.cgi?action=setConfig&{setting}={value}"
            response = requests.get(url, timeout=timeout)

            if response.status_code == 200:
                print(f"  ✓ {setting} = {value}")
                applied.append(setting)
            else:
                msg = f"{setting}={value} rejected (HTTP {response.status_code})"
                print(f"  ⚠️  {msg}")
                errors.append(msg)

        except Exception as e:
            msg = f"{setting}: {e}"
            print(f"  ❌ {msg}")
            errors.append(msg)

    if errors:
        print(f"\n✗ Preset '{preset_name}' failed on {len(errors)} setting(s)")
    else:
        print(f"\n✅ Preset '{preset_name}' applied!")

    return {
        "success": len(errors) == 0,
        "errors": errors,
        "applied": applied,
        "camera_ip": ip,
        "preset": preset_name
    }


def list_presets():
    """List all available presets"""
    print("\n📋 Available Camera Presets:\n")
    print("=" * 70)

    for idx, (key, preset) in enumerate(PRESETS.items(), 1):
        print(f"\n{idx}. {preset['name']}")
        print(f"   Key: {key}")
        print(f"   {preset['description']}")
        print(f"   Settings: {', '.join(preset['settings'].keys())}")

    print("\n" + "=" * 70)
    print(f"\nUsage: python camera_presets.py <preset_name>")
    print(f"Example: python camera_presets.py night_vision\n")


def main():
    import sys

    if len(sys.argv) < 2:
        list_presets()
        sys.exit(0)

    preset_name = sys.argv[1]
    result = apply_preset(preset_name)
    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
