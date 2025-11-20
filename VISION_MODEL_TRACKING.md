# Vision Model Tracking

**Feature:** Track which vision AI model was used for each meter reading

## Overview

Every meter reading now includes:
- `vision_model`: The specific model used (e.g., "claude-sonnet-4-5-20250929", "gemini-2.5-flash", "llava:13b")
- `vision_provider`: The provider/platform ("anthropic", "google", "openai", "ollama", "local")

## Tracked Models

| Provider | Model | vision_model | vision_provider |
|----------|-------|--------------|-----------------|
| Claude | Sonnet 4.5 | claude-sonnet-4-5-20250929 | anthropic |
| Gemini | 2.5 Flash | gemini-2.5-flash | google |
| OpenAI | GPT-4o-mini | gpt-4o-mini | openai |
| Ollama | llava:13b | llava:13b | ollama |
| Ollama | llama3.2-vision | llama3.2-vision:11b | ollama |
| OpenCV | Basic CV | opencv-cv | local |

## Where It's Logged

### 1. JSONL Reading Logs

Location: `logs/water_readings.jsonl`

Each reading entry includes:
```json
{
  "digital_reading": 2271,
  "black_digit": 8,
  "dial_reading": 0.81,
  "total_reading": 2271.81,
  "confidence": "high",
  "timestamp": "2025-11-19T21:49:42.712663",
  "vision_model": "gemini-2.5-flash",
  "vision_provider": "google"
}
```

### 2. Snapshot Metadata

Location: `logs/meter_snapshots/{meter_name}/{timestamp}.json`

```json
{
  "snapshot": {
    "filename": "water_main_20251119_214942.jpg",
    "timestamp": "2025-11-19T21:49:42Z"
  },
  "meter_reading": {
    "total_reading": 2271.81,
    "vision_model": "gemini-2.5-flash",
    "vision_provider": "google"
  }
}
```

### 3. API Response

Every reading API call returns model info:
```python
result = read_meter_with_claude(image_path)
print(result['vision_model'])  # "claude-sonnet-4-5-20250929"
print(result['vision_provider'])  # "anthropic"
```

## Use Cases

### 1. Cost Analysis

Query JSONL to see API cost breakdown by model:
```bash
# Count readings by model
cat logs/water_readings.jsonl | jq -r '.vision_model' | sort | uniq -c

# Example output:
#  145 claude-sonnet-4-5-20250929
#   89 gemini-2.5-flash
#    5 llava:13b
```

### 2. Accuracy Comparison

Compare readings from different models:
```bash
# Get last reading from each model
cat logs/water_readings.jsonl | jq -s 'group_by(.vision_model) | map({model: .[0].vision_model, reading: .[-1].total_reading})'
```

### 3. Model Migration Tracking

Track when you switched models:
```bash
# See model timeline
cat logs/water_readings.jsonl | jq -r '[.timestamp, .vision_model, .total_reading] | @tsv'
```

### 4. UI Display

When viewing readings in the UI, you can now see which model was used:
- Reading history shows model badge
- Model-specific filtering
- Cost tracking per model

## Testing

Test model tracking:
```bash
# Test Claude
python src/llm_reader.py /tmp/snapshot.jpg | jq '.vision_model, .vision_provider'

# Test Gemini
python src/local_vision_reader.py /tmp/snapshot.jpg --method gemini | jq '.vision_model, .vision_provider'

# Test Ollama
python src/local_vision_reader.py /tmp/snapshot.jpg --method ollama | jq '.vision_model, .vision_provider'
```

## Future Enhancements

1. **Model Selection in UI**
   - Add dropdown to select which model to use
   - Default to Gemini (free + accurate)
   - Fallback to Claude if Gemini fails

2. **A/B Testing**
   - Run multiple models on same image
   - Compare results
   - Flag discrepancies

3. **Cost Dashboard**
   - Show cost breakdown by model
   - Monthly/weekly usage stats
   - Recommend cost optimizations

4. **Auto-Fallback**
   - Try Gemini first (free)
   - Fall back to Claude if Gemini unavailable
   - Log which model succeeded

## Migration Guide

### For Existing Logs

Old readings without `vision_model` field:
```bash
# Add default model to old entries
cat logs/water_readings.jsonl | jq '. + {vision_model: "claude-sonnet-4-5-20250929", vision_provider: "anthropic"}' > logs/water_readings_migrated.jsonl
```

### For New Deployments

1. Model tracking is automatic - no configuration needed
2. All new readings include `vision_model` and `vision_provider`
3. Compatible with all reading methods (API, manual, automated)

## Branch

This feature was developed in: `experiment/local-vision-ml`

Recommendation: **Use Gemini 2.5 Flash as default** (free + accurate)

---

**Status:** ✅ Implemented and tested
**Compatibility:** All reading methods
**Performance Impact:** None (fields added to existing data structure)
