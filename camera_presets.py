#!/usr/bin/env python3
"""
Camera Preset Modes

Pre-configured camera settings optimized for different conditions.
Use these as quick-apply presets in the dashboard.
"""

import os
import requests
from typing import Dict

CAMERA_IP = os.getenv("WATER_CAM_IP", "10.10.10.207")
CAMERA_USER = os.getenv("WATER_CAM_USER", "root")
CAMERA_PASS = os.getenv("WATER_CAM_PASS", "***REMOVED***")
CAMERA_BASE_URL = f"http://{CAMERA_USER}:{CAMERA_PASS}@{CAMERA_IP}"

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


def apply_preset(preset_name: str) -> bool:
    """
    Apply a camera preset

    Args:
        preset_name: Name of preset to apply (from PRESETS dict)

    Returns:
        True if successful
    """
    if preset_name not in PRESETS:
        print(f"❌ Unknown preset: {preset_name}")
        print(f"Available presets: {', '.join(PRESETS.keys())}")
        return False

    preset = PRESETS[preset_name]
    print(f"\n{preset['name']}")
    print(f"{preset['description']}")
    print(f"\nApplying settings...")

    for setting, value in preset['settings'].items():
        try:
            # Try Thingino CGI
            url = f"{CAMERA_BASE_URL}/cgi-bin/configManager.cgi?action=setConfig&{setting}={value}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                print(f"  ✓ {setting} = {value}")
            else:
                print(f"  ⚠️  {setting} = {value} (may not be supported)")

        except Exception as e:
            print(f"  ❌ {setting}: {e}")

    print(f"\n✅ Preset '{preset_name}' applied!")
    return True


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
    apply_preset(preset_name)


if __name__ == "__main__":
    main()
