#!/usr/bin/env python3
"""
Demo Script for Advanced Features

Demonstrates all five feature areas:
1. Snapshot and ML Optimization
2. Push Data Capabilities
3. QR-Based Device Onboarding
4. Geolocation Integration
5. Sound Feedback System

Usage:
    # Start the server first:
    python meter_preview_ui.py --port 2500
    
    # Then run this demo:
    python examples/demo_advanced_features.py
"""

import requests
import json
import base64
from io import BytesIO
from PIL import Image


# Base URL for API
BASE_URL = "http://localhost:2500"


def demo_snapshots():
    """Demo: Snapshot and ML Optimization"""
    print("\n" + "=" * 60)
    print("DEMO 1: Snapshot and ML Optimization")
    print("=" * 60)
    
    # Get clean snapshot
    print("\n1. Getting clean snapshot for dashboard viewing...")
    response = requests.get(f"{BASE_URL}/api/snapshot/clean/water")
    if response.status_code == 200:
        print("   ✓ Clean snapshot retrieved successfully")
        with open("/tmp/clean_snapshot.jpg", "wb") as f:
            f.write(response.content)
        print("   → Saved to: /tmp/clean_snapshot.jpg")
    else:
        print(f"   ✗ Error: {response.json()}")
    
    # Get ML-optimized snapshot
    print("\n2. Getting ML-optimized snapshot for processing...")
    response = requests.get(f"{BASE_URL}/api/snapshot/ml-optimized/water")
    if response.status_code == 200:
        print("   ✓ ML-optimized snapshot retrieved successfully")
        with open("/tmp/ml_snapshot.png", "wb") as f:
            f.write(response.content)
        print("   → Saved to: /tmp/ml_snapshot.png")
    else:
        print(f"   ✗ Error: {response.json()}")


def demo_push_data():
    """Demo: Push Data Capabilities"""
    print("\n" + "=" * 60)
    print("DEMO 2: Push Data Capabilities")
    print("=" * 60)
    
    # Register device
    print("\n1. Registering camera device...")
    device_data = {
        "device_id": "demo_camera_001",
        "camera_ip": "192.168.1.100",
        "meter_type": "water",
        "location": "basement"
    }
    response = requests.post(f"{BASE_URL}/api/device/register", json=device_data)
    
    if response.status_code == 201:
        result = response.json()
        print("   ✓ Device registered successfully")
        print(f"   → Device ID: {result['device_id']}")
        print(f"   → Auth Token: {result['auth_token'][:20]}...")
        print(f"   → Push Endpoint: {result['push_endpoint']}")
        
        auth_token = result['auth_token']
        
        # Push data
        print("\n2. Pushing meter reading data...")
        
        # Create test image
        img = Image.new('RGB', (100, 100), color='blue')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        push_data = {
            "auth_token": auth_token,
            "timestamp": "2025-12-18T12:00:00",
            "image_base64": image_base64,
            "meter_reading": 123.45,
            "confidence": 0.95,
            "metadata": {"temperature": 20.5}
        }
        
        response = requests.post(
            f"{BASE_URL}/api/push/data/demo_camera_001",
            json=push_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✓ Data pushed successfully")
            print(f"   → Timestamp: {result['timestamp']}")
        else:
            print(f"   ✗ Error: {response.json()}")
    else:
        print(f"   ✗ Error: {response.json()}")


def demo_qr_onboarding():
    """Demo: QR-Based Device Onboarding"""
    print("\n" + "=" * 60)
    print("DEMO 3: QR-Based Device Onboarding")
    print("=" * 60)
    
    # Generate QR code
    print("\n1. Generating QR code for device binding...")
    qr_data = {
        "user_id": "demo_user_001",
        "meter_type": "electric",
        "location": "garage"
    }
    response = requests.post(f"{BASE_URL}/api/qr/generate", json=qr_data)
    
    if response.status_code == 200:
        result = response.json()
        print("   ✓ QR code generated successfully")
        print(f"   → Binding Token: {result['binding_token'][:20]}...")
        print(f"   → Expires At: {result['expires_at']}")
        
        # Save QR code image
        qr_image_data = base64.b64decode(result['qr_code_image'])
        with open("/tmp/device_qr_code.png", "wb") as f:
            f.write(qr_image_data)
        print("   → QR Code saved to: /tmp/device_qr_code.png")
        
        binding_token = result['binding_token']
        
        # Register device using QR code
        print("\n2. Registering device using QR code...")
        reg_data = {
            "binding_token": binding_token,
            "device_id": "qr_camera_001",
            "camera_ip": "192.168.1.200"
        }
        response = requests.post(f"{BASE_URL}/api/qr/register", json=reg_data)
        
        if response.status_code == 201:
            result = response.json()
            print("   ✓ Device registered via QR code")
            print(f"   → Device ID: {result['device_id']}")
            print(f"   → User ID: {result['user_id']}")
            print(f"   → Meter Type: {result['meter_type']}")
            print(f"   → Auth Token: {result['auth_token'][:20]}...")
        else:
            print(f"   ✗ Error: {response.json()}")
    else:
        print(f"   ✗ Error: {response.json()}")


def demo_geolocation():
    """Demo: Geolocation Integration"""
    print("\n" + "=" * 60)
    print("DEMO 4: Geolocation Integration")
    print("=" * 60)
    
    # First register a device
    print("\n1. Registering device for geolocation...")
    device_data = {
        "device_id": "geo_camera_001",
        "camera_ip": "192.168.1.150",
        "meter_type": "gas"
    }
    response = requests.post(f"{BASE_URL}/api/device/register", json=device_data)
    
    if response.status_code == 201:
        print("   ✓ Device registered")
        
        # Add geolocation
        print("\n2. Adding GPS coordinates...")
        location_data = {
            "device_id": "geo_camera_001",
            "latitude": 43.6532,
            "longitude": -79.3832,
            "accuracy": 10.0,
            "altitude": 100.0,
            "source": "mobile_gps"
        }
        response = requests.post(f"{BASE_URL}/api/device/location", json=location_data)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✓ Location registered successfully")
            print(f"   → Latitude: {result['location']['latitude']}")
            print(f"   → Longitude: {result['location']['longitude']}")
            
            # Search for nearby devices
            print("\n3. Searching for nearby devices...")
            params = {
                "latitude": 43.6532,
                "longitude": -79.3832,
                "radius_km": 5
            }
            response = requests.get(f"{BASE_URL}/api/devices/nearby", params=params)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✓ Found {result['count']} device(s) within {result['radius_km']} km")
                for device in result['devices']:
                    print(f"   → {device['device_id']}: {device['distance_km']} km away")
            else:
                print(f"   ✗ Error: {response.json()}")
        else:
            print(f"   ✗ Error: {response.json()}")
    else:
        print(f"   ✗ Error: {response.json()}")


def demo_sound_feedback():
    """Demo: Sound Feedback System"""
    print("\n" + "=" * 60)
    print("DEMO 5: Sound Feedback System")
    print("=" * 60)
    
    # Trigger audio feedback
    print("\n1. Triggering 'connected' audio feedback...")
    feedback_data = {
        "event_type": "connected",
        "device_id": "demo_device_001"
    }
    response = requests.post(f"{BASE_URL}/api/audio/trigger", json=feedback_data)
    
    if response.status_code == 200:
        result = response.json()
        print("   ✓ Audio feedback triggered")
        print(f"   → Event: {result['event_type']}")
        print(f"   → Message: {result['text_message']}")
        print(f"   → Audio URL: {result['audio_url']}")
    else:
        print(f"   ✗ Error: {response.json()}")
    
    # Get audio feedback
    print("\n2. Getting audio feedback for different events...")
    events = ['connected', 'error', 'success', 'reading_complete']
    
    for event in events:
        response = requests.get(f"{BASE_URL}/api/audio/feedback/{event}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ {event}: {result['text_message']}")
        else:
            print(f"   ✗ {event}: Error")


def main():
    """Run all demos"""
    print("\n")
    print("*" * 60)
    print("* Advanced Features Demo")
    print("* Computer Vision Utility Monitor")
    print("*" * 60)
    print("\nMake sure the server is running:")
    print("  python meter_preview_ui.py --port 2500")
    print("\nPress Enter to continue...")
    input()
    
    try:
        # Test server connection
        response = requests.get(f"{BASE_URL}/")
        print("\n✓ Server is running")
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Cannot connect to server")
        print("  Please start the server first:")
        print("  python meter_preview_ui.py --port 2500")
        return
    
    # Run demos
    demo_snapshots()
    demo_push_data()
    demo_qr_onboarding()
    demo_geolocation()
    demo_sound_feedback()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nCheck the following locations for generated files:")
    print("  - /tmp/clean_snapshot.jpg")
    print("  - /tmp/ml_snapshot.png")
    print("  - /tmp/device_qr_code.png")
    print("\nFor more information, see: ADVANCED_FEATURES_README.md")
    print()


if __name__ == "__main__":
    main()
