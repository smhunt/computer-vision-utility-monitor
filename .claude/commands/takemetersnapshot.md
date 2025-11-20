---
description: Take a snapshot from one of the configured meters and read the values
---

Take a snapshot from a configured meter and process it through the **COMPLETE PRODUCTION WORKFLOW** (exactly like the UI does).

**This command performs ALL steps:**
1. Capture image from camera MJPEG stream
2. Analyze with Claude Vision API (3-component format: white digits + black digit + dial)
3. Validate against previous readings
4. Archive snapshot with timestamp
5. Create metadata JSON file
6. Log to JSONL file (logs/{meter_type}_readings.jsonl)
7. Log to InfluxDB (if configured)

Perfect for development/testing without running the full daemon.

---

## Implementation

### Step 1: Load Configuration & Select Meter

Read `config/meters.yaml` to get configured meters.
- If 1 meter: auto-select it
- If multiple: show numbered list and ask user to select

### Step 2: Capture Snapshot from MJPEG Stream

Use this exact pattern (proven to work):
```bash
curl -s --max-time 15 "http://{user}:{pass}@{ip}/mjpeg" | head -c 2000000 > /tmp/meter_mjpeg_stream.raw && python3 << 'EOF'
with open('/tmp/meter_mjpeg_stream.raw', 'rb') as f:
    data = f.read()
start_idx = data.find(b'\xff\xd8')
end_idx = data.find(b'\xff\xd9', start_idx)
jpeg_frame = data[start_idx:end_idx + 2]
output_path = '/tmp/meter_snapshot_{meter_name}_capture.jpg'
with open(output_path, 'wb') as f:
    f.write(jpeg_frame)
print(f"✓ Extracted: {len(jpeg_frame)} bytes → {output_path}")
EOF
```

**IMPORTANT:** Display the captured image using Read tool so user can see what was captured.

### Step 3: Analyze with Vision API (Gemini + Claude fallback)

```bash
source .env && python3 << 'EOF'
import sys
import json
sys.path.insert(0, 'src')
from gemini_reader import read_meter

# Use Gemini (free + accurate) with Claude fallback
result = read_meter('/tmp/meter_snapshot_{meter_name}_capture.jpg', fallback_to_claude=True)
print(json.dumps(result, indent=2))

# Save result to temp file for use in later steps
with open('/tmp/meter_reading_result.json', 'w') as f:
    json.dump(result, f, indent=2)
EOF
```

Parse the JSON and display formatted output:
```
✅ Reading successful!

White Digits:    {digital_reading} m³
Black Digit:     {black_digit} → 0.{black_digit} m³
Red Dial:        {dial_reading:.3f} m³
────────────────────────────────────────
Total Reading:   {total_reading:.3f} m³
Confidence:      {confidence}

Notes: {notes}
```

### Step 4: Validate Against Previous Readings

```bash
python3 << 'EOF'
import sys
import json
from pathlib import Path
sys.path.insert(0, 'src')

meter_type = "{meter_type}"
current_reading = {total_reading}

# Check if log file exists
log_file = Path(f'logs/{meter_type}_readings.jsonl')

if log_file.exists():
    # Read recent readings
    recent = []
    with open(log_file, 'r') as f:
        lines = f.readlines()
        for line in lines[-5:]:  # Last 5 readings
            try:
                recent.append(json.loads(line))
            except:
                pass

    if recent:
        last_reading = recent[-1].get('total_reading', 0)
        print(f"\n📊 VALIDATION:")
        print(f"  Last reading:    {last_reading:.3f} m³")
        print(f"  Current reading: {current_reading:.3f} m³")

        if current_reading < last_reading:
            print(f"  ⚠️  WARNING: Reading DECREASED by {last_reading - current_reading:.3f} m³")
        elif current_reading > last_reading + 100:
            print(f"  ⚠️  WARNING: Large jump of {current_reading - last_reading:.2f} m³")
        else:
            print(f"  ✓ Valid: Increased by {current_reading - last_reading:.3f} m³")

        # Show last 3 readings for context
        print(f"\n  Recent history:")
        for i, r in enumerate(recent[-3:], 1):
            ts = r.get('timestamp', 'unknown')[:19]
            val = r.get('total_reading', 0)
            print(f"    {i}. {ts} → {val:.3f} m³")
    else:
        print("\nℹ️  No valid previous readings to validate against")
else:
    print("\nℹ️  No previous readings found (first reading for this meter)")
EOF
```

### Step 5: Archive Snapshot with Metadata

```bash
python3 << 'EOF'
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

meter_name = "{meter_name}"
meter_type = "{meter_type}"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Create archive directory
snapshot_dir = Path("logs/meter_snapshots") / meter_name
snapshot_dir.mkdir(parents=True, exist_ok=True)

# Archive snapshot
snapshot_path = snapshot_dir / f"{meter_name}_{timestamp}.jpg"
shutil.copy(f"/tmp/meter_snapshot_{meter_name}_capture.jpg", snapshot_path)

# Load the reading result
with open('/tmp/meter_reading_result.json', 'r') as f:
    reading = json.load(f)

# Create metadata JSON
metadata = {
    "snapshot": {
        "filename": snapshot_path.name,
        "timestamp": datetime.now().isoformat(),
        "path": str(snapshot_path)
    },
    "meter_reading": {
        "digital_reading": reading['digital_reading'],
        "black_digit": reading['black_digit'],
        "dial_reading": reading['dial_reading'],
        "total_reading": reading['total_reading'],
        "confidence": reading['confidence'],
        "notes": reading['notes']
    },
    "api_usage": reading.get('api_usage', {}),
    "camera": {
        "source_file": f"meter_snapshot_{meter_name}_capture.jpg",
        "model": "Wyze Cam V2 (Thingino)",
        "ip": "{camera_ip}"
    }
}

# Save metadata
metadata_path = snapshot_dir / f"{meter_name}_{timestamp}.json"
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"\n💾 ARCHIVED:")
print(f"  Snapshot: {snapshot_path}")
print(f"  Metadata: {metadata_path}")
print(f"  Size: {snapshot_path.stat().st_size / 1024:.1f} KB")
EOF
```

### Step 6: Log to JSONL File

```bash
python3 << 'EOF'
import sys
import json
from pathlib import Path
from datetime import datetime

meter_type = "{meter_type}"

# Load the reading result
with open('/tmp/meter_reading_result.json', 'r') as f:
    result = json.load(f)

# Prepare reading for log
reading = {
    "digital_reading": result['digital_reading'],
    "black_digit": result['black_digit'],
    "dial_reading": result['dial_reading'],
    "total_reading": result['total_reading'],
    "confidence": result['confidence'],
    "notes": result['notes'],
    "timestamp": datetime.now().isoformat(),
    "meter_type": meter_type,
    "api_usage": result.get('api_usage', {})
}

# Log to JSONL file
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"{meter_type}_readings.jsonl"

with open(log_file, 'a') as f:
    f.write(json.dumps(reading) + '\n')

print(f"\n📝 LOGGED TO:")
print(f"  JSONL: {log_file}")
print(f"  Entry: {reading['timestamp']}")

# Count total entries
with open(log_file, 'r') as f:
    total_entries = sum(1 for line in f if line.strip())
print(f"  Total readings: {total_entries}")
EOF
```

### Step 7: Log to InfluxDB (If Configured)

```bash
source .env && python3 << 'EOF'
import sys
import os
from datetime import datetime
sys.path.insert(0, 'src')

# Check if InfluxDB is configured
if os.getenv('INFLUXDB_TOKEN'):
    try:
        from influx_logger import MeterInfluxLogger
        import json

        # Load reading result
        with open('/tmp/meter_reading_result.json', 'r') as f:
            result = json.load(f)

        logger = MeterInfluxLogger(
            url=os.getenv('INFLUXDB_URL'),
            token=os.getenv('INFLUXDB_TOKEN'),
            org=os.getenv('INFLUXDB_ORG'),
            bucket=os.getenv('INFLUXDB_BUCKET')
        )

        logger.log_reading(
            meter_name="{meter_name}",
            total_reading=result['total_reading'],
            digital_reading=result['digital_reading'],
            dial_reading=result['dial_reading'],
            confidence=result['confidence'],
            timestamp=datetime.now()
        )

        print(f"  ✅ InfluxDB: {os.getenv('INFLUXDB_BUCKET')}/{meter_name}")
    except Exception as e:
        print(f"  ⚠️  InfluxDB logging failed: {e}")
else:
    print("  ℹ️  InfluxDB: Not configured (skipped)")
EOF
```

### Step 8: Show Final Summary

```bash
python3 << 'EOF'
import json
from datetime import datetime

# Load reading result
with open('/tmp/meter_reading_result.json', 'r') as f:
    result = json.load(f)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
meter_name = "{meter_name}"
meter_type = "{meter_type}"
camera_ip = "{camera_ip}"

# Check if API credits were used
api_usage = result.get('api_usage', {})
if api_usage.get('source') == 'claude-code-direct-analysis':
    api_credits_used = False
    api_info = "No API credits used (Claude Code direct analysis)"
elif api_usage.get('input_tokens', 0) > 0:
    api_credits_used = True
    api_info = f"{api_usage['input_tokens']} in / {api_usage['output_tokens']} out (Anthropic API credits used)"
else:
    api_credits_used = False
    api_info = "Unknown analysis method"

print("═══════════════════════════════════════════════════════")
print("✅ METER READING COMPLETE")
print("═══════════════════════════════════════════════════════")
print()
print(f"Meter:           {meter_name} ({meter_type})")
print(f"Camera:          {camera_ip}")
print(f"Timestamp:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
print("READING BREAKDOWN:")
print(f"  White Digits:  {result['digital_reading']} m³")
print(f"  Black Digit:   {result['black_digit']} → 0.{result['black_digit']} m³")
print(f"  Red Dial:      {result['dial_reading']:.3f} m³")
print("  ────────────────────────────────────────")
print(f"  TOTAL:         {result['total_reading']:.3f} m³")
print()
print(f"Confidence:      {result['confidence']}")
print()
if api_credits_used:
    print(f"💳 API Credits:  ✅ USED - {api_info}")
else:
    print(f"💳 API Credits:  ⭕ NOT USED - {api_info}")
print()
print("ARCHIVED FILES:")
print(f"  📸 Image:      logs/meter_snapshots/{meter_name}/{meter_name}_{timestamp}.jpg")
print(f"  📄 Metadata:   logs/meter_snapshots/{meter_name}/{meter_name}_{timestamp}.json")
print()
print("LOGGED TO:")
print(f"  📝 JSONL:      logs/{meter_type}_readings.jsonl")
print(f"  📊 InfluxDB:   utility_meters/{meter_name}")
print()
print("VIEW IN UI:")
print("  python meter_preview_ui.py")
print()
print("═══════════════════════════════════════════════════════")
EOF
```

---

## Error Handling

- **Camera connection fails**: Show clear error and suggest checking config/meters.yaml
- **Claude API fails**: Show error and verify ANTHROPIC_API_KEY in .env
  - If API credits are low/exhausted, Claude Code can analyze the image directly
  - Direct analysis uses Claude Code subscription (no Anthropic API credits)
  - Marked clearly in output: "No API credits used (Claude Code direct analysis)"
- **Validation warning**: Show warning but CONTINUE (don't block)
- **InfluxDB fails**: Show warning but CONTINUE (don't block)
- **Temperature unavailable**: Show info message and CONTINUE

## Implementation Notes

- Always `source .env` before Python commands that need API keys
- Use `sys.path.insert(0, 'src')` to import from src/ directory
- Display the captured image with Read tool for visual verification
- Format readings with 3 decimal places for cubic meters
- Use exact file paths: `/tmp/meter_snapshot_{meter_name}_capture.jpg`
- Save reading result to `/tmp/meter_reading_result.json` after Step 3 for use in later steps
- Create directories with `mkdir(parents=True, exist_ok=True)`
- Log files use meter_type: `logs/{meter_type}_readings.jsonl`
- Archive uses meter_name: `logs/meter_snapshots/{meter_name}/`
- **API Credit Tracking**: Command clearly reports whether Anthropic API credits were used
  - If using Claude API directly: Shows token usage (input/output)
  - If using Claude Code direct analysis: Shows "No API credits used"
- **Model Configuration**: Uses `claude-sonnet-4-5-20250929` (configured in `src/llm_reader.py`)
  - Requires Max tier Anthropic API subscription or sufficient credits
  - Update MODEL constant in `src/llm_reader.py` if using different model

## Key Differences from Old Command

The new command does EVERYTHING the production app does:
- ✅ Archives snapshots (old: just temp file)
- ✅ Validates readings (old: skipped)
- ✅ Logs to JSONL (old: skipped)
- ✅ Logs to InfluxDB (old: skipped)
- ✅ Creates metadata (old: skipped)
- ✅ Uses new 3-component format (old: 2-component)
- ✅ Proper error handling (old: basic)

This makes it perfect for development testing!
