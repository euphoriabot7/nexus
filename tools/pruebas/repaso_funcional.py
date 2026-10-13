#!/usr/bin/env python3
"""Repaso funcional completo de NEXUS con el modelo local."""
import json
import os
import time
import urllib.request

BASE = "http://127.0.0.1:8765"
MODELO = os.environ.get("NEXUS_TEST_MODEL", "huihui_ai/qwen3-abliterated:1.7b")


def api(ruta, cuerpo=None, metodo=None, timeout=180):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(BASE + ruta, data=datos, method=metodo or ("POST" if cuerpo is not None else "GET"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def sse_chat(chat_id, texto, agent=0, timeout=300):
    cuerpo = json.dumps({"chat_id": chat_id, "provider": "ollama", "model": MODELO, "agent": agent, "content": texto}).encode()
    req = urllib.request.Request(BASE + "/api/chat", data=cuerpo, headers={"Content-Type": "application/json"})
    t0 = time.time()
    primera, salida, meta, error = None, "", {}, ""
    with urllib.request.urlopen(req, timeout=timeout) as r:
        for linea in r:
            l = linea.decode("utf-8", "replace").strip()
            if l.startswith("data:"):
                try:
                    d = json.loads(l[5:])
                except Exception:
                    continue
                if d.get("text"):
                    if primera is None:
                        primera = time.time() - t0
                    salida += d["text"]
                if "usage" in d or "error" in d:
                    meta = d
                    error = d.get("error") or error
    return primera, time.time() - t0, salida, meta, error


print("=== 1) Servicios ===")
print("  NEXUS:", "OK" if api("/api/health") else "FALLO")
loc = api("/api/local")
print("  Ollama:", loc["ollama_bin"], "| en marcha:", loc["ollama_running"],
      "| modelos:", [m["name"] for m in loc["ollama_instalados"]])
print("  catalogo:", len(loc["catalogo"]), "modelos |", sum(1 for m in loc["catalogo"] if m["herramientas"]), "con herramientas")
print("  memoria libre:", loc["ram_libre"], "GB de", loc["ram_total"], "| disco libre:", loc["espacio_libre"])

print("=== 2) El modelo por dentro ===")
req = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=json.dumps({
    "model": MODELO, "stream": False, "messages": [{"role": "user", "content": "Saluda en una frase corta"}],
    "options": {"num_predict": 40}}).encode(), headers={"Content-Type": "application/json"})
t0 = time.time()
d = json.loads(urllib.request.urlopen(req, timeout=300).read().decode())
dur = time.time() - t0
print(f"  charla: {dur:.1f}s | {d.get('eval_count')} tokens | "
      f"{d.get('eval_count', 0) / max(d.get('eval_duration', 1) / 1e9, 0.001):.1f} t/s")
print("  respuesta:", repr((d.get("message") or {}).get("content", "")[:70]))

print("=== 3) Herramientas (lo que necesita un agente) ===")
HERR = [{"type": "function", "function": {"name": "abrir_carpeta",
         "description": "Lista los archivos de una carpeta del ordenador",
         "parameters": {"type": "object", "properties": {"ruta": {"type": "string"}}, "required": ["ruta"]}}}]
req = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=json.dumps({
    "model": MODELO, "stream": False, "tools": HERR,
    "messages": [{"role": "user", "content": "Dime que hay en la carpeta /home/andy"}],
    "options": {"num_predict": 100, "temperature": 0.2}}).encode(), headers={"Content-Type": "application/json"})
t0 = time.time()
d2 = json.loads(urllib.request.urlopen(req, timeout=300).read().decode())
llamadas = (d2.get("message") or {}).get("tool_calls") or []
print(f"  {time.time() - t0:.1f}s | llamada valida: {'SI' if llamadas else 'NO'}"
      f" -> {json.dumps(llamadas, ensure_ascii=False)[:140]}")

print("=== 4) Conversaciones de especialista por NEXUS ===")
for pid in ("seo", "analista", "vida"):
    ag = next(a for a in api("/api/agents")["agents"] if a["id"] == pid)
    chat = api(f"/api/agents/{pid}/chat", {})["chat"]
    prompt = (ag["sugerencias"] or ["Hola"])[0]
    primera, total, salida, meta, error = sse_chat(chat["id"], prompt)
    pal = len(salida.split())
    t1 = f"{primera:.1f}s" if primera is not None else ">espera"
    tt = f"{total:.1f}s" if total is not None else "-"
    print(f"  {ag['emoji']} {ag['nombre']:22} | 1ª palabra {t1} | total {tt} | "
          f"{pal} palabras | {'OK' if salida and not error else 'ERROR'}")
    print(f"      {salida[:110].replace(chr(10), ' ')!r}")
    api(f"/api/chats/{chat['id']}", metodo="DELETE")

print("=== 5) Regenerar y adjuntos ===")
chat = api("/api/chats", {"title": "prueba interna", "provider": "ollama", "model": MODELO})["chat"]
primera, total, salida, _, _ = sse_chat(chat["id"], "Di la palabra prueba")
msgs = api(f"/api/chats/{chat['id']}/messages")["messages"]
tt = f"{total:.1f}s" if total is not None else "-"
print(f"  turno: {tt} | mensajes guardados: {len(msgs)} | roles: {[m['role'] for m in msgs]}")
api(f"/api/chats/{chat['id']}", metodo="DELETE")
print("  (chat de prueba borrado)")
