# Dial Reading Challenge - Vision AI Accuracy Issue

## Current Status: ✅ FIX IMPLEMENTED - Ready for Testing

**Update 2025-11-19:** A comprehensive fix has been implemented using a 6-step visual reasoning approach. See:
- `.claude/DIAL_READING_FIX_SUMMARY.md` - Quick overview
- `.claude/DIAL_READING_FIX_REPORT.md` - Full technical details
- `.claude/TESTING_GUIDE.md` - How to test

---

## Original Status: BLOCKED - Vision Model Inaccuracy

### What's Working ✅
- UI displays historical meter readings with dial angles
- Reprocess button allows re-analyzing images without page reload
- JSON button displays full reading data in popup modal
- Dial formula is correct: `reading = angle_degrees / 3600`
- White digits (5 digits) reading: **ACCURATE**
- Black digit (tenths) reading: **ACCURATE**
- Server running on port 2500

### Critical Issue ❌
**Red dial hand angle detection is WRONG**

**Example:**
- Image shows: Hand pointing RIGHT (approximately 90°, or 3 o'clock)
- Claude reports: 180° (pointing DOWN, or 6 o'clock)
- Error: ~90° off, consistently wrong direction

**Sample Image:** `logs/meter_snapshots/water_main/water_main_20251119_194417.jpg`
- Actual: Hand pointing RIGHT
- Claude sees: "180° (the red hand is pointing at 180 degrees, straight down)"

### The Dial System

**Badger Meter Absolute Digital - Red Sweep Hand:**
- One full rotation (360°) = 0.10 m³
- Dial scale: 0-10 marked around edge
- Reading formula: `cubic_meters = angle_degrees / 3600`

**Examples:**
- 0° (12 o'clock) = 0.00 m³
- 90° (3 o'clock) = 0.025 m³
- 180° (6 o'clock) = 0.05 m³
- 270° (9 o'clock) = 0.075 m³
- 360° (full rotation) = 0.10 m³

### Prompt Attempts Made

**Attempt 1:** Clock positions (12 o'clock, 3 o'clock, etc.)
- Result: Confused, reported "5 o'clock" when hand at 2-3 o'clock

**Attempt 2:** Directional descriptions (UP, DOWN, LEFT, RIGHT)
- Result: Still inaccurate

**Attempt 3:** Angle in degrees (0°=UP, 90°=RIGHT, 180°=DOWN, 270°=LEFT)
- Result: Consistently wrong by ~90-180°

**Attempt 4:** Emphasis on "red hand is ONLY red element"
- Result: No improvement

**Attempt 5:** Ask to identify which edge the pointed tip is nearest to
- Result: Still reports wrong angle

### Why This Is Hard

**Hypotheses:**
1. **Image orientation** - Claude might be interpreting image upside-down or rotated
2. **Hand ambiguity** - Might be reading wrong end of the hand (base vs tip)
3. **Vision model limitation** - Small object, subtle angle differences
4. **Context confusion** - Multiple circular elements on meter face
5. **Perspective distortion** - Camera angle affects apparent hand position

### What to Research

**Computer Vision Approaches for Analog Gauge Reading:**
1. **Line detection algorithms** (Hough Transform)
   - Detect the red hand as a line segment
   - Calculate angle from center to tip

2. **Color segmentation**
   - Isolate red pixels
   - Find centroid and orientation

3. **Template matching**
   - Create reference images at known angles
   - Match current image to closest template

4. **Machine learning**
   - Train model on labeled gauge images
   - Direct angle regression

5. **Image preprocessing**
   - Perspective correction
   - Enhanced contrast for red channel
   - Rotation normalization

**Alternative: Traditional CV Instead of LLM Vision?**
- OpenCV for hand detection
- Hough Line Transform for angle
- LLM only for digital digits
- Hybrid approach: CV for dial, LLM for digits

### Files Modified (Ready to Commit)

```
meter_preview_ui.py - Added reprocess endpoint, updated routes
run_meter_reading.py - Added dial_angle_degrees output, size field
src/llm_reader.py - Enhanced prompt with angle-based dial reading
templates/meter.html - JSON button fix, dial angle display with clock equivalent
```

### Next Steps for Troubleshooting

**Immediate Actions:**
1. Test with manually rotated images to see if angle detection improves
2. Try different Claude models (Opus vs Sonnet)
3. Crop image to only dial area before sending to Claude
4. Add reference markers in prompt (e.g., show example dial images)

**Alternative Solutions:**
1. Implement OpenCV-based dial reading
2. Use traditional computer vision for angle detection
3. Create a calibration system with known hand positions
4. Accept lower precision and round to nearest major tick

### Environment Info

- Model: claude-sonnet-4-5-20250929
- Server: http://127.0.0.1:2500
- Config: config/meters.yaml
- Logs: logs/water_readings.jsonl
- Snapshots: logs/meter_snapshots/water_main/

### How to Resume This Work

1. **Start server:** `python3 meter_preview_ui.py --host 127.0.0.1 --port 2500`
2. **Open dashboard:** http://127.0.0.1:2500
3. **Test reprocess:** Click "🔄 Reprocess" on any image
4. **View JSON:** Click blue "{ }" button to see full reading data
5. **Check dial angle:** Look for "🧭 Dial: X° (~Y o'clock)" under reading

### Research Resources to Explore

- OpenCV gauge reader examples
- Hough Transform for line detection
- Analog meter reading with computer vision
- Perspective transformation for camera correction
- Red color channel isolation techniques

---

**Bottom Line:** The digits are reading perfectly, but the red dial hand angle detection is fundamentally broken. This needs either:
- A completely different prompting approach
- Traditional computer vision instead of LLM vision
- Manual calibration/correction system
