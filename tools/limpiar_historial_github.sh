#!/usr/bin/env bash
# Deja el repositorio de GitHub sin el historial antiguo (los commits viejos
# dejan de ser legibles) SIN perder nada en local: tu rama main y tus etiquetas
# de version se quedan tal cual estan en este equipo.
#
# Como funciona: se construye un unico commit con el arbol actual y se empuja
# con --force a la rama remota. El historial local no se toca.
#
# Uso:
#   ./tools/limpiar_historial_github.sh --dry-run    solo comprueba, no cambia nada
#   ./tools/limpiar_historial_github.sh --si         hace la limpieza (pide confirmacion)
#
# Requiere una credencial que funcione para empujar (clave SSH registrada en
# GitHub, o token en el gestor de credenciales / config local de NEXUS).
# Nunca pide ni muestra secretos: usa la que ya tienes configurada.

set -euo pipefail

RAMAL_REMOTA="main"
SECO=0
CONFIRMA=0
for a in "$@"; do
  case "$a" in
    --dry-run) SECO=1 ;;
    --si)      CONFIRMA=1 ;;
    *) echo "Opcion no reconocida: $a"; exit 2 ;;
  esac
done

cd "$(cd "$(dirname "$0")/.." && pwd)"
echo "Repositorio: $(pwd)"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Esto no es una copia de git. No hay nada que limpiar." >&2
  exit 1
fi

REMOTO="$(git remote get-url origin 2>/dev/null || true)"
if [ -z "$REMOTO" ]; then
  echo "No hay remoto 'origin'." >&2
  exit 1
fi
echo "Remoto:      $REMOTO"
echo "Rama actual: $(git rev-parse --abbrev-ref HEAD)"
echo "Commit local: $(git rev-parse --short HEAD) ($(cat VERSION 2>/dev/null || echo 'sin VERSION'))"
echo "Commits en local que se conservaran: $(git rev-list --count HEAD)"

if [ -n "$(git status --porcelain)" ]; then
  echo
  echo "AVISO: hay cambios sin guardar. El commit limpio incluiria solo lo guardado."
fi

echo
echo "Comprobando permiso de escritura (git push --dry-run)..."
# 'git ls-remote' no sirve de prueba en un repositorio publico: cualquiera puede
# leer. Lo que de verdad importa es poder EMPUJAR, y eso se comprueba con un
# push simulado a una rama que no llega a crearse.
if git push --dry-run origin "HEAD:refs/heads/_nexus_permiso_$$" >/dev/null 2>&1; then
  echo "  credencial OK: puedo empujar al remoto."
else
  echo "  SIN permiso de escritura: el push simulado ha fallado." >&2
  echo "  Anade la clave SSH en https://github.com/settings/keys o un token," >&2
  echo "  y vuelve a intentarlo. No se ha cambiado nada." >&2
  exit 3
fi

PLAN="crear un commit unico con el arbol actual y empujarlo con --force a origin/$RAMAL_REMOTA"
if [ "$SECO" = "1" ]; then
  echo
  echo "SIMULACION (--dry-run): haria $PLAN. No se ha cambiado nada."
  exit 0
fi

if [ "$CONFIRMA" != "1" ]; then
  echo
  echo "Esto borra el historial visible en GitHub y es irreversible."
  echo "Repite con --si para hacerlo de verdad."
  exit 4
fi

RAMA_ORIGINAL="$(git rev-parse --abbrev-ref HEAD)"
TEMPORAL="_limpio_$(date +%s)"

echo
echo "1/4 creando rama sin historia: $TEMPORAL"
git checkout --orphan "$TEMPORAL" >/dev/null 2>&1
git add -A
git -c user.name="${GIT_AUTHOR_NAME:-NEXUS}" -c user.email="${GIT_AUTHOR_EMAIL:-nexus@localhost}" \
    commit -q -m "NEXUS $(cat VERSION 2>/dev/null || echo '')"

echo "2/4 empujando a origin/$RAMAL_REMOTA (--force)"
git push --force origin "$TEMPORAL:$RAMAL_REMOTA"

echo "3/4 volviendo a $RAMA_ORIGINAL (tu historial local intacto)"
git checkout "$RAMA_ORIGINAL" >/dev/null 2>&1
git branch -D "$TEMPORAL" >/dev/null

echo "4/4 comprobando el remoto"
git ls-remote origin "refs/heads/$RAMAL_REMOTA"
echo
echo "Hecho. El historial antiguo ya no es accesible por la rama $RAMAL_REMOTA."
echo "Tu copia local conserva todos los commits y versiones."
