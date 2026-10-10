#!/usr/bin/env bash
# NEXUS · instala los accesos directos (menu de aplicaciones + Escritorio).
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ICON="$APP_DIR/app/assets/icon.svg"
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Escritorio")"
APPS_DIR="$HOME/.local/share/applications"

mkdir -p "$APPS_DIR"
chmod +x "$APP_DIR/run.sh" "$APP_DIR/stop.sh" 2>/dev/null || true

write_desktop() {
  cat >"$1" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=NEXUS
GenericName=Consola de chat IA
Comment=Chat multi-modelo con historial
Exec=/bin/bash $APP_DIR/run.sh
Icon=$ICON
Terminal=false
Categories=Utility;Network;InstantMessaging;
Keywords=chat;ia;ai;nexus;llm;
StartupNotify=true
StartupWMClass=NEXUS
EOF
  chmod +x "$1"
}

write_desktop "$APPS_DIR/nexus.desktop"
if [ -d "$DESKTOP_DIR" ]; then
  write_desktop "$DESKTOP_DIR/nexus.desktop"
  # marca de confianza (Nemo / Cinnamon)
  gio set "$DESKTOP_DIR/nexus.desktop" metadata::trusted true 2>/dev/null || true
fi

update-desktop-database "$APPS_DIR" 2>/dev/null || true

echo "Instalado:"
echo "  · Menú de aplicaciones -> NEXUS"
[ -d "$DESKTOP_DIR" ] && echo "  · Escritorio -> $DESKTOP_DIR/nexus.desktop"
