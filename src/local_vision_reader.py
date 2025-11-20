#!/usr/bin/env python3
"""
Local Vision Reader - Test alternative vision models
Supports:
  - OpenAI GPT-4o-mini (API, cheap)
  - Google Gemini Flash (API, free tier)
  - Ollama with llama-vision/llava (LOCAL, free)
  - Traditional OpenCV (LOCAL, free)
"""

import os
import sys
import json
import base64
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List


def test_with_openai(image_path: str, prompt_format: str = "simple") -> Dict:
    """Test using OpenAI API (GPT-4o-mini)"""
    try:
        import openai
    except ImportError:
        return {'error': 'Run: pip install openai'}

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return {'error': 'Set OPENAI_API_KEY environment variable'}

    # Load prompts
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from llm_reader import METER_READING_PROMPT_SIMPLE, parse_simple_response

    # Encode image
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    client = openai.OpenAI(api_key=api_key)

    try:
        print(f"🚀 Calling OpenAI GPT-4o-mini...")
        print(f"📝 Using {prompt_format} prompt")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                        },
                        {
                            "type": "text",
                            "text": METER_READING_PROMPT_SIMPLE
                        }
                    ]
                }
            ],
            max_tokens=1024
        )

        response_text = response.choices[0].message.content
        print(f"\n📄 Raw response:\n{response_text}\n")

        # Parse response
        result = parse_simple_response(response_text)

        # Add usage info
        result['api_usage'] = {
            'input_tokens': response.usage.prompt_tokens,
            'output_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens,
            'model': 'gpt-4o-mini'
        }

        return result

    except Exception as e:
        return {'error': f'OpenAI API error: {str(e)}'}


def test_with_gemini(image_path: str, prompt_format: str = "simple") -> Dict:
    """Test using Google Gemini Flash (free tier available)"""
    try:
        import google.generativeai as genai
    except ImportError:
        return {'error': 'Run: pip install google-generativeai'}

    # Load API key from .env if not in environment
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('GOOGLE_API_KEY')

    if not api_key:
        return {'error': 'Set GOOGLE_API_KEY environment variable or add to .env file'}

    # Load prompts
    sys.path.insert(0, os.path.dirname(__file__))
    from llm_reader import METER_READING_PROMPT_SIMPLE, parse_simple_response

    genai.configure(api_key=api_key)
    # Use latest stable flash model
    model = genai.GenerativeModel('gemini-2.5-flash')

    try:
        print(f"🚀 Calling Google Gemini Flash...")
        print(f"📝 Using {prompt_format} prompt")

        # Upload image
        with open(image_path, 'rb') as f:
            image_data = f.read()

        response = model.generate_content([
            METER_READING_PROMPT_SIMPLE,
            {'mime_type': 'image/jpeg', 'data': image_data}
        ])

        response_text = response.text
        print(f"\n📄 Raw response:\n{response_text}\n")

        # Parse response
        result = parse_simple_response(response_text)

        # Add usage info if available
        if hasattr(response, 'usage_metadata'):
            result['api_usage'] = {
                'input_tokens': response.usage_metadata.prompt_token_count,
                'output_tokens': response.usage_metadata.candidates_token_count,
                'total_tokens': response.usage_metadata.total_token_count,
                'model': 'gemini-2.0-flash-exp'
            }

        return result

    except Exception as e:
        return {'error': f'Gemini API error: {str(e)}'}


def test_with_ollama(
    image_path: str,
    model: str = "llama3.2-vision:11b",
    prompt_format: str = "simple"
) -> Dict:
    """
    Test using Ollama with local vision model (TRULY LOCAL, NO API!)

    Requires: ollama installed and running
    Install: https://ollama.ai/download

    Vision models to try:
    - llama3.2-vision:11b (recommended, best quality)
    - llava:7b (smaller, faster)
    - llava:13b (good balance)
    - bakllava (alternative)
    """
    try:
        import ollama
    except ImportError:
        return {'error': 'Run: pip install ollama'}

    # Load prompts
    sys.path.insert(0, os.path.dirname(__file__))
    from llm_reader import METER_READING_PROMPT_SIMPLE, parse_simple_response

    try:
        print(f"🚀 Calling Ollama ({model})...")
        print(f"📝 Using {prompt_format} prompt")
        print(f"🏠 Running LOCALLY (no API, no internet needed)")

        # Read image as base64
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        response = ollama.chat(
            model=model,
            messages=[
                {
                    'role': 'user',
                    'content': METER_READING_PROMPT_SIMPLE,
                    'images': [image_data]
                }
            ]
        )

        response_text = response['message']['content']
        print(f"\n📄 Raw response:\n{response_text}\n")

        # Parse response
        result = parse_simple_response(response_text)

        # Add usage info
        result['api_usage'] = {
            'model': model,
            'local': True,
            'cost': 0.0
        }

        return result

    except Exception as e:
        error_msg = str(e)
        if 'connection refused' in error_msg.lower():
            return {
                'error': 'Ollama not running. Start with: ollama serve'
            }
        elif 'model' in error_msg.lower() and 'not found' in error_msg.lower():
            return {
                'error': f'Model not found. Pull with: ollama pull {model}'
            }
        else:
            return {'error': f'Ollama error: {error_msg}'}


def test_with_opencv(image_path: str) -> Dict:
    """Fallback: Pure OpenCV approach (no ML, basic CV only)"""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return {'error': 'Run: pip install opencv-python'}

    try:
        print(f"🚀 Using OpenCV (basic computer vision)...")
        print(f"🏠 Running LOCALLY (no ML models needed)")

        img = cv2.imread(image_path)
        if img is None:
            return {'error': f'Could not read image: {image_path}'}

        # Very basic approach - detect bright regions (odometer digits)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect red needle for dial reading
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(mask1, mask2)

        # Find needle angle
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        needle_angle = 0.0
        if contours:
            # Get largest red contour (likely needle)
            largest = max(contours, key=cv2.contourArea)
            # Fit line to contour
            [vx, vy, x, y] = cv2.fitLine(largest, cv2.DIST_L2, 0, 0.01, 0.01)
            # Convert numpy types to Python float
            angle = float(np.arctan2(float(vy), float(vx)))
            needle_angle = float((np.degrees(angle) + 90) % 360)

        # Estimate dial value from needle angle
        dial_value = (needle_angle / 360.0) * 0.10

        return {
            'odometer_value': 0.0,  # Can't read without OCR/ML
            'dial_value': float(round(dial_value, 3)),
            'total_reading': float(round(dial_value, 3)),
            'needle_angle_degrees': float(round(needle_angle, 1)),
            'confidence': 0.3,
            'notes': 'OpenCV only - no digit recognition, needle detection only',
            'method': 'opencv',
            'api_usage': {
                'model': 'opencv',
                'local': True,
                'cost': 0.0
            }
        }

    except Exception as e:
        return {'error': f'OpenCV error: {str(e)}'}


def compare_all_methods(image_path: str, ollama_model: str = None) -> Dict[str, Dict]:
    """
    Compare all available vision methods

    Args:
        image_path: Path to meter image
        ollama_model: Ollama model to use (default: auto-detect)
    """
    # Auto-detect available Ollama model if not specified
    if ollama_model is None:
        try:
            import subprocess
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if 'llava:13b' in result.stdout:
                ollama_model = 'llava:13b'
            elif 'llama3.2-vision:11b' in result.stdout:
                ollama_model = 'llama3.2-vision:11b'
            elif 'llava:7b' in result.stdout:
                ollama_model = 'llava:7b'
            else:
                ollama_model = 'llama3.2-vision:11b'  # Default
        except:
            ollama_model = 'llama3.2-vision:11b'

    methods = {
        'claude': lambda: test_with_claude(image_path),
        'openai': lambda: test_with_openai(image_path),
        'gemini': lambda: test_with_gemini(image_path),
        'ollama': lambda: test_with_ollama(image_path, model=ollama_model),
        'opencv': lambda: test_with_opencv(image_path)
    }

    results = {}

    print("\n" + "="*60)
    print("COMPARING ALL VISION METHODS")
    print("="*60 + "\n")

    for name, method_func in methods.items():
        print(f"\n{'='*60}")
        print(f"Testing: {name.upper()}")
        print('='*60)

        start = time.time()
        try:
            result = method_func()
            elapsed = time.time() - start

            if 'error' not in result:
                result['elapsed_time'] = round(elapsed, 2)
                print(f"✅ Success in {elapsed:.2f}s")
                if 'total_reading' in result:
                    print(f"   Reading: {result['total_reading']} m³")
                    print(f"   Confidence: {result.get('confidence', 'N/A')}")
            else:
                result['elapsed_time'] = round(elapsed, 2)
                print(f"❌ {result['error']}")
        except Exception as e:
            result = {
                'error': str(e),
                'elapsed_time': round(time.time() - start, 2)
            }
            print(f"❌ Exception: {e}")

        results[name] = result

    return results


def test_with_claude(image_path: str) -> Dict:
    """Test with Claude (reference implementation)"""
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        from llm_reader import read_meter_with_claude
        print(f"🚀 Calling Claude Sonnet...")
        return read_meter_with_claude(image_path)
    except Exception as e:
        return {'error': f'Claude error: {str(e)}'}


def print_comparison_summary(results: Dict[str, Dict]):
    """Print a nice comparison table"""

    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)

    headers = ["Method", "Reading", "Confidence", "Time", "Cost", "Local"]
    widths = [12, 15, 12, 10, 10, 8]

    # Print header
    header_row = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_row)
    print("-"*80)

    # Print results
    for method, result in results.items():
        if 'error' in result:
            row = [
                method.upper().ljust(widths[0]),
                "ERROR".ljust(widths[1]),
                "N/A".ljust(widths[2]),
                f"{result.get('elapsed_time', 0):.2f}s".ljust(widths[3]),
                "N/A".ljust(widths[4]),
                "N/A".ljust(widths[5])
            ]
        else:
            reading = f"{result.get('total_reading', 'N/A')} m³"
            # Handle confidence as either string or number
            conf_val = result.get('confidence', 0)
            if isinstance(conf_val, str):
                confidence = conf_val
            else:
                confidence = f"{conf_val:.2f}"
            elapsed = f"{result.get('elapsed_time', 0):.2f}s"

            # Estimate cost
            usage = result.get('api_usage', {})
            if usage.get('local'):
                cost = "$0"
            elif 'gpt-4o-mini' in usage.get('model', ''):
                # ~$0.00015 per 1K input tokens, $0.0006 per 1K output
                cost = f"${(usage.get('input_tokens', 0) * 0.15 + usage.get('output_tokens', 0) * 0.6) / 1000000:.4f}"
            elif 'gemini' in usage.get('model', ''):
                cost = "$0*"  # Free tier
            elif 'claude' in usage.get('model', ''):
                # ~$3 per 1M input tokens, $15 per 1M output for Sonnet
                cost = f"${(usage.get('input_tokens', 0) * 3 + usage.get('output_tokens', 0) * 15) / 1000000:.4f}"
            else:
                cost = "N/A"

            local = "✓" if usage.get('local') else "✗"

            row = [
                method.upper().ljust(widths[0]),
                reading.ljust(widths[1]),
                confidence.ljust(widths[2]),
                elapsed.ljust(widths[3]),
                cost.ljust(widths[4]),
                local.ljust(widths[5])
            ]

        print("  ".join(row))

    print("="*80)
    print("* Gemini has free tier (rate limited)")
    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Test alternative vision models for meter reading'
    )
    parser.add_argument('image_path', help='Path to meter image')
    parser.add_argument(
        '--method',
        choices=['claude', 'openai', 'gemini', 'ollama', 'opencv', 'compare'],
        default='compare',
        help='Vision method to use (default: compare all)'
    )
    parser.add_argument(
        '--ollama-model',
        default='llama3.2-vision:11b',
        help='Ollama model to use (default: llama3.2-vision:11b)'
    )
    parser.add_argument(
        '--output',
        help='Save result to JSON file'
    )

    args = parser.parse_args()

    if not Path(args.image_path).exists():
        print(f"❌ Error: Image not found: {args.image_path}")
        sys.exit(1)

    # Run comparison or single method
    if args.method == 'compare':
        results = compare_all_methods(args.image_path)
        print_comparison_summary(results)

        # Save comparison results
        output_path = args.output or '/tmp/vision_comparison.json'
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {output_path}")

    else:
        # Run single method
        method_map = {
            'claude': test_with_claude,
            'openai': test_with_openai,
            'gemini': test_with_gemini,
            'ollama': lambda p: test_with_ollama(p, model=args.ollama_model),
            'opencv': test_with_opencv
        }

        result = method_map[args.method](args.image_path)

        print("\n" + "="*60)
        print(f"RESULT ({args.method.upper()}):")
        print("="*60)
        print(json.dumps(result, indent=2))

        # Save result
        output_path = args.output or f'/tmp/{args.method}_result.json'
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Saved to: {output_path}")


if __name__ == "__main__":
    main()
