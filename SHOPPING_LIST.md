# Shopping List - Wyze Cam V2 to Thingino Conversion

Complete shopping guide for converting a Wyze Cam V2 into a Thingino-powered utility meter reading camera.

---

## Required Items

### 1. MicroSD Card (REQUIRED)

**Specifications:**
- **Capacity:** 8GB to 32GB (16GB recommended)
- **Speed Class:** Class 10 or higher (U1/U3)
- **Format:** Must support FAT32
- **Type:** MicroSD (not full-size SD)

**Recommended Cards (Verified Compatible):**

| Brand | Model | Capacity | Speed | Price | Link |
|-------|-------|----------|-------|-------|------|
| SanDisk Ultra | SDSQUA4 | 16GB | Class 10, U1 | ~$6 | [Amazon](https://www.amazon.com/dp/B08GY9NYRM) |
| SanDisk Ultra | SDSQUA4 | 32GB | Class 10, U1 | ~$8 | [Amazon](https://www.amazon.com/dp/B08GYG5SVL) |
| Samsung EVO Select | MB-ME | 16GB | Class 10, U1 | ~$7 | [Amazon](https://www.amazon.com/dp/B0887CHVFF) |
| Samsung EVO Select | MB-ME | 32GB | Class 10, U3 | ~$9 | [Amazon](https://www.amazon.com/dp/B0887GP791) |
| Kingston Canvas Select Plus | SDCS2 | 16GB | Class 10, U1 | ~$6 | [Amazon](https://www.amazon.com/dp/B07YTRFDQX) |

**Budget Option:**
- Any Class 10 MicroSD card 8-32GB from major brands (SanDisk, Samsung, Kingston, Lexar)
- Typically $5-10 at retailers

**⚠️ Cards to Avoid:**
- Generic/no-name brands (reliability issues)
- Cards >64GB (may have boot issues with Thingino)
- Cards <Class 10 (slower performance)

---

### 2. USB MicroSD Card Reader (IF NEEDED)

**Do you need one?**
- ✅ YES: If your computer doesn't have a built-in SD card slot
- ✅ YES: If you only have full-size SD slot and no adapter
- ❌ NO: If your computer has SD/MicroSD slot

**Recommended Readers:**

| Brand | Type | Speed | Price | Link |
|-------|------|-------|-------|------|
| Anker 2-in-1 | USB-A + MicroSD | USB 3.0 | ~$8 | [Amazon](https://www.amazon.com/dp/B006T9B6R2) |
| SanDisk MobileMate | USB-A + MicroSD | USB 3.0 | ~$7 | [Amazon](https://www.amazon.com/dp/B07G5JV2B5) |
| UGREEN USB-C | USB-C + MicroSD | USB 3.1 | ~$10 | [Amazon](https://www.amazon.com/dp/B07C16XZ53) |

---

### 3. Wyze Cam V2 (IF YOU DON'T HAVE ONE)

**Where to Buy:**
- **Used/Refurbished:** eBay, Facebook Marketplace, Craigslist ($10-20)
- **New (if available):** Wyze website, Amazon (~$25-30)

**⚠️ Important:**
- Must be **Wyze Cam V2** specifically (not V3, Pan Cam, etc.)
- Verify model before purchasing
- Used cameras work fine - firmware will be replaced anyway

---

## Optional Items

### 4. Power Adapter & Cable (Usually Included with Camera)

If your camera didn't come with power supply:

| Item | Specs | Price | Link |
|------|-------|-------|------|
| USB Power Adapter | 5V 1A+ (standard phone charger) | ~$8 | Any USB charger works |
| Micro-USB Cable | Standard Micro-USB | ~$5 | [Amazon](https://www.amazon.com/dp/B0711PVX6Z) |

---

### 5. MicroSD to SD Adapter (Usually Included with MicroSD)

Most MicroSD cards include a free adapter. If yours doesn't:

| Item | Price | Link |
|------|-------|------|
| MicroSD to SD Adapter | ~$3 | [Amazon](https://www.amazon.com/dp/B01G8GQAVY) |

---

## Software Requirements (FREE)

### 1. Balena Etcher (Firmware Flashing Tool)

**Download:** https://www.balena.io/etcher/

**Platforms:**
- ✅ Windows
- ✅ macOS
- ✅ Linux

**Cost:** FREE

---

### 2. Thingino Firmware

**Download Location:**
- Already on your Desktop: `/Users/seanhunt/Desktop/wyze-cam-2-thingino.img` (120MB)

**Official Source (if re-downloading):**
- https://github.com/themactep/thingino-firmware/releases
- Look for: `wyze-cam-v2` or similar Wyze Cam V2 build

**Cost:** FREE (Open Source)

---

## Complete Kit Pricing

### Minimal Setup (You have computer & SD card reader)
```
MicroSD Card (16GB):           $6-8
────────────────────────────────────
TOTAL:                         $6-8
```

### Full Setup (Need everything)
```
Wyze Cam V2 (used):           $15-20
MicroSD Card (16GB):           $6-8
USB SD Card Reader:            $8
────────────────────────────────────
TOTAL:                        $29-36
```

### Multi-Camera Setup (3 cameras for comprehensive monitoring)
```
3x Wyze Cam V2 (used):        $45-60
3x MicroSD Card (16GB):       $18-24
1x USB SD Card Reader:         $8
────────────────────────────────────
TOTAL:                        $71-92
```

---

## Next Steps After Purchasing

1. **Wait for delivery** (usually 1-2 days with Amazon Prime)

2. **Follow setup guide:** See [THINGINO_QUICKSTART.md](THINGINO_QUICKSTART.md)

3. **Total setup time:** ~30 minutes per camera

---

## Frequently Asked Questions

### Q: Can I use a larger SD card (64GB, 128GB)?
**A:** Technically yes, but 32GB is the sweet spot. Larger cards may have compatibility issues and are unnecessary since Thingino firmware is only 120MB.

### Q: Do I need a fast UHS-II or V30 card?
**A:** No. Standard Class 10 is plenty fast for snapshot capture. Don't overpay for high-speed cards.

### Q: Can I reuse an SD card from another device?
**A:** Yes! Just make sure to back up any data first. The flashing process will completely erase the card.

### Q: What if my SD card doesn't work?
**A:** Try formatting it to FAT32 first, then reflash. If still failing, try a different brand (SanDisk and Samsung are most reliable).

### Q: Where can I buy SD cards locally?
**A:** Best Buy, Target, Walmart, Staples all carry compatible cards. Bring this list to verify specs.

### Q: Do I need multiple SD cards for multiple cameras?
**A:** Yes, one SD card per camera. They stay inserted in the camera permanently.

---

## Troubleshooting Purchases

### SD Card Won't Format to FAT32
- **Issue:** Windows only allows FAT32 for cards ≤32GB
- **Solution:** Use third-party tool like [FAT32 Format](http://www.ridgecrop.demon.co.uk/index.htm?guiformat.htm) or `diskutil` on Mac

### Card Reader Not Recognized
- **Issue:** Driver or connection problem
- **Solution:** Try different USB port, update drivers, or use different reader

### Camera Not Powering On
- **Issue:** Insufficient power supply
- **Solution:** Use minimum 5V 1A adapter (standard phone charger)

---

## Ready to Start?

Once you have your SD card delivered:

👉 **[Continue to THINGINO_QUICKSTART.md](THINGINO_QUICKSTART.md)** for step-by-step setup instructions

---

**Last Updated:** 2025-11-19
**Compatibility:** Wyze Cam V2 + Thingino Firmware
**Estimated Total Cost:** $6-36 depending on what you already have
