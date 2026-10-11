#!/usr/bin/env bash
# NEXUS · arranca el backend si hace falta y abre la ventana de la app.
# Linux y macOS. En Windows se usa run.bat.
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${NEXUS_PORT:-8765}"
URL="http://127.0.0.1:${PORT}"
SO="$(uname -s)"

# datos: misma logica que server.py
if [ "$SO" = "Darwin" ]; then
  DEF_DATA="$HOME/Library/Application Support/NEXUS"
else
  DEF_DATA="$HOME/.local/share/nexus"
  if [ ! -d "$DEF_DATA" ] && [ -d "$HOME/.local/share/ocdesk" ]; then
    DEF_DATA="$HOME/.local/share/ocdesk"      # instalacion antigua: no perder historiales
  fi
fi
DATA_DIR="${NEXUS_DATA:-$DEF_DATA}"
LOG="$DATA_DIR/server.log"
PIDFILE="$DATA_DIR/server.pid"
mkdir -p "$DATA_DIR"

# --- busca un python3 util (3.9 o superior) ---
PY=""
for cand in python3 python python3.14 python3.13 python3.12 python3.11 python3.10 python3.9; do
  if command -v "$cand" >/dev/null 2>&1; then PY="$(command -v "$cand")"; break; fi
done
if [ -z "$PY" ]; then
  echo "No encuentro python3. Instalalo (por ejemplo: sudo apt install python3) y vuelve a intentarlo." >&2
  exit 1
fi
if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info>=(3,9) else 1)'; then
  echo "Tu Python es anterior a 3.9. Actualizalo y vuelve a intentarlo." >&2
  exit 1
fi

# --- busca un navegador tipo chromium (modo aplicacion) ---
BROWSER=""
if [ "$SO" = "Darwin" ]; then
  for b in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
           "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
           "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
           "/Applications/Chromium.app/Contents/MacOS/Chromium"; do
    [ -x "$b" ] && BROWSER="$b" && break
  done
fi
if [ -z "$BROWSER" ]; then
  for b in google-chrome chromium chromium-browser brave-browser microsoft-edge vivaldi; do
    if command -v "$b" >/dev/null 2>&1; then BROWSER="$(command -v "$b")"; break; fi
  done
fi

health() { "$PY" -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('$URL/api/health',timeout=2).status==200 else 1)" >/dev/null 2>&1; }

# --- arranca el servidor si no responde ---
if ! health; then
  ( cd "$APP_DIR" && nohup "$PY" server.py >>"$LOG" 2>&1 & echo $! >"$PIDFILE" )
  for _ in $(seq 1 50); do
    health && break
    sleep 0.2
  done
fi

if ! health; then
  echo "No se pudo iniciar NEXUS. Revisa el registro: $LOG" >&2
  if command -v zenity >/dev/null 2>&1; then
    zenity --error --title="NEXUS" --text="No se pudo iniciar el backend.\nRevisa: $LOG" || true
  fi
  exit 1
fi

# --- abre la ventana (modo app, sin barra del navegador) ---
if [ -n "$BROWSER" ]; then
  exec "$BROWSER" \
    --app="$URL" \
    --class=NEXUS \
    --user-data-dir="$DATA_DIR/browser-profile" \
    --no-first-run --no-default-browser-check \
    --window-size=1360,880
else
  echo "NEXUS listo en $URL (abrelo en tu navegador)"
  if [ "$SO" = "Darwin" ]; then exec open "$URL"; else exec xdg-open "$URL" 2>/dev/null || true; fi
fi
