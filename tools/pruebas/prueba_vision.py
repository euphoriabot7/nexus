#!/usr/bin/env python3
"""¿Qué pasa de verdad al adjuntar una imagen a un modelo que no ve?

Se manda el adjunto en el MISMO formato que usa la interfaz (base64 puro) y se
imprimen todos los eventos del flujo, incluidos los errores.
"""
import base64
import json
import time
import urllib.request

BASE = "http://127.0.0.1:8765"
MODELO = "huihui_ai/qwen2.5-abliterate:0.5b"
png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==")


def api(ruta, cuerpo=None, metodo=None, timeout=60):
    d = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(BASE + ruta, data=d, method=metodo or ("POST" if cuerpo is not None else "GET"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def turno(titulo, adjuntos, texto="¿Qué ves? Una palabra."):
    chat = api("/api/chats", {"title": titulo, "provider": "ollama", "model": MODELO})["chat"]
    cuerpo = json.dumps({"chat_id": chat["id"], "provider": "ollama", "model": MODELO, "agent": 0,
                         "content": texto, "attachments": adjuntos}).encode()
    req = urllib.request.Request(BASE + "/api/chat", data=cuerpo, headers={"Content-Type": "application/json"})
    t0 = time.time()
    texto_out, eventos, detalle = "", [], {}
    with urllib.request.urlopen(req, timeout=300) as r:
        for linea in r:
            l = linea.decode("utf-8", "replace").strip()
            if l.startswith("event:"):
                eventos.append(l.split(":", 1)[1].strip())
            elif l.startswith("data:"):
                try:
                    d = json.loads(l[5:])
                except Exception:
                    continue
                if d.get("text"):
                    texto_out += d["text"]
                if any(k in d for k in ("message_id", "message", "meta")):
                    detalle = d
    msgs = api(f"/api/chats/{chat['id']}/messages")["messages"]
    fichas = [f for m in msgs for f in ((m.get("meta") or {}).get("files") or [])]
    api(f"/api/chats/{chat['id']}", metodo="DELETE")
    return {"dur": round(time.time() - t0, 1), "eventos": sorted(set(eventos)), "salida": texto_out[:120],
            "detalle": detalle, "fichas": [f["file"] for f in fichas]}


print("=== 1) imagen en base64 puro (como manda la interfaz) ===")
r = turno("prueba imagen", [{"name": "punto.png", "mime": "image/png", "img": True,
                            "data": base64.b64encode(png).decode()}])
print(f"  {r['dur']}s | eventos: {r['eventos']}")
print(f"  adjuntos guardados: {r['fichas']}")
print(f"  salida: {r['salida']!r}")
print(f"  detalle: {json.dumps(r['detalle'], ensure_ascii=False)[:300]}")

print("=== 2) texto en base64 puro ===")
r = turno("prueba texto", [{"name": "notas.txt", "mime": "text/plain", "img": False,
                            "data": base64.b64encode("El codigo secreto es 4711".encode()).decode()}],
          texto="¿Cuál es el código secreto del archivo?")
print(f"  {r['dur']}s | eventos: {r['eventos']}")
print(f"  adjuntos guardados: {r['fichas']}")
print(f"  salida: {r['salida']!r}")

print("=== 3) adjunto con formato data URL (por si lo manda otro cliente) ===")
r = turno("prueba dataurl", [{"name": "punto.png", "mime": "image/png", "img": True,
                             "data": "data:image/png;base64," + base64.b64encode(png).decode()}])
print(f"  {r['dur']}s | eventos: {r['eventos']}")
print(f"  adjuntos guardados: {r['fichas']}")
print(f"  detalle: {json.dumps(r['detalle'], ensure_ascii=False)[:200]}")
