import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

import meter_preview_ui


class ConsumptionApiTests(unittest.TestCase):
    """Tests for the consumption API endpoint"""

    def setUp(self):
        meter_preview_ui.app.testing = True
        self.client = meter_preview_ui.app.test_client()

    @patch('meter_preview_ui.LOG_DIR')
    def test_consumption_endpoint_no_data(self, mock_log_dir):
        """Test consumption endpoint when no log file exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_log_dir.__truediv__ = lambda self, other: Path(tmpdir) / other

            response = self.client.get('/api/consumption/water')

            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload['status'], 'success')
            self.assertEqual(payload['hours'], [])
            self.assertEqual(payload['consumption'], [])

    @patch('meter_preview_ui.LOG_DIR')
    def test_consumption_endpoint_with_data(self, mock_log_dir):
        """Test consumption endpoint with valid JSONL data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            mock_log_dir.__truediv__ = lambda self, other: log_dir / other

            # Create test JSONL file
            log_file = log_dir / 'water_readings.jsonl'
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Write test data - two readings an hour apart
            test_data = [
                {
                    'total_reading': 100.0,
                    'timestamp': '2025-11-19T10:00:00',
                    'confidence': 'high'
                },
                {
                    'total_reading': 100.5,
                    'timestamp': '2025-11-19T10:30:00',
                    'confidence': 'high'
                },
                {
                    'total_reading': 101.2,
                    'timestamp': '2025-11-19T11:00:00',
                    'confidence': 'high'
                }
            ]

            with open(log_file, 'w') as f:
                for data in test_data:
                    f.write(json.dumps(data) + '\n')

            response = self.client.get('/api/consumption/water')

            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload['status'], 'success')
            self.assertIsInstance(payload['hours'], list)
            self.assertIsInstance(payload['consumption'], list)
            self.assertEqual(payload['unit'], 'm³')


class SnapshotsApiTests(unittest.TestCase):
    """Tests for the snapshots API endpoint"""

    def setUp(self):
        meter_preview_ui.app.testing = True
        self.client = meter_preview_ui.app.test_client()

    @patch('meter_preview_ui.LOG_DIR')
    def test_snapshots_endpoint_no_data(self, mock_log_dir):
        """Test snapshots endpoint when no snapshots exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            mock_log_dir.__truediv__ = lambda self, other: log_dir / other

            response = self.client.get('/api/snapshots/water_main')

            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload['status'], 'success')
            self.assertEqual(payload['snapshots'], [])
            self.assertEqual(payload['count'], 0)

    @patch('meter_preview_ui.LOG_DIR')
    def test_snapshots_endpoint_with_data(self, mock_log_dir):
        """Test snapshots endpoint with valid snapshot metadata"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            mock_log_dir.__truediv__ = lambda self, other: log_dir / other

            # Create test snapshot directory
            snapshot_dir = log_dir / 'meter_snapshots' / 'water_main'
            snapshot_dir.mkdir(parents=True, exist_ok=True)

            # Create test metadata file
            test_metadata = {
                'snapshot': {
                    'filename': 'water_main_20251119_120000.jpg',
                    'timestamp': '2025-11-19T12:00:00',
                    'size': 123456
                },
                'meter_reading': {
                    'total_reading': 2271.81,
                    'confidence': 'high',
                    'vision_model': 'gemini-2.5-flash'
                }
            }

            metadata_file = snapshot_dir / 'water_main_20251119_120000.json'
            with open(metadata_file, 'w') as f:
                json.dump(test_metadata, f)

            response = self.client.get('/api/snapshots/water_main')

            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload['status'], 'success')
            self.assertEqual(payload['count'], 1)
            self.assertIsInstance(payload['snapshots'], list)
            self.assertEqual(len(payload['snapshots']), 1)

            # Verify image_url was added
            snapshot = payload['snapshots'][0]
            self.assertIn('image_url', snapshot)
            self.assertIn('/static/snapshots/water_main/', snapshot['image_url'])

    @patch('meter_preview_ui.LOG_DIR')
    def test_snapshots_endpoint_invalid_json(self, mock_log_dir):
        """Test snapshots endpoint handles invalid JSON gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            mock_log_dir.__truediv__ = lambda self, other: log_dir / other

            # Create test snapshot directory
            snapshot_dir = log_dir / 'meter_snapshots' / 'water_main'
            snapshot_dir.mkdir(parents=True, exist_ok=True)

            # Create invalid JSON file
            invalid_file = snapshot_dir / 'water_main_20251119_120000.json'
            with open(invalid_file, 'w') as f:
                f.write('{ invalid json')

            response = self.client.get('/api/snapshots/water_main')

            # Should succeed but skip invalid files
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload['status'], 'success')
            self.assertEqual(payload['count'], 0)


class IntegrationTests(unittest.TestCase):
    """Integration tests for combined functionality"""

    def setUp(self):
        meter_preview_ui.app.testing = True
        self.client = meter_preview_ui.app.test_client()

    def test_root_endpoint(self):
        """Test that root endpoint returns a response"""
        response = self.client.get('/')
        # Should redirect or return 200
        self.assertIn(response.status_code, [200, 302, 308])

    def test_api_meters_endpoint(self):
        """Test that /api/meters endpoint exists"""
        response = self.client.get('/api/meters')
        self.assertEqual(response.status_code, 200)


class EdgeCaseTests(unittest.TestCase):
    """Edge case and error handling tests"""

    def setUp(self):
        meter_preview_ui.app.testing = True
        self.client = meter_preview_ui.app.test_client()

    @patch('meter_preview_ui.LOG_DIR')
    def test_consumption_empty_file(self, mock_log_dir):
        """Test consumption endpoint with empty JSONL file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            mock_log_dir.__truediv__ = lambda self, other: log_dir / other

            # Create empty file
            log_file = log_dir / 'water_readings.jsonl'
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_file.touch()

            response = self.client.get('/api/consumption/water')

            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload['status'], 'success')
            self.assertEqual(payload['hours'], [])

    @patch('meter_preview_ui.LOG_DIR')
    def test_consumption_malformed_json(self, mock_log_dir):
        """Test consumption endpoint handles malformed JSON lines"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            mock_log_dir.__truediv__ = lambda self, other: log_dir / other

            log_file = log_dir / 'water_readings.jsonl'
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Write mix of valid and invalid JSON
            with open(log_file, 'w') as f:
                f.write('{ invalid json }\n')
                f.write(json.dumps({
                    'total_reading': 100.0,
                    'timestamp': '2025-11-19T10:00:00'
                }) + '\n')
                f.write('not json at all\n')

            response = self.client.get('/api/consumption/water')

            # Should succeed, skipping invalid lines
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload['status'], 'success')

    @patch('meter_preview_ui.LOG_DIR')
    def test_consumption_missing_fields(self, mock_log_dir):
        """Test consumption endpoint with missing required fields"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            mock_log_dir.__truediv__ = lambda self, other: log_dir / other

            log_file = log_dir / 'water_readings.jsonl'
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Write data without required fields
            test_data = [
                {'timestamp': '2025-11-19T10:00:00'},  # Missing total_reading
                {'total_reading': None, 'timestamp': '2025-11-19T10:00:00'},  # Null reading
                {'total_reading': 'not_a_number', 'timestamp': '2025-11-19T10:00:00'},  # Invalid type
            ]

            with open(log_file, 'w') as f:
                for data in test_data:
                    f.write(json.dumps(data) + '\n')

            response = self.client.get('/api/consumption/water')

            # Should succeed, skipping invalid entries
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload['status'], 'success')

    @patch('meter_preview_ui.LOG_DIR')
    def test_consumption_negative_values(self, mock_log_dir):
        """Test consumption endpoint with negative readings"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            mock_log_dir.__truediv__ = lambda self, other: log_dir / other

            log_file = log_dir / 'water_readings.jsonl'
            log_file.parent.mkdir(parents=True, exist_ok=True)

            test_data = [
                {'total_reading': -100.0, 'timestamp': '2025-11-19T10:00:00'},
                {'total_reading': -50.0, 'timestamp': '2025-11-19T10:30:00'},
            ]

            with open(log_file, 'w') as f:
                for data in test_data:
                    f.write(json.dumps(data) + '\n')

            response = self.client.get('/api/consumption/water')

            # Should handle negative values
            self.assertEqual(response.status_code, 200)

    @patch('meter_preview_ui.LOG_DIR')
    def test_consumption_very_large_values(self, mock_log_dir):
        """Test consumption endpoint with extremely large readings"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            mock_log_dir.__truediv__ = lambda self, other: log_dir / other

            log_file = log_dir / 'water_readings.jsonl'
            log_file.parent.mkdir(parents=True, exist_ok=True)

            test_data = [
                {'total_reading': 999999999.999, 'timestamp': '2025-11-19T10:00:00'},
                {'total_reading': 1000000000.0, 'timestamp': '2025-11-19T10:30:00'},
            ]

            with open(log_file, 'w') as f:
                for data in test_data:
                    f.write(json.dumps(data) + '\n')

            response = self.client.get('/api/consumption/water')

            # Should handle large values
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload['status'], 'success')

    @patch('meter_preview_ui.LOG_DIR')
    def test_snapshots_directory_not_exist(self, mock_log_dir):
        """Test snapshots endpoint when directory doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            mock_log_dir.__truediv__ = lambda self, other: log_dir / other
            # Don't create the directory

            response = self.client.get('/api/snapshots/water_main')

            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload['status'], 'success')
            self.assertEqual(payload['count'], 0)

    @patch('meter_preview_ui.LOG_DIR')
    def test_snapshots_file_without_image(self, mock_log_dir):
        """Test snapshots endpoint with JSON but no corresponding image"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            mock_log_dir.__truediv__ = lambda self, other: log_dir / other

            snapshot_dir = log_dir / 'meter_snapshots' / 'water_main'
            snapshot_dir.mkdir(parents=True, exist_ok=True)

            # Create JSON without corresponding JPG
            metadata = {
                'snapshot': {
                    'filename': 'missing_image.jpg',
                    'timestamp': '2025-11-19T12:00:00'
                }
            }

            with open(snapshot_dir / 'missing_image.json', 'w') as f:
                json.dump(metadata, f)

            response = self.client.get('/api/snapshots/water_main')

            # Should still include the metadata
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload['count'], 1)

    def test_consumption_invalid_meter_type(self):
        """Test consumption endpoint with invalid/non-existent meter type"""
        response = self.client.get('/api/consumption/nonexistent_meter')

        # Should succeed but return empty data
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['status'], 'success')

    def test_snapshots_special_characters_in_name(self):
        """Test snapshots endpoint with special characters in meter name"""
        # Test with URL-encoded special chars
        response = self.client.get('/api/snapshots/water%20main%20test')

        # Should not crash
        self.assertIn(response.status_code, [200, 400, 404])

    @patch('meter_preview_ui.LOG_DIR')
    def test_consumption_single_reading_per_hour(self, mock_log_dir):
        """Test consumption endpoint with only one reading per hour"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            mock_log_dir.__truediv__ = lambda self, other: log_dir / other

            log_file = log_dir / 'water_readings.jsonl'
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Only one reading per hour - can't calculate consumption
            test_data = [
                {'total_reading': 100.0, 'timestamp': '2025-11-19T10:00:00'},
                {'total_reading': 200.0, 'timestamp': '2025-11-19T11:00:00'},
            ]

            with open(log_file, 'w') as f:
                for data in test_data:
                    f.write(json.dumps(data) + '\n')

            response = self.client.get('/api/consumption/water')

            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            # Should have empty hours list since we need >= 2 readings per hour
            self.assertEqual(payload['status'], 'success')

    @patch('meter_preview_ui.LOG_DIR')
    def test_consumption_identical_timestamps(self, mock_log_dir):
        """Test consumption endpoint with duplicate timestamps"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            mock_log_dir.__truediv__ = lambda self, other: log_dir / other

            log_file = log_dir / 'water_readings.jsonl'
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Same timestamp, different readings
            test_data = [
                {'total_reading': 100.0, 'timestamp': '2025-11-19T10:00:00'},
                {'total_reading': 100.5, 'timestamp': '2025-11-19T10:00:00'},
                {'total_reading': 101.0, 'timestamp': '2025-11-19T10:00:00'},
            ]

            with open(log_file, 'w') as f:
                for data in test_data:
                    f.write(json.dumps(data) + '\n')

            response = self.client.get('/api/consumption/water')

            # Should handle duplicate timestamps
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload['status'], 'success')


if __name__ == '__main__':
    unittest.main()
