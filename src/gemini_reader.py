#!/usr/bin/env python3
"""
Gemini Vision Reader - Primary meter reading method
Uses Google Gemini 2.5 Flash (free tier, accurate)
"""

import os
import sys
from typing import Dict

def read_meter_with_gemini(image_path: str) -> Dict:
    """
    Read water meter using Google Gemini 2.5 Flash

    This is now the PRIMARY reading method (free + accurate!)
    Falls back to Claude if needed.

    Args:
        image_path: Path to meter image

    Returns:
        Dict with meter reading results including vision_model tracking
    """
    # Import from local_vision_reader
    sys.path.insert(0, os.path.dirname(__file__))
    from local_vision_reader import test_with_gemini

    return test_with_gemini(image_path)


def read_meter(image_path: str, fallback_to_claude: bool = True) -> Dict:
    """
    Primary meter reading function - uses Gemini, optionally falls back to Claude

    Args:
        image_path: Path to meter image
        fallback_to_claude: If True, use Claude if Gemini fails (default: True)

    Returns:
        Dict with meter reading results
    """
    # Try Gemini first (free + accurate)
    result = read_meter_with_gemini(image_path)

    # If Gemini failed and fallback enabled, try Claude
    if 'error' in result and fallback_to_claude:
        import sys
        print("⚠️  Gemini failed, falling back to Claude...", file=sys.stderr)
        from llm_reader import read_meter_with_claude
        result = read_meter_with_claude(image_path)
        result['fallback_used'] = True
        result['primary_method'] = 'gemini'

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python gemini_reader.py <image_path>")
        sys.exit(1)

    import json
    result = read_meter(sys.argv[1])
    print(json.dumps(result, indent=2))
