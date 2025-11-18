import unittest
from unittest.mock import MagicMock, patch

import camera_presets


class CameraPresetsTests(unittest.TestCase):
    @patch("camera_presets.requests.get")
    def test_apply_preset_uses_specific_camera(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = camera_presets.apply_preset(
            "day_clear",
            camera_ip="1.2.3.4",
            camera_user="user",
            camera_pass="pass",
        )

        self.assertTrue(result["success"])
        self.assertEqual(len(result["errors"]), 0)

        called_urls = [call.args[0] for call in mock_get.call_args_list]
        self.assertTrue(all(url.startswith("http://user:pass@1.2.3.4") for url in called_urls))

    @patch("camera_presets.requests.get")
    def test_apply_preset_reports_http_failures(self, mock_get):
        failing_response = MagicMock()
        failing_response.status_code = 500
        mock_get.return_value = failing_response

        result = camera_presets.apply_preset("night_vision", camera_ip="1.1.1.1")

        self.assertFalse(result["success"])
        self.assertGreaterEqual(len(result["errors"]), 1)


if __name__ == "__main__":
    unittest.main()
