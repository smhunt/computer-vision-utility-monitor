#!/usr/bin/env python3
"""
Compare different meter reading methods:
- Claude Vision API (via llm_reader.py)
- Local OpenCV approach
- Local EasyOCR approach
- Hybrid local approach
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List
import argparse

# Import both readers
try:
    from src.llm_reader import read_meter_with_claude
    API_AVAILABLE = True
except Exception as e:
    API_AVAILABLE = False
    print(f"Warning: Claude API reader not available: {e}")

try:
    from src.local_vision_reader import read_meter_locally
    LOCAL_AVAILABLE = True
except Exception as e:
    LOCAL_AVAILABLE = False
    print(f"Warning: Local vision reader not available: {e}")


def compare_methods(image_path: str, methods: List[str] = None) -> Dict:
    """
    Compare different meter reading methods on the same image.

    Args:
        image_path: Path to meter image
        methods: List of methods to test. Options:
                 - 'api': Claude Vision API
                 - 'opencv': OpenCV-based local
                 - 'easyocr': EasyOCR-based local
                 - 'hybrid': Hybrid local approach
                 If None, tests all available methods.

    Returns:
        Dict with results from each method
    """
    if methods is None:
        methods = ['api', 'opencv', 'easyocr', 'hybrid']

    results = {}

    # Test Claude Vision API
    if 'api' in methods and API_AVAILABLE:
        print("\n🔍 Testing Claude Vision API...")
        try:
            start_time = time.time()
            api_result = read_meter_with_claude(image_path)
            elapsed = time.time() - start_time

            results['api'] = {
                **api_result,
                'elapsed_time': round(elapsed, 2),
                'status': 'success'
            }
            print(f"✅ API Reading: {api_result.get('total_reading', 'N/A')} m³ "
                  f"(took {elapsed:.2f}s)")
        except Exception as e:
            results['api'] = {'status': 'error', 'error': str(e)}
            print(f"❌ API Error: {e}")

    # Test local methods
    local_methods = {'opencv', 'easyocr', 'hybrid'}
    for method in methods:
        if method in local_methods and LOCAL_AVAILABLE:
            print(f"\n🔍 Testing Local {method.upper()}...")
            try:
                start_time = time.time()
                local_result = read_meter_locally(image_path, method=method, debug=False)
                elapsed = time.time() - start_time

                results[method] = {
                    **local_result,
                    'elapsed_time': round(elapsed, 2),
                    'status': 'success'
                }
                print(f"✅ {method.upper()} Reading: "
                      f"{local_result.get('total_reading', 'N/A')} m³ "
                      f"(took {elapsed:.2f}s)")
            except Exception as e:
                results[method] = {'status': 'error', 'error': str(e)}
                print(f"❌ {method.upper()} Error: {e}")

    return results


def print_comparison_table(results: Dict):
    """Print a formatted comparison table"""
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)

    headers = ["Method", "Reading", "Confidence", "Time (s)", "Status"]
    col_widths = [15, 15, 12, 10, 15]

    # Print headers
    header_row = "  ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(header_row)
    print("-"*80)

    # Print results
    for method, result in results.items():
        if result.get('status') == 'success':
            reading = f"{result.get('total_reading', 'N/A')} m³"
            confidence = f"{result.get('confidence', 0):.2f}"
            elapsed = f"{result.get('elapsed_time', 0):.2f}"
            status = "✅ Success"
        else:
            reading = "N/A"
            confidence = "N/A"
            elapsed = "N/A"
            status = f"❌ {result.get('error', 'Failed')[:15]}"

        row = [
            method.upper().ljust(col_widths[0]),
            reading.ljust(col_widths[1]),
            confidence.ljust(col_widths[2]),
            elapsed.ljust(col_widths[3]),
            status.ljust(col_widths[4])
        ]
        print("  ".join(row))

    print("="*80)

    # Print detailed notes
    print("\nDETAILED NOTES:")
    for method, result in results.items():
        if result.get('status') == 'success' and 'notes' in result:
            print(f"\n{method.upper()}: {result['notes']}")


def main():
    parser = argparse.ArgumentParser(
        description="Compare different meter reading methods"
    )
    parser.add_argument(
        "image_path",
        help="Path to meter image"
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=['api', 'opencv', 'easyocr', 'hybrid', 'all'],
        default=['all'],
        help="Methods to test (default: all available)"
    )
    parser.add_argument(
        "--output",
        help="Save results to JSON file"
    )

    args = parser.parse_args()

    # Check if image exists
    if not Path(args.image_path).exists():
        print(f"Error: Image not found: {args.image_path}")
        sys.exit(1)

    # Determine methods to test
    if 'all' in args.methods:
        methods = ['api', 'opencv', 'easyocr', 'hybrid']
    else:
        methods = args.methods

    # Run comparison
    print(f"\n📸 Testing image: {args.image_path}")
    print(f"🧪 Methods: {', '.join(methods)}")

    results = compare_methods(args.image_path, methods)

    # Print comparison table
    print_comparison_table(results)

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {output_path}")

    # Return exit code based on success
    if any(r.get('status') == 'success' for r in results.values()):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
