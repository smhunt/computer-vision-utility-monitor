#!/usr/bin/env python3
"""
Test script for improved dial reading prompt
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from llm_reader import read_meter_with_claude

def test_image(image_path):
    """Test dial reading with an image"""
    print(f"\n{'='*80}")
    print(f"Testing: {Path(image_path).name}")
    print(f"{'='*80}\n")

    result = read_meter_with_claude(image_path)

    if 'error' in result:
        print(f"❌ ERROR: {result['error']}")
        if 'raw_response' in result:
            print(f"\nRaw response:\n{result['raw_response']}")
        return False

    print("✅ READING SUCCESSFUL!\n")
    print(f"{'─'*80}")
    print(f"RESULTS:")
    print(f"{'─'*80}")
    print(f"  White Digits:        {result['digital_reading']} m³")
    print(f"  Black Digit:         {result['black_digit']} → 0.{result['black_digit']} m³")
    print(f"  Dial Angle:          {result.get('dial_angle_degrees', 'N/A')}°")
    print(f"  Dial Reading:        {result['dial_reading']:.4f} m³")
    print(f"  {'─'*80}")
    print(f"  TOTAL READING:       {result['total_reading']:.3f} m³")
    print(f"  {'─'*80}")
    print(f"  Confidence:          {result['confidence'].upper()}")

    if result.get('notes'):
        print(f"\n{'─'*80}")
        print(f"NOTES:")
        print(f"{'─'*80}")
        print(f"{result['notes']}")

    if 'api_usage' in result:
        print(f"\n{'─'*80}")
        print(f"API USAGE:")
        print(f"{'─'*80}")
        print(f"  Input tokens:        {result['api_usage']['input_tokens']}")
        print(f"  Output tokens:       {result['api_usage']['output_tokens']}")

    print(f"\n{'='*80}\n")

    # Save result
    output_file = Path(image_path).parent / f"{Path(image_path).stem}_test_result.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"💾 Result saved to: {output_file}\n")

    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_dial_reading.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]

    if not Path(image_path).exists():
        print(f"❌ Error: Image not found: {image_path}")
        sys.exit(1)

    success = test_image(image_path)
    sys.exit(0 if success else 1)
