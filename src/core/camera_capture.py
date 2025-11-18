"""
Camera Capture Module - Handles image capture from various camera sources

Supports:
- MJPEG streams (Thingino firmware)
- Static snapshot URLs (Dafang Hacks)
- RTSP streams (with ffmpeg)
"""

import base64
import urllib.request
import requests
import subprocess
from typing import Dict, Any, Optional


class CameraCapture:
    """Handles image capture from Wyze cameras with various firmware"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize camera capture with configuration

        Args:
            config: Dictionary containing camera configuration
                Required keys:
                    - camera_ip: IP address of camera
                    - camera_user: Camera username
                    - camera_pass: Camera password
                Optional keys:
                    - stream_url: MJPEG stream URL
                    - snapshot_url: Static snapshot URL
        """
        self.config = config
        self.camera_ip = config.get("camera_ip")
        self.camera_user = config.get("camera_user")
        self.camera_pass = config.get("camera_pass")
        self.stream_url = config.get("stream_url")

        # Determine snapshot mode
        if self.stream_url:
            self.snapshot_mode = "mjpeg"
            self.snapshot_url = self.stream_url
        else:
            self.snapshot_mode = "static"
            self.snapshot_url = config.get("snapshot_url") or \
                f"http://{self.camera_user}:{self.camera_pass}@{self.camera_ip}/cgi-bin/currentpic.cgi"

    def extract_mjpeg_frame(self, stream_url: str, output_path: str) -> bool:
        """
        Extract a single JPEG frame from an MJPEG stream

        Args:
            stream_url: URL of MJPEG stream
            output_path: Path to save extracted frame

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create authorization header if credentials are provided
            req = urllib.request.Request(stream_url)
            if self.camera_user and self.camera_pass:
                credentials = base64.b64encode(
                    f"{self.camera_user}:{self.camera_pass}".encode()
                ).decode()
                req.add_header('Authorization', f'Basic {credentials}')

            response = urllib.request.urlopen(req, timeout=10)

            # Read MJPEG stream and extract first JPEG frame
            data = b''
            while len(data) < 600000:  # Read up to 600KB
                chunk = response.read(4096)
                if not chunk:
                    break
                data += chunk

            # Find JPEG frame boundaries (FFD8 = start, FFD9 = end)
            start = data.find(b'\xff\xd8')
            end = data.find(b'\xff\xd9', start) + 2

            if start >= 0 and end > start:
                jpeg_data = data[start:end]
                with open(output_path, 'wb') as f:
                    f.write(jpeg_data)
                return True
            return False
        except Exception as e:
            print(f"  MJPEG extraction error: {e}")
            return False

    def capture_static_snapshot(self, snapshot_url: str, output_path: str) -> bool:
        """
        Capture from static snapshot URL (Dafang Hacks)

        Args:
            snapshot_url: URL of snapshot endpoint
            output_path: Path to save snapshot

        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.get(snapshot_url, timeout=10)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except Exception as e:
            print(f"  Capture error: {e}")
            return False

    def capture_from_rtsp(self, rtsp_url: str, output_path: str) -> bool:
        """
        Capture from RTSP stream using ffmpeg

        Requires: ffmpeg installed on system

        Args:
            rtsp_url: RTSP stream URL
            output_path: Path to save frame

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = [
                'ffmpeg',
                '-i', rtsp_url,
                '-frames:v', '1',
                '-q:v', '2',
                '-y',
                output_path
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=15,
                stderr=subprocess.DEVNULL
            )
            return result.returncode == 0
        except Exception as e:
            print(f"  RTSP capture error: {e}")
            return False

    def capture_snapshot(self, output_path: str) -> bool:
        """
        Capture snapshot using configured method

        Args:
            output_path: Path to save snapshot

        Returns:
            True if successful, False otherwise
        """
        if self.snapshot_mode == "mjpeg":
            return self.extract_mjpeg_frame(self.snapshot_url, output_path)
        else:
            return self.capture_static_snapshot(self.snapshot_url, output_path)

    def test_connection(self) -> bool:
        """
        Test if camera is accessible

        Returns:
            True if camera is reachable, False otherwise
        """
        import tempfile

        try:
            # Create temporary file for test
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=True) as tmp:
                success = self.capture_snapshot(tmp.name)
                return success
        except Exception as e:
            print(f"  Connection test error: {e}")
            return False

    def get_snapshot_url(self) -> str:
        """
        Get the snapshot URL (with credentials masked)

        Returns:
            Snapshot URL with password masked
        """
        if self.camera_pass:
            return self.snapshot_url.replace(self.camera_pass, '***')
        return self.snapshot_url

    def get_camera_info(self) -> Dict[str, str]:
        """
        Get camera configuration information

        Returns:
            Dictionary with camera info
        """
        return {
            "camera_ip": self.camera_ip,
            "snapshot_mode": self.snapshot_mode,
            "snapshot_url": self.get_snapshot_url()
        }
