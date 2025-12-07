#!/usr/bin/env python3
"""
Camera Pre-Inspection Tool

Quickly tests different camera modes to determine which provides
the best meter reading quality. Much faster than full optimization.
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
CAMERA_PASS = os.getenv("WATER_CAM_PASS", "")
CAMERA_BASE_URL = f"http://{CAMERA_USER}:{CAMERA_PASS}@{CAMERA_IP}"

# Quick test modes (3 modes instead of 6)
TEST_MODES = [
    {
        "name": "Day Mode (IR OFF)",
        "description": "Natural light only - no IR LEDs",
        "settings": {
            "day_night_enabled": "false",
            "day_night_ir850": "false",
            "day_night_ircut": "true",   # IR filter ON (blocks IR)
            "day_night_color": "true"     # Color mode
        }
    },
    {
        "name": "Night Mode (IR ON)",
        "description": "IR LEDs enabled for low light",
        "settings": {
            "day_night_enabled": "false",
            "day_night_ir850": "true",    # IR LEDs ON
            "day_night_ircut": "false",   # IR filter OFF (allows IR)
            "day_night_color": "false"    # B&W mode
        }
    },
    {
        "name": "Auto Mode",
        "description": "Let camera decide based on light levels",
        "settings": {
            "day_night_enabled": "true",
            "day_night_ir850": "true",
            "day_night_ircut": "true",
            "day_night_color": "true"
        }
    }
]


def apply_camera_mode(mode_settings):
    """Apply camera settings via Thingino API"""
    try:
        url = f"{CAMERA_BASE_URL}/x/config-daynight.cgi"
        response = requests.post(url, data=mode_settings, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"  ⚠️ Error applying settings: {e}")
        return False


def capture_snapshot():
    """Capture snapshot from camera"""
    try:
        snapshot_url = f"{CAMERA_BASE_URL}/x/image.cgi"
        response = requests.get(snapshot_url, timeout=10)

        if response.status_code == 200:
            return response.content

    except Exception as e:
        print(f"  ❌ Error capturing snapshot: {e}")

    return None


def save_snapshot(image_data, mode_name):
    """Save snapshot to logs"""
    snapshot_dir = Path("logs/preinspection")
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = mode_name.replace(" ", "_").replace("(", "").replace(")", "")
    snapshot_path = snapshot_dir / f"{safe_name}_{timestamp}.jpg"

    with open(snapshot_path, 'wb') as f:
        f.write(image_data)

    return snapshot_path


def evaluate_mode(mode, mode_num, total_modes):
    """Test a camera mode and evaluate reading quality"""
    print(f"\n{'='*70}")
    print(f"🔍 Mode {mode_num}/{total_modes}: {mode['name']}")
    print(f"{'='*70}")
    print(f"📝 {mode['description']}")

    # Apply settings
    print(f"\n⚙️  Applying camera settings...")
    if not apply_camera_mode(mode['settings']):
        return {
            'mode': mode['name'],
            'success': False,
            'score': 0,
            'error': 'Failed to apply camera settings'
        }

    # Wait for camera to adjust
    print(f"⏳ Waiting 5 seconds for camera to adjust...")
    time.sleep(5)

    # Capture snapshot
    print(f"📸 Capturing snapshot...")
    image_data = capture_snapshot()

    if not image_data:
        return {
            'mode': mode['name'],
            'success': False,
            'score': 0,
            'error': 'Failed to capture snapshot'
        }

    # Save snapshot
    snapshot_path = save_snapshot(image_data, mode['name'])
    print(f"✅ Saved: {snapshot_path}")

    # Analyze with Claude
    print(f"🤖 Analyzing with Claude Vision API...")
    try:
        result = read_meter_with_claude(str(snapshot_path))

        if 'error' in result:
            # Failed reading
            notes = result.get('raw_reading', {}).get('notes', result.get('error', 'Unknown error'))
            return {
                'mode': mode['name'],
                'success': False,
                'confidence': 'error',
                'score': 0,
                'notes': notes,
                'snapshot': str(snapshot_path)
            }

        # Successful reading
        confidence = result.get('confidence', 'low')
        score_map = {'high': 100, 'medium': 60, 'low': 20}
        score = score_map.get(confidence, 0)

        # Bonus for numeric reading
        if result.get('total_reading') is not None:
            score += 20

        print(f"\n📊 Results:")
        print(f"   Confidence: {confidence.upper()}")
        print(f"   Reading: {result.get('total_reading', 'N/A')} m³")
        print(f"   Score: {score}/120")

        return {
            'mode': mode['name'],
            'success': True,
            'confidence': confidence,
            'total_reading': result.get('total_reading'),
            'score': score,
            'notes': result.get('notes', ''),
            'snapshot': str(snapshot_path),
            'api_usage': result.get('api_usage', {})
        }

    except Exception as e:
        return {
            'mode': mode['name'],
            'success': False,
            'score': 0,
            'error': str(e),
            'snapshot': str(snapshot_path)
        }


def run_preinspection():
    """Run quick pre-inspection test"""
    print("\n" + "="*70)
    print("🔍 CAMERA PRE-INSPECTION")
    print("="*70)
    print(f"\n📹 Camera: {CAMERA_IP}")
    print(f"🧪 Testing {len(TEST_MODES)} modes")
    print(f"⏱️  Estimated time: ~{len(TEST_MODES) * 1} minute(s)")
    print("\n" + "="*70)

    results = []

    for idx, mode in enumerate(TEST_MODES, 1):
        result = evaluate_mode(mode, idx, len(TEST_MODES))
        results.append(result)

        # Brief pause between modes
        if idx < len(TEST_MODES):
            time.sleep(2)

    # Print summary
    print("\n" + "="*70)
    print("📊 PRE-INSPECTION RESULTS")
    print("="*70)

    # Sort by score
    results.sort(key=lambda x: x.get('score', 0), reverse=True)

    print(f"\n🏆 RECOMMENDED MODE:\n")
    best = results[0]
    print(f"   {best['mode']}")
    print(f"   Score: {best['score']}/120")
    print(f"   Confidence: {best.get('confidence', 'N/A').upper()}")
    if best.get('total_reading'):
        print(f"   Reading: {best['total_reading']} m³")
    print(f"\n   Why: {best.get('notes', 'N/A')[:200]}...")

    # Show all results
    print(f"\n\n📋 All Modes (ranked by score):\n")
    for i, result in enumerate(results, 1):
        status = "✓" if result['success'] else "✗"
        print(f"{i}. {status} {result['mode']}: {result['score']}/120 ({result.get('confidence', 'error')})")

    # Save results
    import json
    results_file = Path("logs/preinspection_results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'camera': CAMERA_IP,
            'results': results
        }, f, indent=2)

    print(f"\n\n💾 Results saved to: {results_file}")
    print("="*70)

    # Apply best mode
    print(f"\n⚙️  Applying recommended mode: {best['mode']}...")
    best_mode_settings = next(m['settings'] for m in TEST_MODES if m['name'] == best['mode'])
    apply_camera_mode(best_mode_settings)
    print(f"✅ Camera configured!\n")

    return results


def main():
    """Main entry point"""
    # Check API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Run pre-inspection
    results = run_preinspection()

    # Exit with success if best mode scored > 40
    best_score = results[0].get('score', 0)
    sys.exit(0 if best_score > 40 else 1)


if __name__ == "__main__":
    main()
