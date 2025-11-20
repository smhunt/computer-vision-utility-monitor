# Setup Guide: Alternative Vision Models

This guide helps you set up alternative vision models for meter reading - from cheap APIs to completely local/offline solutions.

## 🎯 Quick Decision Guide

**Choose your approach based on your priorities:**

| Priority | Best Option | Cost | Setup Time | Accuracy |
|----------|-------------|------|------------|----------|
| **Best accuracy** | Claude Sonnet | ~$0.02/img | 5 min | ⭐⭐⭐⭐⭐ |
| **Cheapest API** | OpenAI GPT-4o-mini | ~$0.0002/img | 5 min | ⭐⭐⭐⭐ |
| **Free tier** | Google Gemini Flash | Free* | 10 min | ⭐⭐⭐⭐ |
| **Fully local/offline** | Ollama llama-vision | $0 | 30 min | ⭐⭐⭐⭐ |
| **Minimal deps** | OpenCV only | $0 | 2 min | ⭐⭐ |

*Rate limited

## 🚀 Setup Instructions

### Option 1: OpenAI GPT-4o-mini (Cheapest API)

**Cost:** ~$0.0002 per image (~500x cheaper than Claude)
**Pros:** Fast, accurate, cheap
**Cons:** Still requires API key and internet

```bash
# Install
pip3 install openai

# Get API key from: https://platform.openai.com/api-keys
export OPENAI_API_KEY="sk-..."

# Test
python src/local_vision_reader.py path/to/meter.jpg --method openai
```

### Option 2: Google Gemini Flash (Free Tier)

**Cost:** Free tier available (15 RPM, 1500 RPD)
**Pros:** Free tier, fast, good accuracy
**Cons:** Rate limited on free tier

```bash
# Install
pip3 install google-generativeai

# Get API key from: https://makersuite.google.com/app/apikey
export GOOGLE_API_KEY="..."

# Test
python src/local_vision_reader.py path/to/meter.jpg --method gemini
```

### Option 3: Ollama with Local Vision Model (RECOMMENDED for Local)

**Cost:** $0 (completely free, runs on your machine)
**Pros:** Fully local, no API, no internet, no cost
**Cons:** Requires ~7GB disk space, slower than API

#### Step 1: Install Ollama

```bash
# macOS
brew install ollama

# Or download from: https://ollama.ai/download

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download installer from https://ollama.ai/download
```

#### Step 2: Start Ollama

```bash
# Start the Ollama service
ollama serve
```

#### Step 3: Pull a Vision Model

```bash
# Recommended: llama3.2-vision (11B, best quality)
ollama pull llama3.2-vision:11b

# OR smaller/faster options:
ollama pull llava:7b          # Smaller, faster
ollama pull llava:13b         # Good balance
ollama pull bakllava          # Alternative
```

#### Step 4: Install Python Client

```bash
pip3 install ollama
```

#### Step 5: Test

```bash
# Use default model (llama3.2-vision:11b)
python src/local_vision_reader.py path/to/meter.jpg --method ollama

# Or specify a different model
python src/local_vision_reader.py path/to/meter.jpg --method ollama --ollama-model llava:7b
```

### Option 4: OpenCV Only (Minimal)

**Cost:** $0
**Pros:** Minimal dependencies, fast
**Cons:** Low accuracy, can only detect needle angle

```bash
# Install
pip3 install opencv-python numpy

# Test (limited functionality)
python src/local_vision_reader.py path/to/meter.jpg --method opencv
```

## 📊 Compare All Methods

Test all available methods at once:

```bash
# This will try all configured methods
python src/local_vision_reader.py path/to/meter.jpg --method compare

# Save results
python src/local_vision_reader.py path/to/meter.jpg --method compare --output results.json
```

Example output:
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
* Gemini has free tier (rate limited)
```

## 🔧 Integration with Existing System

### Update .env File

Add your API keys:

```bash
# OpenAI (optional)
OPENAI_API_KEY=sk-...

# Google Gemini (optional)
GOOGLE_API_KEY=...

# Claude (existing)
ANTHROPIC_API_KEY=sk-ant-...
```

### Use in Slash Command

The `/takemetersnapshot` command will automatically use Claude by default, but you can modify it to use alternative methods.

## 🧪 Testing & Validation

### Test on Sample Images

```bash
# Test with a known reading
python src/local_vision_reader.py test_images/meter_known_2271.37.jpg --method compare
```

### Benchmark Accuracy

Create a ground truth file with known readings:

```json
{
  "test_images/meter1.jpg": 2271.37,
  "test_images/meter2.jpg": 2275.82
}
```

Then compare:

```bash
# Test all methods against ground truth
for img in test_images/*.jpg; do
    python src/local_vision_reader.py "$img" --method compare
done
```

## 💡 Tips & Tricks

### For Best Accuracy with Ollama

1. **Use the largest model you can fit:**
   - `llama3.2-vision:11b` - Best quality (recommended)
   - `llava:13b` - Good balance
   - `llava:7b` - Faster but less accurate

2. **Ensure good hardware:**
   - At least 16GB RAM recommended for 11B model
   - 8GB RAM sufficient for 7B model
   - GPU acceleration helps but not required

3. **Pre-warm the model:**
   ```bash
   # First request is slower, subsequent ones are faster
   ollama run llama3.2-vision:11b "test"
   ```

### For Cost Optimization

1. **Use Gemini free tier for development:**
   - 15 requests/minute
   - 1500 requests/day
   - Perfect for testing

2. **Use OpenAI for production:**
   - ~500x cheaper than Claude
   - Still very accurate
   - Good rate limits

3. **Use Ollama for privacy/bulk processing:**
   - No per-request cost
   - Process thousands of images for free
   - No data sent to external services

### For Speed

- **Fastest:** OpenCV (0.5s, but limited functionality)
- **Fast API:** OpenAI GPT-4o-mini (1-2s)
- **Fast Local:** llava:7b on GPU (2-3s)
- **Accurate:** Claude Sonnet (2-3s)

## 🐛 Troubleshooting

### Ollama Issues

**Error: "connection refused"**
```bash
# Start Ollama service
ollama serve
```

**Error: "model not found"**
```bash
# Pull the model first
ollama pull llama3.2-vision:11b
```

**Slow performance**
```bash
# Use smaller model
ollama pull llava:7b
python src/local_vision_reader.py meter.jpg --method ollama --ollama-model llava:7b
```

### API Issues

**Error: "API key not found"**
```bash
# Export your API key
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="..."
```

**Error: "Rate limit exceeded" (Gemini)**
```bash
# Wait 60 seconds or use paid tier
# Free tier: 15 RPM, 1500 RPD
```

### OpenCV Issues

**Low accuracy**
- OpenCV can only detect needle angle, not digits
- Use for testing/debugging only
- Switch to OCR or vision models for production

## 📈 Next Steps

1. **Test all methods** on your specific meter images
2. **Choose the best method** based on accuracy/cost/speed trade-offs
3. **Integrate into workflow** by updating slash command
4. **Monitor performance** over time

## 🔗 Resources

- **Ollama:** https://ollama.ai/
- **OpenAI API:** https://platform.openai.com/
- **Google AI Studio:** https://makersuite.google.com/
- **Claude API:** https://console.anthropic.com/

---

**Branch:** `experiment/local-vision-ml`
**Status:** ✅ Ready for testing
