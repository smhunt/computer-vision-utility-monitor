#!/usr/bin/env python3
"""
Water Meter Reader using Claude Vision API

This module uses Anthropic's Claude vision model to read water meter values
from images captured by a camera.

Usage:
    from llm_reader import read_meter_with_claude
    result = read_meter_with_claude("path/to/image.jpg")
"""

import os
import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Union, Optional

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed")
    print("Install with: pip install anthropic")
    exit(1)

try:
    from image_processor import preprocess_meter_image, image_to_bytes
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False


# ============================================================================
# CONFIGURATION
# ============================================================================

# Project identifier for API usage tracking
# This helps track API usage across different projects in your Anthropic dashboard
PROJECT_ID = os.getenv("PROJECT_ID", "utility-meter-monitor")

# Claude model to use (using latest available version)
# Options: claude-sonnet-4-5-20250929, claude-sonnet-3-5-20241022, claude-haiku, or specific dated versions
# Using Sonnet 4.5 for best performance with max tier access
MODEL = "claude-sonnet-4-5-20250929"

# Prompt for water meter reading
METER_READING_PROMPT = """You are analyzing a Badger Meter "Absolute Digital" residential water meter.

**DISPLAY FORMAT - CRITICAL:**
This meter has:
- 5 WHITE digits (whole m³): "02271" = 2271 m³
- 1 BLACK digit (tenths): "2" = 0.2 m³
- Red dial (hundredths): position "5" = 0.05 m³
- **Total: 2271.25 cubic meters**

**THE THREE COMPONENTS:**

1. **WHITE ROLLER DIGITS (Left portion of display):**
   - Shows EXACTLY 5 WHITE digits representing whole cubic meters
   - Example: "0 2 2 7 1" = 2271 m³ (integer part)
   - Example: "0 0 1 5 8" = 158 m³ (integer part)
   - Ignore leading zeros
   - COUNT CAREFULLY: Read from LEFT to RIGHT

2. **BLACK DIGIT (6th digit, right side of display - SEPARATE from white digits):**
   - This is a SINGLE BLACK DIGIT (0-9) on the RIGHT side of the display
   - It is PHYSICALLY SEPARATED from the 5 white digits with a small gap
   - The black digit shows TENTHS of a cubic meter (first decimal place)
   - **CRITICAL - DO NOT CONFUSE:**
     * The rightmost WHITE digit and the BLACK digit are DIFFERENT
     * If you see "02271  5" → white digits = "02271", black digit = "5"
     * If you see "02271  1" → white digits = "02271", black digit = "1"
     * The black digit has its own housing/frame, slightly separated
   - Examples:
     * Black digit "5" = 0.5 m³
     * Black digit "2" = 0.2 m³
     * Black digit "7" = 0.7 m³
     * Black digit "0" = 0.0 m³

3. **RED SWEEP HAND DIAL (Bottom circular gauge):**

   **FIND THE SINGLE RED HAND - IT'S THE ONLY RED THING ON THE METER**

   The red sweep hand is:
   - The ONLY red element on the entire meter face
   - A SINGLE HAND that rotates around the center point of the dial
   - It has a POINTED TIP that indicates the reading
   - Like the hour hand on a clock, but it's RED

   **CRITICAL - WHICH WAY IS THE HAND POINTING?**
   Look at the red hand and identify which EDGE of the meter face the pointed tip is nearest to:
   - Is the tip near the TOP edge? → 0° (12 o'clock)
   - Is the tip near the RIGHT edge? → 90° (3 o'clock)
   - Is the tip near the BOTTOM edge? → 180° (6 o'clock)
   - Is the tip near the LEFT edge? → 270° (9 o'clock)

   **MEASURE THE ANGLE IN DEGREES:**
   * 0° = pointing straight UP (12 o'clock, north, top of circle)
   * 90° = pointing straight RIGHT (3 o'clock, east, right side)
   * 180° = pointing straight DOWN (6 o'clock, south, bottom)
   * 270° = pointing straight LEFT (9 o'clock, west, left side)

   **EXAMPLES:**
   - Red hand pointing straight up → 0°
   - Red hand pointing up and slightly right → 30°
   - Red hand pointing to upper right → 60°
   - Red hand pointing straight right → 90°
   - Red hand pointing down-right → 120°
   - Red hand pointing straight down → 180°
   - Red hand pointing down-left → 240°
   - Red hand pointing straight left → 270°
   - Red hand pointing up-left → 330°

   **YOUR TASK:**
   - Find the red hand (it's the only red thing!)
   - Estimate its angle from vertical (0° = straight up / 12 o'clock)
   - Report the angle as a number (0-359)
   - BE PRECISE: The dial scale goes 0-10 for one full rotation

   **CRITICAL ANGLE CHECK:**
   - Is the hand pointing UP? → Should be near 0°
   - Is the hand pointing RIGHT? → Should be near 90°
   - Is the hand pointing DOWN? → Should be near 180°
   - Is the hand pointing LEFT? → Should be near 270°

   Set dial_reading to (dial_angle_degrees / 3600) and dial_angle_degrees to your angle estimate

**STEP-BY-STEP READING:**

Example: White digits "02271", black digit "2", red dial at "5"

Step 1: Read white roller digits (integer part)
- White digits: "0 2 2 7 1"
- Remove leading zeros: "2271"
- Integer part: 2271 m³

Step 2: Read black digit (tenths)
- Black digit: "2"
- Tenths: 0.2 m³

Step 3: Read red dial (hundredths)
- Dial position: "5"
- Calculation: 5 ÷ 100 = 0.05 m³

Step 4: Calculate total
- 2271 + 0.2 + 0.05 = **2271.25 m³**

**MORE EXAMPLES:**

Example 1: White "00158" + Black "7" + Dial "3"
- Integer: 158 m³
- Tenths: 0.7 m³
- Hundredths: 0.03 m³
- Total: **158.73 m³**

Example 2: White "02315" + Black "4" + Dial "0"
- Integer: 2315 m³
- Tenths: 0.4 m³
- Hundredths: 0.00 m³
- Total: **2315.40 m³**

Example 3: White "00995" + Black "9" + Dial "8"
- Integer: 995 m³
- Tenths: 0.9 m³
- Hundredths: 0.08 m³
- Total: **995.98 m³**

**CRITICAL: COUNT AND DESCRIBE ALL COMPONENTS - REQUIRED FORMAT**
In your notes, you MUST describe what you see in this EXACT format:

"White digits (5 digits on left): [digit] [digit] [digit] [digit] [digit] = [value] m³.
Black digit (single digit on right, separated): [digit] = [value] m³.
Red dial hand: [angle]° (the red hand is pointing at [angle] degrees).
Total: [sum]"

Example: "White digits (5 digits on left): 0 2 2 7 1 = 2271 m³. Black digit (single digit on right, separated): 5 = 0.5 m³. Red dial hand: 90° (the red hand is pointing at 90 degrees). Dial reading: 90/3600 = 0.025 m³. Total: 2271.525 m³"

**CRITICAL OUTPUT FORMAT:**

Return your response in JSON format:
{
    "digital_reading": <integer, 5 white digits with leading zeros removed, e.g., 2271>,
    "black_digit": <integer, the black tenths digit 0-9, e.g., 5>,
    "dial_reading": <float, calculated as dial_angle_degrees / 3600, e.g., 0.025>,
    "dial_angle_degrees": <integer, angle 0-359 where 0=UP, 90=RIGHT, 180=DOWN, 270=LEFT>,
    "total_reading": <float, digital_reading + (black_digit/10) + dial_reading, e.g., 2271.525>,
    "confidence": "high|medium|low",
    "notes": "<follow the format above>"
}

**VALIDATION CHECKS - CRITICAL FOR CONFIDENCE:**
- Water meters only increase, never decrease
- THIS SPECIFIC METER: Expected range is 2000-3000 m³ (NOT 20,000+!)
- If your total_reading is outside 1000-5000 m³ range, you likely miscounted digits - RECOUNT!
- **BLACK DIGIT CHECK:**
  * black_digit MUST be 0-9 (single digit)
  * If black_digit is not in response, YOU MADE AN ERROR - there is ALWAYS a black digit
- **DIAL READING SANITY CHECK:**
  * dial_reading MUST be between 0.00 and 0.099 (hundredths only!)
  * If dial_reading is >= 0.10, YOU ARE WRONG (that would be in the black digit)
  * If you see "hand between 0 and 1" → dial position ~0.5 → reading should be ~0.005 m³
  * Your notes MUST show: dial position ÷ 100 = dial_reading value
- **TOTAL CALCULATION CHECK:**
  * total_reading = digital_reading + (black_digit ÷ 10) + dial_reading
  * Example: 2271 + (2÷10) + 0.05 = 2271 + 0.2 + 0.05 = 2271.25 m³
- If you read exactly 5 white digits + 1 black digit + dial, and result is in expected range (2000-3000 m³), confidence should be HIGH
- Only mark confidence as LOW if the image is blurry, digits are unclear, or you're uncertain
"""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def encode_image(image_path: str, rotation: Optional[int] = None, auto_orient: bool = True) -> tuple[str, str]:
    """
    Encode image to base64 for Claude API with optional preprocessing

    Args:
        image_path: Path to image file or URL
        rotation: Rotation angle in degrees (0, 90, 180, 270) or None
        auto_orient: Automatically correct orientation from EXIF data

    Returns:
        Tuple of (base64_data, media_type)
    """
    # Check if we need preprocessing
    needs_preprocessing = IMAGE_PROCESSING_AVAILABLE and (rotation or auto_orient)

    if image_path.startswith(('http://', 'https://')):
        # For HTTP URLs, we'll need to download first
        import requests
        response = requests.get(image_path, timeout=10)
        image_data = response.content

        # Determine media type from content-type header
        content_type = response.headers.get('content-type', 'image/jpeg')
        media_type = content_type if 'image/' in content_type else 'image/jpeg'
    else:
        # Check if preprocessing is needed
        if needs_preprocessing:
            # Preprocess the image (rotation, auto-orient, etc.)
            img, metadata = preprocess_meter_image(
                image_path,
                rotation=rotation,
                auto_orient=auto_orient
            )

            # Convert preprocessed image to bytes
            image_data = image_to_bytes(img, format='JPEG', quality=95)
            media_type = 'image/jpeg'
        else:
            # Local file without preprocessing
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Determine media type from extension
            ext = Path(image_path).suffix.lower()
            media_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            media_type = media_type_map.get(ext, 'image/jpeg')

    # Encode to base64
    base64_data = base64.standard_b64encode(image_data).decode('utf-8')

    return base64_data, media_type


def parse_claude_response(response_text: str) -> Dict:
    """
    Parse Claude's response and extract meter reading data

    Args:
        response_text: Raw text response from Claude

    Returns:
        Dictionary with reading data
    """
    try:
        # Try to find JSON in the response
        # Claude might wrap it in markdown code blocks
        text = response_text.strip()

        # Remove markdown code blocks if present
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()

        # Parse JSON
        data = json.loads(text)

        # Validate required fields
        required_fields = ['digital_reading', 'black_digit', 'dial_reading', 'total_reading', 'confidence']
        for field in required_fields:
            if field not in data:
                return {
                    'error': f'Missing required field: {field}',
                    'raw_response': response_text
                }

        # Validate black_digit is 0-9
        if not (0 <= data.get('black_digit', -1) <= 9):
            return {
                'error': f'Invalid black_digit: {data.get("black_digit")} (must be 0-9)',
                'raw_response': response_text
            }

        # Validate dial_reading is hundredths (0.00-0.099)
        if not (0.0 <= data.get('dial_reading', -1) < 0.10):
            return {
                'error': f'Invalid dial_reading: {data.get("dial_reading")} (must be 0.00-0.099)',
                'raw_response': response_text
            }

        # Add timestamp
        data['timestamp'] = datetime.now().isoformat()

        return data

    except json.JSONDecodeError as e:
        return {
            'error': f'Failed to parse JSON: {str(e)}',
            'raw_response': response_text
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}',
            'raw_response': response_text
        }


# ============================================================================
# MAIN API FUNCTION
# ============================================================================

def read_meter_with_claude(
    image_path: str,
    api_key: str = None,
    model: str = MODEL,
    prompt: str = METER_READING_PROMPT,
    custom_prompt: str = None,
    rotation: Optional[int] = None,
    auto_orient: bool = True
) -> Dict:
    """
    Read water meter from image using Claude Vision API

    Args:
        image_path: Path to image file or HTTP URL
        api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        model: Claude model to use
        prompt: Custom prompt (uses default if not provided)
        custom_prompt: Alternative way to specify custom prompt (overrides prompt)
        rotation: Rotation angle in degrees (0, 90, 180, 270) or None
        auto_orient: Automatically correct orientation from EXIF data

    Returns:
        Dictionary with reading data:
        {
            'digital_reading': int,          # 5 white digits (whole m³)
            'black_digit': int,               # Black digit (tenths, 0-9)
            'dial_reading': float,            # Red dial (hundredths, 0.00-0.099)
            'total_reading': float,           # Complete reading
            'confidence': str,                # high|medium|low
            'notes': str,                     # Detailed observations
            'timestamp': str                  # ISO format timestamp
        }

        Or on error:
        {
            'error': str,
            'raw_response': str (optional)
        }
    """
    # Use custom_prompt if provided, otherwise use prompt
    if custom_prompt is not None:
        prompt = custom_prompt

    # Get API key
    if api_key is None:
        api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        return {
            'error': 'No API key provided. Set ANTHROPIC_API_KEY environment variable.'
        }

    try:
        # Initialize client with custom headers for project tracking
        client = anthropic.Anthropic(
            api_key=api_key,
            default_headers={
                "anthropic-client-id": PROJECT_ID,
            }
        )

        # Encode image with optional preprocessing
        try:
            image_data, media_type = encode_image(
                image_path,
                rotation=rotation,
                auto_orient=auto_orient
            )
        except Exception as e:
            return {
                'error': f'Failed to load image: {str(e)}'
            }

        # Make API call with metadata for usage tracking
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            metadata={
                "user_id": PROJECT_ID,
            },
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )

        # Extract text from response
        response_text = response.content[0].text

        # Parse response
        result = parse_claude_response(response_text)

        # Add usage info
        if hasattr(response, 'usage'):
            result['api_usage'] = {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens
            }

        return result

    except anthropic.APIError as e:
        return {
            'error': f'API error: {str(e)}'
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}'
        }


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Command-line interface for testing"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python llm_reader.py <image_path>")
        print("\nExample:")
        print("  python llm_reader.py /path/to/meter.jpg")
        print("  python llm_reader.py http://camera-ip/snapshot.jpg")
        print("\nEnvironment:")
        print("  ANTHROPIC_API_KEY: Required")
        sys.exit(1)

    image_path = sys.argv[1]

    # Check API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("\nSet it with:")
        print("  export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    print(f"Reading meter from: {image_path}")
    print()

    # Read meter
    result = read_meter_with_claude(image_path)

    # Display result
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        if 'raw_response' in result:
            print(f"\nRaw response:\n{result['raw_response']}")
        sys.exit(1)
    else:
        print("✅ Reading successful!")
        print()
        print(f"White Digits:    {result['digital_reading']} m³")
        print(f"Black Digit:     {result['black_digit']} → 0.{result['black_digit']} m³")
        print(f"Red Dial:        {result['dial_reading']:.3f} m³")
        print(f"─" * 40)
        print(f"Total Reading:   {result['total_reading']:.3f} m³")
        print(f"Confidence:      {result['confidence']}")

        if result.get('notes'):
            print(f"Notes:           {result['notes']}")

        if 'api_usage' in result:
            print()
            print(f"API Usage:")
            print(f"  Input tokens:  {result['api_usage']['input_tokens']}")
            print(f"  Output tokens: {result['api_usage']['output_tokens']}")

        # Save to JSON
        output_file = 'last_reading.json'
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print()
        print(f"Result saved to: {output_file}")


if __name__ == "__main__":
    main()
