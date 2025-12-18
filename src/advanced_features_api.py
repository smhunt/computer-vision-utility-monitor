#!/usr/bin/env python3
"""
Advanced Features API Module

Implements advanced features for the computer vision utility monitor:
1. Snapshot and ML Optimization
2. Push Data Capabilities
3. QR-Based Device Onboarding
4. Geolocation Integration
5. Sound Feedback System
"""

import os
import json
import base64
import hashlib
import secrets
import io
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any
from flask import jsonify, request, send_file, Response
from PIL import Image
import qrcode

# Try to import database models
try:
    from src.database import get_db_session, Meter
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


class AdvancedFeaturesAPI:
    """API handler for advanced features"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize advanced features API
        
        Args:
            log_dir: Base directory for logs and snapshots
        """
        self.log_dir = Path(log_dir)
        self.snapshots_dir = self.log_dir / "meter_snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Device registry (in production, use database)
        self.device_registry_file = self.log_dir / "device_registry.json"
        self._load_device_registry()
        
        # Audio feedback files
        self.audio_dir = Path("static") / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_device_registry(self):
        """Load device registry from file"""
        if self.device_registry_file.exists():
            with open(self.device_registry_file, 'r') as f:
                self.device_registry = json.load(f)
        else:
            self.device_registry = {
                'devices': {},
                'qr_codes': {},
                'pending_registrations': {}
            }
    
    def _save_device_registry(self):
        """Save device registry to file"""
        with open(self.device_registry_file, 'w') as f:
            json.dump(self.device_registry, f, indent=2)
    
    # ============================================================
    # 1. SNAPSHOT AND ML OPTIMIZATION
    # ============================================================
    
    def get_clean_snapshot(self, meter_type: str, meter_name: str = None):
        """
        Get clean, human-readable snapshot for dashboard viewing
        
        Args:
            meter_type: Type of meter (water, electric, gas)
            meter_name: Optional specific meter name
            
        Returns:
            Flask response with clean snapshot image
        """
        try:
            # Find latest snapshot
            snapshot_dir = self.snapshots_dir / meter_name if meter_name else self.snapshots_dir / meter_type
            
            if not snapshot_dir.exists():
                return jsonify({
                    'status': 'error',
                    'message': f'No snapshots found for {meter_type}'
                }), 404
            
            snapshots = sorted(snapshot_dir.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
            
            if not snapshots:
                return jsonify({
                    'status': 'error',
                    'message': f'No snapshots available for {meter_type}'
                }), 404
            
            latest_snapshot = snapshots[0]
            
            # Load and enhance for viewing
            img = Image.open(latest_snapshot)
            
            # Apply viewer-friendly enhancements
            # - Auto-rotate to correct orientation
            # - Adjust brightness/contrast for display
            # - Add metadata overlay (optional)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save to buffer
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=95)
            buffer.seek(0)
            
            return send_file(
                buffer,
                mimetype='image/jpeg',
                as_attachment=False,
                download_name=f'{meter_type}_clean.jpg'
            )
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def get_ml_optimized_snapshot(self, meter_type: str, meter_name: str = None):
        """
        Get ML-optimized raw snapshot for machine learning processing
        
        Args:
            meter_type: Type of meter (water, electric, gas)
            meter_name: Optional specific meter name
            
        Returns:
            Flask response with ML-optimized snapshot
        """
        try:
            # Find latest snapshot
            snapshot_dir = self.snapshots_dir / meter_name if meter_name else self.snapshots_dir / meter_type
            
            if not snapshot_dir.exists():
                return jsonify({
                    'status': 'error',
                    'message': f'No snapshots found for {meter_type}'
                }), 404
            
            snapshots = sorted(snapshot_dir.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
            
            if not snapshots:
                return jsonify({
                    'status': 'error',
                    'message': f'No snapshots available for {meter_type}'
                }), 404
            
            latest_snapshot = snapshots[0]
            
            # Load and prepare for ML
            img = Image.open(latest_snapshot)
            
            # ML-friendly preprocessing:
            # - High contrast for digit recognition
            # - Grayscale conversion (optional)
            # - Normalization
            # - No compression artifacts
            
            # For now, return high-quality raw image
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')  # PNG for lossless
            buffer.seek(0)
            
            return send_file(
                buffer,
                mimetype='image/png',
                as_attachment=False,
                download_name=f'{meter_type}_ml_optimized.png'
            )
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    # ============================================================
    # 2. PUSH DATA CAPABILITIES
    # ============================================================
    
    def register_device(self):
        """
        Register a camera device for push data capabilities
        
        Expected JSON payload:
        {
            "device_id": "unique_device_id",
            "camera_ip": "192.168.1.100",
            "meter_type": "water",
            "location": "basement",
            "auth_token": "device_specific_token"
        }
        
        Returns:
            Registration confirmation with push endpoint details
        """
        try:
            data = request.get_json()
            
            required_fields = ['device_id', 'camera_ip', 'meter_type']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'status': 'error',
                        'message': f'Missing required field: {field}'
                    }), 400
            
            device_id = data['device_id']
            
            # Generate secure auth token if not provided
            auth_token = data.get('auth_token') or secrets.token_urlsafe(32)
            
            # Store device registration
            self.device_registry['devices'][device_id] = {
                'device_id': device_id,
                'camera_ip': data['camera_ip'],
                'meter_type': data['meter_type'],
                'location': data.get('location', 'unknown'),
                'auth_token': auth_token,
                'registered_at': datetime.now().isoformat(),
                'last_push': None,
                'status': 'active'
            }
            
            self._save_device_registry()
            
            return jsonify({
                'status': 'success',
                'message': 'Device registered successfully',
                'device_id': device_id,
                'auth_token': auth_token,
                'push_endpoint': f'/api/push/data/{device_id}',
                'push_method': 'POST'
            }), 201
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def receive_push_data(self, device_id: str):
        """
        Receive pushed data from a registered camera device
        
        Args:
            device_id: Unique device identifier
            
        Expected JSON payload:
        {
            "auth_token": "device_auth_token",
            "timestamp": "2025-12-18T12:00:00",
            "image_base64": "base64_encoded_image",
            "meter_reading": 123.45,
            "confidence": 0.95,
            "metadata": {...}
        }
        
        Returns:
            Acknowledgment of data receipt
        """
        try:
            # Verify device is registered
            if device_id not in self.device_registry['devices']:
                return jsonify({
                    'status': 'error',
                    'message': 'Device not registered'
                }), 404
            
            device = self.device_registry['devices'][device_id]
            data = request.get_json()
            
            # Verify auth token
            if data.get('auth_token') != device['auth_token']:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid auth token'
                }), 401
            
            # Process pushed data
            timestamp = datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
            
            # Save image if provided
            if 'image_base64' in data:
                image_data = base64.b64decode(data['image_base64'])
                meter_type = device['meter_type']
                snapshot_dir = self.snapshots_dir / meter_type
                snapshot_dir.mkdir(parents=True, exist_ok=True)
                
                filename = f"{meter_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
                snapshot_path = snapshot_dir / filename
                
                with open(snapshot_path, 'wb') as f:
                    f.write(image_data)
            
            # Update device last push time
            device['last_push'] = datetime.now().isoformat()
            self._save_device_registry()
            
            # Store reading data
            reading_data = {
                'device_id': device_id,
                'meter_type': device['meter_type'],
                'timestamp': timestamp.isoformat(),
                'meter_reading': data.get('meter_reading'),
                'confidence': data.get('confidence'),
                'metadata': data.get('metadata', {})
            }
            
            # Log to JSONL
            log_file = self.log_dir / f"{device['meter_type']}_push_readings.jsonl"
            with open(log_file, 'a') as f:
                f.write(json.dumps(reading_data) + '\n')
            
            return jsonify({
                'status': 'success',
                'message': 'Data received and processed',
                'device_id': device_id,
                'timestamp': timestamp.isoformat()
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    # ============================================================
    # 3. QR-BASED DEVICE ONBOARDING
    # ============================================================
    
    def generate_qr_code(self):
        """
        Generate QR code for device onboarding
        
        Expected JSON payload:
        {
            "user_id": "user_account_id",
            "meter_type": "water",
            "location": "basement"
        }
        
        Returns:
            QR code image and binding token
        """
        try:
            data = request.get_json()
            
            user_id = data.get('user_id', 'default_user')
            meter_type = data.get('meter_type', 'water')
            location = data.get('location', 'unknown')
            
            # Generate unique binding token
            binding_token = secrets.token_urlsafe(32)
            
            # Create QR code data
            qr_data = {
                'binding_token': binding_token,
                'user_id': user_id,
                'meter_type': meter_type,
                'location': location,
                'registration_endpoint': '/api/device/register',
                'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
            }
            
            # Store pending registration
            self.device_registry['qr_codes'][binding_token] = {
                'user_id': user_id,
                'meter_type': meter_type,
                'location': location,
                'created_at': datetime.now().isoformat(),
                'expires_at': qr_data['expires_at'],
                'status': 'pending'
            }
            self._save_device_registry()
            
            # Generate QR code image
            qr_data_str = json.dumps(qr_data)
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data_str)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to buffer
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Return both QR image and data
            qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return jsonify({
                'status': 'success',
                'binding_token': binding_token,
                'qr_code_image': qr_image_base64,
                'qr_data': qr_data,
                'expires_at': qr_data['expires_at']
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def decode_and_register_qr(self):
        """
        Decode QR code and register device
        
        Expected JSON payload:
        {
            "binding_token": "token_from_qr",
            "device_id": "unique_device_id",
            "camera_ip": "192.168.1.100"
        }
        
        Returns:
            Registration confirmation
        """
        try:
            data = request.get_json()
            
            binding_token = data.get('binding_token')
            device_id = data.get('device_id')
            camera_ip = data.get('camera_ip')
            
            if not all([binding_token, device_id, camera_ip]):
                return jsonify({
                    'status': 'error',
                    'message': 'Missing required fields: binding_token, device_id, camera_ip'
                }), 400
            
            # Verify QR code
            if binding_token not in self.device_registry['qr_codes']:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid or expired QR code'
                }), 404
            
            qr_info = self.device_registry['qr_codes'][binding_token]
            
            # Check expiration
            expires_at = datetime.fromisoformat(qr_info['expires_at'])
            if datetime.now() > expires_at:
                return jsonify({
                    'status': 'error',
                    'message': 'QR code has expired'
                }), 400
            
            # Check if already used
            if qr_info['status'] != 'pending':
                return jsonify({
                    'status': 'error',
                    'message': 'QR code has already been used'
                }), 400
            
            # Generate auth token
            auth_token = secrets.token_urlsafe(32)
            
            # Register device
            self.device_registry['devices'][device_id] = {
                'device_id': device_id,
                'camera_ip': camera_ip,
                'meter_type': qr_info['meter_type'],
                'location': qr_info['location'],
                'user_id': qr_info['user_id'],
                'auth_token': auth_token,
                'registered_at': datetime.now().isoformat(),
                'binding_token': binding_token,
                'status': 'active'
            }
            
            # Mark QR code as used
            qr_info['status'] = 'used'
            qr_info['device_id'] = device_id
            qr_info['used_at'] = datetime.now().isoformat()
            
            self._save_device_registry()
            
            return jsonify({
                'status': 'success',
                'message': 'Device registered successfully via QR code',
                'device_id': device_id,
                'auth_token': auth_token,
                'user_id': qr_info['user_id'],
                'meter_type': qr_info['meter_type'],
                'push_endpoint': f'/api/push/data/{device_id}'
            }), 201
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    # ============================================================
    # 4. GEOLOCATION INTEGRATION
    # ============================================================
    
    def register_device_location(self):
        """
        Register device geolocation during onboarding
        
        Expected JSON payload:
        {
            "device_id": "unique_device_id",
            "latitude": 43.6532,
            "longitude": -79.3832,
            "accuracy": 10.0,
            "altitude": 100.0,
            "source": "mobile_gps"
        }
        
        Returns:
            Confirmation of location registration
        """
        try:
            data = request.get_json()
            
            device_id = data.get('device_id')
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            if not all([device_id, latitude, longitude]):
                return jsonify({
                    'status': 'error',
                    'message': 'Missing required fields: device_id, latitude, longitude'
                }), 400
            
            # Verify device exists
            if device_id not in self.device_registry['devices']:
                return jsonify({
                    'status': 'error',
                    'message': 'Device not registered'
                }), 404
            
            device = self.device_registry['devices'][device_id]
            
            # Store geolocation
            device['geolocation'] = {
                'latitude': latitude,
                'longitude': longitude,
                'accuracy': data.get('accuracy'),
                'altitude': data.get('altitude'),
                'source': data.get('source', 'mobile_gps'),
                'registered_at': datetime.now().isoformat()
            }
            
            self._save_device_registry()
            
            return jsonify({
                'status': 'success',
                'message': 'Location registered successfully',
                'device_id': device_id,
                'location': {
                    'latitude': latitude,
                    'longitude': longitude
                }
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def get_devices_by_location(self):
        """
        Get devices near a specific location
        
        Query parameters:
        - latitude: Center latitude
        - longitude: Center longitude
        - radius_km: Search radius in kilometers (default: 10)
        
        Returns:
            List of nearby devices
        """
        try:
            latitude = float(request.args.get('latitude', 0))
            longitude = float(request.args.get('longitude', 0))
            radius_km = float(request.args.get('radius_km', 10))
            
            nearby_devices = []
            
            for device_id, device in self.device_registry['devices'].items():
                if 'geolocation' not in device:
                    continue
                
                # Simple distance calculation (Haversine formula would be more accurate)
                device_lat = device['geolocation']['latitude']
                device_lon = device['geolocation']['longitude']
                
                # Approximate distance (simplified)
                lat_diff = abs(device_lat - latitude)
                lon_diff = abs(device_lon - longitude)
                distance_approx = ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 111  # rough km conversion
                
                if distance_approx <= radius_km:
                    nearby_devices.append({
                        'device_id': device_id,
                        'meter_type': device['meter_type'],
                        'location': device.get('location'),
                        'geolocation': device['geolocation'],
                        'distance_km': round(distance_approx, 2)
                    })
            
            return jsonify({
                'status': 'success',
                'center': {'latitude': latitude, 'longitude': longitude},
                'radius_km': radius_km,
                'devices': nearby_devices,
                'count': len(nearby_devices)
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    # ============================================================
    # 5. SOUND FEEDBACK SYSTEM
    # ============================================================
    
    def get_audio_feedback(self, event_type: str):
        """
        Get audio feedback for specific events
        
        Args:
            event_type: Type of event (connected, error, success, reading_complete)
            
        Returns:
            Audio file response
        """
        try:
            # Audio feedback mapping
            audio_files = {
                'connected': 'connected_welcome.mp3',
                'error': 'error_beep.mp3',
                'success': 'success_chime.mp3',
                'reading_complete': 'reading_complete.mp3'
            }
            
            if event_type not in audio_files:
                return jsonify({
                    'status': 'error',
                    'message': f'Unknown event type: {event_type}',
                    'available_types': list(audio_files.keys())
                }), 400
            
            audio_file = self.audio_dir / audio_files[event_type]
            
            # If audio file doesn't exist, return a text-to-speech alternative
            if not audio_file.exists():
                return jsonify({
                    'status': 'success',
                    'event_type': event_type,
                    'audio_available': False,
                    'text_message': self._get_text_feedback(event_type),
                    'message': 'Audio file not available, use text-to-speech'
                }), 200
            
            return send_file(
                audio_file,
                mimetype='audio/mpeg',
                as_attachment=False
            )
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def _get_text_feedback(self, event_type: str) -> str:
        """Get text feedback message for TTS"""
        messages = {
            'connected': 'Connected. Welcome to the Future!',
            'error': 'Error occurred. Please check the system.',
            'success': 'Operation successful.',
            'reading_complete': 'Meter reading complete.'
        }
        return messages.get(event_type, 'System notification.')
    
    def trigger_audio_feedback(self):
        """
        Trigger audio feedback and return message
        
        Expected JSON payload:
        {
            "event_type": "connected",
            "device_id": "device_123"
        }
        
        Returns:
            Audio feedback information
        """
        try:
            data = request.get_json()
            event_type = data.get('event_type', 'connected')
            device_id = data.get('device_id')
            
            text_message = self._get_text_feedback(event_type)
            audio_url = f'/api/audio/feedback/{event_type}'
            
            # Log the event
            event_log = {
                'event_type': event_type,
                'device_id': device_id,
                'timestamp': datetime.now().isoformat(),
                'text_message': text_message
            }
            
            log_file = self.log_dir / 'audio_feedback_events.jsonl'
            with open(log_file, 'a') as f:
                f.write(json.dumps(event_log) + '\n')
            
            return jsonify({
                'status': 'success',
                'event_type': event_type,
                'text_message': text_message,
                'audio_url': audio_url,
                'message': 'Audio feedback triggered'
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500


def register_advanced_features_routes(app, log_dir: str = "logs"):
    """
    Register all advanced features API routes with a Flask app
    
    Args:
        app: Flask application instance
        log_dir: Base directory for logs and data
    """
    api = AdvancedFeaturesAPI(log_dir)
    
    # Snapshot and ML Optimization
    @app.route('/api/snapshot/clean/<meter_type>', methods=['GET'])
    def api_snapshot_clean(meter_type):
        """Get clean snapshot for dashboard viewing"""
        meter_name = request.args.get('meter_name')
        return api.get_clean_snapshot(meter_type, meter_name)
    
    @app.route('/api/snapshot/ml-optimized/<meter_type>', methods=['GET'])
    def api_snapshot_ml_optimized(meter_type):
        """Get ML-optimized snapshot for processing"""
        meter_name = request.args.get('meter_name')
        return api.get_ml_optimized_snapshot(meter_type, meter_name)
    
    # Push Data Capabilities
    @app.route('/api/device/register', methods=['POST'])
    def api_device_register():
        """Register a device for push capabilities"""
        return api.register_device()
    
    @app.route('/api/push/data/<device_id>', methods=['POST'])
    def api_push_data(device_id):
        """Receive pushed data from device"""
        return api.receive_push_data(device_id)
    
    # QR-Based Device Onboarding
    @app.route('/api/qr/generate', methods=['POST'])
    def api_qr_generate():
        """Generate QR code for device onboarding"""
        return api.generate_qr_code()
    
    @app.route('/api/qr/register', methods=['POST'])
    def api_qr_register():
        """Register device using QR code"""
        return api.decode_and_register_qr()
    
    # Geolocation Integration
    @app.route('/api/device/location', methods=['POST'])
    def api_device_location():
        """Register device geolocation"""
        return api.register_device_location()
    
    @app.route('/api/devices/nearby', methods=['GET'])
    def api_devices_nearby():
        """Get devices near a location"""
        return api.get_devices_by_location()
    
    # Sound Feedback System
    @app.route('/api/audio/feedback/<event_type>', methods=['GET'])
    def api_audio_feedback(event_type):
        """Get audio feedback for event"""
        return api.get_audio_feedback(event_type)
    
    @app.route('/api/audio/trigger', methods=['POST'])
    def api_audio_trigger():
        """Trigger audio feedback"""
        return api.trigger_audio_feedback()
    
    print("✓ Advanced features API routes registered")
    print("  - Snapshot and ML Optimization: /api/snapshot/...")
    print("  - Push Data: /api/device/register, /api/push/data/...")
    print("  - QR Onboarding: /api/qr/...")
    print("  - Geolocation: /api/device/location, /api/devices/nearby")
    print("  - Sound Feedback: /api/audio/...")
