#!/usr/bin/env bash
# ============================================================
#  NEXUS · acceso directo en macOS
#  Crea ~/Applications/NEXUS.app, un lanzador de doble clic que
#  arranca el backend y abre la ventana de la app.
#  Doble clic sobre este archivo (o: bash install-mac.command).
# ============================================================
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${NEXUS_APPDIR:-$HOME/Applications}"
APP="$DEST/NEXUS.app"
VERSION="$(cat "$APP_DIR/VERSION" 2>/dev/null | tr -d '[:space:]' || echo '0')"

mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cat >"$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>NEXUS</string>
  <key>CFBundleDisplayName</key><string>NEXUS</string>
  <key>CFBundleIdentifier</key><string>com.euphoriabot7.nexus</string>
  <key>CFBundleVersion</key><string>${VERSION:-0}</string>
  <key>CFBundleShortVersionString</key><string>${VERSION:-0}</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleExecutable</key><string>NEXUS</string>
  <key>LSMinimumSystemVersion</key><string>10.13</string>
  <key>LSUIElement</key><true/>
  <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
PLIST

cat >"$APP/Contents/MacOS/NEXUS" <<LANZADOR
#!/bin/bash
# Lanzador generado por install-mac.command. Los datos viven en
# ~/Library/Application Support/NEXUS
exec "/bin/bash" "$APP_DIR/run.sh"
LANZADOR

chmod +x "$APP/Contents/MacOS/NEXUS" "$APP_DIR/run.sh" "$APP_DIR/stop.sh" 2>/dev/null || true
# avisa a Finder / LaunchServices de que el .app es nuevo
touch "$APP" 2>/dev/null || true

echo "Instalado:"
echo "  · $APP  (buscalo en Launchpad o en ~/Aplicaciones)"
echo "  · Para pararlo: bash $APP_DIR/stop.sh"
if command -v xattr >/dev/null 2>&1; then
  echo
  echo "  Si macOS dice que el archivo no se puede abrir, ejecuta:"
  echo "    xattr -dr com.apple.quarantine \"$APP\" \"$APP_DIR\""
fi
