# Firmware Download Links

**⚠️ Important:** Download firmware directly from official sources. Do not trust third-party mirrors.

## OpenMiko (Recommended)

**Official Repository:** https://github.com/openmiko/openmiko

**Latest Release:** https://github.com/openmiko/openmiko/releases/latest

**Download Command:**
```bash
cd firmware/openmiko
wget https://github.com/openmiko/openmiko/releases/latest/download/openmiko-0.1.17.tgz
tar -xzf openmiko-0.1.17.tgz
# Extract openmiko.bin from the archive
```

**What you need:** `openmiko.bin` (will be renamed to `demo.bin` on SD card)

---

## Dafang Hacks (Alternative)

**Official Repository:** https://github.com/EliasKotlyar/Xiaomi-Dafang-Hacks

**Latest Release:** https://github.com/EliasKotlyar/Xiaomi-Dafang-Hacks/releases/latest

**Download Command:**
```bash
cd firmware/dafang
wget https://github.com/EliasKotlyar/Xiaomi-Dafang-Hacks/releases/latest/download/firmware_factory.bin
```

**What you need:** `firmware_factory.bin` (will be renamed to `demo.bin` on SD card)

---

## Verification

Always verify the integrity of downloaded firmware:

```bash
# Check file size (should be ~8-10MB)
ls -lh openmiko.bin
ls -lh firmware_factory.bin

# Optional: Verify checksums if provided in release notes
sha256sum openmiko.bin
sha256sum firmware_factory.bin
```

---

## Need Help?

- See: `firmware/README.md` for full setup instructions
- See: `WYZE_QUICKSTART.md` for step-by-step guide
