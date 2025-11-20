# Universal Anthropic API Connector

**📦 GitHub Repository:** [computer-vision-utility-monitor](https://github.com/smhunt/computer-vision-utility-monitor)
**📄 Connector File:** [`src/anthropic_connector.py`](https://github.com/smhunt/computer-vision-utility-monitor/blob/main/src/anthropic_connector.py)

A reusable module that handles Anthropic Claude API connections with automatic project tracking. Copy this file to any project that uses Claude API.

## Quick Links
- **Get the connector:** `curl -O https://raw.githubusercontent.com/smhunt/computer-vision-utility-monitor/main/src/anthropic_connector.py`
- **Browse code:** https://github.com/smhunt/computer-vision-utility-monitor/blob/main/src/anthropic_connector.py
- **Clone repo:** `git clone https://github.com/smhunt/computer-vision-utility-monitor.git`

## Quick Start

### 1. Copy the connector to your project
```bash
# From any new project
cp /path/to/utility-meter-monitor/src/anthropic_connector.py src/
# Or create a shared lib and symlink it
```

### 2. Set up environment variables
```bash
# In your project's .env file
ANTHROPIC_API_KEY=sk-ant-...
PROJECT_ID=your-project-name  # Optional, auto-detects from directory
```

### 3. Use in your code

#### Vision API (image analysis)
```python
from anthropic_connector import make_vision_call

result = make_vision_call(
    image_path="/path/to/image.jpg",
    prompt="Analyze this image and extract the text",
    model="claude-opus-4-1"  # Optional, defaults to opus
)

print(result['response_text'])
print(f"Used {result['usage']['input_tokens']} input tokens")
print(f"Tracked under: {result['project_id']}")
```

#### Text API (no images)
```python
from anthropic_connector import make_text_call

result = make_text_call(
    prompt="Explain quantum computing in simple terms",
    model="claude-sonnet-4-5",  # Faster, cheaper for text
    system="You are a helpful science teacher"
)

print(result['response_text'])
```

#### Direct client access (advanced)
```python
from anthropic_connector import get_claude_client

client = get_claude_client()  # Auto-loads API key and project ID
# Use client with full Anthropic API...
```

## Features

✅ **Automatic API Key Management**
- Loads from `ANTHROPIC_API_KEY` environment variable
- Validates key is present before making calls

✅ **Project Tracking**
- Uses `PROJECT_ID` from environment
- Auto-detects from directory name if not set
- Adds tracking headers and metadata to all API calls

✅ **Usage Monitoring**
- Returns token usage with every call
- Tracks which project generated the usage
- View in Anthropic dashboard by project

✅ **Simple Helpers**
- `make_vision_call()` - Image analysis
- `make_text_call()` - Text generation
- `get_claude_client()` - Direct client access

## Example Projects

### This project (Utility Meter Monitor)
```python
# In src/llm_reader.py
from anthropic_connector import make_vision_call

result = make_vision_call(
    image_path=meter_image,
    prompt=METER_READING_PROMPT
)
```

### Generic script
```python
#!/usr/bin/env python3
import os
from anthropic_connector import make_text_call

# Set project ID for this script
os.environ['PROJECT_ID'] = 'data-analysis-scripts'

response = make_text_call(
    prompt="Analyze this dataset...",
    model="claude-sonnet-4-5"
)
```

## Centralized Benefits

1. **Consistent tracking** across all projects
2. **Easy cost attribution** per project
3. **Single source of truth** for API configuration  
4. **Portable** - copy to any Python project
5. **No vendor lock-in** - uses official Anthropic SDK

## Migration Guide

To add this to existing projects:

1. Copy `anthropic_connector.py` to project
2. Add to `.env`: `PROJECT_ID=project-name`
3. Replace direct anthropic client creation:
   ```python
   # Before
   client = anthropic.Anthropic(api_key=api_key)
   
   # After
   from anthropic_connector import get_claude_client
   client = get_claude_client()
   ```

4. Or use helpers for simpler code:
   ```python
   # Before (lots of boilerplate)
   client = anthropic.Anthropic(api_key=api_key)
   with open(image_path, 'rb') as f:
       image_data = base64.b64encode(f.read()).decode()
   response = client.messages.create(
       model="claude-opus-4-1",
       messages=[{"role": "user", "content": [...]}]
   )
   text = response.content[0].text
   
   # After (one line)
   from anthropic_connector import make_vision_call
   result = make_vision_call(image_path, prompt)
   text = result['response_text']
   ```

---

**Created:** 2025-11-18  
**Author:** Computer Vision Utility Monitor Project  
**Purpose:** Share best practices across all AI projects
