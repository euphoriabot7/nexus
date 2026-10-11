#!/usr/bin/env python3
"""NEXUS · modelos locales (Ollama y LM Studio).

Todo con la biblioteca estandar. Se encarga de:
  · detectar si Ollama / LM Studio estan instalados y en marcha,
  · instalar Ollama (Linux, Windows, macOS),
  · descargar modelos con progreso,
  · dejar el proveedor local configurado y listo para probar.

`server.py` llama a `init(...)` con las rutas y las funciones que ya tiene,
para no repetir logica.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

IS_WIN = os.name == "nt"
IS_MAC = sys.platform == "darwin"
PLATFORM = "windows" if IS_WIN else ("macos" if IS_MAC else "linux")
EXE = ".exe" if IS_WIN else ""
OLLAMA_URL = "http://127.0.0.1:11434"
LMS_URL = "http://127.0.0.1:1234"
OLLAMA_DOWNLOAD = {"windows": "https://ollama.com/download/OllamaSetup.exe",
                   "macos": "https://ollama.com/download/Ollama-darwin.zip",
                   "linux": "https://ollama.com/install.sh"}
LMSTUDIO_DOWNLOAD = "https://lmstudio.ai/download"

CTX = {"app_dir": Path("."), "data_dir": Path("."), "config_dir": Path("."),
       "env": None, "shell": None, "config_get": None, "config_save": None}
STATE = {"running": False, "kind": "", "code": None, "started": 0.0}
PULL = {"running": False, "model": "", "backend": "ollama", "line": "", "percent": 0,
        "done": False, "error": "", "proc": None, "started": 0.0}
LOCK = threading.Lock()


def init(app_dir, data_dir, config_dir, env_builder, shell_runner, config_get, config_save):
    CTX.update(app_dir=Path(app_dir), data_dir=Path(data_dir), config_dir=Path(config_dir),
               env=env_builder, shell=shell_runner, config_get=config_get, config_save=config_save)


def _log_path():
    return Path(CTX["data_dir"]) / "local-install.log"


def _load(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def catalog():
    return _load(Path(CTX["app_dir"]) / "local_models.json", {"modelos": [], "lmstudio": []})


def http_json(url, timeout=4):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# deteccion
# --------------------------------------------------------------------------- #

def ollama_bin():
    p = shutil.which("ollama")
    if p:
        return p
    cands = []
    if IS_WIN:
        cands += [Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe",
                  Path(os.environ.get("PROGRAMFILES", "")) / "Ollama" / "ollama.exe"]
    elif IS_MAC:
        cands += [Path("/usr/local/bin/ollama"), Path("/opt/homebrew/bin/ollama"),
                  Path.home() / "Applications" / "Ollama.app" / "Contents" / "Resources" / "ollama",
                  Path("/Applications/Ollama.app/Contents/Resources/ollama")]
    else:
        cands += [Path.home() / ".local" / "bin" / "ollama", Path("/usr/local/bin/ollama"), Path("/usr/bin/ollama")]
    for c in cands:
        if str(c) and Path(c).is_file():
            return str(c)
    return ""


def ollama_version():
    b = ollama_bin()
    if not b:
        return ""
    try:
        out = subprocess.run([b, "--version"], capture_output=True, text=True, timeout=20)
        return ((out.stdout or "") + (out.stderr or "")).strip().splitlines()[0][:60]
    except Exception:
        return ""


def ollama_running():
    return http_json(OLLAMA_URL + "/api/tags") is not None


def ollama_models():
    d = http_json(OLLAMA_URL + "/api/tags") or {}
    out = []
    for m in d.get("models") or []:
        nombre = m.get("name") or m.get("model") or ""
        if not nombre:
            continue
        det = m.get("details") or {}
        out.append({"name": nombre, "size": m.get("size") or 0,
                    "params": det.get("parameter_size", ""), "family": det.get("family", ""),
                    "quant": det.get("quantization_level", "")})
    out.sort(key=lambda x: x["name"])
    return out


def lms_bin():
    p = shutil.which("lms")
    if p:
        return p
    cands = [Path.home() / ".lmstudio" / "bin" / f"lms{EXE}"]
    if IS_WIN:
        cands += [Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "lm-studio" / "resources" / "app" / ".webpack" / "lms.exe",
                  Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "LM Studio" / "resources" / "app" / ".webpack" / "lms.exe"]
    if IS_MAC:
        cands += [Path("/Applications/LM Studio.app/Contents/Resources/app/.webpack/lms")]
    for c in cands:
        if str(c) and Path(c).is_file():
            return str(c)
    return ""


def lmstudio_installed():
    if lms_bin():
        return True
    if IS_WIN:
        return (Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "lm-studio").exists()
    if IS_MAC:
        return Path("/Applications/LM Studio.app").exists()
    return (Path.home() / ".lmstudio").exists() or (Path.home() / ".cache" / "lm-studio").exists()


def lmstudio_running():
    return http_json(LMS_URL + "/v1/models") is not None


def lmstudio_models():
    out = []
    b = lms_bin()
    if b:
        try:
            r = subprocess.run([b, "ls", "--json"], capture_output=True, text=True, timeout=30)
            data = json.loads(r.stdout or "[]")
            for it in (data if isinstance(data, list) else []):
                mid = it.get("modelKey") or it.get("identifier") or it.get("path") or ""
                if mid:
                    out.append({"name": str(mid), "size": it.get("sizeBytes") or 0,
                                "params": it.get("paramsString", "")})
        except Exception:
            out = []
    if not out:
        for base in [Path.home() / ".lmstudio" / "models", Path.home() / ".cache" / "lm-studio" / "models"]:
            if base.is_dir():
                try:
                    for f in sorted(base.rglob("*.gguf"))[:300]:
                        out.append({"name": f.parent.name, "size": f.stat().st_size, "params": f.name})
                except Exception:
                    pass
    return out[:300]


def models_dir():
    """Carpeta donde Ollama guarda los modelos."""
    base = Path(os.environ.get("OLLAMA_MODELS") or (Path.home() / ".ollama" / "models"))
    return str(base)


def status():
    cat = catalog()
    instalados = {m["name"]: m for m in ollama_models()}
    modelos = []
    for m in cat.get("modelos", []):
        mm = dict(m)
        mm["instalado"] = bool(instalados.get(m["id"]))
        mm["tamano_disco"] = instalados.get(m["id"], {}).get("size", 0)
        modelos.append(mm)
    return {
        "platform": PLATFORM,
        "ollama_bin": ollama_bin(), "ollama_version": ollama_version(),
        "ollama_running": ollama_running(), "ollama_instalados": ollama_models(),
        "lms_bin": lms_bin(), "lmstudio_instalado": lmstudio_installed(),
        "lmstudio_running": lmstudio_running(), "lmstudio_modelos": lmstudio_models(),
        "catalogo": modelos, "lmstudio_catalogo": cat.get("lmstudio", []),
        "nota": cat.get("nota", ""), "revisado": cat.get("revisado", ""),
        "instalando": STATE["running"], "instalacion": STATE["kind"],
        "pull": {k: v for k, v in PULL.items() if k != "proc"},
        "descargas": {"ollama": OLLAMA_DOWNLOAD[PLATFORM], "lmstudio": LMSTUDIO_DOWNLOAD},
        "espacio_libre": _free_gb(),
        "carpeta_modelos": models_dir(),
        "ram_libre": ram_gb()[0], "ram_total": ram_gb()[1],
        "agente": {"contexto_sugerido": agent_context_goal("")[0] if False else None,
                   "aviso": agent_context_goal("")[1] if False else ""},
    }


def ram_gb():
    """(libre, total) en GB, o (None, None) si no se puede saber."""
    try:
        if not IS_WIN and Path("/proc/meminfo").is_file():
            datos = {}
            for linea in Path("/proc/meminfo").read_text().splitlines():
                campos = linea.split()
                if len(campos) >= 2:
                    datos[campos[0].rstrip(":")] = int(campos[1])
            return round(datos.get("MemAvailable", 0) / 1024 ** 2, 1), round(datos.get("MemTotal", 0) / 1024 ** 2, 1)
        pagina = os.sysconf("SC_PAGE_SIZE")
        total = os.sysconf("SC_PHYS_PAGES") * pagina / 1024 ** 3
        try:
            libre = os.sysconf("SC_AVPHYS_PAGES") * pagina / 1024 ** 3
        except (ValueError, OSError):
            libre = total * 0.5
        return round(libre, 1), round(total, 1)
    except Exception:
        return None, None


def _free_gb():
    try:
        p = Path(CTX["data_dir"])
        p.mkdir(parents=True, exist_ok=True)
        return round(shutil.disk_usage(str(p)).free / 1024 ** 3, 1)
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# instalar Ollama
# --------------------------------------------------------------------------- #

def _run_install(cmd, shell_env):
    trabajo = Path(CTX["data_dir"])
    trabajo.mkdir(parents=True, exist_ok=True)
    with open(_log_path(), "w", encoding="utf-8") as fh:
        fh.write(" ".join(cmd) + "\n\n")
    log = open(_log_path(), "a", encoding="utf-8")  # noqa: SIM115
    try:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=shell_env,
                                cwd=str(Path.home()))
    except Exception as exc:  # noqa: BLE001
        return None, f"No se pudo lanzar la instalacion: {exc}"
    STATE.update(running=True, code=None, started=time.time())

    def _wait():
        code = proc.wait()
        STATE.update(running=False, code=code)
        with open(_log_path(), "a", encoding="utf-8") as fh:
            fh.write(f"\n[fin] codigo {code}\n")
        log.close()
    threading.Thread(target=_wait, daemon=True).start()
    return proc, ""


def install(backend="ollama"):
    """Instala Ollama. Devuelve (ok, mensaje)."""
    if backend != "ollama":
        return False, "LM Studio se descarga desde su web (se abre en el navegador)."
    if STATE["running"]:
        return False, "Ya hay una instalacion en marcha."
    if ollama_bin():
        return False, "Ollama ya esta instalado."
    env = CTX["env"]() if CTX["env"] else dict(os.environ)

    if PLATFORM == "windows":
        destino = Path(os.environ.get("TEMP", ".")) / "OllamaSetup.exe"
        try:
            url = OLLAMA_DOWNLOAD["windows"]
            with urllib.request.urlopen(url, timeout=600) as r, open(destino, "wb") as fh:
                shutil.copyfileobj(r, fh)
        except Exception as exc:  # noqa: BLE001
            return False, f"No se pudo descargar el instalador: {exc}"
        _run_install([str(destino), "/SILENT"], env)
        return True, ("Instalador descargado y lanzado. Si aparece una ventana, pulsa Instalar; "
                      "cuando termine, vuelve aqui y pulsa Actualizar.")

    if PLATFORM == "macos":
        destino = Path.home() / "Downloads" / "Ollama-darwin.zip"
        try:
            with urllib.request.urlopen(OLLAMA_DOWNLOAD["macos"], timeout=900) as r, open(destino, "wb") as fh:
                shutil.copyfileobj(r, fh)
        except Exception as exc:  # noqa: BLE001
            return False, f"No se pudo descargar Ollama: {exc}"
        _run_install(["/usr/bin/unzip", "-o", str(destino), "-d", str(Path.home() / "Applications")], env)
        webbrowser.open("file://" + str(Path.home() / "Applications" / "Ollama.app"))
        return True, "Descargado. Arrastra Ollama a Aplicaciones y abrelo una vez."

    # Linux: script oficial. Necesita root para /usr/local/bin y el servicio systemd.
    if not shutil.which("curl"):
        return False, "Hace falta curl para instalar Ollama."
    script = "curl -fsSL https://ollama.com/install.sh | sh"
    puede_sudo = subprocess.run(["/usr/bin/sudo", "-n", "true"], capture_output=True).returncode == 0 \
        if Path("/usr/bin/sudo").exists() else False
    if puede_sudo:
        _run_install(["/bin/bash", "-lc", f"sudo {script}"], env)
        return True, "Instalando Ollama con permisos de administrador (mira el registro)."
    if shutil.which("pkexec"):
        entorno = dict(env)
        entorno.setdefault("DISPLAY", os.environ.get("DISPLAY", ":0.0"))
        _run_install(["pkexec", "/bin/bash", "-c", script], entorno)
        return True, ("Instalando Ollama: se abrira una ventana pidiendo tu contrasena "
                      "(la de administrador del sistema).")
    return False, ("No puedo instalar con permisos. Abre una terminal y pega:\n"
                   "curl -fsSL https://ollama.com/install.sh | sh")


def install_log(limit=4000):
    try:
        texto = _log_path().read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    return texto[-limit:]


def start_backend(backend="ollama"):
    """Arranca Ollama si esta instalado pero parado."""
    if backend != "ollama":
        b = lms_bin()
        if not b:
            return False, "LM Studio no esta instalado."
        try:
            subprocess.Popen([b, "server", "start"], env=CTX["env"]() if CTX["env"] else None)
            return True, "Arrancando el servidor de LM Studio..."
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)
    b = ollama_bin()
    if not b:
        return False, "Ollama no esta instalado."
    if ollama_running():
        return True, "Ollama ya estaba en marcha."
    env = CTX["env"]() if CTX["env"] else dict(os.environ)
    try:
        if IS_WIN:
            app = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama app.exe"
            exe = str(app) if app.is_file() else b
            subprocess.Popen([exe], env=env, creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
        else:
            subprocess.Popen([b, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             env=env, start_new_session=True)
    except Exception as exc:  # noqa: BLE001
        return False, f"No se pudo arrancar Ollama: {exc}"
    for _ in range(40):
        if ollama_running():
            return True, "Ollama arrancado."
        time.sleep(0.5)
    return False, "Ollama no responde en el puerto 11434. Abrelo a mano una vez."


# --------------------------------------------------------------------------- #
# descargar y borrar modelos
# --------------------------------------------------------------------------- #

def _percent(linea):
    import re
    m = re.search(r"(\d{1,3})%", linea)
    return int(m.group(1)) if m else None


def model_context(model):
    """Ventana de contexto que anuncia el modelo (0 si no se puede saber)."""
    b = ollama_bin()
    if not b:
        return 0
    try:
        r = subprocess.run([b, "show", model], capture_output=True, text=True, timeout=45,
                           env=(CTX["env"]() if CTX["env"] else None))
        import re as _re
        m = _re.search(r"(?i)context length\s+([\d.,]+)", r.stdout or "")
        if m:
            return int(m.group(1).replace(".", "").replace(",", ""))
    except Exception:
        pass
    return 0


def agent_context_goal(model, min_ctx=64000):
    """Ventana que se le va a pedir al modelo para el agente, con el por que.

    Hermes exige >= 64k para el modo agente. Ollama reserva memoria para esa
    ventana (KV cache): en un equipo de 7 GB, 40k se come la RAM entera. Por eso
    se limita a lo que quepa segun la memoria libre, sin pasar del maximo del
    modelo. Devuelve (contexto, motivo)."""
    libre, _total = ram_gb()
    techo = min_ctx
    motivo = "ventana completa"
    if libre is not None:
        if libre < 3.5:
            techo, motivo = 24576, "memoria libre baja: ventana reducida a 24k"
        elif libre < 5.5:
            techo, motivo = 32768, "memoria libre justa: ventana reducida a 32k"
    propio = model_context(model)
    if propio and propio < techo:
        techo, motivo = propio, f"el modelo admite {propio} como maximo"
    return int(techo), motivo


def agent_variant(model, min_ctx=64000):
    """Modelo que hay que usar para el modo agente (crea la variante si hace falta).

    Ollama ignora el `num_ctx` que Hermes manda por la API compatible con OpenAI
    (carga el modelo con 4096), asi que la ventana se fija en un Modelfile. Las
    variantes reutilizan los blobs del modelo base: no ocupan disco extra real."""
    b = ollama_bin()
    if not b:
        return model, "Ollama no esta instalado", 0
    objetivo, motivo = agent_context_goal(model, min_ctx)
    ctx_modelo = model_context(model)
    if ctx_modelo and ctx_modelo >= min_ctx and objetivo >= min_ctx:
        return model, f"{model}: {ctx_modelo} de contexto, vale para agente tal cual", ctx_modelo
    variante = f"{model}-agente-{objetivo // 1024}k"
    if variante.endswith("-agente") or variante == model:
        variante = f"{model}-agente"
    instalados = {m["name"] for m in ollama_models()}
    if variante in instalados:
        return variante, f"reutilizo la variante {variante}", objetivo
    trabajo = Path(CTX["data_dir"]) / "modelfiles"
    trabajo.mkdir(parents=True, exist_ok=True)
    archivo = trabajo / (variante.replace("/", "_").replace(":", "_") + ".Modelfile")
    archivo.write_text(f"FROM {model}\nPARAMETER num_ctx {objetivo}\nPARAMETER temperature 0.7\n", encoding="utf-8")
    try:
        r = subprocess.run([b, "create", variante, "-f", str(archivo)], capture_output=True, text=True,
                           timeout=600, env=(CTX["env"]() if CTX["env"] else None))
        if r.returncode != 0:
            return model, f"no se pudo crear la variante: {(r.stderr or r.stdout or '')[:200]}", 0
    except Exception as exc:  # noqa: BLE001
        return model, f"no se pudo crear la variante: {exc}", 0
    return variante, f"variante {variante} lista para el agente ({motivo})", objetivo


def pull(model, backend="ollama"):
    if PULL["running"]:
        return False, "Ya hay una descarga en marcha."
    if backend == "lmstudio":
        b = lms_bin()
        if not b:
            return False, "LM Studio no esta instalado (o falta el comando lms)."
        cmd = [b, "get", model, "--yes"]
    else:
        b = ollama_bin()
        if not b:
            return False, "Ollama no esta instalado."
        if not ollama_running():
            ok, msg = start_backend("ollama")
            if not ok:
                return False, msg
        cmd = [b, "pull", model]
    with LOCK:
        PULL.update(running=True, model=model, backend=backend, line="descargando...", percent=0,
                    done=False, error="", started=time.time(), proc=None, _ultimo=time.time())
    env = CTX["env"]() if CTX["env"] else dict(os.environ)

    def _run():
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                    bufsize=1, env=env)
            PULL["proc"] = proc
            # vigilante: si la descarga deja de dar senales, se corta y se avisa en vez de quedarse colgada.
            # Ojo: NO vale mirar la linea, porque el hilillo giratorio ("pulling manifest") cambia
            # cada tick y pareceria que avanza. Solo cuenta el porcentaje real subiendo.
            def _vigila():
                visto = -1
                while PULL["running"] and not PULL["done"]:
                    time.sleep(5)
                    pct = PULL.get("percent") or 0
                    linea = (PULL.get("line") or "").lower()
                    avanza = pct > visto or any(x in linea for x in ("success", "verifying", "writing manifest"))
                    if avanza:
                        visto = max(visto, pct)
                        PULL["_ultimo"] = time.time()
                    elif time.time() - PULL.get("_ultimo", time.time()) > 150:
                        try:
                            proc.kill()
                        except Exception:  # noqa: BLE001
                            pass
                        PULL.update(done=True, running=False,
                                    error="la descarga se ha quedado parada: el servidor de modelos no responde "
                                          "o tu conexion ha fallado. Comprueba la red y vuelve a intentarlo.")
                        return
            threading.Thread(target=_vigila, daemon=True).start()

            for linea in proc.stdout or []:
                linea = linea.rstrip()
                if not linea:
                    continue
                PULL["line"] = linea[:200]
                p = _percent(linea)
                if p is not None:
                    PULL["percent"] = p
            code = proc.wait()
            if code == 0:
                PULL.update(done=True, percent=100, line="descarga completada", running=False)
            else:
                # si el vigilante ya explico el motivo, no se pisa con el codigo a secas
                if not PULL.get("error"):
                    PULL.update(error=f"la descarga termino con codigo {code}")
                PULL.update(done=True, running=False)
        except Exception as exc:  # noqa: BLE001
            PULL.update(done=True, running=False, error=str(exc))
    threading.Thread(target=_run, daemon=True).start()
    return True, "Descarga iniciada."


def cancel_pull():
    proc = PULL.get("proc")
    if proc and PULL["running"]:
        try:
            proc.terminate()
            PULL.update(running=False, done=True, error="cancelado")
            return True, "Descarga cancelada."
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)
    return False, "No hay ninguna descarga en marcha."


def remove(model, backend="ollama"):
    if backend == "lmstudio":
        b = lms_bin()
        if not b:
            return False, "LM Studio no esta instalado."
        # descargarlo de memoria antes de borrarlo
        try:
            subprocess.run([b, "unload", model], capture_output=True, text=True, timeout=30,
                           env=(CTX["env"]() if CTX["env"] else None))
        except Exception:  # noqa: BLE001
            pass
        cmd = [b, "rm", model]
    else:
        b = ollama_bin()
        if not b:
            return False, "Ollama no esta instalado."
        # Si el modelo esta cargado en memoria, Ollama puede quedarse colgado ("Stopping...")
        # al borrarlo: primero se descarga y se le da un momento para soltarlo.
        try:
            subprocess.run([b, "stop", model], capture_output=True, text=True, timeout=45,
                           env=(CTX["env"]() if CTX["env"] else None))
            time.sleep(1.5)
        except Exception:  # noqa: BLE001
            pass
        cmd = [b, "rm", model]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=90,
                           env=(CTX["env"]() if CTX["env"] else None))
        if r.returncode == 0:
            return True, "Modelo borrado."
        return False, (r.stderr or r.stdout or "no se pudo borrar").strip()[:300]
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def use(model, backend="ollama"):
    """Deja el proveedor local configurado con ese modelo y como predeterminado."""
    pid = "lmstudio" if backend == "lmstudio" else "ollama"
    base = (LMS_URL + "/v1") if pid == "lmstudio" else (OLLAMA_URL + "/v1")
    etiqueta = "LM Studio (local, sin clave)" if pid == "lmstudio" else "Ollama (local, sin clave)"
    cfg = CTX["config_get"]()
    provs = cfg.setdefault("providers", {})
    spec = dict(provs.get(pid) or {})
    modelos = [m for m in (spec.get("models") or []) if m != model]
    spec.update({"id": pid, "label": etiqueta, "base_url": base, "requires_key": False,
                 "models": [model] + modelos, "local": True})
    spec.setdefault("api_key", "local")
    provs[pid] = spec
    cfg["default"] = {"provider": pid, "model": model}
    CTX["config_save"](cfg)
    return {"ok": True, "provider": pid, "model": model}


# --------------------------------------------------------------------------- #
# abrir cosas en el escritorio
# --------------------------------------------------------------------------- #

def open_target(que):
    urls = {"ollama_download": OLLAMA_DOWNLOAD[PLATFORM],
            "lmstudio_download": LMSTUDIO_DOWNLOAD,
            "ollama_docs": "https://ollama.com/download",
            "lmstudio_docs": "https://lmstudio.ai/docs/cli"}
    if que in urls:
        try:
            webbrowser.open(urls[que])
            return True, f"Abriendo {urls[que]}"
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)
    if que == "modelos":
        carpeta = Path.home() / ".ollama" / "models"
        if IS_WIN:
            subprocess.Popen(["explorer", str(carpeta)], shell=True)
        elif IS_MAC:
            subprocess.Popen(["open", str(carpeta)])
        else:
            subprocess.Popen(["xdg-open", str(carpeta)])
        return True, f"Abriendo {carpeta}"
    return False, "no se que abrir"
