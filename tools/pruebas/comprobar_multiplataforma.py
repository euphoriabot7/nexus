#!/usr/bin/env python3
"""Comprueba que NEXUS puede funcionar en Windows y en macOS.

Todo lo que aqui se mira son cosas que, si estan mal, rompen la app en otro
sistema y no se notan cuando desarrollas en uno solo:

  * lanzadores de las tres plataformas y sus finales de linea / BOM
  * permisos de ejecucion de los .sh / .command
  * rutas de datos por plataforma (server.py vs. los lanzadores)
  * codificacion explicita en subprocess / open  (Windows no es UTF-8)
  * llamadas que solo existen en Linux (xdg-open, /proc, sudo, unzip...)
  * que la app no dependa de la CLI sqlite3 ni de paquetes externos
  * sintaxis de todos los .py y de los .js de la interfaz

Uso:  python3 tools/pruebas/comprobar_multiplataforma.py
Se puede ejecutar en Linux, macOS o Windows (solo biblioteca estandar).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
fallos = []
avisos = []
ok = []


def bien(texto):
    ok.append(texto)


def fallo(texto):
    fallos.append(texto)


def aviso(texto):
    avisos.append(texto)


def leer(p):
    return p.read_text(encoding="utf-8", errors="replace")


def ficheros(patron, raiz=RAIZ):
    fuera = []
    for p in raiz.rglob(patron):
        if ".git" in p.parts or "__pycache__" in p.parts:
            continue
        fuera.append(p)
    return sorted(fuera)


# --------------------------------------------------------------------------- #
# 1. lanzadores presentes
# --------------------------------------------------------------------------- #
LANZADORES = ["run.bat", "stop.bat", "update.bat", "install-windows.bat",
              "run.sh", "stop.sh", "update.sh", "install-desktop.sh", "install-mac.command"]
for nombre in LANZADORES:
    if (RAIZ / nombre).is_file():
        bien(f"lanzador presente: {nombre}")
    else:
        fallo(f"falta el lanzador {nombre}")

# --------------------------------------------------------------------------- #
# 2. finales de linea y BOM
# --------------------------------------------------------------------------- #
for p in ficheros("*"):
    if not p.is_file() or p.suffix.lower() not in (".bat", ".cmd", ".sh", ".command", ".desktop", ".ps1"):
        continue
    datos = p.read_bytes()
    rel = p.relative_to(RAIZ)
    if datos[:3] == b"\xef\xbb\xbf":
        fallo(f"{rel}: tiene BOM (rompe el shebang en Unix y el primer comando en cmd.exe)")
    crlf = datos.count(b"\r\n")
    lf = datos.count(b"\n") - crlf
    if p.suffix.lower() in (".bat", ".cmd", ".ps1"):
        if lf and not crlf:
            fallo(f"{rel}: esta en LF; cmd.exe necesita CRLF")
        else:
            bien(f"{rel}: CRLF correcto")
    elif p.suffix.lower() in (".sh", ".command"):
        if crlf:
            fallo(f"{rel}: tiene CRLF; el shebang (#!...) no funciona en Unix con CR")
        else:
            bien(f"{rel}: LF correcto")

# --------------------------------------------------------------------------- #
# 3. permisos de ejecucion
# --------------------------------------------------------------------------- #
if os.name != "nt":
    for p in ficheros("*"):
        if p.is_file() and p.suffix.lower() in (".sh", ".command"):
            if not os.access(p, os.X_OK):
                aviso(f"{p.relative_to(RAIZ)}: sin permiso de ejecucion (usa: chmod +x ...)")

# --------------------------------------------------------------------------- #
# 4. rutas de datos por plataforma: servidor y lanzadores deben coincidir
# --------------------------------------------------------------------------- #
servidor = leer(RAIZ / "server.py")
esperado = {
    "windows": r'LOCALAPPDATA',
    "macos": r'Library.*Application Support.*NEXUS',
}
for sistema, patron in esperado.items():
    if re.search(patron, servidor):
        bien(f"server.py define la carpeta de datos de {sistema}")
    else:
        fallo(f"server.py no define la carpeta de datos de {sistema}")

run_bat, run_sh, stop_bat, stop_sh = (leer(RAIZ / f) for f in ("run.bat", "run.sh", "stop.bat", "stop.sh"))
if r"LOCALAPPDATA%\NEXUS" in run_bat and r"LOCALAPPDATA%\NEXUS" in stop_bat:
    bien("los .bat usan %LOCALAPPDATA%\\NEXUS (igual que el servidor)")
else:
    fallo("los .bat no usan la misma carpeta de datos que server.py")
if "Library/Application Support/NEXUS" in run_sh and "Library/Application Support/NEXUS" in stop_sh:
    bien("los .sh usan ~/Library/Application Support/NEXUS en macOS")
else:
    fallo("los .sh no contemplan la carpeta de datos de macOS")

# --------------------------------------------------------------------------- #
# 5. codificacion explicita (en Windows la de por defecto es cp1252, no UTF-8)
# --------------------------------------------------------------------------- #
for p in ficheros("*.py"):
    rel = p.relative_to(RAIZ)
    texto = leer(p)
    # una llamada puede envolver varias lineas: se mira la llamada entera
    for m in re.finditer(r"subprocess\.\w+\((?:[^()]|\([^()]*\))*\)", texto, re.S):
        llamada = m.group(0)
        if re.search(r"\btext\s*=\s*True", llamada) and "encoding" not in llamada:
            linea = texto[:m.start()].count("\n") + 1
            fallo(f"{rel}:{linea}: text=True sin encoding (usa encoding=\"utf-8\")")
    for i, linea in enumerate(texto.splitlines(), 1):
        if re.search(r"\b(?:open|read_text|write_text)\s*\(", linea) and "encoding" not in linea \
                and '"wb"' not in linea and "'wb'" not in linea and "urlopen" not in linea \
                and "tarfile" not in linea and "zipfile" not in linea:
            aviso(f"{rel}:{i}: {linea.strip()[:90]}")
bien("revision de codificacion terminada")

# --------------------------------------------------------------------------- #
# 6. cosas que solo existen en Linux, fuera de un bloque por plataforma
# --------------------------------------------------------------------------- #
SOLO_LINUX = re.compile(r"xdg-open|xdg-user-dir|/proc/|/bin/bash|/usr/bin/env|os\.geteuid|"
                        r"import pwd|import fcntl|import termios|systemctl|apt install")
for p in ficheros("*.py"):
    rel = p.relative_to(RAIZ)
    for i, linea in enumerate(leer(p).splitlines(), 1):
        if SOLO_LINUX.search(linea):
            aviso(f"{rel}:{i}: {linea.strip()[:100]}")
bien("revision de llamadas solo-Linux terminada (mira los avisos)")

# --------------------------------------------------------------------------- #
# 7. sin dependencias externas ni CLI sqlite3
# --------------------------------------------------------------------------- #
EXTERNAS = {"requests", "flask", "fastapi", "django", "numpy", "pandas", "psutil", "yaml", "dotenv"}
for p in ficheros("*.py"):
    rel = p.relative_to(RAIZ)
    for i, linea in enumerate(leer(p).splitlines(), 1):
        m = re.match(r"\s*(?:import|from)\s+([A-Za-z_][\w]*)", linea)
        if m and m.group(1) in EXTERNAS:
            fallo(f"{rel}:{i}: importa {m.group(1)} (NEXUS no usa dependencias externas)")
if re.search(r'subprocess\.\w+\(\s*\[?["\']sqlite3["\']', servidor):
    fallo("server.py llama a la CLI sqlite3 (no esta en macOS ni en muchos Windows)")
else:
    bien("la base de datos se maneja con el modulo sqlite3 de Python, no con la CLI")

# --------------------------------------------------------------------------- #
# 8. sintaxis de .py y .js
# --------------------------------------------------------------------------- #
import py_compile                                    # noqa: E402
import tempfile                                      # noqa: E402
_tmp = Path(tempfile.mkdtemp(prefix="nexus-pycheck-"))
for p in ficheros("*.py"):
    try:
        py_compile.compile(str(p), doraise=True, cfile=str(_tmp / (p.stem + ".pyc")))
        bien(f"sintaxis py OK: {p.relative_to(RAIZ)}")
    except py_compile.PyCompileError as exc:
        fallo(f"{p.relative_to(RAIZ)}: error de sintaxis: {exc}")

if os.name != "nt":     # node --check no esta en Windows por defecto
    import shutil
    import subprocess
    if shutil.which("node"):
        for p in ficheros("*.js"):
            r = subprocess.run(["node", "--check", str(p)], capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            if r.returncode:
                fallo(f"{p.relative_to(RAIZ)}: error de sintaxis JS: {(r.stderr or '')[:200]}")
        bien("sintaxis JS comprobada con node --check")
    else:
        aviso("node no esta instalado: no se ha comprobado la sintaxis de los .js")

# --------------------------------------------------------------------------- #
# informe
# --------------------------------------------------------------------------- #
print("=" * 70)
print("NEXUS · comprobacion multiplataforma (Windows / macOS / Linux)")
print("=" * 70)
print(f"\nCorrecto: {len(ok)}")
print(f"Avisos:   {len(avisos)}")
print(f"FALLOS:   {len(fallos)}\n")
if avisos:
    print("--- avisos (revisar si aplican a tu instalacion) ---")
    for a in avisos:
        print("  ·", a)
    print()
if fallos:
    print("--- FALLOS (esto rompe la app en otro sistema) ---")
    for f in fallos:
        print("  x", f)
    print()
else:
    print("Sin fallos: los lanzadores y el codigo son coherentes en las tres plataformas.")
print(f"\nPlataforma actual: {sys.platform}")
sys.exit(1 if fallos else 0)
