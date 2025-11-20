#!/usr/bin/env python3
"""
Universal Anthropic API Connector

A reusable module for connecting to Anthropic's Claude API with automatic:
- API key management from environment
- Project-specific usage tracking
- Standardized configuration

Source: https://github.com/smhunt/computer-vision-utility-monitor
File: src/anthropic_connector.py

Copy this file to any project that uses Claude API for consistent tracking.

Usage:
    from anthropic_connector import get_claude_client, make_vision_call

    # Get a configured client
    client = get_claude_client()

    # Or use helper functions
    response = make_vision_call(image_path, prompt)
"""

import os
from typing import Optional, Dict, Any, List
try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed")
    print("Install with: pip install anthropic")
    exit(1)


def get_project_id() -> str:
    """
    Get project ID from environment or auto-detect from current directory
    
    Returns:
        Project identifier string
    """
    # Try environment variable first
    project_id = os.getenv("PROJECT_ID")
    
    if not project_id:
        # Auto-detect from current directory name
        import pathlib
        current_dir = pathlib.Path.cwd().name
        project_id = current_dir.lower().replace('_', '-').replace(' ', '-')
    
    return project_id


def get_claude_client(
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> anthropic.Anthropic:
    """
    Get a configured Anthropic Claude client with project tracking
    
    Args:
        api_key: Optional API key (defaults to ANTHROPIC_API_KEY env var)
        project_id: Optional project ID (defaults to PROJECT_ID env var or auto-detect)
    
    Returns:
        Configured Anthropic client
    
    Raises:
        ValueError: If no API key is available
    """
    # Get API key
    if api_key is None:
        api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        raise ValueError(
            'No API key provided. Set ANTHROPIC_API_KEY environment variable '
            'or pass api_key parameter.'
        )
    
    # Get project ID
    if project_id is None:
        project_id = get_project_id()
    
    # Initialize client with project tracking headers
    client = anthropic.Anthropic(
        api_key=api_key,
        default_headers={
            "anthropic-client-id": project_id,
        }
    )
    
    return client


def make_vision_call(
    image_path: str,
    prompt: str,
    model: str = "claude-opus-4-1",
    max_tokens: int = 1024,
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Helper function to make a vision API call
    
    Args:
        image_path: Path to image file
        prompt: Text prompt for analysis
        model: Claude model to use
        max_tokens: Maximum tokens in response
        api_key: Optional API key override
        project_id: Optional project ID override
    
    Returns:
        Dictionary with response data and usage info
    """
    import base64
    
    client = get_claude_client(api_key=api_key, project_id=project_id)
    proj_id = project_id or get_project_id()
    
    # Load and encode image
    with open(image_path, 'rb') as f:
        image_data = base64.standard_b64encode(f.read()).decode('utf-8')
    
    # Determine media type from extension
    from pathlib import Path
    ext = Path(image_path).suffix.lower()
    media_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    media_type = media_type_map.get(ext, 'image/jpeg')
    
    # Make API call with project tracking
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        metadata={
            "user_id": proj_id,
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
    
    # Return structured response
    return {
        'response_text': response.content[0].text,
        'model': response.model,
        'usage': {
            'input_tokens': response.usage.input_tokens,
            'output_tokens': response.usage.output_tokens,
        },
        'project_id': proj_id,
        'stop_reason': response.stop_reason,
    }


def make_text_call(
    prompt: str,
    model: str = "claude-sonnet-4-5",
    max_tokens: int = 1024,
    system: Optional[str] = None,
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Helper function to make a text-only API call
    
    Args:
        prompt: Text prompt
        model: Claude model to use
        max_tokens: Maximum tokens in response
        system: Optional system prompt
        api_key: Optional API key override
        project_id: Optional project ID override
    
    Returns:
        Dictionary with response data and usage info
    """
    client = get_claude_client(api_key=api_key, project_id=project_id)
    proj_id = project_id or get_project_id()
    
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "metadata": {
            "user_id": proj_id,
        },
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
    }
    
    if system:
        kwargs["system"] = system
    
    response = client.messages.create(**kwargs)
    
    return {
        'response_text': response.content[0].text,
        'model': response.model,
        'usage': {
            'input_tokens': response.usage.input_tokens,
            'output_tokens': response.usage.output_tokens,
        },
        'project_id': proj_id,
        'stop_reason': response.stop_reason,
    }


if __name__ == "__main__":
    # Test the connector
    print(f"Project ID: {get_project_id()}")
    print(f"API Key set: {'Yes' if os.getenv('ANTHROPIC_API_KEY') else 'No'}")
    
    try:
        client = get_claude_client()
        print("✅ Client initialized successfully")
        print(f"   Tracking under: {get_project_id()}")
    except ValueError as e:
        print(f"❌ Error: {e}")
