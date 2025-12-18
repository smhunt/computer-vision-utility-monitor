#!/usr/bin/env python3
"""
Tests for Advanced Features API

Tests all five feature areas:
1. Snapshot and ML Optimization
2. Push Data Capabilities
3. QR-Based Device Onboarding
4. Geolocation Integration
5. Sound Feedback System
"""

import unittest
import json
import tempfile
import base64
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
from io import BytesIO
from PIL import Image

# Import the advanced features API
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from advanced_features_api import AdvancedFeaturesAPI

# Import Flask for testing
from flask import Flask


class TestSnapshotOptimization(unittest.TestCase):
    """Test snapshot and ML optimization features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.api = AdvancedFeaturesAPI(log_dir=self.test_dir)
        self.app = Flask(__name__)
        self.app.testing = True
        
        # Create test snapshot
        self.create_test_snapshot('water')
    
    def create_test_snapshot(self, meter_type):
        """Create a test snapshot image"""
        snapshot_dir = Path(self.test_dir) / "meter_snapshots" / meter_type
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a simple test image
        img = Image.new('RGB', (640, 480), color='blue')
        img.save(snapshot_dir / f"{meter_type}_test.jpg")
    
    def test_clean_snapshot_exists(self):
        """Test getting clean snapshot when it exists"""
        with self.app.test_request_context():
            result = self.api.get_clean_snapshot('water')
            # Should attempt to send file
            self.assertIsNotNone(result)
    
    def test_ml_optimized_snapshot_exists(self):
        """Test getting ML-optimized snapshot when it exists"""
        with self.app.test_request_context():
            result = self.api.get_ml_optimized_snapshot('water')
            # Should attempt to send file
            self.assertIsNotNone(result)
    
    def test_snapshot_not_found(self):
        """Test handling of missing snapshots"""
        with self.app.test_request_context():
            result = self.api.get_clean_snapshot('nonexistent_meter')
            data = json.loads(result[0].get_data(as_text=True))
            # Should return error response
            self.assertEqual(data['status'], 'error')


class TestPushDataCapabilities(unittest.TestCase):
    """Test push data capabilities"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.api = AdvancedFeaturesAPI(log_dir=self.test_dir)
        self.app = Flask(__name__)
        self.app.testing = True
    
    def test_device_registration(self):
        """Test device registration"""
        with self.app.test_request_context(
            json={
                'device_id': 'test_device_001',
                'camera_ip': '192.168.1.100',
                'meter_type': 'water',
                'location': 'basement'
            }
        ):
            result = self.api.register_device()
            data = json.loads(result[0].get_data(as_text=True))
            
            self.assertEqual(data['status'], 'success')
            self.assertEqual(data['device_id'], 'test_device_001')
            self.assertIn('auth_token', data)
            self.assertIn('push_endpoint', data)
    
    def test_device_registration_missing_fields(self):
        """Test device registration with missing required fields"""
        with self.app.test_request_context(json={'device_id': 'test_device'}):
            result = self.api.register_device()
            data = json.loads(result[0].get_data(as_text=True))
            
            self.assertEqual(data['status'], 'error')
            self.assertIn('Missing required field', data['message'])
    
    def test_push_data_with_auth(self):
        """Test receiving pushed data with authentication"""
        # First register a device
        with self.app.test_request_context(
            json={
                'device_id': 'test_device_002',
                'camera_ip': '192.168.1.101',
                'meter_type': 'water'
            }
        ):
            reg_result = self.api.register_device()
            reg_data = json.loads(reg_result[0].get_data(as_text=True))
            auth_token = reg_data['auth_token']
        
        # Now push data
        test_image = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        test_image.save(buffer, format='JPEG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        with self.app.test_request_context(
            json={
                'auth_token': auth_token,
                'timestamp': datetime.now().isoformat(),
                'image_base64': image_base64,
                'meter_reading': 123.45,
                'confidence': 0.95
            }
        ):
            result = self.api.receive_push_data('test_device_002')
            data = json.loads(result[0].get_data(as_text=True))
            
            self.assertEqual(data['status'], 'success')
            self.assertEqual(data['device_id'], 'test_device_002')
    
    def test_push_data_invalid_auth(self):
        """Test push data with invalid authentication"""
        with self.app.test_request_context(
            json={
                'device_id': 'test_device_003',
                'camera_ip': '192.168.1.102',
                'meter_type': 'electric'
            }
        ):
            self.api.register_device()
        
        # Push with wrong auth token
        with self.app.test_request_context(
            json={
                'auth_token': 'wrong_token',
                'timestamp': datetime.now().isoformat(),
                'meter_reading': 100.0
            }
        ):
            result = self.api.receive_push_data('test_device_003')
            data = json.loads(result[0].get_data(as_text=True))
            
            self.assertEqual(data['status'], 'error')
            self.assertIn('Invalid auth token', data['message'])


class TestQROnboarding(unittest.TestCase):
    """Test QR-based device onboarding"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.api = AdvancedFeaturesAPI(log_dir=self.test_dir)
        self.app = Flask(__name__)
        self.app.testing = True
    
    def test_generate_qr_code(self):
        """Test QR code generation"""
        with self.app.test_request_context(
            json={
                'user_id': 'user_001',
                'meter_type': 'water',
                'location': 'basement'
            }
        ):
            result = self.api.generate_qr_code()
            data = json.loads(result[0].get_data(as_text=True))
            
            self.assertEqual(data['status'], 'success')
            self.assertIn('binding_token', data)
            self.assertIn('qr_code_image', data)
            self.assertIn('qr_data', data)
            self.assertIn('expires_at', data)
    
    def test_qr_registration_workflow(self):
        """Test complete QR registration workflow"""
        # Step 1: Generate QR code
        with self.app.test_request_context(
            json={
                'user_id': 'user_002',
                'meter_type': 'electric',
                'location': 'garage'
            }
        ):
            qr_result = self.api.generate_qr_code()
            qr_data = json.loads(qr_result[0].get_data(as_text=True))
            binding_token = qr_data['binding_token']
        
        # Step 2: Register device using QR code
        with self.app.test_request_context(
            json={
                'binding_token': binding_token,
                'device_id': 'qr_device_001',
                'camera_ip': '192.168.1.200'
            }
        ):
            reg_result = self.api.decode_and_register_qr()
            reg_data = json.loads(reg_result[0].get_data(as_text=True))
            
            self.assertEqual(reg_data['status'], 'success')
            self.assertEqual(reg_data['device_id'], 'qr_device_001')
            self.assertEqual(reg_data['meter_type'], 'electric')
            self.assertIn('auth_token', reg_data)
    
    def test_qr_invalid_token(self):
        """Test QR registration with invalid token"""
        with self.app.test_request_context(
            json={
                'binding_token': 'invalid_token',
                'device_id': 'device_xyz',
                'camera_ip': '192.168.1.201'
            }
        ):
            result = self.api.decode_and_register_qr()
            data = json.loads(result[0].get_data(as_text=True))
            
            self.assertEqual(data['status'], 'error')
            self.assertIn('Invalid or expired', data['message'])
    
    def test_qr_already_used(self):
        """Test that QR codes can only be used once"""
        # Generate QR code
        with self.app.test_request_context(
            json={
                'user_id': 'user_003',
                'meter_type': 'gas'
            }
        ):
            qr_result = self.api.generate_qr_code()
            qr_data = json.loads(qr_result[0].get_data(as_text=True))
            binding_token = qr_data['binding_token']
        
        # Use it once
        with self.app.test_request_context(
            json={
                'binding_token': binding_token,
                'device_id': 'device_first',
                'camera_ip': '192.168.1.202'
            }
        ):
            self.api.decode_and_register_qr()
        
        # Try to use it again
        with self.app.test_request_context(
            json={
                'binding_token': binding_token,
                'device_id': 'device_second',
                'camera_ip': '192.168.1.203'
            }
        ):
            result = self.api.decode_and_register_qr()
            data = json.loads(result[0].get_data(as_text=True))
            
            self.assertEqual(data['status'], 'error')
            self.assertIn('already been used', data['message'])


class TestGeolocation(unittest.TestCase):
    """Test geolocation integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.api = AdvancedFeaturesAPI(log_dir=self.test_dir)
        self.app = Flask(__name__)
        self.app.testing = True
        
        # Register a test device
        with self.app.test_request_context(
            json={
                'device_id': 'geo_device_001',
                'camera_ip': '192.168.1.100',
                'meter_type': 'water'
            }
        ):
            self.api.register_device()
    
    def test_register_device_location(self):
        """Test registering device geolocation"""
        with self.app.test_request_context(
            json={
                'device_id': 'geo_device_001',
                'latitude': 43.6532,
                'longitude': -79.3832,
                'accuracy': 10.0,
                'source': 'mobile_gps'
            }
        ):
            result = self.api.register_device_location()
            data = json.loads(result[0].get_data(as_text=True))
            
            self.assertEqual(data['status'], 'success')
            self.assertEqual(data['device_id'], 'geo_device_001')
            self.assertIn('location', data)
    
    def test_register_location_missing_fields(self):
        """Test location registration with missing fields"""
        with self.app.test_request_context(
            json={'device_id': 'geo_device_001'}
        ):
            result = self.api.register_device_location()
            data = json.loads(result[0].get_data(as_text=True))
            
            self.assertEqual(data['status'], 'error')
            self.assertIn('Missing required fields', data['message'])
    
    def test_get_nearby_devices(self):
        """Test finding devices by location"""
        # Register multiple devices with locations
        devices = [
            ('geo_device_002', 43.6532, -79.3832),
            ('geo_device_003', 43.6600, -79.3900),
            ('geo_device_004', 43.7000, -79.4000)
        ]
        
        for device_id, lat, lon in devices:
            with self.app.test_request_context(
                json={
                    'device_id': device_id,
                    'camera_ip': '192.168.1.100',
                    'meter_type': 'water'
                }
            ):
                self.api.register_device()
            
            with self.app.test_request_context(
                json={
                    'device_id': device_id,
                    'latitude': lat,
                    'longitude': lon
                }
            ):
                self.api.register_device_location()
        
        # Search for nearby devices
        with self.app.test_request_context(
            query_string={
                'latitude': 43.6532,
                'longitude': -79.3832,
                'radius_km': 5
            }
        ):
            result = self.api.get_devices_by_location()
            data = json.loads(result[0].get_data(as_text=True))
            
            self.assertEqual(data['status'], 'success')
            self.assertIn('devices', data)
            self.assertGreater(len(data['devices']), 0)


class TestSoundFeedback(unittest.TestCase):
    """Test sound feedback system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.api = AdvancedFeaturesAPI(log_dir=self.test_dir)
        self.app = Flask(__name__)
        self.app.testing = True
    
    def test_get_audio_feedback_no_file(self):
        """Test audio feedback when file doesn't exist"""
        with self.app.test_request_context():
            result = self.api.get_audio_feedback('connected')
            data = json.loads(result[0].get_data(as_text=True))
            
            self.assertEqual(data['status'], 'success')
            self.assertEqual(data['event_type'], 'connected')
            self.assertFalse(data['audio_available'])
            self.assertIn('text_message', data)
            self.assertEqual(data['text_message'], 'Connected. Welcome to the Future!')
    
    def test_get_audio_feedback_invalid_event(self):
        """Test audio feedback with invalid event type"""
        with self.app.test_request_context():
            result = self.api.get_audio_feedback('invalid_event')
            data = json.loads(result[0].get_data(as_text=True))
            
            self.assertEqual(data['status'], 'error')
            self.assertIn('Unknown event type', data['message'])
            self.assertIn('available_types', data)
    
    def test_trigger_audio_feedback(self):
        """Test triggering audio feedback"""
        with self.app.test_request_context(
            json={
                'event_type': 'connected',
                'device_id': 'device_123'
            }
        ):
            result = self.api.trigger_audio_feedback()
            data = json.loads(result[0].get_data(as_text=True))
            
            self.assertEqual(data['status'], 'success')
            self.assertEqual(data['event_type'], 'connected')
            self.assertIn('text_message', data)
            self.assertIn('audio_url', data)
    
    def test_text_feedback_messages(self):
        """Test all text feedback messages"""
        event_types = ['connected', 'error', 'success', 'reading_complete']
        
        for event_type in event_types:
            text = self.api._get_text_feedback(event_type)
            self.assertIsNotNone(text)
            self.assertIsInstance(text, str)
            self.assertGreater(len(text), 0)


if __name__ == '__main__':
    unittest.main()
