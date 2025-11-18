#!/usr/bin/env python3
"""
Camera Settings Optimizer

Automatically experiments with different camera settings to find
the best configuration for reading the water meter.
"""

import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from llm_reader import read_meter_with_claude

# Camera configuration
CAMERA_IP = os.getenv("WATER_CAM_IP", "10.10.10.207")
CAMERA_USER = os.getenv("WATER_CAM_USER", "root")
CAMERA_PASS = os.getenv("WATER_CAM_PASS", "thinginoSh4114!")
CAMERA_BASE_URL = f"http://{CAMERA_USER}:{CAMERA_PASS}@{CAMERA_IP}"

# Test configurations to try
EXPERIMENTS = [
    # Experiment 1: IR + High Contrast
    {
        "name": "IR_LED_ON + High_Contrast",
        "settings": {
            "irled": "on",
            "nightmode": "on",
            "contrast": "200",
            "sharpness": "150"
        }
    },
    # Experiment 2: IR + Medium settings
    {
        "name": "IR_LED_ON + Medium",
        "settings": {
            "irled": "on",
            "nightmode": "on",
            "contrast": "128",
            "sharpness": "128"
        }
    },
    # Experiment 3: Day mode + Enhanced
    {
        "name": "Day_Mode + Enhanced",
        "settings": {
            "irled": "off",
            "nightmode": "off",
            "contrast": "180",
            "sharpness": "180",
            "brightness": "150"
        }
    },
    # Experiment 4: IR + Low settings (reduce noise)
    {
        "name": "IR_LED_ON + Low_Noise",
        "settings": {
            "irled": "on",
            "nightmode": "on",
            "contrast": "100",
            "sharpness": "100"
        }
    },
    # Experiment 5: Auto night + Balanced
    {
        "name": "Auto_Night + Balanced",
        "settings": {
            "irled": "auto",
            "nightmode": "auto",
            "contrast": "128",
            "sharpness": "128"
        }
    },
    # Experiment 6: Max sharpness
    {
        "name": "Max_Sharpness",
        "settings": {
            "irled": "on",
            "nightmode": "on",
            "contrast": "150",
            "sharpness": "255",
            "brightness": "128"
        }
    },
]


def apply_camera_settings(settings_dict):
    """Apply settings to Thingino camera"""
    print(f"  Applying settings: {settings_dict}")

    for setting, value in settings_dict.items():
        try:
            # Try Thingino CGI interface
            url = f"{CAMERA_BASE_URL}/cgi-bin/configManager.cgi?action=setConfig&{setting}={value}"
            response = requests.get(url, timeout=5)

            # Also try alternative endpoint
            if response.status_code != 200:
                url2 = f"{CAMERA_BASE_URL}/api.cgi?cmd=set{setting}&value={value}"
                requests.get(url2, timeout=5)

        except Exception as e:
            print(f"  Warning: Could not set {setting}: {e}")

    # Wait for camera to adjust
    time.sleep(3)


def capture_snapshot(output_path):
    """Capture snapshot from camera"""
    try:
        snapshot_url = f"{CAMERA_BASE_URL}/cgi-bin/snapshot.cgi"

        # Try MJPEG stream
        if not os.path.exists(output_path):
            snapshot_url = f"{CAMERA_BASE_URL}/mjpeg"

        response = requests.get(snapshot_url, timeout=10)

        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"  Error capturing snapshot: {e}")

    return False


def evaluate_reading(snapshot_path):
    """Evaluate meter reading quality"""
    try:
        result = read_meter_with_claude(snapshot_path)

        if 'error' in result:
            return {
                'success': False,
                'confidence': 'low',
                'notes': result.get('raw_reading', {}).get('notes', result.get('error', 'Unknown error')),
                'score': 0
            }

        # Calculate score based on confidence
        confidence = result.get('confidence', 'low')
        score_map = {'high': 100, 'medium': 60, 'low': 20}
        score = score_map.get(confidence, 0)

        # Bonus points if we got numeric readings
        if result.get('total_reading') is not None:
            score += 20

        return {
            'success': True,
            'confidence': confidence,
            'total_reading': result.get('total_reading'),
            'digital_reading': result.get('digital_reading'),
            'dial_reading': result.get('dial_reading'),
            'notes': result.get('notes', ''),
            'score': score,
            'api_usage': result.get('api_usage', {})
        }

    except Exception as e:
        return {
            'success': False,
            'confidence': 'error',
            'notes': str(e),
            'score': 0
        }


def run_experiments():
    """Run all camera setting experiments"""
    print("\n" + "=" * 70)
    print("🔬 CAMERA SETTINGS OPTIMIZATION EXPERIMENT")
    print("=" * 70)
    print(f"\nCamera: {CAMERA_IP}")
    print(f"Total experiments: {len(EXPERIMENTS)}")
    print(f"Expected duration: ~{len(EXPERIMENTS) * 2} minutes")
    print("\n" + "=" * 70 + "\n")

    results = []
    snapshot_dir = Path("logs/optimization_tests")
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    for idx, experiment in enumerate(EXPERIMENTS, 1):
        print(f"\n📊 Experiment {idx}/{len(EXPERIMENTS)}: {experiment['name']}")
        print("-" * 70)

        # Apply settings
        apply_camera_settings(experiment['settings'])

        # Capture snapshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = snapshot_dir / f"exp{idx:02d}_{experiment['name']}_{timestamp}.jpg"

        print(f"  📸 Capturing snapshot...")
        if not capture_snapshot(str(snapshot_path)):
            print(f"  ❌ Failed to capture snapshot")
            results.append({
                'experiment': experiment['name'],
                'settings': experiment['settings'],
                'success': False,
                'score': 0,
                'error': 'Snapshot capture failed'
            })
            continue

        print(f"  ✓ Snapshot saved: {snapshot_path.name}")

        # Evaluate with Claude
        print(f"  🤖 Analyzing with Claude Vision API...")
        evaluation = evaluate_reading(str(snapshot_path))

        # Store result
        result = {
            'experiment': experiment['name'],
            'settings': experiment['settings'],
            **evaluation,
            'snapshot': str(snapshot_path)
        }
        results.append(result)

        # Print result
        print(f"  📈 Score: {evaluation['score']}/120")
        print(f"  📊 Confidence: {evaluation['confidence'].upper()}")
        if evaluation.get('total_reading'):
            print(f"  💧 Reading: {evaluation['total_reading']} m³")
        print(f"  📝 Notes: {evaluation['notes'][:100]}...")

        # Wait between experiments
        if idx < len(EXPERIMENTS):
            print(f"\n  ⏸️  Waiting 5 seconds before next experiment...")
            time.sleep(5)

    # Print summary
    print("\n" + "=" * 70)
    print("📊 OPTIMIZATION RESULTS SUMMARY")
    print("=" * 70)

    # Sort by score
    results.sort(key=lambda x: x.get('score', 0), reverse=True)

    print(f"\n🏆 Best Configuration:\n")
    best = results[0]
    print(f"  Name: {best['experiment']}")
    print(f"  Score: {best['score']}/120")
    print(f"  Confidence: {best['confidence'].upper()}")
    if best.get('total_reading'):
        print(f"  Reading: {best['total_reading']} m³")
    print(f"\n  Settings:")
    for key, value in best['settings'].items():
        print(f"    {key}: {value}")
    print(f"\n  Notes: {best['notes']}")

    # Show top 3
    print(f"\n\n📋 Top 3 Configurations:\n")
    for i, result in enumerate(results[:3], 1):
        print(f"{i}. {result['experiment']}: {result['score']}/120 ({result['confidence']})")

    # Save detailed results
    import json
    results_file = Path("logs/optimization_results.json")
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'camera': CAMERA_IP,
            'results': results
        }, f, indent=2)

    print(f"\n\n💾 Detailed results saved to: {results_file}")
    print("\n" + "=" * 70)

    # Apply best settings
    print(f"\n🔧 Applying best configuration...")
    apply_camera_settings(best['settings'])
    print(f"✅ Camera configured with optimal settings!")

    return results


def main():
    """Main entry point"""
    # Check API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Run experiments
    results = run_experiments()

    print(f"\n🎉 Optimization complete! Try taking a new reading with the dashboard.\n")


if __name__ == "__main__":
    main()
