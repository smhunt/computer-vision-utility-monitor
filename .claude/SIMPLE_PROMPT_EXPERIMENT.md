# Simple Prompt Experiment - GPT-4o-Mini Vision

This branch (`experiment/gpt4o-mini-vision`) includes an alternate prompt format optimized for simpler vision models like GPT-4o-mini.

## What's Different?

### Detailed Prompt (Default - Main Branch)
- 6-step visual reasoning approach
- Orientation checks and validation
- Strict component-by-component analysis
- Returns: `digital_reading`, `black_digit`, `dial_reading`, `dial_angle_degrees`
- Best for: Claude Sonnet 4.5, complex analysis needs

### Simple Prompt (This Branch)
- Odometer-based reading approach
- Simpler, more direct instructions
- Returns: `odometer_value`, `dial_value`, `needle_angle_degrees`
- Best for: GPT-4o-mini, cost optimization, faster inference

## How to Use

### Option 1: Environment Variable

Set the prompt format in your `.env` file:

```bash
# Use simple prompt format
METER_READER_PROMPT=simple

# Use detailed prompt format (default)
METER_READER_PROMPT=detailed
```

### Option 2: Function Parameter

```python
from llm_reader import read_meter_with_claude

# Use simple format
result = read_meter_with_claude(
    'path/to/image.jpg',
    prompt_format='simple'
)

# Use detailed format (default)
result = read_meter_with_claude(
    'path/to/image.jpg',
    prompt_format='detailed'
)
```

### Option 3: Command Line Testing

```bash
# Test with simple prompt
METER_READER_PROMPT=simple python3 test_dial_reading.py path/to/image.jpg

# Test with detailed prompt
METER_READER_PROMPT=detailed python3 test_dial_reading.py path/to/image.jpg
```

## Response Format Conversion

The simple format response is automatically converted to the standard format:

**Simple Format Input:**
```json
{
  "odometer_value": 2271.3,
  "dial_value": 0.07,
  "total_reading": 2271.37,
  "needle_angle_degrees": 252,
  "confidence": 0.85,
  "notes": "Clear reading, slight glare on dial"
}
```

**Converted to Standard Format:**
```json
{
  "digital_reading": 2271,
  "black_digit": 3,
  "dial_reading": 0.07,
  "dial_angle_degrees": 252,
  "total_reading": 2271.37,
  "confidence": "high",
  "confidence_numeric": 0.85,
  "notes": "Clear reading, slight glare on dial",
  "format": "simple"
}
```

## Testing Strategy

### 1. Baseline Comparison

Run both prompts on the same images:

```bash
# Detailed prompt
python3 test_dial_reading.py logs/meter_snapshots/water_main/*.jpg > detailed_results.txt

# Simple prompt
METER_READER_PROMPT=simple python3 test_dial_reading.py logs/meter_snapshots/water_main/*.jpg > simple_results.txt

# Compare results
diff detailed_results.txt simple_results.txt
```

### 2. Live Testing

```bash
# Test with simple prompt
METER_READER_PROMPT=simple /takemetersnapshot

# Check the confidence and notes
cat /tmp/meter_reading_result.json | jq '.confidence, .notes, .format'
```

### 3. Accuracy Analysis

```bash
# Analyze readings with simple prompt
METER_READER_PROMPT=simple python3 compare_dial_readings.py
```

## Expected Differences

| Aspect | Detailed Prompt | Simple Prompt |
|--------|----------------|---------------|
| Token usage | ~5500 input tokens | ~800 input tokens |
| Response format | Structured components | Odometer + dial |
| Validation | Built-in angle validation | Basic sanity checks |
| Notes detail | Step-by-step reasoning | Brief explanation |
| Confidence format | high/medium/low | 0.0-1.0 (converted) |
| Best for | High accuracy needs | Cost/speed optimization |

## When to Use Each

### Use Detailed Prompt When:
- Accuracy is critical
- You want detailed reasoning/debugging
- Working with challenging images
- Need angle validation

### Use Simple Prompt When:
- Cost optimization is important
- Using faster/cheaper models (GPT-4o-mini)
- Images are generally clear
- Simple odometer reading is sufficient

## Switching Back to Main Branch

```bash
# Save any experiments
git add -A
git commit -m "experiment: test simple prompt results"

# Switch back to main
git checkout main

# Or merge if successful
git checkout main
git merge experiment/gpt4o-mini-vision
```

## Notes

- Both formats output the same standard structure
- The `format` field indicates which was used
- Existing code (UI, logging, etc.) works with both
- Simple format is tagged with `"format": "simple"` for tracking

## Experimentation Ideas

1. **A/B Testing**: Run both prompts on same images, compare accuracy
2. **Cost Analysis**: Track token usage differences
3. **Model Comparison**: Try with different vision models
4. **Hybrid Approach**: Use simple for initial reading, detailed for validation
5. **Confidence Thresholds**: Compare confidence calibration between formats
