# Ready-to-Copy SD Card Files

These folders contain firmware files already renamed to `demo.bin` and ready to copy to your SD card.

## Quick Start

### Option 1: OpenMiko (Recommended)

```bash
# Copy entire folder to your FAT32-formatted SD card
cp sd_card_ready/openmiko/demo.bin /Volumes/YOUR_SD_CARD/

# Or on Linux
cp sd_card_ready/openmiko/demo.bin /media/$USER/YOUR_SD_CARD/
```

**After WiFi setup:**
- SSH: `ssh root@192.168.1.XXX` (password: `root`)
- RTSP: `rtsp://192.168.1.XXX:8554/video3_unicast`
- HTTP Snapshot: `http://192.168.1.XXX:8080/snapshot.jpg`

### Option 2: Dafang Hacks

```bash
# Copy entire folder to your FAT32-formatted SD card
cp sd_card_ready/dafang/demo.bin /Volumes/YOUR_SD_CARD/

# Or on Linux
cp sd_card_ready/dafang/demo.bin /media/$USER/YOUR_SD_CARD/
```

**After WiFi setup:**
- SSH: `ssh root@192.168.1.XXX` (password: `ismart12`)
- RTSP: `rtsp://root:ismart12@192.168.1.XXX:554/live/ch00_0`
- HTTP Snapshot: `http://root:ismart12@192.168.1.XXX/cgi-bin/currentpic.cgi`

## Flashing Instructions

1. **Format SD card as FAT32** (8-32GB recommended)
2. **Copy demo.bin** from either `openmiko/` or `dafang/` folder
3. **Flash camera:**
   - Power OFF camera
   - Insert SD card
   - Hold SETUP button (on bottom)
   - Plug in power (keep holding button)
   - Wait for solid BLUE LED (~30 seconds)
   - Release button
   - Yellow LED = flashing in progress
   - Wait 3-4 minutes

4. **Configure WiFi:**
   - OpenMiko: Connect to `MIKO_XXXX` (password: `12345678`)
   - Dafang: Connect to `DAFANG_XXXX` (password: `1234567890`)
   - Open browser: `http://192.168.1.1`
   - Enter your WiFi credentials

5. **Find camera IP** from your router's DHCP leases

6. **Test snapshot:**
   ```bash
   # OpenMiko
   curl http://CAMERA_IP:8080/snapshot.jpg -o test.jpg

   # Dafang
   curl --user root:ismart12 http://CAMERA_IP/cgi-bin/currentpic.cgi -o test.jpg
   ```

## File Verification

**OpenMiko** (v1.0.0-alpha.1):
- File: `demo.bin`
- Size: ~11MB
- Source: https://github.com/openmiko/openmiko/releases

**Dafang Hacks** (cfw-1.2):
- File: `demo.bin`
- Size: ~11MB
- Source: https://github.com/EliasKotlyar/Xiaomi-Dafang-Hacks

## Using with Monitor Script

### For OpenMiko:

Edit `wyze_cam_monitor.py` or set environment variables:

```bash
export WYZE_CAM_IP=192.168.1.100
export WYZE_CAM_USER=root
export WYZE_CAM_PASS=root
export ANTHROPIC_API_KEY=sk-ant-...

# Update snapshot URL in script to:
SNAPSHOT_URL = f"http://{CAMERA_IP}:8080/snapshot.jpg"
```

### For Dafang:

The existing `wyze_cam_monitor.py` is already configured for Dafang! Just set:

```bash
export WYZE_CAM_IP=192.168.1.100
export WYZE_CAM_PASS=ismart12  # (or your new password)
export ANTHROPIC_API_KEY=sk-ant-...

python3 wyze_cam_monitor.py
```

## Troubleshooting

### LED doesn't turn yellow
- Verify SD card is FAT32
- Make sure ONLY `demo.bin` is on the card
- Try a different SD card (some are incompatible)
- Hold setup button firmly during power-on

### Can't connect to WiFi hotspot
- Wait 5 minutes after flashing
- Check 2.4GHz WiFi is enabled on your device
- Power cycle camera

### Camera not accessible after WiFi setup
- Check camera IP from router
- Wait 5 minutes after WiFi configuration
- Verify you're on the same network

## Next Steps

After successful flash and WiFi setup:
1. Set a static IP for the camera (recommended)
2. Change default password
3. Test the snapshot URL
4. Update and run `wyze_cam_monitor.py`
5. Mount camera to view your water meter

See `WYZE_QUICKSTART.md` for complete setup guide.
