# Advanced Features Examples

This directory contains example scripts demonstrating the advanced features of the computer vision utility monitor.

## Demo Script

### `demo_advanced_features.py`

A comprehensive demonstration of all five advanced feature areas:

1. **Snapshot and ML Optimization** - Clean and ML-optimized snapshot retrieval
2. **Push Data Capabilities** - Device registration and data pushing
3. **QR-Based Device Onboarding** - QR code generation and device binding
4. **Geolocation Integration** - GPS coordinate registration and proximity search
5. **Sound Feedback System** - Audio feedback triggers and text-to-speech

### Running the Demo

1. **Start the server:**
   ```bash
   python meter_preview_ui.py --port 2500
   ```

2. **Run the demo script:**
   ```bash
   python examples/demo_advanced_features.py
   ```

3. **Follow the on-screen prompts**

### Expected Output

The demo will:
- ✓ Connect to the running server
- ✓ Test all 5 feature areas
- ✓ Display success/error messages for each operation
- ✓ Generate sample files in `/tmp/`:
  - `clean_snapshot.jpg` - Clean snapshot for viewing
  - `ml_snapshot.png` - ML-optimized snapshot
  - `device_qr_code.png` - QR code for device binding

### Demo Output Example

```
************************************************************
* Advanced Features Demo
* Computer Vision Utility Monitor
************************************************************

============================================================
DEMO 1: Snapshot and ML Optimization
============================================================

1. Getting clean snapshot for dashboard viewing...
   ✓ Clean snapshot retrieved successfully
   → Saved to: /tmp/clean_snapshot.jpg

2. Getting ML-optimized snapshot for processing...
   ✓ ML-optimized snapshot retrieved successfully
   → Saved to: /tmp/ml_snapshot.png

============================================================
DEMO 2: Push Data Capabilities
============================================================

1. Registering camera device...
   ✓ Device registered successfully
   → Device ID: demo_camera_001
   → Auth Token: abc123...
   → Push Endpoint: /api/push/data/demo_camera_001

2. Pushing meter reading data...
   ✓ Data pushed successfully
   → Timestamp: 2025-12-18T12:00:00

...and so on for all 5 demos
```

## API Examples

### Python Examples

```python
import requests

# Example 1: Get clean snapshot
response = requests.get("http://localhost:2500/api/snapshot/clean/water")
with open("snapshot.jpg", "wb") as f:
    f.write(response.content)

# Example 2: Register device
device_data = {
    "device_id": "camera_001",
    "camera_ip": "192.168.1.100",
    "meter_type": "water"
}
response = requests.post("http://localhost:2500/api/device/register", json=device_data)
print(response.json())

# Example 3: Generate QR code
qr_data = {
    "user_id": "user_001",
    "meter_type": "water"
}
response = requests.post("http://localhost:2500/api/qr/generate", json=qr_data)
qr_code = response.json()
```

### cURL Examples

```bash
# Get clean snapshot
curl http://localhost:2500/api/snapshot/clean/water > snapshot.jpg

# Register device
curl -X POST http://localhost:2500/api/device/register \
  -H "Content-Type: application/json" \
  -d '{"device_id":"cam001","camera_ip":"192.168.1.100","meter_type":"water"}'

# Generate QR code
curl -X POST http://localhost:2500/api/qr/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user001","meter_type":"water"}'

# Get nearby devices
curl "http://localhost:2500/api/devices/nearby?latitude=43.6532&longitude=-79.3832&radius_km=5"

# Trigger audio feedback
curl -X POST http://localhost:2500/api/audio/trigger \
  -H "Content-Type: application/json" \
  -d '{"event_type":"connected","device_id":"cam001"}'
```

## Integration Examples

### Device-Side Integration (Camera)

Example code for a camera to push data to the backend:

```python
import requests
import base64
from datetime import datetime

# Device configuration
DEVICE_ID = "camera_001"
AUTH_TOKEN = "your_secure_token_here"
SERVER_URL = "http://your-server:2500"

def push_meter_reading(image_path, reading, confidence):
    """Push meter reading to backend"""
    
    # Encode image
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode()
    
    # Prepare data
    data = {
        "auth_token": AUTH_TOKEN,
        "timestamp": datetime.now().isoformat(),
        "image_base64": image_base64,
        "meter_reading": reading,
        "confidence": confidence,
        "metadata": {"temperature": 20.5}
    }
    
    # Push to server
    response = requests.post(
        f"{SERVER_URL}/api/push/data/{DEVICE_ID}",
        json=data
    )
    
    return response.json()

# Use it
result = push_meter_reading("meter.jpg", 123.45, 0.95)
print(result)
```

### Mobile App Integration (QR Onboarding)

Example code for a mobile app to handle QR onboarding:

```python
import requests
import qrcode
from PIL import Image

def onboard_device_via_qr(server_url, user_id, meter_type):
    """Complete QR onboarding workflow"""
    
    # Step 1: Get QR code from server
    response = requests.post(
        f"{server_url}/api/qr/generate",
        json={
            "user_id": user_id,
            "meter_type": meter_type,
            "location": "basement"
        }
    )
    qr_data = response.json()
    
    # Step 2: Display QR code to user
    # (In mobile app, show on screen for scanning)
    
    # Step 3: Device scans QR and registers
    # (This happens on the device)
    registration = requests.post(
        f"{server_url}/api/qr/register",
        json={
            "binding_token": qr_data['binding_token'],
            "device_id": "scanned_device_id",
            "camera_ip": "192.168.1.100"
        }
    )
    
    return registration.json()
```

## Troubleshooting

### Server Not Running
```
✗ Error: Cannot connect to server
  Please start the server first:
  python meter_preview_ui.py --port 2500
```
**Solution:** Start the Flask server before running demos.

### Snapshot Not Found
```
✗ Error: {'status': 'error', 'message': 'No snapshots found for water'}
```
**Solution:** Capture a meter reading first:
```bash
python multi_meter_monitor.py --run-once
```

### Permission Denied
```
PermissionError: [Errno 13] Permission denied: '/tmp/snapshot.jpg'
```
**Solution:** Check write permissions on `/tmp/` or change output directory.

## Additional Resources

- **Full Documentation:** [ADVANCED_FEATURES_README.md](../ADVANCED_FEATURES_README.md)
- **API Implementation:** [src/advanced_features_api.py](../src/advanced_features_api.py)
- **Test Suite:** [tests/test_advanced_features.py](../tests/test_advanced_features.py)

## Contributing

To add new examples:

1. Create a new Python script in this directory
2. Follow the existing demo structure
3. Add documentation to this README
4. Test thoroughly before committing

---

**Last Updated:** December 18, 2025  
**Maintainer:** Project Team
