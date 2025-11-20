# Thingino Quick Start Guide
## Convert Wyze Cam V2 to Meter Reading Camera in 30 Minutes

Complete step-by-step guide to flash Thingino firmware and integrate with the utility meter monitoring system.

---

## Prerequisites

✅ **You have:**
- Wyze Cam V2 camera
- MicroSD card (8-32GB, Class 10) - [See shopping list](SHOPPING_LIST.md)
- Computer with SD card reader
- WiFi network (2.4GHz required)

⏱️ **Time required:** 30 minutes
🔧 **Difficulty:** Easy (no soldering, no hardware modification)

---

## Step 1: Download Required Software

### A. Install Balena Etcher (Firmware Flashing Tool)

1. **Download Balena Etcher:** https://www.balena.io/etcher/
2. **Install for your platform:**
   - Windows: Run `.exe` installer
   - macOS: Open `.dmg` and drag to Applications
   - Linux: Extract `.AppImage` and make executable

### B. Verify Thingino Firmware File

**Location:** `/Users/seanhunt/Desktop/wyze-cam-2-thingino.img` (120MB)

**If missing, download from:**
- Official: https://github.com/themactep/thingino-firmware/releases
- Look for: Wyze Cam V2 compatible build (`.img` file)

---

## Step 2: Prepare SD Card

### A. Insert SD Card into Computer

- Use built-in SD card reader, OR
- Use USB SD card adapter

### B. Backup Existing Data (if card has files)

**⚠️ Warning:** Flashing will ERASE ALL DATA on the SD card!

---

## Step 3: Flash Thingino Firmware

### Open Balena Etcher

1. **Launch Balena Etcher** application

### Select Firmware Image

2. **Click "Flash from file"**
3. **Navigate to:** `/Users/seanhunt/Desktop/wyze-cam-2-thingino.img`
4. **Click "Open"**

### Select SD Card

5. **Click "Select target"**
6. **Choose your MicroSD card** (verify size matches your card)
7. **Click "Select"**

### Flash!

8. **Click "Flash!"**
9. **Enter admin password** if prompted (macOS/Linux)
10. **Wait 3-5 minutes** for flashing to complete

### Verify

11. **Wait for "Flash Complete!"** message
12. **Click "Close"**
13. **Eject SD card safely**

**✅ Your SD card is now ready!**

---

## Step 4: Install SD Card in Camera

### Insert Card

1. **Locate SD card slot** on Wyze Cam V2 (bottom of camera)
2. **Insert MicroSD card** (metal contacts facing camera lens)
3. **Push until it clicks** into place

### Prepare to Boot

4. **Locate SETUP button** (on bottom of camera, small hole)
5. **Have micro-USB cable ready** (do not plug in yet)

---

## Step 5: First Boot & Initial Setup

### Boot into Thingino

1. **Press and HOLD the SETUP button** (use paperclip if needed)
2. **While holding, plug in USB power cable**
3. **Keep holding for 5-10 seconds**
4. **Release SETUP button**
5. **Wait for blue LED to flash** (indicates Thingino booted successfully)

**⏱️ First boot takes ~1-2 minutes**

### What Happens During First Boot

- Thingino firmware loads from SD card
- Camera creates a WiFi hotspot named `THINGINO_XXXX`
- Blue LED indicates ready for setup

---

## Step 6: Connect to Camera WiFi

### On Your Computer or Phone

1. **Open WiFi settings**
2. **Look for network:** `THINGINO_XXXX` (where XXXX is random characters)
3. **Connect to this network** (no password required initially)

**⏱️ Wait ~30 seconds** for connection to establish

---

## Step 7: Access Setup Wizard

### Open Web Browser

1. **Open browser** (Chrome, Firefox, Safari)
2. **Navigate to:** `http://192.168.1.1` or `http://thingino.local`

### Initial Configuration Wizard

3. **Set admin password**
   - Enter a password you'll remember
   - Confirm password
   - Click "Next"

4. **Configure WiFi**
   - **SSID:** Select your home WiFi network (must be 2.4GHz)
   - **Password:** Enter your WiFi password
   - **Click "Connect"**

5. **Wait for camera to reboot** (~30 seconds)
   - Camera will disconnect from hotspot
   - Camera will connect to your WiFi network
   - Blue LED will stabilize

---

## Step 8: Find Camera on Your Network

### Option A: Check Router's DHCP Client List

1. Log into your router admin panel
2. Look for device named `thingino` or similar
3. Note the assigned IP address (e.g., `192.168.1.123`)

### Option B: Use Network Scanner

**macOS/Linux:**
```bash
# Scan your network for Thingino camera
nmap -sn 192.168.1.0/24 | grep -B 2 "thingino"
```

**Windows:**
- Use "Advanced IP Scanner" or similar tool
- Look for device with hostname containing "thingino"

### Option C: Reconnect to Camera Hotspot

If camera didn't connect to WiFi:
1. Camera will recreate hotspot after 2 minutes
2. Reconnect and reconfigure WiFi settings

---

## Step 9: Configure Camera Settings

### Access Camera Web Interface

1. **Navigate to:** `http://[CAMERA_IP]` (e.g., `http://192.168.1.123`)
2. **Login:**
   - Username: `root`
   - Password: (the admin password you set in Step 7)

### Set Static IP (Recommended)

3. **Go to:** Settings → Network
4. **Configure static IP:**
   - IP Address: `10.10.10.207` (or your preferred static IP)
   - Gateway: Your router IP (e.g., `192.168.1.1`)
   - Subnet: `255.255.255.0`
   - DNS: `8.8.8.8` (Google DNS)
5. **Save and Reboot**

### Enable Snapshot Feature

6. **Go to:** Settings → Image/Video
7. **Enable:** HTTP Snapshot
8. **Set quality:** High or Maximum
9. **Note the snapshot URL** (usually `/api/image/snapshot` or `/api/v1/image/snapshot`)
10. **Save settings**

### Test Snapshot URL

```bash
# Test snapshot access (replace with your camera IP)
curl http://10.10.10.207/api/image/snapshot --output test_snapshot.jpg

# Or open in browser:
# http://10.10.10.207/api/image/snapshot
```

**✅ You should see a JPEG image of what the camera sees**

---

## Step 10: Configure SSH Access (Optional - For Temperature Reading)

### Enable SSH

1. **In camera web interface, go to:** Settings → Services
2. **Enable SSH server**
3. **Set SSH password** (can be same as admin password)
4. **Save settings**

### Test SSH Connection

```bash
# From your computer
ssh root@10.10.10.207

# Enter password when prompted
# You should see Thingino shell prompt
```

### Get Temperature Reading

```bash
# While connected via SSH
cat /sys/class/thermal/thermal_zone0/temp

# Output: temperature in millidegrees Celsius (e.g., 45200 = 45.2°C)
```

---

## Step 11: Integrate with Meter Reading System

### Update `config/meters.yaml`

Edit your meter configuration file:

```yaml
meters:
  water_main:
    name: "Water Main"
    camera:
      type: "thingino"  # Specify Thingino firmware type
      ip: "10.10.10.207"
      snapshot_url: "http://10.10.10.207/api/image/snapshot"

      # SSH credentials for temperature reading (optional)
      ssh_user: "root"
      ssh_password: "your_ssh_password"

    meter:
      type: "badger_absolute_digital"
      digits: 5
      has_dial: true
```

### Test Integration

```bash
# Capture a snapshot using your meter reading system
/takemetersnapshot

# Or run the full meter reading workflow
python3 run_meter_reading.py
```

**✅ You should see:**
- Snapshot captured successfully
- Meter reading analyzed
- Results saved to logs

---

## Step 12: Verify Everything Works

### Run Verification Script (If Available)

```bash
# Automated verification (we'll create this)
./verify_camera_ready.sh 10.10.10.207
```

### Manual Verification Checklist

✅ **Camera is accessible:**
```bash
ping 10.10.10.207
# Should get replies
```

✅ **Snapshot URL works:**
```bash
curl http://10.10.10.207/api/image/snapshot --output test.jpg
# Should download JPEG image
```

✅ **SSH works (optional):**
```bash
ssh root@10.10.10.207 "cat /sys/class/thermal/thermal_zone0/temp"
# Should return temperature value
```

✅ **Meter reading system integration:**
```bash
python3 run_meter_reading.py
# Should complete successfully with meter reading
```

---

## Troubleshooting

### Camera Won't Boot

**Symptoms:** No LED activity, camera doesn't power on

**Solutions:**
1. Verify SD card is fully inserted (should click)
2. Try different power adapter (minimum 5V 1A)
3. Try different USB cable
4. Reflash SD card with Balena Etcher

### Can't Connect to WiFi Hotspot

**Symptoms:** `THINGINO_XXXX` network not appearing

**Solutions:**
1. Wait 2 minutes after plugging in (first boot takes time)
2. Press and hold SETUP button, then power cycle
3. Verify SD card is correctly flashed (reflash if needed)
4. Move closer to camera (hotspot has limited range)

### Camera Won't Connect to Home WiFi

**Symptoms:** Camera creates hotspot again after configuration

**Solutions:**
1. **Verify WiFi is 2.4GHz** (Thingino doesn't support 5GHz)
2. Check WiFi password is correct
3. Ensure router is not blocking new devices (MAC filtering)
4. Try moving camera closer to router (signal strength issue)
5. Check router DHCP pool has available IPs

### Can't Find Camera IP Address

**Solutions:**
1. Check router's DHCP client list
2. Use network scanner: `nmap -sn 192.168.1.0/24`
3. Reconnect to camera hotspot and set static IP manually
4. Check router logs for new device connections

### Snapshot URL Returns 404

**Solutions:**
1. Try alternative URLs:
   - `/api/image/snapshot`
   - `/api/v1/image/snapshot`
   - `/image/snapshot`
   - `/snapshot`
2. Check camera web interface → Settings → Image/Video
3. Verify snapshot feature is enabled
4. Try rebooting camera

### Temperature Reading Not Working

**Solutions:**
1. Verify SSH is enabled in camera settings
2. Check SSH credentials are correct
3. Test SSH connection: `ssh root@10.10.10.207`
4. Temperature reading is optional - meter reading works without it

### SD Card Keeps Corrupting

**Solutions:**
1. Use a different/better quality SD card (SanDisk, Samsung recommended)
2. Ensure proper power supply (cheap adapters cause issues)
3. Avoid Class 4 or older cards (use Class 10+)
4. Check if card is fake/counterfeit (test with H2testw on Windows)

---

## Next Steps

### Single Camera Setup
- ✅ Position camera to view your utility meter
- ✅ Adjust focus and angle for clear digit reading
- ✅ Run test readings to verify accuracy
- ✅ Set up automated reading schedule (cron job)

### Multi-Camera Setup
- Repeat Steps 3-11 for each additional camera
- Use different static IPs for each camera (e.g., 10.10.10.207, 10.10.10.208, etc.)
- Add each camera to `config/meters.yaml`

### View Historical Data
```bash
# Start snapshot viewer web interface
./start_snapshot_viewer.sh

# Open browser to: http://127.0.0.1:5001
```

---

## Advanced Configuration

### Camera Positioning Tips
- Mount ~6-12 inches from meter face
- Ensure good lighting (add LED strip if needed)
- Avoid direct sunlight or reflections on glass
- Keep camera level with meter display

### Optimize Image Quality
- **Settings → Image → Resolution:** 1920x1080 (Full HD)
- **Settings → Image → Compression:** Low (higher quality)
- **Settings → Image → Sharpness:** Medium-High
- **Settings → Image → Brightness:** Auto or adjust based on lighting

### Network Security
- Change default SSH password
- Use strong admin password
- Consider placing cameras on separate VLAN
- Disable SSH if not using temperature readings

---

## Resources

### Documentation
- [SHOPPING_LIST.md](SHOPPING_LIST.md) - What to buy
- [WYZE_CAM_V2_INTEGRATION.md](WYZE_CAM_V2_INTEGRATION.md) - Detailed Wyze Cam guide
- [.claude/THINGINO_CAMERA_REFERENCE.md](.claude/THINGINO_CAMERA_REFERENCE.md) - API reference
- [sd_card_ready/README.md](sd_card_ready/README.md) - SD card preparation

### Official Thingino Resources
- GitHub: https://github.com/themactep/thingino-firmware
- Wiki: https://github.com/themactep/thingino-firmware/wiki
- Releases: https://github.com/themactep/thingino-firmware/releases

### Community Support
- Thingino Discord/Forum (check GitHub for links)
- Home Assistant community
- Reddit: /r/homeautomation

---

## Success!

🎉 **Your Wyze Cam V2 is now a Thingino-powered utility meter reading camera!**

**What you've accomplished:**
- ✅ Converted stock Wyze Cam to open-source Thingino firmware
- ✅ Full local control (no cloud dependency)
- ✅ Integrated with automated meter reading system
- ✅ Snapshot capture and analysis working
- ✅ Temperature monitoring (optional)
- ✅ Ready for 24/7 automated monitoring

---

**Setup Time:** ~30 minutes per camera
**Last Updated:** 2025-11-19
**Firmware:** Thingino (Open Source)
**Compatibility:** Wyze Cam V2 only
