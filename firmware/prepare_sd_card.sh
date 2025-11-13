#!/bin/bash
# Quick SD card preparation script for Wyze Cam V2

set -e

echo "=============================================="
echo "Wyze Cam V2 - SD Card Preparation"
echo "=============================================="
echo

# Check for SD card mount point
if [ -z "$1" ]; then
    echo "Usage: ./prepare_sd_card.sh /path/to/sdcard"
    echo
    echo "Examples:"
    echo "  macOS:   ./prepare_sd_card.sh /Volumes/WYZE"
    echo "  Linux:   ./prepare_sd_card.sh /media/$USER/WYZE"
    echo "  Windows: ./prepare_sd_card.sh /d"
    echo
    exit 1
fi

SD_CARD="$1"

if [ ! -d "$SD_CARD" ]; then
    echo "Error: SD card not found at $SD_CARD"
    echo "Please check the path and try again"
    exit 1
fi

echo "SD Card: $SD_CARD"
echo

# Check available space
if command -v df &> /dev/null; then
    echo "Available space:"
    df -h "$SD_CARD" | tail -1
    echo
fi

# Choose firmware
echo "Select firmware to install:"
echo
echo "1. OpenMiko (recommended)"
echo "   - Modern, actively maintained"
echo "   - Simpler setup"
echo "   - URL: http://IP:8080/snapshot.jpg"
echo
echo "2. Dafang Hacks"
echo "   - Older but stable"
echo "   - More features (MQTT, etc.)"
echo "   - URL: http://root:ismart12@IP/cgi-bin/currentpic.cgi"
echo
read -p "Choice (1 or 2): " choice
echo

case "$choice" in
    1)
        FIRMWARE_NAME="OpenMiko"
        FIRMWARE_FILE="openmiko/openmiko.bin"
        DOWNLOAD_URL="https://github.com/openmiko/openmiko/releases/latest"
        ;;
    2)
        FIRMWARE_NAME="Dafang Hacks"
        FIRMWARE_FILE="dafang/firmware_factory.bin"
        DOWNLOAD_URL="https://github.com/EliasKotlyar/Xiaomi-Dafang-Hacks/releases/latest"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

# Check if firmware exists
if [ ! -f "$FIRMWARE_FILE" ]; then
    echo "❌ Firmware not found: $FIRMWARE_FILE"
    echo
    echo "Please download $FIRMWARE_NAME firmware first:"
    echo "  $DOWNLOAD_URL"
    echo
    echo "Then extract and place in the firmware/ directory"
    exit 1
fi

# Copy firmware
echo "Copying $FIRMWARE_NAME firmware to SD card..."
cp "$FIRMWARE_FILE" "$SD_CARD/demo.bin"

if [ $? -eq 0 ]; then
    echo "✅ Firmware copied successfully!"
else
    echo "❌ Failed to copy firmware"
    exit 1
fi

# Verify
if [ -f "$SD_CARD/demo.bin" ]; then
    FILE_SIZE=$(ls -lh "$SD_CARD/demo.bin" | awk '{print $5}')
    echo "✅ Verified: demo.bin ($FILE_SIZE)"
else
    echo "❌ Verification failed"
    exit 1
fi

echo
echo "=============================================="
echo "SD Card is Ready!"
echo "=============================================="
echo
echo "Next steps:"
echo
echo "1. Safely eject SD card:"
echo "   macOS:   diskutil eject $SD_CARD"
echo "   Linux:   umount $SD_CARD"
echo
echo "2. Insert SD card into Wyze Cam V2"
echo
echo "3. Flash the camera:"
echo "   a. Power OFF camera"
echo "   b. Hold SETUP button on bottom"
echo "   c. Plug in power (keep holding button)"
echo "   d. Wait for solid BLUE LED (~30 sec)"
echo "   e. Release button"
echo "   f. Yellow LED = flashing in progress"
echo "   g. Wait 3-4 minutes for completion"
echo
echo "4. Configure WiFi:"
if [ "$choice" = "1" ]; then
    echo "   - Connect to WiFi: MIKO_XXXX"
    echo "   - Password: 12345678"
    echo "   - Browser: http://192.168.1.1"
else
    echo "   - Connect to WiFi: DAFANG_XXXX"
    echo "   - Password: 1234567890"
    echo "   - Browser: http://192.168.1.1"
fi
echo
echo "5. Test snapshot URL (after WiFi setup):"
if [ "$choice" = "1" ]; then
    echo "   curl http://CAMERA_IP:8080/snapshot.jpg -o test.jpg"
else
    echo "   curl --user root:ismart12 http://CAMERA_IP/cgi-bin/currentpic.cgi -o test.jpg"
fi
echo
echo "Full setup guide: ../WYZE_QUICKSTART.md"
echo
