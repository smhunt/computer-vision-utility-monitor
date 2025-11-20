# Thingino Camera Reference
**Wyze Cam V2 with Thingino Firmware**

Last Updated: 2025-11-18

## Camera Details

- **Model**: Wyze Cam V2 (ing-wyze-cam2-2d2e)
- **IP Address**: `${WATER_CAM_IP}` (default: 10.10.10.207)
- **Firmware**: Thingino (Open-source firmware for Ingenic SoC IP cameras)
- **SoC**: Ingenic T20 (likely, based on Wyze Cam V2 hardware)
- **Credentials**: `${WATER_CAM_USER}` / `${WATER_CAM_PASS}` (stored in `.env`)

## Available HTTP Endpoints

### Working Endpoints
- `/mjpeg` - MJPEG live stream
- `/x/preview.cgi` - Live preview page (redirects from `/`)
- `/x/info.cgi` - System information page (HTML)
- `/x/image.cgi` - Snapshot/still image capture

### Tested But Not Available
- `/x/config-system.cgi` - 404
- `/x/config-isp.cgi` - 404
- `/x/status.cgi` - 404
- `/x/temperature.cgi` - 404
- `/x/sensors.cgi` - 404
- `/x/json-*` endpoints - 403 Forbidden

## Image Capture

### MJPEG Stream
```python
import requests
from requests.auth import HTTPBasicAuth

url = "http://10.10.10.207/mjpeg"
auth = HTTPBasicAuth("root", "***REMOVED***")
response = requests.get(url, auth=auth, stream=True)
```

### Still Image
```python
url = "http://10.10.10.207/x/image.cgi"
auth = HTTPBasicAuth("root", "***REMOVED***")
response = requests.get(url, auth=auth)
image_data = response.content
```

## Camera Control (Day/Night Modes)

The camera supports day/night mode control via `/x/config-daynight.cgi`:

```python
import requests

url = "http://root:***REMOVED***@10.10.10.207/x/config-daynight.cgi"
settings = {
    "day_night_enabled": "false",  # true = auto, false = manual
    "day_night_ir850": "true",     # IR LEDs on/off
    "day_night_ircut": "false",    # IR cut filter (true = blocks IR)
    "day_night_color": "false"     # Color vs B&W
}
requests.post(url, data=settings)
```

### Common Configurations

**Day Mode (Natural Light)**
```python
{
    "day_night_enabled": "false",
    "day_night_ir850": "false",   # IR off
    "day_night_ircut": "true",    # Block IR
    "day_night_color": "true"     # Color
}
```

**Night Mode (IR Illumination)**
```python
{
    "day_night_enabled": "false",
    "day_night_ir850": "true",    # IR on
    "day_night_ircut": "false",   # Allow IR
    "day_night_color": "false"    # B&W
}
```

**Auto Mode**
```python
{
    "day_night_enabled": "true",  # Let camera decide
    "day_night_ir850": "true",
    "day_night_ircut": "true",
    "day_night_color": "true"
}
```

## Temperature Data

### Status: ⚠️ **NOT CURRENTLY ACCESSIBLE**

Temperature sensor access requires SSH access to the camera. The following sources were tested but are not currently accessible via HTTP:

#### Potential Temperature Sources (via SSH)
1. `/sys/class/thermal/thermal_zone0/temp` - Linux thermal zone (SoC temperature)
2. `/proc/jz/temperature` - Ingenic-specific SoC temperature
3. `/sys/class/hwmon/hwmon0/temp1_input` - Hardware monitoring
4. `temperature` command - Thingino built-in utility

### To Enable Temperature Capture

**Option 1: Enable SSH Access**
1. Access camera web interface at http://10.10.10.207/x/info.cgi
2. Enable SSH in settings
3. Set up SSH key authentication
4. Run temperature commands via SSH

**Option 2: Request Thingino API Enhancement**
- File feature request with Thingino project to expose temperature via HTTP API
- GitHub: https://github.com/themactep/thingino-firmware/issues

**Option 3: Use External Temperature Sensor**
- Integrate with a separate temperature sensor/service
- Use ambient temperature from home automation system (Home Assistant, etc.)
- Timestamp-based weather API lookup

## Camera Modes for Meter Reading

Based on testing (see `camera_preinspection.py`), the camera performs best for meter reading in:
- **Night Mode with IR** - Provides consistent illumination
- Avoid over-saturation from IR reflections
- May need to adjust camera angle to minimize glare

## Thingino Resources

- **GitHub**: https://github.com/themactep/thingino-firmware
- **Wiki**: https://github.com/themactep/thingino-firmware/wiki
- **Website**: https://thingino.com/
- **Discord**: Community support available
- **Telegram**: Active Telegram group

## Known Limitations

1. **SSH Not Configured**: SSH access is currently not enabled, limiting system-level access
2. **Limited HTTP API**: Many JSON endpoints return 403 Forbidden
3. **No EXIF Data**: Images from `/x/image.cgi` do not contain EXIF metadata
4. **Temperature Access**: Requires SSH; no HTTP endpoint available

## Future Enhancements

1. Configure SSH access for deeper system integration
2. Explore Thingino CGI script customization
3. Investigate MQTT integration for real-time sensor data
4. Consider upgrading firmware to latest Thingino release

## Integration with This Project

### Current Usage
```python
# config/meters.yaml
meters:
  - name: "water_main"
    camera_ip: "10.10.10.207"
    camera_user: "root"
    camera_pass: "***REMOVED***"
    stream_url: "http://10.10.10.207/mjpeg"
```

### Image Capture (see `/takemetersnapshot` command)
1. Fetch MJPEG stream
2. Extract first JPEG frame
3. Save to `/tmp/meter_snapshot_<name>.jpg`
4. Analyze with Claude Vision API

## Notes

- The camera is running Thingino, an open-source firmware replacement
- Original Wyze firmware and cloud features are no longer available
- Full local control via HTTP and (potentially) SSH
- Well-suited for home automation and monitoring projects
- Active development community for firmware improvements
