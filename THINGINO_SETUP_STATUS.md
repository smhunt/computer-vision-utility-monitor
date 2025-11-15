# 🚀 Thingino Setup - Current Status

**Date:** November 14, 2025
**Status:** SD Card Ready for Flashing

---

## ✅ Completed

### 1. Installed Balena Etcher
- **Location:** `/Applications/balenaEtcher.app`
- **Version:** v2.1.4
- **Status:** Ready to use

### 2. Downloaded Thingino Installer
- **Image File:** `/Users/seanhunt/Desktop/wyze-cam-2-thingino.img`
- **Size:** 120MB
- **Source:** WLTechBlog Thingino Installers (https://github.com/wltechblog/thingino-installers)
- **Model:** Wyze Cam V2
- **Status:** Extracted and verified

### 3. Updated Project Documentation
- Updated `wyze_cam_monitor.py` to support both Thingino and Dafang Hacks
- Updated `WYZE_QUICKSTART.md` with Thingino flashing instructions
- Added configuration notes for both firmware types

---

## 🎯 Next Steps

### Phase 1: Flash SD Card (15 minutes)

1. **Insert SD card** into your Mac
2. **Open Balena Etcher** from Applications
3. **Select Image:**
   - Click "Flash from file"
   - Navigate to: `~/Desktop/wyze-cam-2-thingino.img`
4. **Select Target:**
   - Click "Select target"
   - Choose your SD card
5. **Flash:**
   - Click "Flash"
   - Wait for completion (~5-10 minutes)

### Phase 2: Boot Camera (5 minutes)

1. Power OFF your Wyze Cam V2
2. Insert flashed SD card
3. Hold the **SETUP button** on the back
4. Plug in power while holding
5. Release button when **LED turns blue**
6. Wait 3-4 minutes for boot

### Phase 3: Configure Thingino (10 minutes)

1. Look for wireless network from camera (e.g., `WYZE_SETUP_xxxxx`)
2. Connect to it
3. Open browser → `http://192.168.1.1` (or check IP from network)
4. Follow setup wizard:
   - Configure WiFi credentials
   - Set static IP (recommended: `192.168.1.100`)
   - Note snapshot/MJPEG URL
5. Camera reboots and joins your network

### Phase 4: Backup Factory Firmware (Important!)

After setup completes, the SD card will have:
- `WYZE_BACKUP_xxxxx/combined_backup.bin` - Your original firmware

**Save this file separately** - It's unique to your camera and needed if you want to revert to Wyze firmware later.

### Phase 5: Update Firmware (5 minutes)

Once Thingino is running:
1. Access web interface: `http://192.168.1.100`
2. Go to Settings → System Update
3. Install latest firmware version

### Phase 6: Configure Monitoring Script (5 minutes)

Update the monitoring script with your camera details:

```bash
cd ~/Code/computer-vision-utility-monitor

# Set environment variables
export ANTHROPIC_API_KEY=sk-ant-...
export WYZE_CAM_IP=192.168.1.100

# For Thingino: Find snapshot URL in web interface
# Add to environment or edit wyze_cam_monitor.py:
export WYZE_CAM_SNAPSHOT_URL="http://192.168.1.100/api/image/snapshot"

# Test connection
python wyze_cam_monitor.py
```

---

## 📋 Key Configuration Details

### Thingino Firmware
- **Web Interface:** `http://CAMERA_IP`
- **Default Port:** 80
- **Snapshot URL:** Check in web interface (Settings → Snapshot)
- **Common URLs:**
  - `http://192.168.1.100/api/image/snapshot`
  - `http://192.168.1.100/api/v1/image/snapshot`
  - Check camera web interface for exact URL

### Monitoring Script Status
- **File:** `wyze_cam_monitor.py`
- **Updated for:** Both Thingino and Dafang Hacks
- **Default Settings:**
  - Interval: 10 minutes
  - Default Dafang URL configured
  - Thingino users: Update snapshot URL in script or environment

### Required Credentials
For Thingino, check the web interface setup for:
- Admin username/password
- Snapshot/MJPEG endpoint
- RTSP stream endpoint (optional)

---

## 🔧 Troubleshooting Quick Reference

### If camera won't flash:
- Verify SD card is FAT32
- Try different USB card reader
- Try a different SD card

### If camera won't boot:
- Hold SETUP button longer (5+ seconds)
- LED sequence: Yellow (flashing) → Blue (done)
- If stuck on yellow, power cycle and try again

### If can't access web interface:
- Wait 5+ minutes after flashing
- Check camera IP from router
- Try ping: `ping 192.168.1.100`
- Check camera is on same WiFi network

### If monitoring script can't connect:
- Verify snapshot URL is correct
- Test manually: `curl -v http://192.168.1.100/api/image/snapshot`
- Check WYZE_CAM_IP environment variable
- Verify camera has internet connectivity

---

## 📚 Documentation Links

**Project Docs:**
- [WYZE_QUICKSTART.md](WYZE_QUICKSTART.md) - Quick setup guide
- [WYZE_CAM_V2_SETUP.md](WYZE_CAM_V2_SETUP.md) - Detailed setup guide
- [README.md](README.md) - Project overview

**Firmware Docs:**
- [firmware/README.md](firmware/README.md) - Firmware comparison
- [sd_card_ready/README.md](sd_card_ready/README.md) - SD card preparation

**External:**
- Thingino GitHub: https://github.com/ThingiBob/thingino
- WLTechBlog: https://wltechblog.com
- Community Discord: https://wltechblog.com/to/tCXf9

---

## 📊 Timeline Estimate

| Phase | Duration | Status |
|-------|----------|--------|
| Download/Install | Done | ✅ |
| Flash SD Card | 15 min | ⏳ Next |
| Boot Camera | 5 min | ⏳ |
| Configure WiFi | 10 min | ⏳ |
| Backup Firmware | 2 min | ⏳ |
| Update Firmware | 5 min | ⏳ |
| Configure Monitoring | 5 min | ⏳ |
| **Total** | **~45 min** | **⏳** |

---

## 🎯 Success Criteria

You'll know setup is complete when:

- [ ] SD card flashed successfully
- [ ] Camera boots into Thingino
- [ ] Can access web interface
- [ ] Can capture snapshot via HTTP
- [ ] Monitoring script connects successfully
- [ ] Receives first meter reading
- [ ] Flow rate calculations work

---

## 📞 Need Help?

**For Thingino issues:**
- Check web interface settings
- Review WLTechBlog documentation
- Check camera logs in web interface

**For monitoring script issues:**
- Verify snapshot URL: `curl -v http://IP/snapshot_url`
- Check API key: `echo $ANTHROPIC_API_KEY`
- Review logs: `tail logs/readings.jsonl`

---

**You're ready to flash! Insert your SD card and open Balena Etcher. 🚀**
