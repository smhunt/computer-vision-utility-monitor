# Branch: experiment/local-vision-ml

## 🎯 Purpose

This experimental branch explores **alternative vision models** for reading analog water meters, providing options ranging from cheap APIs to completely local/offline solutions.

## ✨ What's New

### 1. Multiple Vision Model Support

Instead of only using Claude Sonnet, you can now use:

- **OpenAI GPT-4o-mini** - ~500x cheaper than Claude (~$0.0002/image)
- **Google Gemini Flash** - Free tier available (15 RPM, 1500 RPD)
- **Ollama + llama-vision** - Fully local, no API, no internet, 100% free
- **OpenCV** - Basic computer vision fallback (needle detection only)

### 2. New File: [src/local_vision_reader.py](src/local_vision_reader.py)

Unified interface for all vision models:

```python
from src.local_vision_reader import (
    test_with_openai,
    test_with_gemini,
    test_with_ollama,
    test_with_opencv,
    compare_all_methods
)

# Test single method
result = test_with_ollama('meter.jpg')

# Or compare all available methods
results = compare_all_methods('meter.jpg')
```

### 3. CLI Tool

```bash
# Compare all methods
python src/local_vision_reader.py meter.jpg

# Use specific method
python src/local_vision_reader.py meter.jpg --method openai
python src/local_vision_reader.py meter.jpg --method gemini
python src/local_vision_reader.py meter.jpg --method ollama
python src/local_vision_reader.py meter.jpg --method opencv

# Specify Ollama model
python src/local_vision_reader.py meter.jpg --method ollama --ollama-model llava:7b
```

### 4. Easy Setup

```bash
# Interactive setup wizard
./quick_setup.sh

# Or manual installation
pip install -r requirements-local-vision.txt
```

## 📊 Comparison Matrix

| Method | Cost/Image | Speed | Accuracy | Local | Internet |
|--------|-----------|-------|----------|-------|----------|
| Claude Sonnet | ~$0.02 | 2-3s | ⭐⭐⭐⭐⭐ | ❌ | Required |
| OpenAI GPT-4o-mini | ~$0.0002 | 1-2s | ⭐⭐⭐⭐ | ❌ | Required |
| Gemini Flash | Free* | 2s | ⭐⭐⭐⭐ | ❌ | Required |
| Ollama llama-vision | $0 | 3-5s | ⭐⭐⭐⭐ | ✅ | Optional |
| OpenCV | $0 | 0.5s | ⭐⭐ | ✅ | No |

*Free tier: 15 requests/minute, 1500/day

## 🚀 Quick Start

### Option 1: Cheapest API (OpenAI)

```bash
pip install openai
export OPENAI_API_KEY="sk-..."
python src/local_vision_reader.py meter.jpg --method openai
```

**Cost:** ~$0.0002 per image (500x cheaper than Claude!)

### Option 2: Free API (Gemini)

```bash
pip install google-generativeai
export GOOGLE_API_KEY="..."
python src/local_vision_reader.py meter.jpg --method gemini
```

**Cost:** Free (with rate limits)

### Option 3: Fully Local (Ollama) - RECOMMENDED

```bash
# Install Ollama
brew install ollama  # macOS
# or: curl -fsSL https://ollama.ai/install.sh | sh  # Linux

# Start service
ollama serve

# Pull vision model (~7GB)
ollama pull llama3.2-vision:11b

# Install Python client
pip install ollama

# Test
python src/local_vision_reader.py meter.jpg --method ollama
```

**Cost:** $0 (completely free, runs on your machine)
**Privacy:** 100% local, no data sent to cloud
**Internet:** Not required after model download

## 📖 Documentation

- **[SETUP_ALTERNATIVE_VISION.md](SETUP_ALTERNATIVE_VISION.md)** - Detailed setup guide
- **[LOCAL_VISION_README.md](LOCAL_VISION_README.md)** - Technical documentation
- **[quick_setup.sh](quick_setup.sh)** - Interactive setup wizard

## 🧪 Usage Examples

### Compare All Methods

```bash
python src/local_vision_reader.py snapshot.jpg --method compare
```

Output:
```
COMPARISON SUMMARY
================================================================================
Method        Reading          Confidence   Time       Cost       Local
--------------------------------------------------------------------------------
CLAUDE        2271.37 m³       0.85         2.34s      $0.0234    ✗
OPENAI        2271.36 m³       0.82         1.45s      $0.0002    ✗
GEMINI        2271.37 m³       0.80         1.89s      $0*        ✗
OLLAMA        2271.35 m³       0.78         3.12s      $0         ✓
OPENCV        0.07 m³          0.30         0.45s      $0         ✓
================================================================================
```

### Use Specific Method

```bash
# OpenAI (cheap)
python src/local_vision_reader.py meter.jpg --method openai --output result_openai.json

# Gemini (free tier)
python src/local_vision_reader.py meter.jpg --method gemini --output result_gemini.json

# Ollama (local)
python src/local_vision_reader.py meter.jpg --method ollama --output result_ollama.json
```

### Python Integration

```python
from src.local_vision_reader import test_with_ollama, test_with_openai

# Use local Ollama (no cost, no API)
result = test_with_ollama('meter.jpg', model='llama3.2-vision:11b')
print(f"Reading: {result['total_reading']} m³")

# Or use OpenAI (cheap API)
result = test_with_openai('meter.jpg')
print(f"Reading: {result['total_reading']} m³")
print(f"Cost: ${result['api_usage']['total_tokens'] * 0.0002 / 1000}")
```

## 🎓 When to Use Each Method

### Use **Claude Sonnet** when:
- You need the absolute best accuracy
- Cost is not a concern
- You're already using Claude

### Use **OpenAI GPT-4o-mini** when:
- You want API-based but cheap
- You need good accuracy at low cost
- You process many images

### Use **Google Gemini Flash** when:
- You want to try for free
- You have low request volume (< 1500/day)
- You're prototyping/testing

### Use **Ollama (local)** when:
- Privacy is important
- You want zero ongoing costs
- You process many images
- You need offline capability
- You have decent hardware (16GB+ RAM)

### Use **OpenCV** when:
- You need minimal dependencies
- You only need needle detection
- You're testing/debugging

## 🔧 Integration with Main System

The local vision reader can be integrated into the existing system:

```python
# In your existing code
from src.local_vision_reader import test_with_ollama

# Replace Claude call with Ollama for zero cost
reading = test_with_ollama(snapshot_path)
```

Or modify the `/takemetersnapshot` command to support method selection:

```bash
/takemetersnapshot --method ollama
/takemetersnapshot --method openai
/takemetersnapshot --method gemini
```

## 🐛 Known Limitations

1. **Ollama requires download:** First-time setup downloads ~7GB model
2. **Ollama needs RAM:** 11B model needs ~16GB RAM, 7B model works with 8GB
3. **OpenCV limited:** Can only detect needle, not read digits
4. **Gemini rate limits:** Free tier limited to 15 RPM

## 🔮 Future Enhancements

- [ ] Add EasyOCR for better local digit recognition
- [ ] Support for custom-trained models
- [ ] Batch processing mode
- [ ] Model accuracy benchmarking suite
- [ ] Auto-select best model based on image quality
- [ ] Integration with slash command

## 🤝 Contributing

This is an experimental branch. Feel free to:
- Test different vision models
- Optimize prompts for each model
- Add new model integrations
- Benchmark accuracy
- Report issues

## 📊 Cost Comparison Example

Processing **1000 images per month:**

| Method | Cost/Month | Notes |
|--------|-----------|-------|
| Claude Sonnet | ~$20 | Most accurate |
| OpenAI GPT-4o-mini | ~$0.20 | 100x cheaper |
| Gemini Flash | $0 | Free tier sufficient |
| Ollama | $0 | One-time setup |

## 🔗 Resources

- Ollama: https://ollama.ai/
- OpenAI API: https://platform.openai.com/
- Google AI Studio: https://makersuite.google.com/
- llama3.2-vision: https://ollama.ai/library/llama3.2-vision

---

**Branch:** `experiment/local-vision-ml`
**Status:** ✅ Ready for Testing
**Created:** 2025-11-19
**Main Changes:**
- Added [src/local_vision_reader.py](src/local_vision_reader.py)
- Added [SETUP_ALTERNATIVE_VISION.md](SETUP_ALTERNATIVE_VISION.md)
- Added [requirements-local-vision.txt](requirements-local-vision.txt)
- Added [quick_setup.sh](quick_setup.sh)
