"""Prueba de NEXUS. Necesita el servidor en marcha (run.sh / run.bat).

Ejecutar desde la carpeta del proyecto:  python3 tools/pruebas/prueba_updater.py
"""
import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(APP_DIR))
#!/usr/bin/env python3
"""Pruebas del sistema de actualizaciones y de las rutas de Windows.

No hace falta publicar nada: se sustituye la descarga por valores controlados.
"""
import importlib
import os
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, "APP_DIR")
import server  # noqa: E402

print("=== 1) Comparacion de versiones ===")
original = server._descarga


def falso(valor):
    def _d(url, timeout=20):
        if isinstance(valor, Exception):
            raise valor
        if "commits" in url:
            return b'[{"commit":{"message":"Arreglo uno\\nsegunda linea"}},{"commit":{"message":"Mejora dos"}}]'
        return valor
    return _d


casos = [
    ("remoto mas nuevo -> hay actualizacion", b"0.9.0\n", True),
    ("remoto igual -> al dia", b"0.2.0\n", False),
    ("remoto mas viejo -> no hay", b"0.1.0\n", False),
]
for nombre, valor, esperado in casos:
    server._descarga = falso(valor)
    info = server.comprobar_actualizacion(guardar=False)
    bien = info["hay"] is esperado and not info["error"]
    print(f"  {'OK  ' if bien else 'FALLO'} {nombre}: local={info['local']} remoto={info['remoto']!r} hay={info['hay']}")
    if esperado:
        print(f"        novedades: {info['notas'][:80]!r}")

server._descarga = falso(RuntimeError("sin conexion"))
info = server.comprobar_actualizacion(guardar=False)
print(f"  {'OK  ' if info['error'] and not info['hay'] else 'FALLO'} sin conexion: error informado y sin falsos positivos"
      f" -> {info['error'][:50]!r}")
server._descarga = original

print("=== 2) Aplicar la actualizacion (via git de verdad) ===")
print("  metodo detectado:", "git" if server.tiene_git() else "zip (sin git)")
t0 = time.time()
ok, salida = server.aplicar_actualizacion()
print(f"  {'OK  ' if ok else 'FALLO'} git pull --ff-only en {time.time() - t0:.1f}s -> {salida[:120]!r}")

print("=== 3) Rutas y comportamiento en Windows ===")
codigo = r'''
import sys, os, pathlib
sys.platform = "win32"
os.environ["LOCALAPPDATA"] = r"C:\Users\Andy\AppData\Local"
os.environ["APPDATA"] = r"C:\Users\Andy\AppData\Roaming"
os.environ["USERPROFILE"] = r"C:\Users\Andy"
sys.path.insert(0, "APP_DIR")
import server
print("PLATAFORMA:", server.PLATFORM, "| IS_WIN:", server.IS_WIN, "| EXE:", repr(server.EXE))
print("DATA_DIR:", server.DATA_DIR)
print("CONFIG_DIR:", server.CONFIG_PATH.parent)
print("pidfile:", server.PID_FILE)
print("hermes:", server.hermes_bin())
'''
r = subprocess.run([sys.executable, "-c", codigo.replace("APP_DIR", str(APP_DIR))], capture_output=True, text=True, timeout=120)
print(r.stdout.strip() or r.stderr.strip()[:400])
