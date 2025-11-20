# Local Vision & ML Approaches for Meter Reading

This experimental branch explores **local, offline** computer vision and machine learning approaches for reading analog water meters, as an alternative to cloud-based Vision API services.

## 🎯 Motivation

- **Privacy**: All processing happens locally, no images sent to external services
- **Cost**: No API costs after initial setup
- **Speed**: Potentially faster for batch processing (no network latency)
- **Offline**: Works without internet connection
- **Learning**: Explore different CV/ML techniques

## 🛠️ Approaches Implemented

### 1. OpenCV-based Reader (`opencv`)

**Pure computer vision approach using OpenCV**

**How it works:**
- Preprocesses image with CLAHE and denoising
- Detects odometer region using contour analysis
- Segments individual digits using bounding boxes
- Finds dial using Hough Circle Detection
- Detects red needle using color filtering (HSV)
- Calculates needle angle using line detection

**Pros:**
- No external dependencies beyond OpenCV
- Fast execution
- Good for needle/dial detection

**Cons:**
- Digit recognition not as accurate without trained model
- Sensitive to lighting and angle variations
- Requires manual tuning of parameters

**Best for:** Needle angle detection, proof-of-concept

### 2. EasyOCR Reader (`easyocr`)

**OCR-based approach using EasyOCR**

**How it works:**
- Uses EasyOCR to detect and recognize all text in image
- Filters for numeric strings (odometer reading)
- Falls back to OpenCV for needle detection
- Combines results

**Pros:**
- Excellent digit recognition (trained on diverse datasets)
- Works well with various fonts and orientations
- Fully local (models downloaded once)
- No API keys needed

**Cons:**
- Larger initial download (~100MB for models)
- Slower than pure OpenCV (but still fast)
- May detect unwanted text (serial numbers, etc.)

**Best for:** Odometer digit recognition

### 3. Hybrid Reader (`hybrid`) - **RECOMMENDED**

**Combines best of both approaches**

**How it works:**
- Uses EasyOCR for odometer digits (if available)
- Uses OpenCV for needle detection
- Cross-validates results
- Falls back gracefully if components unavailable

**Pros:**
- Best accuracy overall
- Robust to variations
- Graceful degradation

**Cons:**
- Requires all dependencies
- Slightly slower than individual methods

**Best for:** Production use with local processing

## 📦 Installation

### Quick Setup (Recommended)

```bash
# Install local vision dependencies
pip install -r requirements-local-vision.txt
```

### Minimal Setup (OpenCV only)

```bash
# Just OpenCV - smallest footprint
pip install opencv-python numpy
```

### Full Setup (All features)

```bash
# All dependencies including optional ones
pip install -r requirements-local-vision.txt
```

**Note:** EasyOCR will download models (~100MB) on first use.

## 🚀 Usage

### Basic Usage

```bash
# Use hybrid approach (recommended)
python src/local_vision_reader.py path/to/meter/image.jpg

# Specify method
python src/local_vision_reader.py path/to/meter/image.jpg opencv
python src/local_vision_reader.py path/to/meter/image.jpg easyocr
python src/local_vision_reader.py path/to/meter/image.jpg hybrid
```

### Python API

```python
from src.local_vision_reader import read_meter_locally

# Read meter with hybrid approach
result = read_meter_locally("meter.jpg", method="hybrid", debug=True)

print(f"Total Reading: {result['total_reading']} m³")
print(f"Confidence: {result['confidence']}")
print(f"Method: {result['method']}")
```

### Compare Methods

Compare all methods side-by-side:

```bash
# Compare all available methods
python compare_reading_methods.py path/to/meter/image.jpg

# Compare specific methods
python compare_reading_methods.py path/to/meter/image.jpg --methods api hybrid

# Save results to JSON
python compare_reading_methods.py path/to/meter/image.jpg --output results.json
```

## 🔬 Experimental Features

### Template-based Digit Recognition

Future enhancement: Train custom digit templates from known meter readings.

```python
# Not yet implemented
from src.local_vision_reader import train_digit_templates

templates = train_digit_templates(training_images_dir)
reader.use_templates(templates)
```

### Deep Learning Models

Future enhancement: Use lightweight CNN for digit recognition.

Options being explored:
- **MNIST-pretrained models** (good baseline)
- **Custom CNN** trained on meter digits
- **ONNX models** (cross-platform)
- **TensorFlow Lite** (mobile/edge deployment)

### Perspective Correction

Future enhancement: Automatically correct camera angle distortion.

## 📊 Performance Comparison

Based on initial testing:

| Method | Speed | Accuracy | Dependencies | Offline |
|--------|-------|----------|--------------|---------|
| Claude API | ~2-3s | ⭐⭐⭐⭐⭐ | Minimal | ❌ |
| OpenCV | ~0.5s | ⭐⭐⭐ | Small | ✅ |
| EasyOCR | ~1-2s | ⭐⭐⭐⭐ | Medium | ✅ |
| Hybrid | ~1-2s | ⭐⭐⭐⭐ | Medium | ✅ |

**Notes:**
- API accuracy is best for complex/tilted images
- Local methods improve with parameter tuning
- Speed can vary based on hardware

## 🐛 Debug Mode

Enable debug mode to save intermediate processing images:

```bash
python src/local_vision_reader.py meter.jpg hybrid
```

Debug images saved to `debug_images/`:
- `01_preprocessed.jpg` - Grayscale + enhanced
- `02_odometer_roi.jpg` - Extracted odometer region
- `03_dial_roi.jpg` - Extracted dial region

## 🔧 Configuration & Tuning

### Adjusting Detection Parameters

Edit [src/local_vision_reader.py](src/local_vision_reader.py) to tune:

```python
# Hough Circle parameters (dial detection)
circles = cv2.HoughCircles(
    blurred, cv2.HOUGH_GRADIENT,
    dp=1,           # Resolution ratio
    minDist=50,     # Min distance between circles
    param1=50,      # Canny edge threshold
    param2=30,      # Accumulator threshold
    minRadius=20,   # Minimum circle radius
    maxRadius=100   # Maximum circle radius
)

# Red color detection (needle)
lower_red1 = np.array([0, 100, 100])    # Lower HSV bound
upper_red1 = np.array([10, 255, 255])   # Upper HSV bound
```

### Training Custom Models

Future: Document how to train custom digit recognition models.

## 🧪 Testing & Validation

### Run Tests

```bash
# Test on sample images
python compare_reading_methods.py test_images/meter1.jpg
python compare_reading_methods.py test_images/meter2.jpg

# Batch test multiple images
for img in test_images/*.jpg; do
    python compare_reading_methods.py "$img" --output "results/$(basename $img .jpg).json"
done
```

### Validate Accuracy

Compare with known ground truth:

```bash
# Compare with manually verified readings
python validate_readings.py test_images/ ground_truth.json
```

## 🚧 Known Limitations

### Current Limitations

1. **Digit Recognition**: OpenCV digit recognition is basic - needs improvement
2. **Perspective Distortion**: Struggles with highly angled images
3. **Glare/Reflections**: Can confuse needle detection
4. **Font Variations**: OCR may misread unusual digit fonts

### Workarounds

- Use hybrid approach for best results
- Ensure good lighting when capturing images
- Try to minimize glare on meter face
- Capture image as straight-on as possible

## 🔮 Future Enhancements

### Short-term
- [ ] Implement template matching for digit recognition
- [ ] Add perspective correction
- [ ] Improve needle angle accuracy
- [ ] Add calibration mode

### Medium-term
- [ ] Train custom lightweight CNN for digits
- [ ] Add support for different meter types
- [ ] Implement multi-frame averaging
- [ ] Add confidence scoring improvements

### Long-term
- [ ] Real-time video processing
- [ ] Mobile/edge deployment (TFLite)
- [ ] Auto-calibration from historical readings
- [ ] Anomaly detection

## 📚 References

- **OpenCV Documentation**: https://docs.opencv.org/
- **EasyOCR**: https://github.com/JaidedAI/EasyOCR
- **Hough Transform**: https://en.wikipedia.org/wiki/Hough_transform
- **MNIST Dataset**: http://yann.lecun.com/exdb/mnist/

## 🤝 Contributing

This is an experimental branch. Feel free to:
- Test different approaches
- Tune parameters
- Add new methods
- Report issues

## 📄 License

Same as main project.

---

**Branch**: `experiment/local-vision-ml`
**Status**: 🧪 Experimental
**Maintained**: Yes
