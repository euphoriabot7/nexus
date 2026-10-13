#!/usr/bin/env bash
# NEXUS · abre el puerto en el cortafuegos (ufw) para tu red local.
# Uso:  sudo bash ~/ocdesk/lan-allow.sh
set -u

PORT="${NEXUS_PORT:-8765}"
DATA_DIR="${NEXUS_DATA:-$HOME/.local/share/nexus}"
[ -d "$DATA_DIR" ] || DATA_DIR="$HOME/.local/share/ocdesk"

# el servidor anota aquí el puerto que acabó usando (si el 8765 estaba pillado)
PUERTO_FILE="$DATA_DIR/puerto.txt"
if [ -f "$PUERTO_FILE" ]; then
  P_ANT="$(tr -dc '0-9' <"$PUERTO_FILE" 2>/dev/null || true)"
  [ -n "$P_ANT" ] && PORT="$P_ANT"
fi

if [ "$(id -u)" -ne 0 ]; then
  echo "Hace falta root. Ejecuta:  sudo bash lan-allow.sh"
  exit 1
fi

# detecta la red local (p.ej. 192.168.0.0/24)
SUBNET="$(ip -4 route show scope link | awk '/dev wlp|dev eth|dev enp|dev wl/{print $1; exit}')"
[ -z "$SUBNET" ] && SUBNET="192.168.0.0/24"

echo "== NEXUS: abriendo el puerto $PORT para $SUBNET =="

if command -v ufw >/dev/null 2>&1; then
  ufw allow from "$SUBNET" to any port "$PORT" proto tcp comment 'NEXUS' >/dev/null 2>&1 \
    || ufw allow "$PORT"/tcp >/dev/null 2>&1
  echo "-- estado de ufw --"
  ufw status | grep -E "Status|$PORT" || ufw status | head -3
else
  echo "ufw no está instalado; no hay nada que abrir."
fi

echo
echo "-- comprobación local --"
if curl -fsS -o /dev/null -m 3 "http://127.0.0.1:$PORT/api/health"; then
  echo "el backend responde en el puerto $PORT"
else
  echo "AVISO: el backend no responde. Arráncalo con: bash ~/ocdesk/run.sh"
fi

IP="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}')"
TOKEN="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['token'])" "$DATA_DIR/lan.json" 2>/dev/null || true)"
echo
echo "== Abre esto en el móvil (misma wifi) =="
echo "  http://$IP:$PORT"
[ -n "$TOKEN" ] && echo "  http://$IP:$PORT/login?token=$TOKEN"
echo
echo "Si el móvil sigue sin entrar, el bloqueo es del router"
echo "(aislamiento de clientes) o el móvil está en otra red/SSID."
