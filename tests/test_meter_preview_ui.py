import unittest
from unittest.mock import patch

import meter_preview_ui


class ApiPresetTests(unittest.TestCase):
    def setUp(self):
        meter_preview_ui.app.testing = True
        self.client = meter_preview_ui.app.test_client()

    @patch("meter_preview_ui.apply_camera_preset")
    def test_preset_endpoint_uses_meter_config(self, mock_apply):
        meter_preview_ui.CONFIG = {
            "meters": [
                {
                    "name": "water_main",
                    "type": "water",
                    "camera_ip": "2.2.2.2",
                    "camera_user": "cfg_user",
                    "camera_pass": "cfg_pass",
                }
            ]
        }

        mock_apply.return_value = {"success": True}

        response = self.client.post("/api/preset/water/day_clear")

        self.assertEqual(response.status_code, 200)
        mock_apply.assert_called_once()

        _, kwargs = mock_apply.call_args
        self.assertEqual(kwargs["camera_ip"], "2.2.2.2")
        self.assertEqual(kwargs["camera_user"], "cfg_user")
        self.assertEqual(kwargs["camera_pass"], "cfg_pass")

    def test_preset_endpoint_missing_meter(self):
        meter_preview_ui.CONFIG = {"meters": []}

        response = self.client.post("/api/preset/water/day_clear")

        self.assertEqual(response.status_code, 404)
        payload = response.get_json()
        self.assertIn("Meter type water not found", payload.get("message", ""))


if __name__ == "__main__":
    unittest.main()
