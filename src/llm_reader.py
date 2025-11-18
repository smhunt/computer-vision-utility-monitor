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

# Claude model to use (using latest available version)
# Options: claude-opus-4-1, claude-sonnet, claude-haiku, or specific dated versions
MODEL = "claude-opus-4-1"

# Prompt for water meter reading
METER_READING_PROMPT = """You are analyzing a water meter image. Please identify and read both components:

1. **Digital Display**: The main numerical display showing cubic meters (usually 4-5 digits)
2. **Dial/Analog Component**: The circular dial with a needle (shows fractional cubic meters, usually 0.000-0.999)

Please provide:
- The complete digital reading (integer part)
- The dial reading (fractional part to 3 decimal places)
- Total reading (digital + dial)
- Confidence level (high/medium/low)
- Any issues or concerns

Return your response in JSON format:
{
    "digital_reading": <integer>,
    "dial_reading": <float, 0.000-0.999>,
    "total_reading": <float>,
    "confidence": "high|medium|low",
    "notes": "any observations or concerns"
}

If you cannot read the meter clearly, explain why in the notes field and set confidence to "low".
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
        required_fields = ['digital_reading', 'dial_reading', 'total_reading', 'confidence']
        for field in required_fields:
            if field not in data:
                return {
                    'error': f'Missing required field: {field}',
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
            'digital_reading': int,
            'dial_reading': float,
            'total_reading': float,
            'confidence': str,
            'notes': str,
            'timestamp': str
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
        # Initialize client
        client = anthropic.Anthropic(api_key=api_key)

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

        # Make API call
        response = client.messages.create(
            model=model,
            max_tokens=1024,
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
        print(f"Digital Reading: {result['digital_reading']}")
        print(f"Dial Reading:    {result['dial_reading']:.3f}")
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
