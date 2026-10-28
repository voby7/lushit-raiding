#!/data/data/com.termux/files/usr/bin/bash

# === CONFIG ===
TARGET_DIR=""
TARGET_FILE="GeoLite2-City.mmdb"
TMP_DIR=".geoip_tmp"

# === PREP ===
mkdir -p "$TARGET_DIR"
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"
cd "$TMP_DIR"

echo "[GeoLite2] Downloading latest community mirror..."
wget -q "https://github.com/P3TERX/GeoLite.mmdb/raw/master/GeoLite2-City.mmdb" -O GeoLite2-City.mmdb

if [ ! -f GeoLite2-City.mmdb ]; then
    echo "[GeoLite2] ERROR: Download failed."
    exit 1
fi

echo "[GeoLite2] Installing updated database..."
mv -f GeoLite2-City.mmdb "$TARGET_FILE"

echo "[GeoLite2] Cleaning up..."
rm -rf "$TMP_DIR"

echo "[GeoLite2] Update complete!"
echo "Installed: $TARGET_FILE"
