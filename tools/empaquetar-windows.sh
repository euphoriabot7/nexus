#!/usr/bin/env bash
# ============================================================
#  NEXUS - empaqueta una copia lista para Windows
#
#  Genera dist/NEXUS-windows-<version>.zip con los ficheros que
#  necesita Windows (nada de .git, pruebas ni caches) y con los
#  finales de linea correctos para cada tipo de fichero:
#    .bat .cmd .vbs  -> CRLF   (cmd.exe y WSH los exigen)
#    el resto        -> LF
#
#  Uso:  tools/empaquetar-windows.sh
# ============================================================
set -u
cd "$(dirname "$0")/.."

VERSION="$(tr -d '\r\n' < VERSION)"
DIST="dist"
NOMBRE="NEXUS-windows-${VERSION}"

if ! command -v zip >/dev/null 2>&1; then
  echo "Falta el programa 'zip'. Instalalo (sudo apt install zip) y repite." >&2
  exit 1
fi

rm -rf "$DIST/$NOMBRE" "$DIST/$NOMBRE.zip" "$DIST/tmp"
mkdir -p "$DIST/tmp/$NOMBRE"
DESTINO="$DIST/tmp/$NOMBRE"

# Que se lleva el paquete
ficheros=(
  server.py local_models.py local_models.json providers.json prompts.json
  pricing.json VERSION LICENSE README.md
  run.bat stop.bat update.bat install-windows.bat NEXUS.vbs
  run.sh stop.sh update.sh install-desktop.sh install-mac.command
)
for f in "${ficheros[@]}"; do
  [ -e "$f" ] && cp -p "$f" "$DESTINO/"
done
for d in app assets agentes tools; do
  [ -d "$d" ] && cp -rp "$d" "$DESTINO/"
done
for f in README_*.md; do
  [ -e "$f" ] && cp -p "$f" "$DESTINO/"
done

# Fuera lo que no pinta nada en el paquete
find "$DESTINO" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null
rm -rf "$DESTINO/tools/pruebas"
rm -f "$DESTINO/tools/build_readmes.py" "$DESTINO/tools/limpiar_historial_github.sh" \
      "$DESTINO/tools/empaquetar-windows.sh" "$DESTINO/tools/LEEME-WINDOWS.txt.bak" 
find "$DESTINO" -name '*.pyc' -delete 2>/dev/null
find "$DESTINO" -name '.DS_Store' -delete 2>/dev/null
rm -rf "$DESTINO/dist" "$DESTINO/__pycache__"

# Nota de instalacion para el usuario final
cp -p tools/LEEME-WINDOWS.txt "$DESTINO/" 2>/dev/null || true

# Finales de linea: CRLF para cmd/WSH, LF para todo lo demas
python3 - "$DESTINO" <<'PY'
import os, sys
base = sys.argv[1]
crlf = {'.bat', '.cmd', '.vbs'}
binario = {'.ico', '.png', '.jpg', '.jpeg', '.webp', '.woff', '.woff2', '.zip', '.pdf'}
n_crlf = n_lf = n_skip = 0
for raiz, dirs, ficheros in os.walk(base):
    for nombre in ficheros:
        ext = os.path.splitext(nombre)[1].lower()
        ruta = os.path.join(raiz, nombre)
        if ext in binario:
            n_skip += 1
            continue
        try:
            with open(ruta, 'rb') as fh:
                crudo = fh.read()
        except OSError:
            continue
        if b'\x00' in crudo[:8192]:
            n_skip += 1
            continue
        limpio = crudo.replace(b'\r\n', b'\n')
        nuevo = limpio.replace(b'\n', b'\r\n') if ext in crlf else limpio
        if nuevo != crudo:
            with open(ruta, 'wb') as fh:
                fh.write(nuevo)
        if ext in crlf:
            n_crlf += 1
        else:
            n_lf += 1
print(f"  finales de linea: {n_crlf} ficheros CRLF, {n_lf} LF, {n_skip} binarios sin tocar")
PY

( cd "$DIST/tmp" && zip -qr "../$NOMBRE.zip" "$NOMBRE" )
rm -rf "$DIST/tmp"

echo "  paquete: $DIST/$NOMBRE.zip"
ls -lh "$DIST/$NOMBRE.zip" | awk '{print "  tamano:  "$5}'
