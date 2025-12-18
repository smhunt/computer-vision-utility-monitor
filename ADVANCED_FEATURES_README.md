# Advanced Features - Computer Vision Utility Monitor

## Overview

This document describes the advanced features added to the computer vision utility monitor system. These features enhance device setup, data processing, and user experience for Wyze-based cameras.

## Features

### 1. Snapshot and ML Optimization

Provides two types of snapshot outputs optimized for different use cases:

#### Clean Snapshots (Dashboard Viewing)
- **Endpoint:** `GET /api/snapshot/clean/<meter_type>`
- **Purpose:** Human-readable snapshots for dashboard viewing
- **Format:** JPEG with high quality (95%)
- **Optimizations:** RGB conversion, orientation correction, display-friendly enhancements

**Example Usage:**
```bash
curl http://localhost:2500/api/snapshot/clean/water > clean_snapshot.jpg
```

#### ML-Optimized Snapshots
- **Endpoint:** `GET /api/snapshot/ml-optimized/<meter_type>`
- **Purpose:** Raw outputs optimized for machine learning processing
- **Format:** PNG (lossless)
- **Optimizations:** High contrast, grayscale option, no compression artifacts

**Example Usage:**
```bash
curl http://localhost:2500/api/snapshot/ml-optimized/water > ml_snapshot.png
```

---

### 2. Push Data Capabilities

Enables cameras to actively push their data payloads to the backend directly.

#### Device Registration
- **Endpoint:** `POST /api/device/register`
- **Purpose:** Register a camera device for push capabilities
- **Features:** Secure authentication tokens, NAT/router resilience

**Request Body:**
```json
{
  "device_id": "camera_001",
  "camera_ip": "192.168.1.100",
  "meter_type": "water",
  "location": "basement"
}
```

**Response:**
```json
{
  "status": "success",
  "device_id": "camera_001",
  "auth_token": "secure_token_here",
  "push_endpoint": "/api/push/data/camera_001",
  "push_method": "POST"
}
```

#### Push Data
- **Endpoint:** `POST /api/push/data/<device_id>`
- **Purpose:** Receive pushed data from registered devices

**Request Body:**
```json
{
  "auth_token": "secure_token_here",
  "timestamp": "2025-12-18T12:00:00",
  "image_base64": "base64_encoded_image_data",
  "meter_reading": 123.45,
  "confidence": 0.95,
  "metadata": {}
}
```

**Network Resilience:**
- Devices behind NAT/routers can push data outbound
- No need for port forwarding or complex network configuration
- Secure token-based authentication

---

### 3. QR-Based Device Onboarding

Simplifies device setup with QR code scanning.

#### Generate QR Code
- **Endpoint:** `POST /api/qr/generate`
- **Purpose:** Create QR code for device binding

**Request Body:**
```json
{
  "user_id": "user_123",
  "meter_type": "water",
  "location": "basement"
}
```

**Response:**
```json
{
  "status": "success",
  "binding_token": "unique_token",
  "qr_code_image": "base64_encoded_qr_image",
  "qr_data": {
    "binding_token": "unique_token",
    "user_id": "user_123",
    "meter_type": "water",
    "registration_endpoint": "/api/device/register",
    "expires_at": "2025-12-19T12:00:00"
  },
  "expires_at": "2025-12-19T12:00:00"
}
```

#### Register with QR Code
- **Endpoint:** `POST /api/qr/register`
- **Purpose:** Register device using scanned QR code

**Request Body:**
```json
{
  "binding_token": "scanned_from_qr",
  "device_id": "camera_001",
  "camera_ip": "192.168.1.100"
}
```

**Security Features:**
- QR codes expire after 24 hours
- One-time use only (prevents replay attacks)
- Secure binding to user account

---

### 4. Geolocation Integration

Ties devices to GPS coordinates for location-aware features.

#### Register Device Location
- **Endpoint:** `POST /api/device/location`
- **Purpose:** Register device geolocation during onboarding

**Request Body:**
```json
{
  "device_id": "camera_001",
  "latitude": 43.6532,
  "longitude": -79.3832,
  "accuracy": 10.0,
  "altitude": 100.0,
  "source": "mobile_gps"
}
```

#### Find Nearby Devices
- **Endpoint:** `GET /api/devices/nearby`
- **Purpose:** Get devices near a specific location

**Query Parameters:**
- `latitude`: Center latitude
- `longitude`: Center longitude
- `radius_km`: Search radius in kilometers (default: 10)

**Example Usage:**
```bash
curl "http://localhost:2500/api/devices/nearby?latitude=43.6532&longitude=-79.3832&radius_km=5"
```

**Use Cases:**
- Location-specific dashboards
- Proximity-based notifications
- Geographic analytics
- Multi-site management

---

### 5. Sound Feedback System

Provides audible signals for key events and setup feedback.

#### Get Audio Feedback
- **Endpoint:** `GET /api/audio/feedback/<event_type>`
- **Purpose:** Get audio file for specific event
- **Event Types:** `connected`, `error`, `success`, `reading_complete`

**Example Usage:**
```bash
curl http://localhost:2500/api/audio/feedback/connected > connected.mp3
```

#### Trigger Audio Feedback
- **Endpoint:** `POST /api/audio/trigger`
- **Purpose:** Trigger audio feedback and get notification

**Request Body:**
```json
{
  "event_type": "connected",
  "device_id": "camera_001"
}
```

**Response:**
```json
{
  "status": "success",
  "event_type": "connected",
  "text_message": "Connected. Welcome to the Future!",
  "audio_url": "/api/audio/feedback/connected",
  "message": "Audio feedback triggered"
}
```

**Audio Messages:**
- **connected:** "Connected. Welcome to the Future!"
- **error:** "Error occurred. Please check the system."
- **success:** "Operation successful."
- **reading_complete:** "Meter reading complete."

**Fallback:** If audio files are not available, the API returns text messages for text-to-speech conversion.

---

## Integration

The advanced features are automatically registered when running the meter preview UI:

```bash
python meter_preview_ui.py --port 2500
```

You should see:
```
✓ Advanced features API routes registered
  - Snapshot and ML Optimization: /api/snapshot/...
  - Push Data: /api/device/register, /api/push/data/...
  - QR Onboarding: /api/qr/...
  - Geolocation: /api/device/location, /api/devices/nearby
  - Sound Feedback: /api/audio/...
```

## Testing

Run the comprehensive test suite:

```bash
python -m unittest tests.test_advanced_features -v
```

All 18 tests should pass:
- 3 tests for Snapshot Optimization
- 4 tests for Push Data Capabilities
- 4 tests for QR Onboarding
- 3 tests for Geolocation
- 4 tests for Sound Feedback

## Data Storage

### Device Registry
- **Location:** `logs/device_registry.json`
- **Contents:** Device registrations, QR codes, and metadata
- **Format:** JSON with devices, qr_codes, and pending_registrations

### Push Reading Logs
- **Location:** `logs/<meter_type>_push_readings.jsonl`
- **Format:** JSONL (one JSON object per line)
- **Contents:** Pushed meter readings with timestamps and metadata

### Audio Event Logs
- **Location:** `logs/audio_feedback_events.jsonl`
- **Format:** JSONL
- **Contents:** Audio feedback events with timestamps

## Security Considerations

1. **Authentication Tokens:** All push data requires secure tokens
2. **QR Code Expiration:** QR codes expire after 24 hours
3. **One-Time Use:** QR codes can only be used once
4. **Device Verification:** Push data requires valid device_id and auth_token
5. **HTTPS Recommended:** Use HTTPS in production for encrypted communication

## Future Enhancements

1. **Audio Files:** Add actual MP3 files for audio feedback
2. **Database Integration:** Store device registry in PostgreSQL
3. **Webhooks:** Add webhook notifications for device events
4. **Mobile App:** Create mobile app for QR scanning and device management
5. **Advanced Geofencing:** Implement complex geofencing rules
6. **Multi-User Support:** Add user authentication and authorization

## API Documentation

For a complete API reference, see the inline documentation in:
- `src/advanced_features_api.py`
- `tests/test_advanced_features.py`

## Support

For issues or questions about advanced features:
1. Check the test suite for usage examples
2. Review inline code documentation
3. Check logs in `logs/` directory
4. Report issues to the project maintainer

---

**Last Updated:** December 18, 2025  
**Version:** 1.0.0  
**Status:** Production Ready
