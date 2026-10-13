#!/usr/bin/env python3
"""Auditoria del servidor de NEXUS: entradas raras, casos limite y flujos completos.

Cada prueba dice OK o FALLO con el detalle. Al final, el resumen.
"""
import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8765"
fallos = []
aviso = []


def pedir(ruta, cuerpo=None, metodo=None, timeout=40, crudo=None, cabeceras=None):
    datos = crudo if crudo is not None else (json.dumps(cuerpo).encode() if cuerpo is not None else None)
    req = urllib.request.Request(BASE + ruta, data=datos, method=metodo or ("POST" if datos is not None else "GET"),
                                 headers={"Content-Type": "application/json", **(cabeceras or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"


def prueba(nombre, fn, esperado=None, critico=True):
    try:
        codigo, cuerpo = fn()
        ok = esperado(codigo, cuerpo) if esperado else (200 <= codigo < 300)
        etiqueta = "OK   " if ok else ("FALLO" if critico else "aviso")
        print(f"  {etiqueta} {nombre}: {codigo} {str(cuerpo)[:90]}")
        if not ok:
            (fallos if critico else aviso).append(nombre)
    except Exception as e:
        print(f"  FALLO {nombre}: {type(e).__name__}: {e}")
        fallos.append(nombre)


print("=== A) entradas mal formadas (no debe caerse el servidor) ===")
prueba("cuerpo JSON roto", lambda: pedir("/api/chats", crudo=b"{esto no es json"),
       lambda c, b: c >= 400)
prueba("cuerpo vacio (crear chat con valores por defecto)", lambda: pedir("/api/chats", crudo=b""),
       lambda c, b: c == 201)
prueba("cuerpo enorme (1 MB)", lambda: pedir("/api/chats", crudo=b'{"title":"' + b"x" * 1_000_000 + b'"}'),
       lambda c, b: c < 600)
prueba("tipo equivocado (title numero)", lambda: pedir("/api/chats", {"title": 12345}),
       lambda c, b: c < 600)
prueba("id inexistente", lambda: pedir("/api/chats/no-existe/messages"), lambda c, b: c == 404)
prueba("borrar chat inexistente", lambda: pedir("/api/chats/no-existe", metodo="DELETE"), lambda c, b: c < 600)
prueba("ruta con ../", lambda: pedir("/api/../../etc/passwd"), lambda c, b: c >= 400)
prueba("metodo raro (PUT)", lambda: pedir("/api/chats", crudo=b"{}", metodo="PUT"), lambda c, b: c in (400, 404, 405, 501))

print("=== B) flujo completo de un chat ===")
codigo, cuerpo = pedir("/api/chats", {"title": "auditoria", "provider": "ollama",
                                      "model": "huihui_ai/qwen2.5-abliterate:0.5b"})
cid = json.loads(cuerpo)["chat"]["id"]
prueba("renombrar", lambda: pedir(f"/api/chats/{cid}", {"title": "auditoria 2"}, metodo="PATCH"),
       lambda c, b: c == 200 and "auditoria 2" in b)
prueba("fijar", lambda: pedir(f"/api/chats/{cid}", {"pinned": 1}, metodo="PATCH"),
       lambda c, b: c == 200)
prueba("duplicar", lambda: pedir(f"/api/chats/{cid}/duplicate", {}),
       lambda c, b: c in (200, 201))
duplicado = json.loads(pedir(f"/api/chats/{cid}/duplicate", {})[1])["chat"]["id"]
prueba("vacio: limpiar mensajes", lambda: pedir(f"/api/chats/{cid}/clear", {}), lambda c, b: c == 200)
prueba("estadisticas", lambda: pedir(f"/api/chats/{cid}/stats"), lambda c, b: c == 200)
prueba("parar turno inexistente", lambda: pedir(f"/api/chats/{cid}/stop", {}), lambda c, b: c == 200)
prueba("borrar duplicado", lambda: pedir(f"/api/chats/{duplicado}", metodo="DELETE"), lambda c, b: c == 200)

print("=== C) adjuntos (la subida va dentro del turno; /api/files solo sirve) ===")
prueba("servir adjunto inexistente", lambda: pedir("/api/files/no-existe.png"), lambda c, b: c == 404)
prueba("traversal por el nombre", lambda: pedir("/api/files/..%2Fnexus.db"), lambda c, b: c == 404)

print("=== D) exportar / importar ===")
codigo, cuerpo = pedir("/api/export")
prueba("exportar", lambda: (codigo, cuerpo), lambda c, b: c == 200 and "chats" in b)
antes_import = {c["id"] for c in json.loads(pedir("/api/chats")[1])["chats"]}
prueba("importar lo exportado", lambda: pedir("/api/import", json.loads(cuerpo)), lambda c, b: c == 200)
# la importacion CREA chats: se borran los que ha traido, para no dejar copias
for ch in json.loads(pedir("/api/chats")[1])["chats"]:
    if ch["id"] not in antes_import:
        pedir(f"/api/chats/{ch['id']}", metodo="DELETE")
prueba("importar basura", lambda: pedir("/api/import", {"chats": "no es lista"}), lambda c, b: c < 600)

print("=== E) especialistas ===")
codigo, cuerpo = pedir("/api/agents", {"nombre": "Auditor", "sistema": "prueba", "sugerencias": ["uno", "dos"]})
aid = json.loads(cuerpo)["agent"]["id"]
prueba("crear", lambda: (codigo, cuerpo), lambda c, b: c == 200)
prueba("editar", lambda: pedir("/api/agents", {"id": aid, "nombre": "Auditor 2"}), lambda c, b: c == 200 and "Auditor 2" in b)
prueba("chat del especialista", lambda: pedir(f"/api/agents/{aid}/chat", {}), lambda c, b: c == 200)
prueba("exportar especialista", lambda: pedir(f"/api/agents/{aid}/export"), lambda c, b: c == 200 and "Auditor" in b)
prueba("importar especialista de archivo inexistente", lambda: pedir("/api/agents/import", {"path": "/no/existe.json"}), lambda c, b: c in (400, 404, 500))
prueba("borrar especialista", lambda: pedir(f"/api/agents/{aid}", metodo="DELETE"), lambda c, b: c == 200)
prueba("borrar especialista inexistente", lambda: pedir("/api/agents/nope", metodo="DELETE"), lambda c, b: c < 600)

print("=== F) proveedores y configuracion ===")
prueba("probar proveedor sin URL", lambda: pedir("/api/config/test", {"provider": "custom", "spec": {"id": "custom"}}),
       lambda c, b: c < 600 and "error" in b.lower())
prueba("guardar proveedor sin id", lambda: pedir("/api/config", {"provider": {}}), lambda c, b: c == 400)
prueba("borrar proveedor inexistente", lambda: pedir("/api/config", {"delete": "no-existe"}), lambda c, b: c < 600)
prueba("modelos de proveedor inventado", lambda: pedir("/api/config/models", {"provider": "inventado"}), lambda c, b: c < 600)
prueba("preferencia de actualizacion", lambda: pedir("/api/config", {"update_auto": True}), lambda c, b: c == 200 and "update_auto" in b)

print("=== G) tareas ===")
prueba("crear tarea sin prompt", lambda: pedir("/api/tasks", {}), lambda c, b: c in (200, 400))
prueba("cancelar tarea inexistente", lambda: pedir("/api/tasks/nope/cancel", {}), lambda c, b: c in (200, 404, 500))

print("=== H) el servidor sigue vivo ===")
prueba("salud", lambda: pedir("/api/health"), lambda c, b: c == 200)
prueba("estado", lambda: pedir("/api/state"), lambda c, b: c == 200 and "chats" in b)
prueba("id de chat con caracteres raros", lambda: pedir("/api/chats/../../x", metodo="DELETE"), lambda c, b: c >= 400)

# limpieza: se borran TODOS los chats de prueba que ha creado esta auditoria
originales = {"c_8f434d4795e64b37a382d503c5061d0d"}
for ch in json.loads(pedir("/api/chats")[1])["chats"]:
    if ch["id"] not in originales:
        pedir(f"/api/chats/{ch['id']}", metodo="DELETE")
for ag in json.loads(pedir("/api/agents")[1])["agents"]:
    if ag["nombre"].startswith("Auditor"):
        pedir(f"/api/agents/{ag['id']}", metodo="DELETE")
print()
print("=" * 60)
print(f"RESULTADO: {len(fallos)} fallos, {len(aviso)} avisos")
if fallos:
    print("FALLAN:", fallos)
if aviso:
    print("AVISOS:", aviso)
