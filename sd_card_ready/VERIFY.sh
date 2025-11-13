#!/bin/bash
# Verify firmware files integrity

echo "=============================================="
echo "Firmware Verification"
echo "=============================================="
echo

if [ ! -f "CHECKSUMS.txt" ]; then
    echo "❌ CHECKSUMS.txt not found"
    exit 1
fi

echo "Verifying firmware files..."
echo

if command -v shasum &> /dev/null; then
    shasum -a 256 -c CHECKSUMS.txt
    if [ $? -eq 0 ]; then
        echo
        echo "✅ All firmware files verified successfully!"
    else
        echo
        echo "❌ Verification failed! Files may be corrupted."
        exit 1
    fi
else
    echo "⚠️  shasum not found, skipping verification"
fi

echo
echo "File sizes:"
ls -lh openmiko/demo.bin dafang/demo.bin | awk '{print "  " $9 ": " $5}'

echo
echo "=============================================="
echo "Firmware files are ready to copy to SD card"
echo "=============================================="
