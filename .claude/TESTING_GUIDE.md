# Dial Reading Fix - Testing Guide

Quick guide for testing the improved dial reading prompt.

---

## Prerequisites

```bash
# Ensure API key is set
source .env

# Or manually export
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Option 1: Test Single Image

```bash
# Test with a specific snapshot
python3 test_dial_reading.py logs/meter_snapshots/water_main/water_main_20251119_194417.jpg

# Expected output:
# ✅ READING SUCCESSFUL!
# ────────────────────────────────────────────────
# RESULTS:
# ────────────────────────────────────────────────
#   White Digits:        2271 m³
#   Black Digit:         2 → 0.2 m³
#   Dial Angle:          XX°
#   Dial Reading:        0.XXXX m³
#   ────────────────────────────────────────────────
#   TOTAL READING:       2271.XXX m³
#   ────────────────────────────────────────────────
#   Confidence:          HIGH/MEDIUM/LOW
#
# NOTES:
# ────────────────────────────────────────────────
# Red dial analysis:
#   - Dial number scale position: pointing at X.X
#   - Clock position: X o'clock
#   - Degrees: XX° (pointing DIRECTION)
#   - Verification: Hand is pointing DIRECTION ✓
```

### What to Look For

✅ **Good Signs:**
- Notes show step-by-step analysis
- Direction in notes matches angle (e.g., 90° says "RIGHT")
- Confidence is "high"
- No `dial_angle_warnings` in saved JSON

❌ **Bad Signs:**
- Notes don't show structured format
- Direction contradicts angle (e.g., 90° but notes say "down")
- Confidence downgraded to "medium"
- `dial_angle_warnings` present in JSON

---

## Option 2: Test Multiple Images

```bash
# Test all recent snapshots
for img in logs/meter_snapshots/water_main/water_main_2025*.jpg; do
    echo "Testing: $(basename $img)"
    python3 test_dial_reading.py "$img" | grep -E "(Dial Angle|TOTAL READING|Confidence)"
    echo "---"
done
```

---

## Option 3: Compare Before/After

```bash
# Analyze all readings in JSONL log
python3 compare_dial_readings.py

# This will show:
# - Statistical analysis of all dial angles
# - Validation warnings
# - Large angle jumps (suspicious changes)
# - Direction distribution
```

### What to Look For

✅ **Good Signs:**
- No validation warnings
- Angles consistent over time (small variation)
- Direction distribution matches expected usage pattern

❌ **Bad Signs:**
- Many validation warnings
- Large angle jumps (>45°) between consecutive readings
- All angles cluster in one direction (suggests systematic error)

---

## Option 4: Reprocess Existing Snapshot via UI

1. Start the web UI:
   ```bash
   python3 meter_preview_ui.py --host 127.0.0.1 --port 2500
   ```

2. Open browser: http://127.0.0.1:2500

3. Navigate to meter detail view

4. Click "Reprocess" button on any snapshot

5. Check the updated reading:
   - Click JSON button to see full details
   - Look for `dial_angle_degrees` and `dial_angle_warnings`
   - Compare to previous reading

---

## Option 5: Capture Fresh Reading

```bash
# Run complete workflow (capture + analyze)
python3 run_meter_reading.py

# Output will include dial_angle_degrees
```

---

## Interpreting Results

### Angle → Direction Mapping

| Angle Range | Direction | Clock Position |
|-------------|-----------|----------------|
| 0-45°       | UP        | 12-1 o'clock   |
| 45-135°     | RIGHT     | 3-4 o'clock    |
| 135-225°    | DOWN      | 6-7 o'clock    |
| 225-315°    | LEFT      | 9-10 o'clock   |
| 315-360°    | UP        | 11-12 o'clock  |

### Dial Scale → Angle Conversion

| Dial Position | Angle | Clock Position |
|---------------|-------|----------------|
| 0             | 0°    | 12 o'clock     |
| 2.5           | 90°   | 3 o'clock      |
| 5.0           | 180°  | 6 o'clock      |
| 7.5           | 270°  | 9 o'clock      |
| 10 (same as 0)| 360°/0° | 12 o'clock   |

### Acceptable Error Margins

- **Angle precision:** ±5-10° is acceptable
- **Reading precision:** ±0.001-0.003 m³ is acceptable
- **10° error** = 0.0028 m³ error (negligible for most purposes)

---

## Troubleshooting

### Issue: Notes don't show step-by-step format

**Cause:** Old prompt still being used
**Fix:** Verify `src/llm_reader.py` has the updated prompt (check lines 81-146)

### Issue: Many validation warnings

**Cause:** Claude still making angle errors
**Fix:**
1. Check notes to see where reasoning fails
2. Consider hybrid OpenCV approach
3. Review image quality (blur, lighting)

### Issue: Angles all cluster in one direction

**Cause:** Systematic bias in angle estimation
**Fix:**
1. Verify dial orientation (is "0" really at top?)
2. Check for camera rotation/perspective issues
3. Consider adding reference images to prompt

### Issue: API calls failing

**Cause:** API key not set or invalid
**Fix:**
```bash
# Check if key is set
echo $ANTHROPIC_API_KEY

# Source .env file
source .env

# Or export manually
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Next Steps

### If Accuracy Improves (>80% correct)

1. ✅ Mark as solved
2. Monitor readings over time
3. Document acceptable error margins
4. Update main README

### If Accuracy Still Poor (<80% correct)

1. Analyze failure patterns:
   ```bash
   python3 compare_dial_readings.py | grep "⚠️"
   ```

2. Consider hybrid approach:
   - Use OpenCV for dial angle detection
   - Keep LLM for digit reading
   - See `.claude/DIAL_READING_FIX_REPORT.md` Section: "Alternative Approaches"

3. Implement few-shot learning:
   - Capture reference images at known angles
   - Include in prompt as examples

4. Accept lower precision:
   - Round to nearest 0.01 m³
   - ±20° error becomes acceptable

---

## Files Reference

- `src/llm_reader.py` - Main LLM reader with improved prompt
- `test_dial_reading.py` - Test single image
- `compare_dial_readings.py` - Analyze all readings
- `.claude/DIAL_READING_FIX_REPORT.md` - Full technical report
- `.claude/DIAL_READING_CHALLENGE.md` - Original problem description

---

## Support

If issues persist, review:
1. Image quality (logs/meter_snapshots/water_main/*.jpg)
2. Camera settings (meter_preview_ui.py settings page)
3. Prompt version (check git diff src/llm_reader.py)
4. API model version (should be claude-sonnet-4-5-20250929)

---

**Last Updated:** 2025-11-19
**Status:** Ready for testing
