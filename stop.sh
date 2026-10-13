#!/usr/bin/env bash
# NEXUS · detiene el backend. Linux y macOS.
PORT="${NEXUS_PORT:-8765}"
if [ -z "${NEXUS_DATA:-}" ]; then
  if [ "$(uname -s)" = "Darwin" ]; then
    DATA_DIR="$HOME/Library/Application Support/NEXUS"
  else
    DATA_DIR="$HOME/.local/share/nexus"
    [ -d "$DATA_DIR" ] || DATA_DIR="$HOME/.local/share/ocdesk"
  fi
else
  DATA_DIR="$NEXUS_DATA"
fi
PIDFILE="$DATA_DIR/server.pid"
if [ -f "$PIDFILE" ]; then
  PID="$(cat "$PIDFILE")"
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID" && echo "NEXUS detenido (pid $PID)"
  else
    echo "El proceso $PID ya no existe"
  fi
  rm -f "$PIDFILE"
else
  ARRANQUE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/server.py"
  pkill -f "$ARRANQUE" && echo "NEXUS detenido" || echo "NEXUS no estaba en marcha"
fi
