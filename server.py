#!/usr/bin/env python3
"""
NEXUS - backend de chat local.

Servidor HTTP sin dependencias externas (solo stdlib) que:
  - guarda chats y mensajes en SQLite (~/.local/share/ocdesk/nexus.db)
  - modo "chat": reenvia al proveedor (OpenCode Go / OpenRouter) con streaming
  - modo "agente": ejecuta `hermes chat -q --format stream-json` (herramientas
    reales + continuidad por sesion de Hermes)
  - sirve la interfaz web en http://127.0.0.1:8765

Las claves y los proveedores viven en ~/.config/nexus/config.json (se configuran desde
  la propia app, pestana Ajustes -> Proveedores y claves). Opcionalmente tambien se leen
  variables de entorno *_API_KEY, y ~/.hermes/.env si existe. El catalogo de ejemplos
  esta en providers.json.
"""

import base64
import hmac
import json
import os
import re
import shutil
import socket
import sqlite3
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "app"
def _data_dir():
    """~/.local/share/nexus; si ya existia la carpeta antigua (ocdesk), se respeta."""
    env = os.environ.get("NEXUS_DATA")
    if env:
        return Path(env)
    nuevo = Path.home() / ".local" / "share" / "nexus"
    viejo = Path.home() / ".local" / "share" / "ocdesk"
    return viejo if (viejo.exists() and not nuevo.exists()) else nuevo


DATA_DIR = _data_dir()
DB_PATH = DATA_DIR / "nexus.db"
HERMES_ENV = Path.home() / ".hermes" / ".env"          # solo como atajo opcional
HERMES_PROVIDER_CACHE = Path.home() / ".hermes" / "provider_models_cache.json"
CONFIG_DIR = Path(os.environ.get("NEXUS_CONFIG_DIR", str(Path.home() / ".config" / "nexus")))
CONFIG_PATH = CONFIG_DIR / "config.json"
MODELS_CACHE = CONFIG_DIR / "models_cache.json"
HOST = "127.0.0.1"
PORT = int(os.environ.get("NEXUS_PORT", "8765"))
USER_AGENT = "nexus-desktop/1.0"
MAX_ATTACH_TEXT = 200_000          # bytes de texto por adjunto
MAX_ATTACH_TOTAL = 12_000_000      # bytes en base64 por peticion
STOP_FLAGS = {}                    # chat_id -> threading.Event
DEFAULT_WORKDIR = str(Path.home())
LAN_FILE = DATA_DIR / "lan.json"
LAN_ENABLED = os.environ.get("NEXUS_LAN", "1") != "0"   # accesible por LAN (con token)
ALLOWED_ROOTS = [Path.home(), Path("/tmp"), Path("/var/tmp")]

MIME_EXTRA = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
    ".webp": "image/webp", ".bmp": "image/bmp", ".avif": "image/avif", ".ico": "image/x-icon",
    ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf", ".otf": "font/otf",
    ".mp4": "video/mp4", ".webm": "video/webm", ".mp3": "audio/mpeg", ".wav": "audio/wav",
    ".pdf": "application/pdf", ".txt": "text/plain; charset=utf-8", ".md": "text/plain; charset=utf-8",
    ".csv": "text/csv; charset=utf-8", ".xml": "application/xml", ".map": "application/json",
    ".webmanifest": "application/manifest+json", ".manifest": "application/manifest+json",
}


def lan_config():
    cfg = load_json(LAN_FILE, {})
    if not cfg.get("token"):
        cfg["token"] = uuid.uuid4().hex + uuid.uuid4().hex[:8]
        try:
            LAN_FILE.write_text(json.dumps(cfg))
        except Exception:
            pass
    return cfg


def lan_addresses():
    ips = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except Exception:
        pass
    for probe in ("8.8.8.8", "1.1.1.1"):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((probe, 80))
            ip = s.getsockname()[0]
            s.close()
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
            break
        except Exception:
            continue
    return ips


def hermes_bin():
    return shutil.which("hermes") or str(Path.home() / ".local/bin/hermes")


def agent_env():
    env = dict(os.environ)
    extra = [str(Path.home() / ".local/bin"), "/usr/local/bin", "/usr/bin", "/bin"]
    env["PATH"] = os.pathsep.join(extra + [env.get("PATH", "")])
    return env


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default


CATALOG = load_json(APP_DIR / "providers.json", {}) or {}
CATALOG_PROVIDERS = CATALOG.get("providers", {}) or {}


# --------------------------------------------------------------------------- #
# configuracion del usuario (~/.config/nexus/config.json)
# --------------------------------------------------------------------------- #


def user_config():
    cfg = load_json(CONFIG_PATH, {})
    if not isinstance(cfg, dict):
        cfg = {}
    cfg.setdefault("providers", {})
    cfg.setdefault("default", {})
    return cfg


def save_user_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)          # lleva claves
    except Exception:
        pass
    tmp.replace(CONFIG_PATH)


def read_env_file(path=HERMES_ENV):
    env = {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                val = re.split(r"\s+#", val, maxsplit=1)[0]
                env[key.strip()] = val.strip().strip('"').strip("'")
    except Exception:
        pass
    return env


def env_keys():
    """Variables de entorno *_API_KEY, y ~/.hermes/.env como atajo si existe."""
    env = dict(read_env_file(HERMES_ENV))
    env.update({k: v for k, v in os.environ.items() if k.endswith("_API_KEY") or k.endswith("_BASE_URL")})
    return env


def provider_ids():
    ids = list(user_config()["providers"].keys())
    for pid in CATALOG_PROVIDERS:
        if pid not in ids:
            ids.append(pid)
    return ids


def provider_spec(pid):
    """Fusiona el catalogo de ejemplo con lo que el usuario haya configurado."""
    base = dict(CATALOG_PROVIDERS.get(pid, {}))
    mine = dict(user_config()["providers"].get(pid, {}))
    spec = dict(base)
    for k, v in mine.items():
        if k in ("models",):
            continue
        if v not in (None, ""):
            spec[k] = v
    spec["id"] = pid
    spec["label"] = mine.get("label") or base.get("label") or pid
    spec["base_url"] = (mine.get("base_url") or base.get("base_url") or "").rstrip("/")
    spec["models"] = list(mine.get("models") or base.get("models") or [])
    spec["custom"] = pid not in CATALOG_PROVIDERS
    spec["in_catalog"] = pid in CATALOG_PROVIDERS
    return spec


def api_key_for(spec):
    """Clave del proveedor: la del spec (config del usuario) o la variable de entorno."""
    key = (spec.get("api_key") or "").strip()
    if key:
        return key
    if spec.get("key_env"):
        return (env_keys().get(spec["key_env"]) or "").strip()
    return ""


def provider_credentials(spec):
    env = env_keys()
    base = env.get(spec.get("base_url_env", ""), "") or spec.get("base_url", "")
    return base.rstrip("/"), api_key_for(spec)


def provider_headers(spec, key, stream=False):
    headers = {"Content-Type": "application/json", "User-Agent": USER_AGENT}
    if stream:
        headers["Accept"] = "text/event-stream"
    if key:
        headers["Authorization"] = "Bearer " + key
    if spec.get("session_header"):
        headers[spec["session_header"]] = spec.get("session_prefix", "sess-") + str(spec.get("session_value") or "")
    return headers


def provider_usable(spec):
    """Un proveedor sirve si no necesita clave (local) o si tiene alguna."""
    if spec.get("requires_key") is False:
        return True
    return bool(api_key_for(spec))


def merged_models(pid, spec=None, refresh=False):
    spec = spec or provider_spec(pid)
    models = list(spec.get("models") or [])
    if not refresh:
        cached = load_json(MODELS_CACHE, {})
        got = cached.get(pid)
        if isinstance(got, dict):
            models = _merge(models, got.get("models") or [])
        legacy = load_json(HERMES_PROVIDER_CACHE, {})
        old = legacy.get(pid)
        if isinstance(old, dict) and old.get("models"):
            models = _merge(models, old["models"])
    return models


def _merge(a, b):
    seen, out = set(), []
    for m in list(a) + list(b):
        if isinstance(m, str) and m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


def fetch_models(pid):
    """Pide la lista al proveedor (GET /models) y la guarda en cache."""
    return fetch_models_spec(provider_spec(pid))


def spec_with_inline(pid, inline=None):
    """Spec del proveedor, permitiendo sobrescribir campos sin guardarlos (asistente)."""
    spec = provider_spec(pid)
    if isinstance(inline, dict):
        for k in ("label", "base_url", "api_key", "key_env", "session_header", "session_prefix", "docs"):
            if inline.get(k):
                spec[k] = str(inline[k]).strip()
        if spec.get("base_url"):
            spec["base_url"] = spec["base_url"].rstrip("/")
        if "requires_key" in inline:
            spec["requires_key"] = bool(inline["requires_key"])
    return spec


def fetch_models_spec(spec):
    base, key = provider_credentials(spec)
    if not base:
        raise RuntimeError("Este proveedor no tiene URL configurada.")
    if spec.get("requires_key") is not False and not key:
        raise RuntimeError("Falta la clave de API.")
    req = urllib.request.Request(base + "/models", headers=provider_headers(spec, key))
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8", "replace"))
    items = data.get("data") if isinstance(data, dict) else None
    if not isinstance(items, list):
        items = data.get("models") if isinstance(data, dict) else []
    ids = []
    for it in items or []:
        mid = it.get("id") if isinstance(it, dict) else (it if isinstance(it, str) else "")
        if mid:
            ids.append(str(mid))
    ids.sort()
    if ids:
        cache = load_json(MODELS_CACHE, {})
        if not isinstance(cache, dict):
            cache = {}
        cache[spec["id"]] = {"models": ids, "at": time.time()}
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            MODELS_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
    return ids


NO_CHAT = re.compile(r"embed|rerank|whisper|tts|audio|image-|dall|moderation|guard|vision-encoder|ocr", re.I)


def pick_chat_model(ids):
    """Primer modelo que parezca de conversacion (evita embeddings, imagen, audio...)."""
    for mid in ids:
        if not NO_CHAT.search(mid):
            return mid
    return ids[0] if ids else ""


def test_provider(pid, model="", inline=None):
    """Comprobacion real: lista de modelos y, si se puede, una respuesta minima."""
    out = {"ok": False, "models": 0, "reply": "", "error": ""}
    spec0 = spec_with_inline(pid, inline)
    try:
        ids = fetch_models_spec(spec0)
        out["models"] = len(ids)
        if not model:
            por_defecto = user_config().get("default") or {}
            if por_defecto.get("provider") == pid and por_defecto.get("model"):
                model = por_defecto["model"]
        if not model:
            model = spec0.get("default_model", "") or pick_chat_model(ids)
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"No se pudo listar modelos: {exc}"
        if not model:
            return out
    if not model:
        out["error"] = out["error"] or "El proveedor no devolvio ningun modelo; escribe uno a mano."
        return out
    spec = spec0
    base, key = provider_credentials(spec)
    payload = {"model": model, "messages": [{"role": "user", "content": "Responde solo: ok"}], "max_tokens": 16}
    try:
        req = urllib.request.Request(base + "/chat/completions", data=json.dumps(payload).encode(),
                                     headers=provider_headers(spec, key, stream=False), method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        out["reply"] = ((data.get("choices") or [{}])[0].get("message") or {}).get("content", "")[:120]
        out["ok"] = True
        out["model"] = model
    except urllib.error.HTTPError as exc:
        detalle = exc.read().decode("utf-8", "replace")[:300] if hasattr(exc, "read") else ""
        out["error"] = f"HTTP {exc.code}. {detalle}"
    except Exception as exc:  # noqa: BLE001
        out["error"] = str(exc)
    return out


def needs_setup():
    """True si no hay ningun proveedor listo para usar."""
    cfg = user_config()
    for pid in provider_ids():
        spec = provider_spec(pid)
        if spec.get("base_url") and provider_usable(spec):
            # un proveedor solo cuenta si ademas tiene algun modelo conocido
            if merged_models(pid, spec) or cfg["default"].get("provider") == pid:
                return False
    return True


def provider_index():
    out = {}
    for pid in provider_ids():
        spec = provider_spec(pid)
        out[pid] = {"id": pid, "label": spec.get("label", pid), "models": merged_models(pid, spec),
                    "key_env": spec.get("key_env", ""), "base_url": spec.get("base_url", ""),
                    "has_key": bool(api_key_for(spec)),
                    "requires_key": spec.get("requires_key", True) is not False,
                    "custom": bool(spec.get("custom")), "docs": spec.get("docs", "")}
    return out


# --------------------------------------------------------------------------- #
# modo agente: Hermes es opcional
# --------------------------------------------------------------------------- #

HERMES_INSTALL = "curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash"
HERMES_DOCS = "https://hermes-agent.nousresearch.com/docs/getting-started/installation"
INSTALL_LOG = DATA_DIR / "hermes-install.log"
INSTALL_STATE = {"running": False, "code": None, "started": 0.0}


def hermes_installed():
    binario = shutil.which("hermes") or str(Path.home() / ".local/bin/hermes")
    return bool(shutil.which("hermes") or Path(binario).is_file())


def hermes_status():
    return {"installed": hermes_installed(), "command": HERMES_INSTALL, "docs": HERMES_DOCS,
            "running": INSTALL_STATE["running"], "exit_code": INSTALL_STATE["code"],
            "log": str(INSTALL_LOG)}


def start_hermes_install():
    """Lanza el instalador oficial de Hermes en segundo plano, dejando el log en disco."""
    if INSTALL_STATE["running"]:
        return False, "Ya hay una instalacion en marcha."
    if hermes_installed():
        return False, "Hermes ya esta instalado."
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(INSTALL_LOG, "w", encoding="utf-8") as fh:
            fh.write(f"$ {HERMES_INSTALL}\n\n")
        log = open(INSTALL_LOG, "a", encoding="utf-8")  # noqa: SIM115
        proc = subprocess.Popen(["/bin/bash", "-lc", HERMES_INSTALL], stdout=log, stderr=subprocess.STDOUT,
                                env=agent_env(), cwd=str(Path.home()))
    except Exception as exc:  # noqa: BLE001
        return False, f"No se pudo lanzar el instalador: {exc}"

    INSTALL_STATE.update({"running": True, "code": None, "started": time.time()})

    def _wait():
        code = proc.wait()
        INSTALL_STATE.update({"running": False, "code": code})
        try:
            log.close()
        except Exception:
            pass

    threading.Thread(target=_wait, daemon=True).start()
    return True, "Instalando Hermes en segundo plano."


def install_log_tail(n=200):
    try:
        lineas = INSTALL_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        lineas = []
    return "\n".join(lineas[-n:])


# --------------------------------------------------------------------------- #
# base de datos
# --------------------------------------------------------------------------- #


def db():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_column(conn, table, col, decl):
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
    if col not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT 'Nuevo chat',
                provider TEXT NOT NULL DEFAULT '',
                model TEXT NOT NULL DEFAULT '',
                system TEXT NOT NULL DEFAULT '',
                pinned INTEGER NOT NULL DEFAULT 0,
                created REAL NOT NULL,
                updated REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                provider TEXT NOT NULL DEFAULT '',
                model TEXT NOT NULL DEFAULT '',
                meta TEXT NOT NULL DEFAULT '{}',
                created REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_msg_chat ON messages(chat_id, created);
            CREATE TABLE IF NOT EXISTS presets (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                created REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                kind TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '',
                chat_id TEXT NOT NULL DEFAULT '',
                model TEXT NOT NULL DEFAULT '',
                tokens INTEGER NOT NULL DEFAULT 0,
                cost REAL NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                prompt TEXT NOT NULL,
                workdir TEXT NOT NULL DEFAULT '',
                provider TEXT NOT NULL DEFAULT '',
                model TEXT NOT NULL DEFAULT '',
                toolsets TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'queued',
                created REAL NOT NULL,
                started REAL,
                finished REAL,
                exit_code INTEGER,
                output TEXT NOT NULL DEFAULT '',
                error TEXT NOT NULL DEFAULT '',
                tokens INTEGER NOT NULL DEFAULT 0,
                cost REAL NOT NULL DEFAULT 0
            );
            """
        )
        for col, decl in (("agent", "INTEGER NOT NULL DEFAULT 0"),
                          ("workdir", "TEXT NOT NULL DEFAULT ''"),
                          ("agent_session", "TEXT NOT NULL DEFAULT ''"),
                          ("toolsets", "TEXT NOT NULL DEFAULT ''")):
            ensure_column(conn, "chats", col, decl)


def now():
    return time.time()


def uid(prefix=""):
    return (prefix + uuid.uuid4().hex)[:40]


def chat_row_to_dict(row, preview=None):
    return {
        "id": row["id"], "title": row["title"], "provider": row["provider"],
        "model": row["model"], "system": row["system"], "pinned": row["pinned"],
        "created": row["created"], "updated": row["updated"],
        "agent": row["agent"], "workdir": row["workdir"],
        "agent_session": row["agent_session"], "toolsets": row["toolsets"],
        "preview": preview or "",
    }


def list_chats():
    with db() as conn:
        rows = conn.execute("SELECT * FROM chats ORDER BY pinned DESC, updated DESC").fetchall()
        out = []
        for r in rows:
            last = conn.execute(
                "SELECT content FROM messages WHERE chat_id=? AND role='user' ORDER BY created DESC LIMIT 1",
                (r["id"],)).fetchone()
            prev = (last["content"] if last else "").strip().replace("\n", " ")
            out.append(chat_row_to_dict(r, prev[:120]))
        return out


def get_chat(chat_id):
    with db() as conn:
        r = conn.execute("SELECT * FROM chats WHERE id=?", (chat_id,)).fetchone()
        return chat_row_to_dict(r) if r else None


def default_provider_model():
    """Proveedor y modelo por defecto: config del usuario, o el primero que sirva."""
    cfg = user_config().get("default") or {}
    pid, model = cfg.get("provider", ""), cfg.get("model", "")
    if pid and provider_spec(pid).get("base_url"):
        return pid, model
    for cand in provider_ids():
        spec = provider_spec(cand)
        if not spec.get("base_url") or not provider_usable(spec):
            continue
        models = merged_models(cand, spec)
        if models:                      # sin modelos conocidos no se puede chatear
            return cand, (model or models[0])
    return "", model


def create_chat(title=None, provider=None, model=None, agent=0, workdir="", toolsets=""):
    pid, mdl = default_provider_model()
    provider = provider or pid
    model = model or mdl
    cid = uid("c_")
    ts = now()
    with db() as conn:
        conn.execute(
            "INSERT INTO chats(id,title,provider,model,system,pinned,created,updated,agent,workdir,agent_session,toolsets)"
            " VALUES(?,?,?,?,?,0,?,?,?,?,?,?)",
            (cid, title or "Nuevo chat", provider, model, "", ts, ts, int(agent), workdir, "", toolsets),
        )
    return get_chat(cid)


def touch_chat(chat_id, **fields):
    sets, vals = [], []
    for k, v in fields.items():
        if v is not None:
            sets.append(f"{k}=?")
            vals.append(v)
    if not sets:
        return
    sets.append("updated=?")
    vals.append(now())
    vals.append(chat_id)
    with db() as conn:
        conn.execute(f"UPDATE chats SET {', '.join(sets)} WHERE id=?", vals)


def add_message(chat_id, role, content, provider="", model="", meta=None):
    mid = uid("m_")
    with db() as conn:
        conn.execute(
            "INSERT INTO messages(id,chat_id,role,content,provider,model,meta,created) VALUES(?,?,?,?,?,?,?,?)",
            (mid, chat_id, role, content, provider, model, json.dumps(meta or {}), now()))
    return mid


def update_message(mid, content, meta=None):
    with db() as conn:
        if meta is None:
            conn.execute("UPDATE messages SET content=? WHERE id=?", (content, mid))
        else:
            conn.execute("UPDATE messages SET content=?, meta=? WHERE id=?",
                         (content, json.dumps(meta), mid))


def get_messages(chat_id):
    with db() as conn:
        rows = conn.execute("SELECT * FROM messages WHERE chat_id=? ORDER BY created ASC", (chat_id,)).fetchall()
    out = []
    for r in rows:
        try:
            meta = json.loads(r["meta"])
        except Exception:
            meta = {}
        out.append({"id": r["id"], "role": r["role"], "content": r["content"],
                    "provider": r["provider"], "model": r["model"], "meta": meta, "created": r["created"]})
    return out


def delete_chat(chat_id):
    with db() as conn:
        conn.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
        conn.execute("DELETE FROM chats WHERE id=?", (chat_id,))


def clear_chat(chat_id):
    with db() as conn:
        conn.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))


def delete_message(mid):
    with db() as conn:
        conn.execute("DELETE FROM messages WHERE id=?", (mid,))


def delete_from_message(chat_id, mid):
    """Borra el mensaje indicado y todos los posteriores del mismo chat."""
    with db() as conn:
        row = conn.execute("SELECT created FROM messages WHERE id=?", (mid,)).fetchone()
        if not row:
            return
        conn.execute("DELETE FROM messages WHERE chat_id=? AND created>=?", (chat_id, row["created"]))


def duplicate_chat(chat_id):
    src = get_chat(chat_id)
    if not src:
        return None
    new = create_chat(src["title"] + " (copia)", src["provider"], src["model"],
                      src["agent"], src["workdir"], src["toolsets"])
    with db() as conn:
        conn.execute("UPDATE chats SET system=? WHERE id=?", (src["system"], new["id"]))
        for m in get_messages(chat_id):
            conn.execute(
                "INSERT INTO messages(id,chat_id,role,content,provider,model,meta,created) VALUES(?,?,?,?,?,?,?,?)",
                (uid("m_"), new["id"], m["role"], m["content"], m["provider"], m["model"],
                 json.dumps(m["meta"]), now()))
    return get_chat(new["id"])


# ------------------------------- busqueda ---------------------------------- #


def search_messages(query, limit=60):
    q = (query or "").strip()
    if not q:
        return []
    like = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    with db() as conn:
        rows = conn.execute(
            "SELECT m.id, m.chat_id, m.role, m.content, m.created, c.title AS ctitle "
            "FROM messages m JOIN chats c ON c.id=m.chat_id "
            "WHERE m.content LIKE ? ESCAPE '\\' ORDER BY m.created DESC LIMIT ?",
            (like, limit)).fetchall()
    out, low = [], q.lower()
    for r in rows:
        idx = r["content"].lower().find(low)
        start = max(0, idx - 45)
        snippet = ("…" if start > 0 else "") + r["content"][start:start + 160].replace("\n", " ")
        out.append({"message_id": r["id"], "chat_id": r["chat_id"], "chat_title": r["ctitle"],
                    "role": r["role"], "snippet": snippet, "created": r["created"]})
    return out


# ----------------------------- estadisticas -------------------------------- #


def chat_stats(chat_id):
    msgs = get_messages(chat_id)
    tin = tout = 0
    models = {}
    for m in msgs:
        u = (m.get("meta") or {}).get("usage") or {}
        tin += u.get("prompt_tokens", 0) or 0
        tout += u.get("completion_tokens", 0) or 0
        if m["model"]:
            models[m["model"]] = models.get(m["model"], 0) + 1
    return {"messages": len(msgs), "tokens_in": tin, "tokens_out": tout,
            "tokens_total": tin + tout, "models": models}


# -------------------------------- plantillas ------------------------------- #


def list_presets():
    with db() as conn:
        rows = conn.execute("SELECT * FROM presets ORDER BY created ASC").fetchall()
    return [{"id": r["id"], "title": r["title"], "body": r["body"]} for r in rows]


def save_preset(pid, title, body):
    with db() as conn:
        if pid:
            conn.execute("UPDATE presets SET title=?, body=? WHERE id=?", (title, body, pid))
        else:
            pid = uid("p_")
            conn.execute("INSERT INTO presets(id,title,body,created) VALUES(?,?,?,?)", (pid, title, body, now()))
    return {"id": pid, "title": title, "body": body}


def delete_preset(pid):
    with db() as conn:
        conn.execute("DELETE FROM presets WHERE id=?", (pid,))


# --------------------------------------------------------------------------- #
# peticion al proveedor
# --------------------------------------------------------------------------- #


def split_attachments(attachments):
    text_blocks, images, total = [], [], 0
    for a in attachments or []:
        name = (a.get("name") or "archivo").strip()
        mime = a.get("mime") or "application/octet-stream"
        data = a.get("data") or ""
        total += len(data)
        if total > MAX_ATTACH_TOTAL:
            raise RuntimeError("Los adjuntos superan el limite de tamaño.")
        if mime.startswith("image/"):
            images.append({"name": name, "url": f"data:{mime};base64,{data}"})
        else:
            try:
                raw = base64.b64decode(data + "===")[:MAX_ATTACH_TEXT]
            except Exception:
                raw = b""
            text_blocks.append((name, raw.decode("utf-8", "replace")))
    return text_blocks, images


def build_messages(chat, history, attachments=None):
    text_blocks, images = split_attachments(attachments)
    msgs = []
    if chat.get("system"):
        msgs.append({"role": "system", "content": chat["system"]})
    for m in history:
        if m["role"] in ("user", "assistant"):
            msgs.append({"role": m["role"], "content": m["content"]})
    if text_blocks and msgs and msgs[-1]["role"] == "user":
        block = "\n\n".join(f"--- {n} ---\n{c}" for n, c in text_blocks)
        msgs[-1] = {"role": "user", "content": msgs[-1]["content"] + "\n\n[Archivos adjuntos]\n" + block}
    if images and msgs and msgs[-1]["role"] == "user":
        parts = [{"type": "text", "text": msgs[-1]["content"] or "(ver imagen adjunta)"}]
        for im in images:
            parts.append({"type": "image_url", "image_url": {"url": im["url"]}})
        msgs[-1] = {"role": "user", "content": parts}
    return msgs


def stream_completion(chat, history, on_delta, attachments=None):
    pid = chat.get("provider") or default_provider_model()[0]
    spec = provider_spec(pid)
    spec["session_value"] = chat["id"]
    base, key = provider_credentials(spec)
    if not base:
        raise RuntimeError(f"El proveedor '{pid}' no tiene URL configurada. Abre Ajustes -> Proveedores.")
    if spec.get("requires_key") is not False and not key:
        raise RuntimeError(f"Falta la clave de API de '{spec.get('label', pid)}'. "
                           "Anadela en Ajustes -> Proveedores y claves.")

    headers = provider_headers(spec, key, stream=True)

    payload = {"model": chat["model"], "messages": build_messages(chat, history, attachments),
               "stream": True, "stream_options": {"include_usage": True}}
    req = urllib.request.Request(base + "/chat/completions",
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers=headers, method="POST")
    text_parts, meta = [], {"usage": None}
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as resp:
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line or not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
            except Exception:
                continue
            if chunk.get("usage"):
                meta["usage"] = chunk["usage"]
                meta["latency_ms"] = int((time.time() - t0) * 1000)
            for choice in chunk.get("choices", []):
                piece = (choice.get("delta") or {}).get("content")
                if piece:
                    text_parts.append(piece)
                    on_delta(piece)
    return "".join(text_parts), meta


# --------------------------------------------------------------------------- #
# modo agente (hermes chat)
# --------------------------------------------------------------------------- #


WRITE_TOOLS = re.compile(r"write|edit|patch|create|append|replace|save|mkdir|move|copy", re.I)
PATH_KEYS = ("path", "file_path", "filepath", "target_file", "target", "filename", "file")


def tool_artifact(name, args, cwd):
    """Devuelve la ruta absoluta si la herramienta escribio en un archivo, o None."""
    if not name or not isinstance(args, dict) or not WRITE_TOOLS.search(name):
        return None
    raw = ""
    for k in PATH_KEYS:
        v = args.get(k)
        if isinstance(v, str) and v.strip():
            raw = v.strip()
            break
    if not raw:
        return None
    p = Path(os.path.expanduser(raw))
    if not p.is_absolute():
        p = Path(cwd or DEFAULT_WORKDIR) / p
    return str(p)


def run_agent_turn(chat, text, on_delta, on_session, stop_event=None, on_artifact=None):
    """Ejecuta un turno del agente Hermes y transmite los deltas de texto."""
    cmd = [hermes_bin(), "chat", "-q", text, "--format", "stream-json"]
    if chat.get("agent_session"):
        cmd += ["--resume", chat["agent_session"]]
    if chat.get("model"):
        cmd += ["-m", chat["model"]]
    if chat.get("provider"):
        cmd += ["--provider", chat["provider"]]
    if chat.get("toolsets"):
        cmd += ["-t", chat["toolsets"]]
    cwd = chat.get("workdir") or DEFAULT_WORKDIR

    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1, env=agent_env())
    text_parts, meta, session = [], {"agent": True, "usage": None}, ""
    pending = {}  # tool_call_id -> ruta, para avisar cuando el archivo ya esta escrito
    t0 = time.time()
    try:
        for line in proc.stdout:
            if stop_event is not None and stop_event.is_set():
                proc.kill()
                break
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            typ = ev.get("type")
            if typ == "system" and ev.get("session_id"):
                session = ev["session_id"]
                on_session(session)
            elif typ == "text" and ev.get("text"):
                text_parts.append(ev["text"])
                on_delta(ev["text"])
            elif typ == "tool_use":
                args = ev.get("input") or {}
                art = tool_artifact(ev.get("name"), args, cwd)
                if art and on_artifact:
                    content = args.get("content")
                    if not isinstance(content, str):
                        content = args.get("new_string") if isinstance(args.get("new_string"), str) else None
                    on_artifact(art, ev.get("name"), None if content is None else content[:200000], False)
                    pending[ev.get("tool_call_id") or art] = art
            elif typ == "tool_result":
                art = pending.pop(ev.get("tool_call_id") or "", None)
                if art is None and pending:
                    art = list(pending.values())[-1]
                if art and on_artifact and not ev.get("is_error"):
                    on_artifact(art, ev.get("name"), None, True)
            elif typ == "result":
                if ev.get("session_id"):
                    session = ev["session_id"]
                    on_session(session)
                tk = ev.get("tokens") or {}
                meta["usage"] = {"prompt_tokens": tk.get("input"), "completion_tokens": tk.get("output"),
                                 "total_tokens": tk.get("total")}
                meta["latency_ms"] = ev.get("duration_ms") or int((time.time() - t0) * 1000)
                meta["exit_code"] = ev.get("exit_code")
    finally:
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
    return "".join(text_parts), meta, session


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# precios, analitica, registro
# --------------------------------------------------------------------------- #

_PRICING = None


def load_pricing():
    global _PRICING
    if _PRICING is not None:
        return _PRICING
    data = load_json(Path.home() / ".hermes" / "models_dev_cache.json", {})
    by_prov, bare = {}, {}
    for prov, pdata in (data or {}).items():
        models = pdata.get("models") if isinstance(pdata, dict) else None
        if not isinstance(models, dict):
            continue
        for mid, m in models.items():
            cost = (m or {}).get("cost") or {}
            if not cost:
                continue
            entry = {"input": cost.get("input", 0) or 0,
                     "output": cost.get("output", 0) or 0,
                     "cache_read": cost.get("cache_read", 0) or 0}
            by_prov[f"{prov}::{mid}"] = entry
            bare.setdefault(mid, entry)
    _PRICING = {"by_prov": by_prov, "bare": bare}
    return _PRICING


def price_for(model, provider=""):
    p = load_pricing()
    if provider and f"{provider}::{model}" in p["by_prov"]:
        return p["by_prov"][f"{provider}::{model}"]
    return p["bare"].get(model or "") or {}


def cost_of(tin, tout, cache, price):
    return ((tin or 0) / 1e6 * (price.get("input", 0) or 0)
            + (tout or 0) / 1e6 * (price.get("output", 0) or 0)
            + (cache or 0) / 1e6 * (price.get("cache_read", 0) or 0))


def log_event(kind, detail="", chat_id="", model="", tokens=0, cost=0.0):
    try:
        with db() as conn:
            conn.execute(
                "INSERT INTO events(ts,kind,detail,chat_id,model,tokens,cost) VALUES(?,?,?,?,?,?,?)",
                (now(), kind, str(detail)[:500], chat_id, model, int(tokens or 0), float(cost or 0)))
    except Exception:
        pass


def recent_events(limit=200, kind=""):
    with db() as conn:
        if kind:
            rows = conn.execute("SELECT * FROM events WHERE kind=? ORDER BY ts DESC LIMIT ?", (kind, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM events ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
    return [{k: r[k] for k in r.keys()} for r in rows]


def _hermes_state():
    p = Path.home() / ".hermes" / "state.db"
    if not p.exists():
        return None
    try:
        c = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=5)
        c.row_factory = sqlite3.Row
        return c
    except Exception:
        return None


def merge_intervals(iv, gap=300):
    iv = sorted([[min(a, b), max(a, b)] for a, b in iv])
    out = []
    for a, b in iv:
        if out and a <= out[-1][1] + gap:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def analytics(days=30):
    since = now() - days * 86400
    models, per_day = {}, {}
    per_hour = [0] * 24
    per_weekday = [0] * 7

    def day_of(ts):
        return time.strftime("%Y-%m-%d", time.localtime(ts or now()))

    def bucket(day):
        return per_day.setdefault(day, {"tokens_in": 0, "tokens_out": 0, "messages": 0,
                                        "cost_usd": 0.0, "cost_api": 0.0})

    def add_model(model, provider, tin, tout, cache, calls, cost, src):
        k = f"{provider}::{model}" if provider else (model or "desconocido")
        e = models.setdefault(k, {"model": model or "?", "provider": provider or "",
                                  "calls": 0, "tokens_in": 0, "tokens_out": 0, "cache_read": 0,
                                  "cost_usd": 0.0, "cost_api": 0.0, "sources": set()})
        e["calls"] += calls or 0
        e["tokens_in"] += tin or 0
        e["tokens_out"] += tout or 0
        e["cache_read"] += cache or 0
        e["cost_usd"] += cost or 0.0
        e["cost_api"] += cost_of(tin, tout, cache, price_for(model, provider))
        e["sources"].add(src)

    # --- fuente NEXUS (modo chat; el modo agente lo contabiliza Hermes) ---
    with db() as conn:
        rows = conn.execute("SELECT model, provider, meta, created FROM messages WHERE role='assistant'").fetchall()
    for r in rows:
        try:
            meta = json.loads(r["meta"])
        except Exception:
            meta = {}
        u = meta.get("usage") or {}
        if not u or meta.get("agent"):
            continue
        tin = u.get("prompt_tokens") or 0
        tout = u.get("completion_tokens") or 0
        add_model(r["model"], r["provider"], tin, tout, 0, 1, 0.0, "nexus")
        if r["created"] >= since:
            b = bucket(day_of(r["created"]))
            b["tokens_in"] += tin
            b["tokens_out"] += tout
            b["messages"] += 1
            b["cost_api"] += cost_of(tin, tout, 0, price_for(r["model"], r["provider"]))
            lt = time.localtime(r["created"])
            per_hour[lt.tm_hour] += 1
            per_weekday[lt.tm_wday] += 1

    # --- fuente Hermes (state.db, incluye el modo agente y otros usos) ---
    sessions_n, hours, tool_calls = 0, 0.0, 0
    hs = _hermes_state()
    if hs:
        try:
            for r in hs.execute("SELECT model, billing_provider, api_call_count, input_tokens, output_tokens,"
                                " cache_read_tokens, estimated_cost_usd, last_seen FROM session_model_usage"):
                add_model(r["model"], r["billing_provider"], r["input_tokens"], r["output_tokens"],
                          r["cache_read_tokens"], r["api_call_count"], r["estimated_cost_usd"], "hermes")
                if (r["last_seen"] or 0) >= since:
                    b = bucket(day_of(r["last_seen"]))
                    b["tokens_in"] += r["input_tokens"] or 0
                    b["tokens_out"] += r["output_tokens"] or 0
                    b["cost_usd"] += r["estimated_cost_usd"] or 0.0
        except Exception:
            pass
        try:
            iv = []
            for s in hs.execute("SELECT started_at, COALESCE(ended_at, last_activity_at, started_at) AS endt,"
                                " tool_call_count FROM sessions"):
                a, b = s["started_at"], s["endt"]
                if not a:
                    continue
                if b and b >= since:
                    iv.append([max(a, since), b])
                tool_calls += s["tool_call_count"] or 0
            sessions_n = len(iv)
            for a, b in merge_intervals(iv):
                hours += (b - a) / 3600
        except Exception:
            pass
        try:
            hs.close()
        except Exception:
            pass

    # --- tiempo de uso de la app (pings) ---
    app_hours = 0.0
    try:
        with db() as conn:
            evs = [r["ts"] for r in conn.execute(
                "SELECT ts FROM events WHERE kind='app_active' AND ts>=? ORDER BY ts", (since,))]
        app_hours = sum((b - a) / 3600 for a, b in merge_intervals(
            [[evs[i], evs[i + 1]] for i in range(len(evs) - 1) if evs[i + 1] - evs[i] <= 600], gap=600))
    except Exception:
        pass

    per_model = sorted(models.values(), key=lambda e: (e["tokens_in"] + e["tokens_out"]), reverse=True)
    for e in per_model:
        e["sources"] = sorted(e["sources"])
        e["tokens_total"] = e["tokens_in"] + e["tokens_out"]

    series = []
    for i in range(days - 1, -1, -1):
        d = day_of(now() - i * 86400)
        series.append({"date": d, **(per_day.get(d) or
                                     {"tokens_in": 0, "tokens_out": 0, "messages": 0,
                                      "cost_usd": 0.0, "cost_api": 0.0})})

    tot_in = sum(e["tokens_in"] for e in per_model)
    tot_out = sum(e["tokens_out"] for e in per_model)
    return {
        "range_days": days, "generated": now(),
        "totals": {
            "tokens_in": tot_in, "tokens_out": tot_out, "tokens_total": tot_in + tot_out,
            "calls": sum(e["calls"] for e in per_model),
            "cost_usd": sum(e["cost_usd"] for e in per_model),
            "cost_api": sum(e["cost_api"] for e in per_model),
            "hours_agent": round(hours, 2), "hours_app": round(app_hours, 2),
            "sessions": sessions_n, "tool_calls": tool_calls, "models": len(per_model),
        },
        "per_model": per_model, "per_day": series,
        "per_hour": per_hour, "per_weekday": per_weekday,
    }


# --------------------------------------------------------------------------- #
# tareas (trabajos en segundo plano)
# --------------------------------------------------------------------------- #

TASK_RUNS = {}


def get_task(tid):
    with db() as conn:
        r = conn.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
    if not r:
        return None
    d = {k: r[k] for k in r.keys()}
    run = TASK_RUNS.get(tid)
    if run and d.get("status") in ("running", "queued"):
        d["output"] = run.get("text", "")[-60000:]
    return d


def list_tasks():
    with db() as conn:
        rows = conn.execute("SELECT id,title,workdir,provider,model,toolsets,status,created,started,"
                            "finished,exit_code,tokens,cost,error FROM tasks ORDER BY created DESC LIMIT 100").fetchall()
    return [{k: r[k] for k in r.keys()} for r in rows]


def create_task(title, prompt, workdir, provider, model, toolsets):
    tid = uid("t_")
    with db() as conn:
        conn.execute("INSERT INTO tasks(id,title,prompt,workdir,provider,model,toolsets,status,created)"
                     " VALUES(?,?,?,?,?,?,?,'queued',?)",
                     (tid, title or "Trabajo", prompt, workdir, provider, model, toolsets, now()))
    log_event("task_created", title or prompt[:80], model=model or "")
    threading.Thread(target=run_task, args=(tid,), daemon=True).start()
    return get_task(tid)


def run_task(tid):
    t = get_task(tid)
    if not t:
        return
    cmd = [hermes_bin(), "chat", "-q", t["prompt"], "--format", "stream-json"]
    if t.get("model"):
        cmd += ["-m", t["model"]]
    if t.get("provider"):
        cmd += ["--provider", t["provider"]]
    if t.get("toolsets"):
        cmd += ["-t", t["toolsets"]]
    cwd = t.get("workdir") or DEFAULT_WORKDIR
    stop = threading.Event()
    run = {"status": "running", "text": "", "stop": stop, "proc": None}
    TASK_RUNS[tid] = run
    with db() as conn:
        conn.execute("UPDATE tasks SET status='running', started=? WHERE id=?", (now(), tid))

    parts, tokens, cost, err, rc = [], 0, 0.0, "", None
    try:
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1, env=agent_env())
        run["proc"] = proc
        for line in proc.stdout:
            if stop.is_set():
                proc.kill()
                break
            s = line.strip()
            if not s or s.startswith("session_id:"):
                continue
            if not s.startswith("{"):
                run["text"] += s + "\n"
                continue
            try:
                ev = json.loads(s)
            except Exception:
                continue
            typ = ev.get("type")
            if typ == "text" and ev.get("text"):
                parts.append(ev["text"])
                run["text"] = "".join(parts)
            elif typ == "tool_use" or typ == "tool":
                name = ev.get("name") or ev.get("tool") or "herramienta"
                run["text"] = "".join(parts) + f"\n» {name}\n"
            elif typ == "result":
                tk = ev.get("tokens") or {}
                tokens = tk.get("total") or 0
                price = price_for(t["model"], t["provider"])
                cost = cost_of(tk.get("input"), tk.get("output"), 0, price)
        rc = proc.wait(timeout=10)
    except Exception as exc:  # noqa: BLE001
        err, rc = str(exc), -1

    status = "cancelled" if stop.is_set() else ("done" if rc == 0 else "error")
    out = "".join(parts) or run["text"]
    with db() as conn:
        conn.execute("UPDATE tasks SET status=?,finished=?,output=?,exit_code=?,tokens=?,cost=?,error=?"
                     " WHERE id=?", (status, now(), out, rc, tokens, cost, err, tid))
    run["status"] = status
    log_event("task_" + status, (t["title"] or "")[:120], model=t.get("model", ""), tokens=tokens, cost=cost)


def cancel_task(tid):
    run = TASK_RUNS.get(tid)
    if run:
        run["stop"].set()
        proc = run.get("proc")
        if proc and proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass
        return True
    return False


def delete_task(tid):
    cancel_task(tid)
    TASK_RUNS.pop(tid, None)
    with db() as conn:
        conn.execute("DELETE FROM tasks WHERE id=?", (tid,))


# --------------------------------------------------------------------------- #
# proyectos (examinar y previsualizar)
# --------------------------------------------------------------------------- #


def safe_path(p):
    try:
        ap = Path(p or DEFAULT_WORKDIR).expanduser()
        if not ap.is_absolute():
            ap = Path.home() / ap
        ap = ap.resolve()
    except Exception:
        return None
    for root in ALLOWED_ROOTS:
        try:
            ap.relative_to(root.resolve())
            return ap
        except Exception:
            continue
    return None


def list_project(path):
    ap = safe_path(path)
    if not ap or not ap.is_dir():
        return None
    entries = []
    try:
        for c in sorted(ap.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if c.name.startswith("."):
                continue
            try:
                is_dir = c.is_dir()
                size = c.stat().st_size if not is_dir else 0
            except Exception:
                is_dir, size = False, 0
            entries.append({"name": c.name, "type": "dir" if is_dir else "file",
                            "size": size, "ext": c.suffix.lower()})
            if len(entries) >= 600:
                break
    except PermissionError:
        return {"path": str(ap), "parent": str(ap.parent), "entries": [], "error": "sin permisos"}
    return {"path": str(ap), "parent": str(ap.parent) if ap.parent != ap else "", "entries": entries}



MIME = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8", ".svg": "image/svg+xml",
        ".json": "application/json; charset=utf-8", ".png": "image/png", ".ico": "image/x-icon"}
MIME.update(MIME_EXTRA)


LOGIN_HTML = """<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>NEXUS · acceso</title>
<style>body{background:#05070d;color:#e6ecff;font-family:system-ui,sans-serif;display:grid;place-items:center;height:100vh;margin:0}
.card{background:#0d1220;border:1px solid rgba(120,160,255,.26);border-radius:18px;padding:30px;max-width:420px;text-align:center}
h1{font-size:18px;letter-spacing:.2em;margin:0 0 6px}p{color:#8b97b8;font-size:13px;line-height:1.6}
code{background:rgba(120,160,255,.12);padding:2px 6px;border-radius:5px;color:#38f5ff;word-break:break-all}</style>
</head><body><div class="card"><h1>◈ NEXUS</h1>
<p>Acceso desde la red local. Abre el enlace con tu token:</p>
<p><code>/login?token=TU_TOKEN</code></p>
<p>El token está en el panel de la app, sección <b>Red local</b>.</p></div></body></html>"""


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "NEXUS"

    def log_message(self, *a):
        pass

    # -- helpers ------------------------------------------------------------
    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _begin_request(self):
        """Lee el cuerpo ANTES de responder, aunque el handler no vaya a usarlo.

        La conexion es keep-alive: si quedan bytes del cuerpo en el socket, la
        siguiente peticion empieza a leerse por ellos y el servidor responde 501
        'Unsupported method' (el sintoma es un fallo aleatorio de fetch en la app)."""
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            n = 0
        self._body_raw = self.rfile.read(n) if n > 0 else b""

    def read_body(self):
        raw = getattr(self, "_body_raw", None)
        if raw is None:
            self._begin_request()
            raw = self._body_raw
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def sse_start(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Connection", "close")
        self.end_headers()

    def sse_send(self, event, data):
        self.wfile.write(f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8"))
        self.wfile.flush()

    def _safe_sse(self, event, data):
        try:
            self.sse_send(event, data)
        except Exception:
            pass

    # -- acceso (LAN con token) --------------------------------------------
    def _client_ip(self):
        return (self.client_address[0] if self.client_address else "") or ""

    def _is_local(self):
        return self._client_ip() in ("127.0.0.1", "::1", "::ffff:127.0.0.1", "localhost")

    def _presented_token(self, params=None):
        tok = ""
        m = re.search(r"nexus_token=([^;]+)", self.headers.get("Cookie", ""))
        if m:
            tok = urllib.parse.unquote(m.group(1))
        if not tok:
            auth = self.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                tok = auth[7:].strip()
        if not tok and params:
            tok = params.get("token", "")
        return tok

    def require_auth(self, params=None):
        if self._is_local():
            return True
        tok = self._presented_token(params)
        if tok and hmac.compare_digest(tok, lan_config().get("token", "")):
            return True
        self.send_response(401)
        if self.path.startswith("/api/"):
            body = json.dumps({"error": "no autorizado"}).encode("utf-8")
            self.send_header("Content-Type", "application/json; charset=utf-8")
        else:
            body = LOGIN_HTML.encode("utf-8")
            self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass
        return False

    def parse_qs(self):
        params = {}
        _, _, qs = self.path.partition("?")
        for pair in qs.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                params[k] = urllib.parse.unquote_plus(v)
        return params

    # -- GET ----------------------------------------------------------------
    def do_GET(self):
        self._begin_request()
        path = self.path.split("?", 1)[0]
        params = self.parse_qs()
        if path == "/login":
            tok = params.get("token", "")
            if tok and hmac.compare_digest(tok, lan_config().get("token", "")):
                self.send_response(302)
                self.send_header("Set-Cookie", f"nexus_token={tok}; Path=/; Max-Age=31536000; SameSite=Lax")
                self.send_header("Location", "/")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            return self.send_json({"error": "token invalido"}, 403)
        if path == "/api/lan":
            if not self.require_auth(params):
                return
            cfg = lan_config()
            return self.send_json({"enabled": LAN_ENABLED, "port": PORT, "addresses": lan_addresses(),
                                   "token": cfg.get("token", "")})
        if not self.require_auth(params):
            return
        if path == "/api/health":
            return self.send_json({"ok": True, "time": now()})
        if path == "/api/config":
            cfg = user_config()
            pub = {"default": cfg.get("default") or {},
                   "providers": {pid: {**{k: v for k, v in spec.items() if k != "api_key"},
                                       "has_key": bool(spec.get("api_key"))}
                                 for pid, spec in (cfg.get("providers") or {}).items()},
                   "config_path": str(CONFIG_PATH),
                   "catalog": {pid: {k: v for k, v in spec.items() if k != "models"}
                               for pid, spec in CATALOG_PROVIDERS.items()},
                   "needs_setup": needs_setup()}
            return self.send_json(pub)
        if path == "/api/hermes":
            st = hermes_status()
            st["tail"] = install_log_tail(120) if (st["running"] or st["exit_code"] is not None) else ""
            return self.send_json(st)
        if path == "/api/state":
            pid, mdl = default_provider_model()
            return self.send_json({"chats": list_chats(), "providers": provider_index(),
                                   "default": {"provider": pid, "model": mdl},
                                   "needs_setup": needs_setup(),
                                   "hermes": hermes_status(),
                                   "home": str(Path.home()),
                                   "config_path": str(CONFIG_PATH),
                                   "presets": list_presets()})
        if path == "/api/chats":
            return self.send_json({"chats": list_chats()})
        if path == "/api/search":
            return self.send_json({"results": search_messages(params.get("q", ""))})
        if path == "/api/presets":
            return self.send_json({"presets": list_presets()})
        if path == "/api/stats":
            with db() as conn:
                r = conn.execute("SELECT COUNT(*) c FROM messages").fetchone()
            return self.send_json({"chats": len(list_chats()), "messages": r["c"]})
        if path == "/api/export":
            data = {"version": 1, "exported": now(), "chats": []}
            for c in list_chats():
                data["chats"].append({"chat": c, "messages": get_messages(c["id"])})
            return self.send_json(data)
        m = re.match(r"^/api/chats/([\w-]+)/messages$", path)
        if m:
            chat = get_chat(m.group(1))
            if not chat:
                return self.send_json({"error": "not found"}, 404)
            return self.send_json({"chat": chat, "messages": get_messages(m.group(1))})
        m = re.match(r"^/api/chats/([\w-]+)/stats$", path)
        if m:
            return self.send_json(chat_stats(m.group(1)))
        if path == "/api/analytics":
            try:
                days = max(1, min(365, int(params.get("days", "30"))))
            except ValueError:
                days = 30
            return self.send_json(analytics(days))
        if path == "/api/log":
            try:
                limit = max(1, min(1000, int(params.get("limit", "200"))))
            except ValueError:
                limit = 200
            return self.send_json({"events": recent_events(limit, params.get("kind", ""))})
        if path == "/api/tasks":
            return self.send_json({"tasks": list_tasks()})
        m = re.match(r"^/api/tasks/([\w-]+)$", path)
        if m:
            t = get_task(m.group(1))
            return self.send_json({"task": t}) if t else self.send_json({"error": "no encontrado"}, 404)
        if path == "/api/project":
            data = list_project(params.get("path", ""))
            return self.send_json(data) if data else self.send_json({"error": "ruta no valida"}, 400)
        if path.startswith("/preview/"):
            return self.serve_project(path)
        return self.serve_static(path)

    # -- PATCH --------------------------------------------------------------
    def do_PATCH(self):
        self._begin_request()
        if not self.require_auth(self.parse_qs()):
            return
        m = re.match(r"^/api/chats/([\w-]+)$", self.path.split("?")[0])
        if not m:
            return self.send_json({"error": "bad path"}, 400)
        body = self.read_body()
        touch_chat(m.group(1),
                   title=body.get("title"), provider=body.get("provider"), model=body.get("model"),
                   system=body.get("system"), workdir=body.get("workdir"), toolsets=body.get("toolsets"),
                   agent=(int(body["agent"]) if "agent" in body else None),
                   pinned=(int(body["pinned"]) if "pinned" in body else None))
        return self.send_json({"chat": get_chat(m.group(1))})

    # -- DELETE -------------------------------------------------------------
    def do_DELETE(self):
        self._begin_request()
        if not self.require_auth(self.parse_qs()):
            return
        path = self.path.split("?")[0]
        m = re.match(r"^/api/chats/([\w-]+)$", path)
        if m:
            delete_chat(m.group(1))
            return self.send_json({"ok": True})
        m = re.match(r"^/api/presets/([\w-]+)$", path)
        if m:
            delete_preset(m.group(1))
            return self.send_json({"ok": True})
        m = re.match(r"^/api/tasks/([\w-]+)$", path)
        if m:
            delete_task(m.group(1))
            return self.send_json({"ok": True})
        return self.send_json({"error": "bad path"}, 400)

    # -- POST ---------------------------------------------------------------
    def do_POST(self):
        self._begin_request()
        if not self.require_auth(self.parse_qs()):
            return
        path = self.path.split("?")[0]
        if path == "/api/config":
            body = self.read_body()
            cfg = user_config()
            if body.get("delete"):
                pid = str(body["delete"])
                cfg.get("providers", {}).pop(pid, None)
                if (cfg.get("default") or {}).get("provider") == pid:
                    cfg["default"] = {}
                save_user_config(cfg)
                return self.send_json({"ok": True, "config": {k: v for k, v in cfg.items() if k != "providers"}})
            prov = body.get("provider") or {}
            pid = (prov.get("id") or "").strip()
            if not pid:
                return self.send_json({"error": "falta el id del proveedor"}, 400)
            entrada = dict(cfg["providers"].get(pid) or {})
            for campo in ("label", "base_url", "api_key", "key_env", "docs", "session_header", "session_prefix"):
                if campo in prov:
                    valor = prov.get(campo)
                    if isinstance(valor, str):
                        valor = valor.strip()
                    if valor in (None, ""):
                        entrada.pop(campo, None)
                    else:
                        entrada[campo] = valor
            if "requires_key" in prov:
                entrada["requires_key"] = bool(prov["requires_key"])
            if isinstance(prov.get("models"), list):
                entrada["models"] = [str(m) for m in prov["models"] if str(m).strip()]
            if not entrada.get("base_url"):
                base_cat = (CATALOG_PROVIDERS.get(pid) or {}).get("base_url", "")
                if base_cat:
                    entrada["base_url"] = base_cat
            if not entrada.get("base_url"):
                return self.send_json({"error": "el proveedor necesita una URL base"}, 400)
            cfg["providers"][pid] = entrada
            if body.get("make_default") or not (cfg.get("default") or {}).get("provider"):
                modelo = (prov.get("model") or body.get("model") or
                          (entrada.get("models") or [""])[0])
                cfg["default"] = {"provider": pid, "model": modelo or ""}
            save_user_config(cfg)
            return self.send_json({"ok": True, "default": cfg.get("default", {}),
                                   "needs_setup": needs_setup(),
                                   "providers": provider_index()})
        if path == "/api/config/test":
            body = self.read_body()
            pid = (body.get("provider") or "").strip()
            if not pid:
                return self.send_json({"ok": False, "error": "falta el proveedor"}, 400)
            resultado = test_provider(pid, (body.get("model") or "").strip(), body.get("spec"))
            return self.send_json(resultado)
        if path == "/api/config/models":
            body = self.read_body()
            pid = (body.get("provider") or "").strip()
            try:
                ids = fetch_models(pid)
            except Exception as exc:  # noqa: BLE001
                return self.send_json({"ok": False, "error": str(exc), "models": []})
            return self.send_json({"ok": True, "models": ids})
        if path == "/api/hermes/install":
            lanzado, mensaje = start_hermes_install()
            return self.send_json({"ok": lanzado, "message": mensaje, "status": hermes_status()})
        if path == "/api/ping":
            with db() as conn:
                last = conn.execute("SELECT ts FROM events WHERE kind='app_active' ORDER BY ts DESC LIMIT 1").fetchone()
            if not last or now() - last["ts"] > 300:
                log_event("app_active", self._client_ip())
            return self.send_json({"ok": True})
        if path == "/api/tasks":
            body = self.read_body()
            prompt = (body.get("prompt") or "").strip()
            if not prompt:
                return self.send_json({"error": "falta el encargo"}, 400)
            t = create_task(body.get("title") or prompt[:60], prompt,
                            body.get("workdir") or DEFAULT_WORKDIR,
                            body.get("provider", ""), body.get("model", ""), body.get("toolsets", ""))
            return self.send_json({"task": t}, 201)
        m = re.match(r"^/api/tasks/([\w-]+)/cancel$", path)
        if m:
            return self.send_json({"ok": cancel_task(m.group(1))})
        if path == "/api/chats":
            body = self.read_body()
            chat = create_chat(body.get("title"), body.get("provider"),
                               body.get("model"), body.get("agent", 0),
                               body.get("workdir", ""), body.get("toolsets", ""))
            log_event("chat_created", chat["title"], chat_id=chat["id"], model=chat["model"])
            return self.send_json({"chat": chat}, 201)
        if path == "/api/presets":
            body = self.read_body()
            return self.send_json({"preset": save_preset(body.get("id"), body.get("title", "Plantilla"),
                                                         body.get("body", ""))})
        if path == "/api/import":
            return self.import_data()
        m = re.match(r"^/api/chats/([\w-]+)/clear$", path)
        if m:
            clear_chat(m.group(1))
            return self.send_json({"ok": True})
        m = re.match(r"^/api/chats/([\w-]+)/duplicate$", path)
        if m:
            return self.send_json({"chat": duplicate_chat(m.group(1))}, 201)
        m = re.match(r"^/api/chats/([\w-]+)/stop$", path)
        if m:
            ev = STOP_FLAGS.get(m.group(1))
            if ev:
                ev.set()
            return self.send_json({"ok": True})
        if path == "/api/chat":
            return self.handle_chat_stream()
        return self.send_json({"error": "bad path"}, 404)

    def import_data(self):
        body = self.read_body()
        n = 0
        for item in body.get("chats", []):
            c = item.get("chat", {})
            new = create_chat(c.get("title", "Importado"), c.get("provider"), c.get("model"),
                              c.get("agent", 0), c.get("workdir", ""), c.get("toolsets", ""))
            with db() as conn:
                if c.get("system"):
                    conn.execute("UPDATE chats SET system=? WHERE id=?", (c["system"], new["id"]))
                for mm in item.get("messages", []):
                    conn.execute(
                        "INSERT INTO messages(id,chat_id,role,content,provider,model,meta,created) VALUES(?,?,?,?,?,?,?,?)",
                        (uid("m_"), new["id"], mm.get("role", "user"), mm.get("content", ""),
                         mm.get("provider", ""), mm.get("model", ""), json.dumps(mm.get("meta", {})), now()))
            n += 1
        return self.send_json({"imported": n})

    # -- streaming de un turno ---------------------------------------------
    def handle_chat_stream(self):
        body = self.read_body()
        chat_id = body.get("chat_id")
        regenerate = bool(body.get("regenerate"))
        edit_id = body.get("edit_message_id")
        content = (body.get("content") or "").strip()
        attachments = body.get("attachments") or []
        chat = get_chat(chat_id) if chat_id else None
        if not chat:
            return self.send_json({"error": "chat no encontrado"}, 404)
        if not regenerate and not edit_id and not content:
            return self.send_json({"error": "mensaje vacio"}, 400)

        if body.get("provider"):
            chat["provider"] = body["provider"]
        if body.get("model"):
            chat["model"] = body["model"]
        if "agent" in body:
            chat["agent"] = int(body["agent"])
        touch_chat(chat_id, provider=chat["provider"], model=chat["model"], agent=chat["agent"])

        user_mid = None
        if edit_id:
            delete_from_message(chat_id, edit_id)
            user_mid = add_message(chat_id, "user", content)
        elif regenerate:
            with db() as conn:
                row = conn.execute("SELECT id FROM messages WHERE chat_id=? AND role='assistant' "
                                   "ORDER BY created DESC LIMIT 1", (chat_id,)).fetchone()
            if row:
                delete_message(row["id"])
        else:
            note = ""
            if attachments:
                names = ", ".join(a.get("name", "archivo") for a in attachments[:6])
                note = f"\n\n_Adjuntos: {names}_"
            user_mid = add_message(chat_id, "user", content + note)

        history = get_messages(chat_id)
        if not regenerate and not edit_id and chat["title"] in ("Nuevo chat", "", None) and user_mid:
            title = re.sub(r"\s+", " ", content)[:48] or "Nuevo chat"
            touch_chat(chat_id, title=title)
            chat["title"] = title

        asst_mid = add_message(chat_id, "assistant", "", chat["provider"], chat["model"])
        self.sse_start()
        self.sse_send("meta", {"chat_id": chat_id, "user_message_id": user_mid,
                               "assistant_message_id": asst_mid, "model": chat["model"],
                               "provider": chat["provider"], "agent": chat["agent"]})

        parts = []
        mode = "agente" if chat["agent"] else "chat"
        stop_event = threading.Event()
        STOP_FLAGS[chat_id] = stop_event

        def on_delta(piece):
            parts.append(piece)
            self.sse_send("delta", {"text": piece})

        try:
            if chat["agent"]:
                artifacts = []

                def on_session(sid):
                    touch_chat(chat_id, agent_session=sid)
                    self._safe_sse("session", {"session_id": sid})

                def on_artifact(path, tool, content=None, final=False):
                    if path not in artifacts:
                        artifacts.append(path)
                    self._safe_sse("artifact", {"path": path, "tool": tool,
                                                "content": content, "final": bool(final)})

                text, meta, _ = run_agent_turn(chat, content, on_delta, on_session, stop_event,
                                               on_artifact=on_artifact)
                if artifacts:
                    meta["artifacts"] = artifacts
            else:
                text, meta = stream_completion(chat, history, on_delta, attachments)
            update_message(asst_mid, text, meta)
            u = meta.get("usage") or {}
            log_event(mode, content[:100] or "(turno)", chat_id=chat_id, model=chat["model"],
                      tokens=(u.get("total_tokens") or 0) if isinstance(u, dict) else 0,
                      cost=cost_of(u.get("prompt_tokens"), u.get("completion_tokens"), 0,
                                   price_for(chat["model"], chat["provider"])) if isinstance(u, dict) else 0)
            self.sse_send("done", {"message_id": asst_mid, "meta": meta, "mode": mode})
        except (BrokenPipeError, ConnectionResetError):
            update_message(asst_mid, "".join(parts), {"interrupted": True})
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", "replace")[:400]
            except Exception:
                detail = ""
            update_message(asst_mid, "".join(parts), {"error": f"HTTP {exc.code}"})
            self._safe_sse("error", {"message": f"El proveedor respondio {exc.code}. {detail}"})
        except Exception as exc:  # noqa: BLE001
            update_message(asst_mid, "".join(parts), {"error": str(exc)})
            self._safe_sse("error", {"message": str(exc)})
        finally:
            STOP_FLAGS.pop(chat_id, None)

    # -- estaticos ----------------------------------------------------------
    def serve_static(self, path):
        rel = "index.html" if path in ("/", "/index.html") else path.lstrip("/")
        target = (STATIC_DIR / rel).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.is_file():
            self.send_error(404, "not found")
            return
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(target.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)


    # -- previsualizacion de proyectos --------------------------------------
    def serve_project(self, path):
        rel = urllib.parse.unquote(path[len("/preview/"):])
        ap = safe_path("/" + rel)
        if not ap or not ap.is_file():
            self.send_error(404, "no encontrado")
            return
        try:
            data = ap.read_bytes()
        except Exception:
            self.send_error(403, "no legible")
            return
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(ap.suffix.lower(), "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)


def main():
    init_db()
    lan_config()
    bind_host = "0.0.0.0" if LAN_ENABLED else HOST
    srv = ThreadingHTTPServer((bind_host, PORT), Handler)
    srv.daemon_threads = True
    print(f"NEXUS listo en http://{HOST}:{PORT}  (datos: {DB_PATH})", flush=True)
    if LAN_ENABLED:
        for ip in lan_addresses():
            print(f"NEXUS en la red local: http://{ip}:{PORT}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
