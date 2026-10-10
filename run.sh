#!/usr/bin/env bash
# NEXUS · arranca el backend si hace falta y abre la ventana de la app.
# No necesita configuracion: usa la carpeta donde este este script.
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${NEXUS_PORT:-8765}"
URL="http://127.0.0.1:${PORT}"

# datos: ~/.local/share/nexus (o la carpeta antigua si ya existia)
DATA_DIR="${NEXUS_DATA:-$HOME/.local/share/nexus}"
if [ ! -d "$DATA_DIR" ] && [ -d "$HOME/.local/share/ocdesk" ]; then
  DATA_DIR="$HOME/.local/share/ocdesk"
fi
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

# --- busca un navegador tipo chromium ---
BROWSER=""
for b in google-chrome chromium chromium-browser brave-browser microsoft-edge vivaldi; do
  if command -v "$b" >/dev/null 2>&1; then BROWSER="$(command -v "$b")"; break; fi
done

health() { curl -fsS -m 2 "$URL/api/health" >/dev/null 2>&1; }

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
  exec xdg-open "$URL" 2>/dev/null || true
fi
