# 🎥 Wyze Cam V2 + Water Meter Reader - Quick Start

**Total setup time: 30 minutes**
**Cost: ~$5 (MicroSD card only - you have the camera!)**

---

## 📋 What You Need

- ✅ Wyze Cam V2 (you have it!)
- ✅ MicroSD card (8-32GB, FAT32)
- ✅ Computer with SD card reader
- ✅ WiFi network (2.4GHz)
- ✅ Anthropic API key
- ✅ Balena Etcher (installed)

---

## ⚡ 5-Step Setup

### 1️⃣ Flash Firmware (15 min)

**Choose one:**

#### Option A: Thingino (RECOMMENDED - Latest, More Features)

```bash
# File location: ~/Desktop/wyze-cam-2-thingino.img
# Size: 120MB

# Flash with Balena Etcher:
# 1. Open Balena Etcher
# 2. Select: ~/Desktop/wyze-cam-2-thingino.img
# 3. Select your SD card
# 4. Click "Flash"
# 5. Wait for completion

# Boot into installer:
# 1. Power OFF camera
# 2. Insert SD card
# 3. Hold SETUP button
# 4. Plug in power
# 5. Release when LED goes blue
# 6. Wait 3-4 minutes
```

**Default Credentials (Thingino):**
- SSH: Check web interface after setup
- HTTP Snapshot: Camera-dependent (follow setup wizard)

#### Option B: Dafang Hacks (Traditional, Stable)

```bash
# Download firmware
wget https://github.com/EliasKotlyar/Xiaomi-Dafang-Hacks/releases/latest/download/firmware_factory.bin

# Format SD card as FAT32
# Copy firmware and rename to "demo.bin"

# Flash camera:
# 1. Power OFF camera
# 2. Insert SD card
# 3. Hold setup button
# 4. Plug in power (keep holding)
# 5. Wait for yellow LED → release
# 6. Wait 3-4 minutes
```

**LED Guide:**
- Yellow = Flashing
- Solid Blue = Complete
- Blinking Blue = Rebooting

### 2️⃣ Configure WiFi (5 min)

```bash
# Camera creates hotspot: DAFANG_XXXX
# Password: 1234567890

# Connect and open: http://192.168.1.1
# Enter your WiFi credentials
# Camera reboots and joins your network
```

### 3️⃣ Set Static IP (2 min)

Find camera IP from router, then:

```bash
# Access web interface
http://192.168.1.XXX

# Default login:
# Username: root
# Password: ismart12

# Settings → Network → Static IP
# Set: 192.168.1.100
```

**⚠️ IMPORTANT: Change password!**

### 4️⃣ Test Snapshot URL (1 min)

```bash
# Test in browser or curl
curl --user root:ismart12 \
     http://192.168.1.100/cgi-bin/currentpic.cgi \
     -o test.jpg

# Should download a JPEG image
open test.jpg  # macOS
xdg-open test.jpg  # Linux
```

### 5️⃣ Start Monitoring (5 min)

```bash
cd water-meter-reader

# Set environment variables
export ANTHROPIC_API_KEY=sk-ant-...
export WYZE_CAM_IP=192.168.1.100
export WYZE_CAM_PASS=ismart12  # Or your new password

# Run monitoring
python examples/wyze_cam_monitor.py
```

**Expected output:**
```
[2025-11-13 19:30:00] Capturing snapshot... ✓ Reading meter... ✓
  Reading: 226.003 m³
  Digital: 226, Dial: 0.003
  Confidence: high
```

---

## 🎯 Camera URLs

After setup, you'll have:

**HTTP Snapshot (recommended):**
```
http://root:ismart12@192.168.1.100/cgi-bin/currentpic.cgi
```

**RTSP Stream (alternative):**
```
rtsp://root:ismart12@192.168.1.100:554/live/ch00_0
```

---

## 📸 Camera Positioning

```
     [Wyze Cam V2]
          ↓
       15-20cm
          ↓
    ┌──────────┐
    │ DIGITAL  │
    │  0226    │  ← Both visible
    │    ●───  │  ← Red needle clear
    └──────────┘
```

**Tips:**
- Distance: 15-20cm from meter
- Angle: Straight on or slight tilt
- Lighting: Constant (add LED if needed)
- Mount: Magnetic, adhesive, or tripod

---

## 🔧 Common Issues & Fixes

### "Camera won't flash"
→ Verify SD card is FAT32  
→ File must be named exactly `demo.bin`  
→ Try different SD card

### "Can't access web interface"
→ Check camera IP from router  
→ Verify on same network  
→ Wait 5 minutes after WiFi config

### "Snapshot URL returns 401"
→ Check username/password  
→ Change default password  
→ Use URL encoding

### "Image quality poor"
→ Clean lens  
→ Increase resolution (1920x1080)  
→ Add lighting  
→ Adjust focus (carefully)

---

## 💰 Cost Breakdown

**One-time:**
- Wyze Cam V2: $0 (you have it!)
- MicroSD card: $5
- **Total: $5**

**Monthly:**
- Power: $0.50 (3W)
- API: $0.43 (10-min intervals)
- **Total: ~$1/month**

**Year 1: ~$17**

---

## 📊 Why Wyze Cam V2?

| Feature | ESP32-CAM | Wyze Cam V2 |
|---------|-----------|-------------|
| Resolution | 640x480 | 1920x1080 |
| Low Light | Poor | Excellent |
| Stability | OK | Great |
| Cost | $12 | $0 (have it) |
| Setup | 1 hour | 30 min |

**Winner: Wyze Cam V2** (better quality + you own it!)

---

## 🏠 Next Steps

**Today:**
- [ ] Flash firmware
- [ ] Configure WiFi
- [ ] Test snapshot

**Tomorrow:**
- [ ] Mount camera
- [ ] Run monitoring script
- [ ] Verify readings

**This Week:**
- [ ] Set up Home Assistant
- [ ] Configure leak alerts
- [ ] Deploy full stack

---

## 📚 Full Documentation

- **[WYZE_CAM_V2_SETUP.md](WYZE_CAM_V2_SETUP.md)** - Complete guide
- **[INSTALLATION.md](INSTALLATION.md)** - Project setup
- **[VSCODE_GUIDE.md](VSCODE_GUIDE.md)** - Development

---

## 🆘 Need Help?

**Dafang Hacks Resources:**
- GitHub: github.com/EliasKotlyar/Xiaomi-Dafang-Hacks
- Wiki: github.com/EliasKotlyar/Xiaomi-Dafang-Hacks/wiki
- Forum: github.com/EliasKotlyar/Xiaomi-Dafang-Hacks/discussions

**This Project:**
- Check docs/TROUBLESHOOTING.md
- Review example scripts
- Check logs/application.log

---

## ✅ Quick Test Commands

```bash
# Test camera snapshot
curl --user root:ismart12 http://192.168.1.100/cgi-bin/currentpic.cgi -o test.jpg

# Test RTSP stream (VLC)
vlc rtsp://root:ismart12@192.168.1.100:554/live/ch00_0

# Test meter reading
python src/llm_reader.py test.jpg

# Start monitoring
python examples/wyze_cam_monitor.py
```

---

**You're ready to go! Flash the firmware and start monitoring your water meter.** 💧

**Total time: 30 minutes**  
**Total cost: $5**  
**Result: Professional water meter monitoring!** 📊
