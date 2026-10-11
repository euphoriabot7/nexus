#!/usr/bin/env bash
# ============================================================
#  NEXUS · trae la última versión desde GitHub
#  Si la carpeta es un clon de git, hace 'git pull'.
#  Si se descargó en zip, baja el paquete y lo copia encima.
#  No toca tus chats, tus claves ni tu configuración.
# ============================================================
set -u
cd "$(dirname "$0")"
REPO="euphoriabot7/nexus"

echo "NEXUS · actualizando desde github.com/$REPO"

if [ -d .git ] && command -v git >/dev/null 2>&1; then
  antes="$(git rev-parse --short HEAD 2>/dev/null || echo "-")"
  if git pull --ff-only; then
    despues="$(git rev-parse --short HEAD 2>/dev/null || echo "-")"
    if [ "$antes" = "$despues" ]; then
      echo "  Ya tenías la última versión ($antes)."
    else
      echo "  Actualizado: $antes -> $despues"
      echo "  Reinicia NEXUS (cierra la ventana y vuelve a abrirlo) para usarlo."
    fi
  else
    echo "  No se pudo actualizar con git (¿cambios locales?). Revisa: git status"
    exit 1
  fi
  exit 0
fi

# sin git: se descarga el paquete publicado
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
echo "  Descargando el paquete..."
if ! curl -fsSL "https://github.com/$REPO/archive/refs/heads/main.tar.gz" -o "$TMP/nexus.tar.gz"; then
  echo "  No se pudo descargar. Comprueba tu conexión."
  exit 1
fi
tar -xzf "$TMP/nexus.tar.gz" -C "$TMP"
RAIZ="$(find "$TMP" -maxdepth 1 -type d -name 'nexus-*' | head -1)"
if [ -z "$RAIZ" ]; then
  echo "  El paquete descargado no tiene la forma esperada."
  exit 1
fi
ANTES_V="$(cat VERSION 2>/dev/null || echo '?')"
( cd "$RAIZ" && tar -cf - --exclude='.git' . ) | tar -xf - -C .
echo "  Actualizado: versión $ANTES_V -> $(cat VERSION 2>/dev/null || echo '?')"
echo "  Reinicia NEXUS (cierra la ventana y vuelve a abrirlo) para usarlo."
