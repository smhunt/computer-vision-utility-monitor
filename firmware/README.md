# Firmware Options for Wyze Cam V2

This directory contains firmware download links and setup instructions for Wyze Cam V2.

## Recommended: OpenMiko

**OpenMiko** is the recommended firmware for this project because:
- ✅ More modern and actively maintained
- ✅ Cleaner codebase built on Buildroot
- ✅ Better documentation
- ✅ Simpler configuration
- ✅ Same RTSP and HTTP snapshot features

### Download OpenMiko

**Latest Release:** https://github.com/openmiko/openmiko/releases/latest

**For Wyze Cam V2:**
1. Go to: https://github.com/openmiko/openmiko/releases/latest
2. Download: `openmiko-*.*.*.tgz` (latest version)
3. Extract the archive
4. Find `openmiko.bin` inside

**Direct Download Commands:**
```bash
cd firmware/openmiko

# Download latest release
wget https://github.com/openmiko/openmiko/releases/latest/download/openmiko-0.1.17.tgz

# Extract
tar -xzf openmiko-0.1.17.tgz

# The file you need is: openmiko.bin
# This will be renamed to demo.bin when copying to SD card
```

### OpenMiko Setup Steps

1. **Format SD card as FAT32** (8-32GB)
2. **Copy firmware:**
   ```bash
   cp openmiko.bin /Volumes/YOUR_SD_CARD/demo.bin
   ```
3. **Flash camera:**
   - Power OFF camera
   - Insert SD card
   - Hold setup button
   - Plug in power (keep holding)
   - Wait for solid blue LED (~30 seconds)
   - Release button
   - Camera will flash (yellow LED), then reboot

4. **Configure WiFi:**
   - Camera creates hotspot: `MIKO_XXXX`
   - Connect with password: `12345678`
   - Open browser: http://192.168.1.1
   - Enter your WiFi credentials

5. **Access camera:**
   - Find camera IP from router
   - SSH: `ssh root@192.168.1.XXX` (password: `root`)
   - RTSP: `rtsp://192.168.1.XXX:8554/video3_unicast`
   - HTTP Snapshot: `http://192.168.1.XXX:8080/snapshot.jpg`

---

## Alternative: Dafang Hacks

**Dafang Hacks** is an older but still functional firmware option.

### Download Dafang Hacks

**Latest Release:** https://github.com/EliasKotlyar/Xiaomi-Dafang-Hacks/releases/latest

**Download Commands:**
```bash
cd firmware/dafang

# Download latest release
wget https://github.com/EliasKotlyar/Xiaomi-Dafang-Hacks/releases/latest/download/firmware_factory.bin
```

### Dafang Hacks Setup Steps

1. **Format SD card as FAT32**
2. **Copy firmware:**
   ```bash
   cp firmware_factory.bin /Volumes/YOUR_SD_CARD/demo.bin
   ```
3. **Flash camera:** (same process as OpenMiko)
4. **Configure WiFi:**
   - Camera creates hotspot: `DAFANG_XXXX`
   - Password: `1234567890`
   - Open browser: http://192.168.1.1
5. **Access camera:**
   - SSH: `ssh root@192.168.1.XXX` (password: `ismart12`)
   - RTSP: `rtsp://root:ismart12@192.168.1.XXX:554/live/ch00_0`
   - HTTP Snapshot: `http://root:ismart12@192.168.1.XXX/cgi-bin/currentpic.cgi`

---

## Comparison

| Feature | OpenMiko | Dafang Hacks |
|---------|----------|--------------|
| **Status** | Active | Maintenance |
| **Codebase** | Modern (Buildroot) | Older |
| **Setup** | Easier | More complex |
| **RTSP** | Yes (8554) | Yes (554) |
| **HTTP Snapshot** | Yes (/snapshot.jpg) | Yes (/cgi-bin/currentpic.cgi) |
| **SSH** | Yes (root/root) | Yes (root/ismart12) |
| **Documentation** | Better | Good |
| **Community** | Growing | Established |

---

## Quick SD Card Prep Script

Save as `prepare_sd_card.sh`:

```bash
#!/bin/bash
# Quick SD card preparation script

# Check for SD card mount point
if [ -z "$1" ]; then
    echo "Usage: ./prepare_sd_card.sh /path/to/sdcard"
    echo "Example: ./prepare_sd_card.sh /Volumes/WYZE"
    exit 1
fi

SD_CARD="$1"

if [ ! -d "$SD_CARD" ]; then
    echo "Error: SD card not found at $SD_CARD"
    exit 1
fi

# Choose firmware
echo "Select firmware:"
echo "1. OpenMiko (recommended)"
echo "2. Dafang Hacks"
read -p "Choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    if [ -f "firmware/openmiko/openmiko.bin" ]; then
        echo "Copying OpenMiko firmware..."
        cp firmware/openmiko/openmiko.bin "$SD_CARD/demo.bin"
        echo "✓ OpenMiko firmware copied to SD card"
    else
        echo "Error: OpenMiko firmware not found. Please download it first."
        exit 1
    fi
elif [ "$choice" = "2" ]; then
    if [ -f "firmware/dafang/firmware_factory.bin" ]; then
        echo "Copying Dafang Hacks firmware..."
        cp firmware/dafang/firmware_factory.bin "$SD_CARD/demo.bin"
        echo "✓ Dafang Hacks firmware copied to SD card"
    else
        echo "Error: Dafang firmware not found. Please download it first."
        exit 1
    fi
else
    echo "Invalid choice"
    exit 1
fi

echo ""
echo "SD card is ready! Next steps:"
echo "1. Eject SD card safely"
echo "2. Insert into Wyze Cam V2"
echo "3. Hold setup button and power on"
echo "4. Wait for solid blue LED"
echo "5. Release button and wait for flashing"
```

---

## Updating the Monitor Script

### For OpenMiko

Edit `wyze_cam_monitor.py`:

```python
# OpenMiko configuration
CAMERA_IP = os.getenv("WYZE_CAM_IP", "192.168.1.100")
SNAPSHOT_URL = f"http://{CAMERA_IP}:8080/snapshot.jpg"

# RTSP (alternative)
# RTSP_URL = f"rtsp://{CAMERA_IP}:8554/video3_unicast"
```

### For Dafang Hacks

```python
# Dafang Hacks configuration
CAMERA_IP = os.getenv("WYZE_CAM_IP", "192.168.1.100")
CAMERA_USER = os.getenv("WYZE_CAM_USER", "root")
CAMERA_PASS = os.getenv("WYZE_CAM_PASS", "ismart12")
SNAPSHOT_URL = f"http://{CAMERA_USER}:{CAMERA_PASS}@{CAMERA_IP}/cgi-bin/currentpic.cgi"

# RTSP (alternative)
# RTSP_URL = f"rtsp://{CAMERA_USER}:{CAMERA_PASS}@{CAMERA_IP}:554/live/ch00_0"
```

---

## Notes

- **DO NOT** include actual firmware binaries in git (they're large files)
- The `.gitignore` file already excludes `*.bin` and `*.tgz` files
- Users should download firmware directly from official sources
- Both firmware options work equally well for this water meter project

---

## Support

**OpenMiko:**
- GitHub: https://github.com/openmiko/openmiko
- Issues: https://github.com/openmiko/openmiko/issues

**Dafang Hacks:**
- GitHub: https://github.com/EliasKotlyar/Xiaomi-Dafang-Hacks
- Wiki: https://github.com/EliasKotlyar/Xiaomi-Dafang-Hacks/wiki
