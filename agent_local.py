"""Modo agente con modelos LOCALES, sin depender del CLI de Hermes.

Hermes mete un prompt de sistema de ~5.000 tokens: en una CPU de portatil eso
son varios minutos solo para el primer token. Aqui el bucle de herramientas lo
hace NEXUS hablando directo con Ollama (/api/chat con `tools`), con un prompt
de sistema de ~200 tokens, asi que el primer token tarda segundos y el modo
agente funciona sin conexion y sin instalar nada mas.

Solo biblioteca estandar.
"""

import fnmatch
import json
import os
import platform
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

# En Windows, cada subproceso que abre consola hace saltar una ventana negra.
NO_WINDOW = 0x08000000 if os.name == "nt" else 0

SISTEMA = (
    "Eres el agente local de NEXUS, en el ordenador del usuario. Tienes "
    "herramientas para mirar y tocar ficheros. Reglas:\n"
    "- Usa las herramientas cuando necesites datos reales; no inventes rutas, "
    "contenidos ni cifras.\n"
    "- Para saber cuantos ficheros hay de un tipo usa la herramienta contar. "
    "Nunca cuentes de memoria.\n"
    "- Para datos del ordenador (memoria RAM libre, sistema, disco) usa la "
    "herramienta sistema o los datos que ya tienes abajo; no los inventes.\n"
    "- Trabaja dentro de la carpeta de trabajo. La carpeta de trabajo es '.' "
    "(rutas relativas a ella: '.', 'app'...). No inventes subcarpetas.\n"
    "- Contesta en el idioma en el que te escriben, corto y directo.\n"
    "- Cuando ya tengas la respuesta, escribe el resultado y no llames a mas "
    "herramientas."
)

# ---------------------------------------------------------------- herramientas

_LEER = [
    {
        "type": "function",
        "function": {
            "name": "listar",
            "description": "Lista ficheros y carpetas de un directorio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ruta": {"type": "string", "description": "Directorio (por defecto la carpeta de trabajo)"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "leer",
            "description": "Lee un fichero de texto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ruta": {"type": "string", "description": "Ruta del fichero"},
                    "lineas": {"type": "integer", "description": "Cuantas lineas devolver (max 400)"},
                },
                "required": ["ruta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "contar",
            "description": "Cuenta ficheros de una carpeta por tipo (ej. *.py). Devuelve el numero exacto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patron": {"type": "string", "description": "Patron de nombre, ej. '*.py'"},
                    "ruta": {"type": "string", "description": "Carpeta donde contar"},
                },
                "required": ["patron"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar",
            "description": "Busca un texto dentro de los ficheros de una carpeta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {"type": "string", "description": "Texto o trozo de texto a buscar"},
                    "ruta": {"type": "string", "description": "Carpeta donde buscar"},
                },
                "required": ["texto"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sistema",
            "description": ("Datos reales de este ordenador: sistema operativo, CPU, memoria RAM "
                            "total y libre, y disco libre. Usala cuando te pregunten por el "
                            "equipo o por la memoria."),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

_ESCRIBIR = [
    {
        "type": "function",
        "function": {
            "name": "escribir",
            "description": "Crea o reemplaza un fichero de texto con el contenido dado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ruta": {"type": "string", "description": "Ruta del fichero"},
                    "contenido": {"type": "string", "description": "Contenido completo del fichero"},
                },
                "required": ["ruta", "contenido"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "comando",
            "description": "Ejecuta un comando de shell y devuelve su salida.",
            "parameters": {
                "type": "object",
                "properties": {
                    "orden": {"type": "string", "description": "Comando a ejecutar"},
                },
                "required": ["orden"],
            },
        },
    },
]


def herramientas(permitir_escritura=False):
    return _LEER + (_ESCRIBIR if permitir_escritura else [])


def _dentro(ruta, base):
    """Devuelve la ruta resuelta si cae dentro de la carpeta de trabajo."""
    p = Path(ruta).expanduser()
    if not p.is_absolute():
        p = Path(base) / p
    try:
        real = p.resolve()
        raiz = Path(base).resolve()
    except Exception:
        return None
    if real == raiz or raiz in real.parents:
        return real
    return None


def _corta(texto, limite=8000):
    texto = texto or ""
    if len(texto) <= limite:
        return texto
    return texto[:limite] + f"\n... (recortado, {len(texto)} caracteres en total)"


def info_equipo(workdir=""):
    """Datos reales del ordenador, sin dependencias. Se los pasamos al modelo
    para que pueda responder por la RAM o el disco con cifras verdaderas (y lo
    pueda comprobar cualquiera): asi se ve si un modelo ligero es valido."""
    libre, total = _ram()
    try:
        sistema = f"{platform.system()} {platform.release()}"
        if platform.machine():
            sistema += f" ({platform.machine()})"
    except Exception:
        sistema = os.name
    try:
        cpu = platform.processor() or platform.machine() or "?"
    except Exception:
        cpu = "?"
    try:
        nucleos = os.cpu_count() or 0
    except Exception:
        nucleos = 0
    carpeta = workdir or str(Path.home())
    try:
        disco = round(shutil.disk_usage(carpeta).free / 1024 ** 3, 1)
    except Exception:
        disco = None
    return {"sistema": sistema, "cpu": cpu, "nucleos": nucleos,
            "ram_libre": libre, "ram_total": total, "disco_libre": disco,
            "carpeta": carpeta}


def _ram():
    """(libre, total) en GB, o (None, None). Linux/Windows/macOS, sin dependencias."""
    try:
        if os.name == "nt":
            return _ram_windows()
        if platform.system() == "Darwin":
            return _ram_macos()
        ruta = Path("/proc/meminfo")
        if ruta.is_file():
            datos = {}
            for linea in ruta.read_text(encoding="utf-8", errors="replace").splitlines():
                campos = linea.split()
                if len(campos) >= 2:
                    try:
                        datos[campos[0].rstrip(":")] = int(campos[1])
                    except ValueError:
                        pass
            if datos.get("MemTotal"):
                return (round(datos.get("MemAvailable", 0) / 1024 ** 2, 1),
                        round(datos["MemTotal"] / 1024 ** 2, 1))
        pagina = os.sysconf("SC_PAGE_SIZE")
        total = os.sysconf("SC_PHYS_PAGES") * pagina / 1024 ** 3
        try:
            libre = os.sysconf("SC_AVPHYS_PAGES") * pagina / 1024 ** 3
        except (ValueError, OSError):
            libre = total * 0.5
        return round(libre, 1), round(total, 1)
    except Exception:
        return None, None


def _ram_windows():
    try:
        import ctypes

        class _Memoria(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

        datos = _Memoria()
        datos.dwLength = ctypes.sizeof(_Memoria)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(datos)):
            return None, None
        return round(datos.ullAvailPhys / 1024 ** 3, 1), round(datos.ullTotalPhys / 1024 ** 3, 1)
    except Exception:
        return None, None


def _ram_macos():
    total = 0
    try:
        r = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=10)
        total = int((r.stdout or "").strip() or 0)
    except Exception:
        total = 0
    if total <= 0:
        return None, None
    libre = None
    try:
        r = subprocess.run(["vm_stat"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=10)
        pagina, libres = 4096, 0
        for linea in (r.stdout or "").splitlines():
            if "page size of" in linea:
                try:
                    pagina = int(linea.split("page size of")[1].split()[0])
                except Exception:
                    pass
            elif linea.lower().startswith(("pages free", "pages inactive", "pages speculative")):
                try:
                    libres += int(linea.split(":")[1].strip().rstrip("."))
                except Exception:
                    pass
        libre = libres * pagina
    except Exception:
        libre = None
    return (round((libre if libre is not None else total * 0.5) / 1024 ** 3, 1),
            round(total / 1024 ** 3, 1))


def texto_equipo(workdir=""):
    """El bloque de datos reales que va dentro del prompt de sistema."""
    d = info_equipo(workdir)
    ram = (f"{d['ram_libre']} GB libres de {d['ram_total']} GB"
           if d["ram_total"] else "no se pudo medir")
    lineas = [f"- memoria RAM: {ram}",
              f"- sistema: {d['sistema']}",
              f"- procesador: {d['cpu']} ({d['nucleos']} nucleos)"]
    if d["disco_libre"] is not None:
        lineas.append(f"- disco libre donde trabajo: {d['disco_libre']} GB")
    lineas.append(f"- carpeta de trabajo: {d['carpeta']}")
    return ("DATOS REALES DE ESTE ORDENADOR (medidos ahora mismo; si te preguntan por "
            "la memoria o el equipo, responde con estas cifras, no las inventes):\n"
            + "\n".join(lineas))


def ejecutar(nombre, args, workdir, permitir_escritura=False):
    """Ejecuta una herramienta y devuelve el texto que vera el modelo."""
    base = workdir or str(Path.home())
    args = args or {}
    if not os.path.isdir(base):
        base = str(Path.home())

    if nombre == "sistema":
        return texto_equipo(workdir)

    if nombre == "listar":
        ruta = _dentro(args.get("ruta") or base, base)
        if not ruta:
            return "Fuera de la carpeta de trabajo. Usa rutas dentro de " + base
        if not ruta.is_dir():
            return "No es un directorio: " + str(ruta)
        filas = []
        try:
            for e in sorted(ruta.iterdir(), key=lambda x: (x.is_dir(), x.name.lower()))[:300]:
                if e.is_dir():
                    filas.append("[dir]  " + e.name)
                else:
                    try:
                        filas.append(f"{e.stat().st_size:>9}  {e.name}")
                    except Exception:
                        filas.append("        ?  " + e.name)
        except PermissionError:
            return "Sin permiso para leer " + str(ruta)
        if not filas:
            return "La carpeta esta vacia."
        return f"{ruta} ({len(filas)} entradas):\n" + "\n".join(filas)

    if nombre == "leer":
        ruta = _dentro(args.get("ruta") or "", base)
        if not ruta:
            return "Fuera de la carpeta de trabajo. Usa rutas dentro de " + base
        if not ruta.is_file():
            return "No existe el fichero: " + str(ruta)
        try:
            limite = int(args.get("lineas") or 200)
        except Exception:
            limite = 200
        limite = max(1, min(limite, 400))
        try:
            with open(ruta, "r", encoding="utf-8", errors="replace") as fh:
                lineas = []
                for i, linea in enumerate(fh, 1):
                    if i > limite:
                        lineas.append(f"... (hay mas lineas en {ruta.name})")
                        break
                    lineas.append(f"{i}|{linea.rstrip()}")
        except Exception as exc:
            return f"No se pudo leer {ruta}: {exc}"
        return f"{ruta} ({len(lineas)} lineas leidas):\n" + "\n".join(lineas)

    if nombre == "contar":
        patron = (args.get("patron") or "").strip() or "*"
        ruta = _dentro(args.get("ruta") or base, base)
        if not ruta:
            return "Fuera de la carpeta de trabajo. Usa rutas dentro de " + base
        if not ruta.is_dir():
            return (f"No existe la carpeta {ruta}. La carpeta de trabajo es '.' : "
                    "vuelve a llamar a contar con ruta '.' (o sin ruta).")
        saltar = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
        hallados = []
        for actual, dirs, ficheros in os.walk(ruta):
            dirs[:] = [d for d in dirs if d not in saltar and not d.startswith(".")]
            for f in ficheros:
                if fnmatch.fnmatch(f.lower(), patron.lower()):
                    hallados.append(os.path.relpath(os.path.join(actual, f), ruta))
        if not hallados:
            return f"0 ficheros coinciden con '{patron}' en {ruta}."
        lista = "\n".join(sorted(hallados)[:40])
        return (f"Hay {len(hallados)} ficheros que coinciden con '{patron}' en {ruta} "
                f"(contados de verdad, recorre subcarpetas):\n{lista}")

    if nombre == "buscar":
        texto = (args.get("texto") or "").strip()
        if not texto:
            return "Falta el texto a buscar."
        ruta = _dentro(args.get("ruta") or base, base)
        if not ruta:
            return "Fuera de la carpeta de trabajo. Usa rutas dentro de " + base
        encontrados = []
        saltar = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
        try:
            for actual, dirs, ficheros in os.walk(ruta):
                dirs[:] = [d for d in dirs if d not in saltar and not d.startswith(".")]
                for f in ficheros:
                    if not f.lower().endswith((".py", ".js", ".json", ".txt", ".md", ".html",
                                               ".css", ".sh", ".bat", ".yml", ".yaml", ".ini",
                                               ".cfg", ".toml", ".ts", ".tsx", ".jsx", ".c", ".h")):
                        continue
                    p = os.path.join(actual, f)
                    try:
                        if os.path.getsize(p) > 2_000_000:
                            continue
                        with open(p, "r", encoding="utf-8", errors="replace") as fh:
                            for i, linea in enumerate(fh, 1):
                                if texto.lower() in linea.lower():
                                    encontrados.append(f"{os.path.relpath(p, ruta)}:{i}: {linea.strip()[:160]}")
                                    if len(encontrados) >= 60:
                                        raise StopIteration
                    except StopIteration:
                        break
                    except Exception:
                        continue
                if len(encontrados) >= 60:
                    break
        except Exception as exc:
            return f"Fallo al buscar: {exc}"
        if not encontrados:
            return f"No encontre '{texto}' dentro de {ruta}."
        return f"{len(encontrados)} coincidencias de '{texto}' en {ruta}:\n" + "\n".join(encontrados)

    if nombre == "escribir":
        if not permitir_escritura:
            return "La escritura esta desactivada: activa el modo agente con 'Archivos y comandos'."
        ruta = _dentro(args.get("ruta") or "", base)
        if not ruta:
            return "Fuera de la carpeta de trabajo. Usa rutas dentro de " + base
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(ruta, "w", encoding="utf-8") as fh:
                fh.write(args.get("contenido") or "")
        except Exception as exc:
            return f"No se pudo escribir {ruta}: {exc}"
        return f"Escrito {ruta} ({len(args.get('contenido') or '')} caracteres)."

    if nombre == "comando":
        if not permitir_escritura:
            return "Los comandos estan desactivados: activa el modo agente con 'Archivos y comandos'."
        orden = (args.get("orden") or "").strip()
        if not orden:
            return "Falta el comando."
        try:
            r = subprocess.run(orden, shell=True, cwd=base, capture_output=True, text=True,
                               timeout=120, creationflags=NO_WINDOW)
        except subprocess.TimeoutExpired:
            return "El comando tardo mas de 2 minutos y lo corte."
        except Exception as exc:
            return f"No se pudo ejecutar: {exc}"
        salida = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr else "")
        return _corta(salida.strip() or f"(sin salida, codigo {r.returncode})")

    return f"Herramienta desconocida: {nombre}"


# --------------------------------------------------------------------- el bucle


def _raiz(endpoint):
    """La base de Ollama, quitando el /v1 que usa la ruta de OpenAI."""
    base = (endpoint or "").strip().rstrip("/")
    if base.endswith("/v1"):
        base = base[:-3].rstrip("/")
    return base


_SOPORTA = {}


def soporta_tools(endpoint, model):
    """True/False/None: si Ollama dice que el modelo admite herramientas.

    None = no se pudo comprobar (Ollama antiguo). En ese caso se intenta igual
    y, si Ollama rechaza la peticion con 400, se reintenta sin herramientas: en
    Windows los errores 400 del modo agente venian de aqui.
    """
    clave = (_raiz(endpoint), model)
    if clave in _SOPORTA:
        return _SOPORTA[clave]
    valor = None
    try:
        req = urllib.request.Request(_raiz(endpoint) + "/api/show",
                                     data=json.dumps({"model": model}).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            dato = json.loads(resp.read().decode("utf-8", "replace"))
        caps = dato.get("capabilities")
        if isinstance(caps, list):
            valor = "tools" in [str(c).lower() for c in caps]
    except Exception:
        valor = None
    _SOPORTA[clave] = valor
    return valor


def _expl(exc, model):
    """Mensaje claro en castellano para el fallo HTTP de Ollama."""
    cuerpo = ""
    try:
        cuerpo = (exc.read() or b"").decode("utf-8", "replace").strip()
    except Exception:
        cuerpo = ""
    if cuerpo:
        try:
            cuerpo = (json.loads(cuerpo).get("error") or cuerpo).strip()
        except Exception:
            pass
        cuerpo = cuerpo[:300]
    cola = (" Detalle de Ollama: " + cuerpo) if cuerpo else ""
    if exc.code == 400:
        return (f"Ollama rechazo la peticion (400) para '{model}'. Suele ser una "
                "version de Ollama antigua o un modelo que no acepta herramientas."
                + cola)
    if exc.code == 404:
        return f"El modelo '{model}' no esta descargado en el proveedor local." + cola
    if exc.code >= 500:
        return (f"El proveedor local no pudo cargar '{model}' (error {exc.code}). "
                "Casi siempre es falta de memoria; baja la ventana o usa un modelo "
                "mas pequeno." + cola)
    return f"El proveedor respondio {exc.code} para '{model}'." + cola


def _pide(endpoint, cuerpo, on_delta, stop_event, timeout=900):
    """Una llamada a /api/chat en streaming. Devuelve (texto, tool_calls, uso)."""
    req = urllib.request.Request(_raiz(endpoint) + "/api/chat",
                                 data=json.dumps(cuerpo).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    texto, llamadas, uso = "", [], {}
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        for linea in resp:
            if stop_event is not None and stop_event.is_set():
                break
            linea = linea.strip()
            if not linea:
                continue
            try:
                dato = json.loads(linea.decode("utf-8", "replace"))
            except Exception:
                continue
            msg = dato.get("message") or {}
            trozo = msg.get("content") or ""
            if trozo:
                texto += trozo
                if on_delta:
                    on_delta(trozo)
            for tc in msg.get("tool_calls") or []:
                llamadas.append(tc)
            if dato.get("done"):
                uso = {"prompt_tokens": dato.get("prompt_eval_count") or 0,
                       "completion_tokens": dato.get("eval_count") or 0,
                       "total_tokens": (dato.get("prompt_eval_count") or 0) + (dato.get("eval_count") or 0),
                       "local": True}
                break
    return texto, llamadas, uso


def turno(endpoint, model, historial, workdir="", permitir_escritura=False, on_delta=None,
          stop_event=None, on_tool=None, on_notice=None, max_turnos=6, ctx=8192,
          hilos=None, segundos_max=1800, sistema=None):
    """Bucle de agente contra Ollama. Devuelve (texto, meta).

    `sistema` es el prompt de sistema del chat (Ajustes / especialista). Se
    antepone a las reglas del agente: antes se perdia y el modelo no veia el
    "sistema" que la app le pasaba.
    """
    t0 = time.time()
    propio = (sistema or "").strip()
    # Las reglas van primero y el prompt del usuario al final: lo que queda mas
    # cerca del turno del usuario pesa mas en el modelo (probado con 0.6B/1.7B,
    # al reves lo ignoraba).
    mensajes = [{"role": "system",
                 "content": "\n\n".join([SISTEMA, texto_equipo(workdir)] + ([propio] if propio else []))}]
    for m in historial or []:
        rol = m.get("role")
        if rol in ("user", "assistant") and (m.get("content") or "").strip():
            mensajes.append({"role": rol, "content": m["content"]})
    if not any(m["role"] == "user" for m in mensajes):
        mensajes.append({"role": "user", "content": "(sin consulta)"})
    # el historial puede ser enorme: con ventana de 8k nos quedamos con lo ultimo
    limite = max(4000, (ctx or 8192) * 3)          # ~3 caracteres por token
    while len(json.dumps(mensajes, ensure_ascii=False)) > limite and len(mensajes) > 2:
        mensajes.pop(1)

    cuerpo_base = {
        "model": model,
        "stream": True,
        "keep_alive": "30m",
        "tools": herramientas(permitir_escritura),
        "options": {"num_ctx": ctx or 8192,
                    "temperature": float(os.environ.get("NEXUS_AGENT_TEMP") or 0.2)},
    }
    sin_tools = False
    if soporta_tools(endpoint, model) is False:
        # el modelo no admite herramientas: mejor no pedirlas (Ollama da 400)
        sin_tools = True
        cuerpo_base["tools"] = []
    if hilos:
        cuerpo_base["options"]["num_thread"] = hilos

    texto_total, usadas, uso_total, espera_total = [], [], {"prompt_tokens": 0, "completion_tokens": 0,
                                                            "total_tokens": 0, "local": True}, 0.0
    for vuelta in range(max_turnos):
        if stop_event is not None and stop_event.is_set():
            break
        if time.time() - t0 > segundos_max:
            texto_total.append("\n\n_(me quede sin tiempo: el equipo tardo demasiado)_")
            break
        cuerpo = dict(cuerpo_base)
        cuerpo["messages"] = mensajes
        if vuelta:
            if on_notice:
                on_notice("agent_run")
        else:
            if on_notice:
                on_notice("local_agent")
        t_espera = time.time()
        try:
            texto, llamadas, uso = _pide(endpoint, cuerpo, on_delta, stop_event)
        except urllib.error.HTTPError as exc:
            if exc.code == 400 and cuerpo.get("tools"):
                # Ollama no traga las herramientas: reintentamos sin ellas
                sin_tools = True
                cuerpo_base["tools"] = []
                cuerpo["tools"] = []
                if on_notice:
                    on_notice("agent_sin_tools")
                try:
                    texto, llamadas, uso = _pide(endpoint, cuerpo, on_delta, stop_event)
                except urllib.error.HTTPError as exc2:
                    raise RuntimeError(_expl(exc2, model)) from exc2
            else:
                raise RuntimeError(_expl(exc, model)) from exc
        espera_total += time.time() - t_espera
        for k in uso_total:
            if k != "local":
                uso_total[k] += uso.get(k) or 0
        if texto.strip():
            texto_total.append(texto)
        if not llamadas:
            break
        mensajes.append({"role": "assistant", "content": texto, "tool_calls": llamadas})
        for tc in llamadas:
            fn = (tc.get("function") or {})
            nombre = fn.get("name") or "?"
            args = fn.get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args or "{}")
                except Exception:
                    args = {}
            usadas.append(nombre)
            if on_tool:
                on_tool(nombre, args or {})
            resultado = ejecutar(nombre, args or {}, workdir, permitir_escritura)
            mensajes.append({"role": "tool", "tool_name": nombre, "content": _corta(resultado)})
    texto = "\n\n".join(t for t in texto_total if t.strip()).strip()
    if sin_tools:
        texto += ("\n\n_(aviso: este modelo no admite herramientas, asi que respondio "
                  "sin poder mirar tus ficheros ni ejecutar nada)_")
    if not texto.strip():
        texto = ("(el modelo no devolvio texto: prueba con una pregunta mas corta o un "
                 "modelo mayor)")
    meta = {"usage": uso_total, "model": model, "local": True, "tools": usadas,
            "agent": True, "sin_tools": sin_tools,
            "segundos": round(time.time() - t0, 1),
            "segundos_espera": round(espera_total, 1)}
    return texto, meta
