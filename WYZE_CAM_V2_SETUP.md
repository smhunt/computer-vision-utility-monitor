# Wyze Cam V2 with Dafang Hacks - Setup Guide

**Using alternative firmware for local RTSP streaming and control**

---

## What is Dafang Hacks?

**Dafang Hacks** (github.com/EliasKotlyar/Xiaomi-Dafang-Hacks) is custom firmware that:
- ✅ Provides **RTSP streaming** (no cloud needed)
- ✅ Enables **local HTTP snapshots**
- ✅ Adds **MQTT control**
- ✅ Removes Wyze cloud dependency
- ✅ Free and open source
- ✅ Works perfectly with Wyze Cam V2

---

## Why Use This Setup?

### Benefits for Water Meter Reading

| Feature | Stock Wyze | Dafang Hacks |
|---------|-----------|--------------|
| RTSP Stream | ❌ No | ✅ Yes |
| Local Snapshots | ❌ No | ✅ Yes |
| Cloud Required | ✅ Yes | ❌ No |
| Privacy | ⚠️ Cloud | ✅ 100% Local |
| Latency | High | Low |
| Cost | $0 (after cam) | $0 (after cam) |

**Perfect for basement/utility room meter monitoring!**

---

## Prerequisites

### Hardware
- Wyze Cam V2 (model WYZEC1)
- MicroSD card (8-32GB, Class 10)
- MicroUSB cable + power adapter
- Computer with SD card reader

### Software
- SD card formatter
- Text editor
- SSH client (optional)

---

## Installation Steps

### 1. Download Firmware

```bash
# Latest release from GitHub
wget https://github.com/EliasKotlyar/Xiaomi-Dafang-Hacks/releases/latest/download/firmware_factory.bin

# Or download manually from:
# https://github.com/EliasKotlyar/Xiaomi-Dafang-Hacks/releases
```

### 2. Prepare SD Card

```bash
# Format SD card as FAT32
# On Linux:
sudo mkfs.vfat -F 32 /dev/sdX1

# On macOS:
diskutil eraseDisk FAT32 WYZE /dev/diskX

# On Windows:
# Use SD Card Formatter tool
# Format as FAT32
```

### 3. Copy Firmware to SD Card

```bash
# Copy firmware to root of SD card
cp firmware_factory.bin /path/to/sdcard/

# Rename it (IMPORTANT!)
mv /path/to/sdcard/firmware_factory.bin /path/to/sdcard/demo.bin

# Verify
ls -la /path/to/sdcard/
# Should see: demo.bin
```

### 4. Flash Camera

1. **Power OFF** Wyze Cam V2
2. Insert prepared SD card
3. Hold **Setup button** on bottom
4. Plug in power (keep holding button)
5. Wait for **yellow LED** (10-15 seconds)
6. Release button when LED turns **solid blue**
7. Wait 3-4 minutes for flash to complete
8. Camera will reboot automatically

**LED Indicators:**
- Yellow → Flashing firmware
- Solid Blue → Flash complete
- Blinking Blue → Booting up

### 5. Initial Configuration

After reboot:
1. Camera creates WiFi hotspot: `DAFANG_XXXX`
2. Connect to this network (password: `1234567890`)
3. Open browser: http://192.168.1.1
4. Configure your home WiFi

**Alternative: USB Serial Console**
- Connect via USB TTL adapter
- Baud: 115200
- Configure WiFi through console

---

## Configuration for Water Meter Reading

### 1. Access Web Interface

After WiFi setup, camera gets IP from your router.

Find camera IP:
```bash
# Check router DHCP leases
# Or use nmap
nmap -sn 192.168.1.0/24 | grep -B 2 "Dafang"

# Or check Dafang web interface discovery
```

Access web interface:
```
http://192.168.1.XXX
```

Default credentials:
- Username: `root`
- Password: `ismart12`

**IMPORTANT: Change default password!**

### 2. Enable RTSP Stream

Web interface → Settings → RTSP

```yaml
RTSP Server: Enabled
Port: 554
Path: /live/ch00_0

# Full URL format:
rtsp://root:ismart12@192.168.1.XXX:554/live/ch00_0
```

### 3. Configure HTTP Snapshots

The camera automatically provides snapshots at:
```
http://192.168.1.XXX/cgi-bin/currentpic.cgi
```

**For authentication:**
```bash
curl --user root:ismart12 http://192.168.1.XXX/cgi-bin/currentpic.cgi -o snapshot.jpg
```

### 4. Optimize for Water Meter

**Video Settings:**
- Resolution: 1920x1080 (full HD)
- FPS: 15 (saves bandwidth, plenty for meter)
- Bitrate: 1024 Kbps (good quality, low bandwidth)
- H.264 encoding

**Camera Settings:**
- IR Night Mode: Auto
- Flip Image: As needed for mounting
- Motion Detection: Disabled (not needed)
- Audio: Disabled (not needed)

### 5. Static IP Configuration

**Recommended for reliability:**

Web interface → Network → Static IP

```yaml
IP Address: 192.168.1.100
Netmask: 255.255.255.0
Gateway: 192.168.1.1
DNS: 192.168.1.1
```

Or via SSH:
```bash
ssh root@192.168.1.XXX
# Password: ismart12

# Edit network config
vi /system/sdcard/config/wpa_supplicant.conf
```

---

## Integration with Water Meter Reader

### Option 1: RTSP Stream (Recommended)

Update your `config/config.yaml`:

```yaml
camera:
  type: "rtsp"
  url: "rtsp://root:ismart12@192.168.1.100:554/live/ch00_0"
  timeout: 10
  retry_attempts: 3
```

**Capture snapshot from RTSP:**

```bash
# Using ffmpeg
ffmpeg -i rtsp://root:ismart12@192.168.1.100:554/live/ch00_0 \
       -frames:v 1 \
       -q:v 2 \
       meter_snapshot.jpg

# In Python (from your monitor script)
import subprocess

def capture_from_rtsp(rtsp_url, output_path):
    cmd = [
        'ffmpeg',
        '-i', rtsp_url,
        '-frames:v', '1',
        '-q:v', '2',
        '-y',  # Overwrite
        output_path
    ]
    subprocess.run(cmd, capture_output=True)
```

### Option 2: HTTP Snapshot (Simpler)

Update your `config/config.yaml`:

```yaml
camera:
  type: "http"
  url: "http://root:ismart12@192.168.1.100/cgi-bin/currentpic.cgi"
  timeout: 5
```

**Use directly with llm_reader.py:**

```bash
python src/llm_reader.py "http://root:ismart12@192.168.1.100/cgi-bin/currentpic.cgi"
```

### Option 3: Continuous Monitoring

```python
#!/usr/bin/env python3
"""
Wyze Cam V2 (Dafang) + Water Meter Reader
"""
import requests
import time
from pathlib import Path
import sys
sys.path.insert(0, 'src')
from llm_reader import read_meter_with_claude

# Camera config
CAMERA_IP = "192.168.1.100"
CAMERA_USER = "root"
CAMERA_PASS = "ismart12"
SNAPSHOT_URL = f"http://{CAMERA_USER}:{CAMERA_PASS}@{CAMERA_IP}/cgi-bin/currentpic.cgi"

# Monitoring config
INTERVAL = 600  # 10 minutes
TEMP_IMAGE = "/tmp/meter_snapshot.jpg"

def capture_snapshot():
    """Capture snapshot from Wyze Cam"""
    response = requests.get(SNAPSHOT_URL, timeout=10)
    if response.status_code == 200:
        with open(TEMP_IMAGE, 'wb') as f:
            f.write(response.content)
        return True
    return False

def main():
    print("Starting Wyze Cam V2 + Water Meter monitoring...")
    print(f"Camera: {CAMERA_IP}")
    print(f"Interval: {INTERVAL} seconds")
    print()
    
    while True:
        try:
            # Capture snapshot
            print("Capturing snapshot...", end=" ")
            if capture_snapshot():
                print("✓")
                
                # Read meter
                print("Reading meter...", end=" ")
                result = read_meter_with_claude(TEMP_IMAGE)
                
                if "error" not in result:
                    print(f"✓ {result['total_reading']:.3f} m³")
                    print(f"  Digital: {result['digital_reading']}")
                    print(f"  Dial: {result['dial_reading']:.3f}")
                else:
                    print(f"✗ Error: {result['error']}")
            else:
                print("✗ Failed to capture")
            
            print()
            time.sleep(INTERVAL)
            
        except KeyboardInterrupt:
            print("\nStopped by user")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)  # Wait 1 minute on error

if __name__ == "__main__":
    main()
```

---

## Physical Mounting

### Positioning the Wyze Cam V2

**Recommended Setup:**

```
┌─────────────────────┐
│   Water Meter       │
│  ┌─────────────┐   │
│  │  Digital    │   │  ← 15-20cm distance
│  │  [0226]     │   │
│  │   ●────     │◄──┼─── Clear view of:
│  │  Dial (Red) │   │    - Digital display
│  └─────────────┘   │    - Full dial face
└─────────────────────┘    - Red needle
         ▲
         │
    [Wyze Cam V2]
```

**Mounting Options:**

1. **Magnetic mount** (if metal surface nearby)
2. **Adhesive mount** (3M command strips)
3. **Mini tripod** (Gorillapod style)
4. **Wall bracket** (3D printed or purchased)

**Positioning Tips:**
- Distance: 15-20cm from meter face
- Angle: Perpendicular or slight tilt (reduce glare)
- Avoid: Direct overhead lighting
- Use: Constant lighting (LED strip if dark)

### Power Options

1. **USB Power Bank** (temporary testing)
2. **Wall Outlet** (via USB adapter)
3. **POE Splitter** (if running ethernet nearby)
4. **Long USB Cable** (from nearby outlet)

---

## Advanced Configuration

### 1. MQTT Integration (Optional)

Dafang firmware includes MQTT support:

```yaml
# Web interface → MQTT Settings
MQTT Broker: 192.168.1.50
Port: 1883
Username: homeassistant
Password: your-password
Topic Prefix: dafang/meter_cam
```

**Benefits:**
- Camera status monitoring
- Remote control (PTZ if applicable)
- Motion detection events
- Integration with Home Assistant

### 2. Scripting via SSH

```bash
ssh root@192.168.1.100

# Take snapshot
/system/sdcard/bin/getimage > /tmp/snapshot.jpg

# Check camera status
/system/sdcard/scripts/status.sh

# Adjust settings
/system/sdcard/scripts/config.sh
```

### 3. Night Vision Optimization

For dark basements:

```bash
# Force IR LEDs on
curl --user root:ismart12 \
     "http://192.168.1.100/cgi-bin/configManager.cgi?action=setConfig&Infra[0].Mode=Night"

# Or via web interface → IR Settings → Always On
```

### 4. Custom Resolution for Lower Bandwidth

If you want to save bandwidth:

```bash
# 1280x720 (720p) - Still good for meter reading
# Web interface → Video Settings
# Or via API:
curl --user root:ismart12 \
     "http://192.168.1.100/cgi-bin/configManager.cgi?action=setConfig&Encode[0].MainFormat[0].Video.Width=1280&Encode[0].MainFormat[0].Video.Height=720"
```

---

## Troubleshooting

### Camera Won't Flash

**Symptoms:** LED doesn't turn yellow
**Solutions:**
1. Verify SD card is FAT32
2. Ensure file is named exactly `demo.bin`
3. Try different SD card (some are incompatible)
4. Hold setup button firmly during power-on

### Can't Connect to WiFi Hotspot

**Symptoms:** `DAFANG_XXXX` network not visible
**Solutions:**
1. Wait 5 minutes after flashing
2. Power cycle camera
3. Check if 2.4GHz WiFi enabled on phone/laptop
4. Use USB serial console for WiFi config

### RTSP Stream Not Working

**Symptoms:** Connection timeout or refused
**Solutions:**
```bash
# Test with VLC
vlc rtsp://root:ismart12@192.168.1.100:554/live/ch00_0

# Test with ffmpeg
ffmpeg -i rtsp://root:ismart12@192.168.1.100:554/live/ch00_0 -frames:v 1 test.jpg

# Check RTSP server status via SSH
ssh root@192.168.1.100
ps | grep rtsp
```

### Snapshot URL Returns 401/403

**Symptoms:** Authentication failed
**Solutions:**
1. Verify username/password
2. Check URL encoding: `http://root:ismart12@...`
3. Try basic auth header:
```python
import requests
response = requests.get(
    'http://192.168.1.100/cgi-bin/currentpic.cgi',
    auth=('root', 'ismart12')
)
```

### Image Quality Poor

**Solutions:**
1. Clean camera lens
2. Increase resolution (1920x1080)
3. Increase bitrate (1024-2048 Kbps)
4. Add lighting (LED strip)
5. Adjust focus (remove lens cover, adjust)

### Camera Randomly Reboots

**Solutions:**
1. Use better power supply (5V 2A minimum)
2. Check for overheating
3. Update to latest Dafang release
4. Check SD card health

---

## Security Best Practices

### 1. Change Default Password

```bash
ssh root@192.168.1.100
passwd root
# Enter new password twice
```

### 2. Restrict Network Access

**Router firewall rules:**
- Block camera from internet access
- Allow only local network access
- Whitelist your monitoring server IP

### 3. Use Strong Authentication

Update `.env`:
```bash
CAMERA_URL="http://admin:NewStrongPassword123@192.168.1.100/cgi-bin/currentpic.cgi"
```

### 4. Keep Firmware Updated

```bash
# Check for updates
https://github.com/EliasKotlyar/Xiaomi-Dafang-Hacks/releases

# Flash new version via web interface
# Settings → Update → Upload new firmware
```

---

## Home Assistant Integration

### Camera Entity

```yaml
# configuration.yaml
camera:
  - platform: generic
    name: Water Meter Cam
    still_image_url: http://root:ismart12@192.168.1.100/cgi-bin/currentpic.cgi
    stream_source: rtsp://root:ismart12@192.168.1.100:554/live/ch00_0
    verify_ssl: false
```

### Automation Example

```yaml
automation:
  - alias: "Read Water Meter Every 10 Minutes"
    trigger:
      platform: time_pattern
      minutes: "/10"
    action:
      - service: shell_command.read_water_meter
```

---

## Complete Example: Continuous Monitoring

Save as `examples/wyze_cam_monitor.py`:

```python
#!/usr/bin/env python3
"""
Water Meter Monitoring with Wyze Cam V2 (Dafang Hacks)
"""

import os
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from llm_reader import read_meter_with_claude

# Configuration from environment
CAMERA_IP = os.getenv("WYZE_CAM_IP", "192.168.1.100")
CAMERA_USER = os.getenv("WYZE_CAM_USER", "root")
CAMERA_PASS = os.getenv("WYZE_CAM_PASS", "ismart12")
INTERVAL = int(os.getenv("READING_INTERVAL", "600"))

SNAPSHOT_URL = f"http://{CAMERA_USER}:{CAMERA_PASS}@{CAMERA_IP}/cgi-bin/currentpic.cgi"
TEMP_IMAGE = "/tmp/meter_snapshot.jpg"


def test_camera_connection():
    """Test camera connectivity"""
    try:
        response = requests.get(SNAPSHOT_URL, timeout=5)
        return response.status_code == 200
    except:
        return False


def capture_snapshot():
    """Capture and save snapshot"""
    try:
        response = requests.get(SNAPSHOT_URL, timeout=10)
        if response.status_code == 200:
            with open(TEMP_IMAGE, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print(f"  HTTP {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("  Timeout")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


def main():
    print("="*60)
    print("Water Meter Monitor - Wyze Cam V2 (Dafang Hacks)")
    print("="*60)
    print()
    print(f"Camera: {CAMERA_IP}")
    print(f"Interval: {INTERVAL} seconds ({INTERVAL/60:.1f} minutes)")
    
    # Test camera first
    print("\nTesting camera connection...", end=" ")
    if test_camera_connection():
        print("✓ Connected")
    else:
        print("✗ Failed")
        print("\nPlease check:")
        print("1. Camera IP address is correct")
        print("2. Camera is powered on")
        print("3. Network connectivity")
        print("4. Username/password")
        return
    
    print("\nStarting monitoring... (Ctrl+C to stop)")
    print()
    
    readings = []
    
    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Capture
            print(f"[{timestamp}] Capturing...", end=" ")
            if not capture_snapshot():
                print()
                time.sleep(60)
                continue
            print("✓", end=" ")
            
            # Read
            print("Reading...", end=" ")
            result = read_meter_with_claude(TEMP_IMAGE)
            
            if "error" not in result:
                print(f"✓ {result['total_reading']:.3f} m³")
                print(f"  Digital: {result['digital_reading']}, Dial: {result['dial_reading']:.3f}")
                print(f"  Confidence: {result['confidence']}")
                
                readings.append(result)
                
                # Calculate flow
                if len(readings) >= 2:
                    prev = readings[-2]
                    time_diff = (datetime.fromisoformat(result['timestamp']) -
                               datetime.fromisoformat(prev['timestamp'])).seconds / 60
                    volume_diff = result['total_reading'] - prev['total_reading']
                    flow_rate = (volume_diff * 1000) / time_diff
                    
                    if flow_rate > 0.01:
                        print(f"  Flow: {flow_rate:.2f} L/min")
            else:
                print(f"✗ {result.get('error', 'Unknown error')}")
            
            print()
            time.sleep(INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nStopped by user")
        if len(readings) >= 2:
            duration = (datetime.fromisoformat(readings[-1]['timestamp']) -
                       datetime.fromisoformat(readings[0]['timestamp'])).seconds / 3600
            usage = (readings[-1]['total_reading'] - readings[0]['total_reading']) * 1000
            print(f"\nSession: {len(readings)} readings over {duration:.1f} hours")
            print(f"Usage: {usage:.1f} liters")


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)
    
    main()
```

Run it:
```bash
export WYZE_CAM_IP=192.168.1.100
export WYZE_CAM_USER=root
export WYZE_CAM_PASS=ismart12
python examples/wyze_cam_monitor.py
```

---

## Cost Breakdown

**Hardware:**
- Wyze Cam V2: $20-25 (if buying new) or $0 (you have it!)
- MicroSD Card (8GB): $5
- **Total: $5-25**

**Ongoing:**
- Power: ~$0.50/month (3W @ $0.12/kWh)
- API: $0.43/month (10-min intervals)
- **Total: ~$1/month**

**Year 1: ~$30** (including hardware)

vs. ESP32-CAM: $12 + $1/month = $24/year

**Why choose Wyze?**
- Better image quality (1080p vs 640x480)
- Better low-light performance
- More stable hardware
- You already have it!

---

## Summary Checklist

### Setup
- [ ] Download Dafang Hacks firmware
- [ ] Format SD card (FAT32)
- [ ] Copy and rename firmware (`demo.bin`)
- [ ] Flash camera (hold button, wait for yellow LED)
- [ ] Configure WiFi

### Configuration
- [ ] Access web interface (http://camera-ip)
- [ ] Change default password
- [ ] Set static IP
- [ ] Enable RTSP stream
- [ ] Test HTTP snapshot URL
- [ ] Optimize video settings

### Integration
- [ ] Update `config/config.yaml` with camera URL
- [ ] Test single reading
- [ ] Mount camera near meter
- [ ] Adjust position/focus
- [ ] Start continuous monitoring

### Optional
- [ ] Configure MQTT
- [ ] Set up Home Assistant integration
- [ ] Enable night vision
- [ ] Create automation rules

---

**You now have a powerful, local, privacy-friendly water meter monitoring system using your Wyze Cam V2!**

📹 Camera: Dafang Hacks firmware  
🌐 Access: 100% local (no cloud)  
💰 Cost: ~$1/month  
🔒 Privacy: Everything stays on your network  
📊 Quality: 1080p clear meter readings  

Next: Mount the camera and start monitoring! 💧
