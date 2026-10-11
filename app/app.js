/* ============================================================
   NEXUS · cliente
   ============================================================ */
const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));

const MQ_MOBILE = window.matchMedia("(max-width: 820px)");
const UA_MOBILE = /Android|iPhone|iPad|iPod|Mobile|Silk|Opera Mini/i.test(navigator.userAgent);
function isMobile() { return MQ_MOBILE.matches || UA_MOBILE; }
if (isMobile()) document.body.classList.add("mobile");

const state = {
  chats: [], providers: {}, defaults: {}, presets: [],
  activeId: null, chat: null, messages: [],
  streaming: false, abort: null,
  filter: "", searchResults: [],
  attachments: [],
  favorites: [],
};

const LS = {
  get(k, d) { try { const v = JSON.parse(localStorage.getItem(k)); return v === null ? d : v; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} },
};

/* ------------------------------- utilidades ------------------------------ */
function toast(msg, ms = 2200) {
  const caja = $("#toast");
  caja.textContent = msg;
  caja.classList.remove("hidden");
  requestAnimationFrame(() => caja.classList.add("show"));
  clearTimeout(caja._t);
  caja._t = setTimeout(() => { caja.classList.remove("show"); setTimeout(() => caja.classList.add("hidden"), 250); }, ms);
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" }, ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) throw new Error("HTTP " + res.status);
  return res.json();
}

function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
function esc(s) { return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }

/* --------------------------- markdown (seguro) --------------------------- */
const KW_DEFAULT = new Set("if else for while return function class const let var new try catch finally throw await async import export from default in of this super static void typeof instanceof delete break continue switch case do null true false undefined yield extends".split(" "));
const KW_PY = new Set("def class return if elif else for while in not and or is None True False import from as try except finally with lambda yield global nonlocal pass raise assert del async await break continue match case self".split(" "));
const KW_BASH = new Set("if then else elif fi for while do done case esac function in local export return echo printf read set unset source alias sudo cd ls grep sed awk cat true false".split(" "));
const KW_SQL = new Set("select from where insert into update delete join left right inner outer on as group by order having limit offset values set create table alter drop index primary key foreign references distinct count sum avg min max and or not null".split(" "));

function kwFor(lang) {
  const l = (lang || "").toLowerCase();
  if (/^(py|python)/.test(l)) return KW_PY;
  if (/^(sh|bash|zsh|shell|console|terminal)/.test(l)) return KW_BASH;
  if (/^sql/.test(l)) return KW_SQL;
  if (/^(json|ya?ml|toml|ini|diff|txt|text|md|markdown|log)/.test(l)) return new Set();
  return KW_DEFAULT;
}
function commentStyle(lang) {
  const l = (lang || "").toLowerCase();
  if (/^(py|python|sh|bash|zsh|shell|console|terminal|ya?ml|toml|ini|rb|ruby|perl|r)$/.test(l)) return "hash";
  if (/^sql/.test(l)) return "dash";
  if (/^(json|txt|text|md|markdown|diff|log)/.test(l)) return "none";
  return "slash";
}

function highlightCode(raw, lang) {
  const kw = kwFor(lang), cs = commentStyle(lang);
  let comment = null;
  if (cs === "hash") comment = "#[^\\n]*";
  else if (cs === "dash") comment = "--[^\\n]*";
  else if (cs === "slash") comment = "\\/\\/[^\\n]*|\\/\\*[\\s\\S]*?\\*\\/";
  const parts = [
    comment ? "(" + comment + ")" : "(?!)",
    "(\"\"\"[\\s\\S]*?\"\"\"|'''[\\s\\S]*?'''|\"(?:\\\\.|[^\"\\\\\\n])*\"|'(?:\\\\.|[^'\\\\\\n])*'|`(?:\\\\.|[^`\\\\])*`)",
    "(\\b\\d[\\d_]*(?:\\.\\d+)?(?:e[+-]?\\d+)?\\b|\\b0x[0-9a-fA-F]+\\b)",
    "([A-Za-z_$][\\w$]*)",
  ];
  let re;
  try { re = new RegExp(parts.join("|"), "g"); } catch { return esc(raw); }
  let out = "", last = 0, m;
  while ((m = re.exec(raw)) !== null) {
    out += esc(raw.slice(last, m.index));
    if (m[1]) out += `<span class="tok-com">${esc(m[1])}</span>`;
    else if (m[2]) out += `<span class="tok-str">${esc(m[2])}</span>`;
    else if (m[3]) out += `<span class="tok-num">${esc(m[3])}</span>`;
    else if (m[4]) {
      const w = m[4];
      if (kw.has(w)) out += `<span class="tok-kw">${esc(w)}</span>`;
      else if (raw[m.index + w.length] === "(") out += `<span class="tok-fn">${esc(w)}</span>`;
      else out += esc(w);
    } else out += esc(m[0]);
    last = m.index + m[0].length;
  }
  out += esc(raw.slice(last));
  return out;
}

const WEB_DOC = /^(html?|xhtml|vue)$/;
const STYLE_LANGS = /^(css|scss|sass|less)$/;
const SCRIPT_LANGS = /^(js|javascript|jsx|ts|typescript|tsx|mjs|coffee)$/;
const SVG_LANG = /^svg$/;

function normLang(l) { return String(l || "").replace(/^language-/, "").trim().toLowerCase(); }
function isRenderable(l) { const n = normLang(l); return WEB_DOC.test(n) || SVG_LANG.test(n); }

/** Compone un documento HTML a partir de los bloques de una respuesta. */
function composeArtifact(blocks) {
  const docs = [], svgs = [], styles = [], scripts = [];
  for (const b of blocks) {
    const l = normLang(b.lang);
    if (WEB_DOC.test(l)) docs.push(b.code);
    else if (SVG_LANG.test(l)) svgs.push(b.code);
    else if (STYLE_LANGS.test(l)) styles.push(b.code);
    else if (SCRIPT_LANGS.test(l)) scripts.push(b.code);
  }
  if (!docs.length && !svgs.length) return null;
  const css = styles.map((c) => `<style>\n${c}\n</style>`).join("\n");
  const js = scripts.map((c) => `<script>\n${c}\n</script>`).join("\n");
  const head = '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">';
  if (!docs.length) {
    return `<!doctype html><html lang="es"><head>${head}${css}</head><body>${svgs.join("\n")}\n${js}</body></html>`;
  }
  let doc = docs.join("\n");
  if (!/^\s*(<!doctype|<html)/i.test(doc)) {
    doc = `<!doctype html><html lang="es"><head>${head}</head><body>\n${doc}\n</body></html>`;
  } else if (!/<head[\s>]/i.test(doc)) {
    doc = doc.replace(/<html[^>]*>/i, (m) => m + `<head>${head}</head>`);
  }
  if (css) doc = /<\/head>/i.test(doc) ? doc.replace(/<\/head>/i, css + "\n</head>") : doc.replace(/(<body[^>]*>)/i, css + "\n$1");
  if (js) doc = /<\/body>/i.test(doc) ? doc.replace(/<\/body>/i, js + "\n</body>") : doc + "\n" + js;
  return doc;
}

function frameHtml(doc) {
  return `<div class="cb-frame"><div class="cb-frame-bar"><span>vista previa</span>` +
    `<button class="cb-mini" data-openframe="1">⤢ aparte</button>` +
    `<button class="cb-mini" data-closeframe="1">✕</button></div>` +
    `<iframe sandbox="allow-scripts allow-forms allow-modals allow-popups" srcdoc="${esc(doc)}"></iframe></div>`;
}

function codeBlockHtml(lang, code) {
  const label = esc((lang || "code").slice(0, 20));
  const view = isRenderable(lang) ? '<button class="cb-view" data-view="1">▤ ver</button>' : "";
  return `<div class="code-block" data-lang="${esc(normLang(lang))}"><div class="cb-head"><span>${label}</span>` +
         `<span class="cb-actions">${view}<button class="cb-copy" data-copy="1">copiar</button></span></div>` +
         `<pre><code>${highlightCode(code.replace(/\n+$/, ""), lang)}</code></pre>` +
         `<div class="cb-frame-slot"></div></div>`;
}

/** Barra "ver resultado" que aparece bajo un mensaje con bloques web. */
function artifactBar(blocks) {
  if (!blocks.some((b) => isRenderable(b.lang))) return "";
  const n = blocks.length;
  return `<div class="artifact-bar" data-artifacts="1">` +
    `<button class="art-view" data-viewmsg="1">▤ Ver resultado</button>` +
    `<button class="art-tab" data-opentab="1">⤢ aparte</button>` +
    `<span class="art-hint">${n} bloque${n === 1 ? "" : "s"} de código</span></div>` +
    `<div class="artifact-slot"></div>`;
}

function mdToHtml(src) {
  const blocks = [];
  src = src.replace(/```([\w.+-]*)\n?([\s\S]*?)```/g, (_m, lang, code) => {
    blocks.push({ lang, code }); return `\u0000B${blocks.length - 1}\u0000`;
  });
  let h = esc(src);
  const inline = [];
  h = h.replace(/`([^`\n]+)`/g, (_m, c) => { inline.push(c); return `\u0000I${inline.length - 1}\u0000`; });
  h = h.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
  h = h.replace(/(^|[\s(])\*([^*\n]+)\*/g, "$1<em>$2</em>");
  h = h.replace(/~~([^~\n]+)~~/g, "<del>$1</del>");
  h = h.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  h = h.replace(/(^|[\s(])(https?:\/\/[^\s<)]+)/g, '$1<a href="$2" target="_blank" rel="noopener noreferrer">$2</a>');

  const out = [];
  const lines = h.split("\n");
  let list = null;
  const closeList = () => { if (list) { out.push(`</${list}>`); list = null; } };
  for (const raw of lines) {
    const line = raw.trimEnd();
    let m;
    if (!line.trim()) { closeList(); continue; }
    if ((m = line.match(/^(#{1,3})\s+(.*)$/))) { closeList(); out.push(`<h${m[1].length}>${m[2]}</h${m[1].length}>`); continue; }
    if (/^(-{3,}|\*{3,})$/.test(line.trim())) { closeList(); out.push("<hr>"); continue; }
    if ((m = line.match(/^&gt;\s?(.*)$/))) { closeList(); out.push(`<blockquote>${m[1]}</blockquote>`); continue; }
    if ((m = line.match(/^\s*[-*+]\s+(.*)$/))) {
      if (list !== "ul") { closeList(); out.push("<ul>"); list = "ul"; }
      out.push(`<li>${m[1]}</li>`); continue;
    }
    if ((m = line.match(/^\s*\d+[.)]\s+(.*)$/))) {
      if (list !== "ol") { closeList(); out.push("<ol>"); list = "ol"; }
      out.push(`<li>${m[1]}</li>`); continue;
    }
    if (line.startsWith("|") && line.endsWith("|")) {
      if (!out._tbl) { closeList(); out.push("<table>"); out._tbl = true; }
      if (/^\|[\s:|-]+\|$/.test(line)) continue;
      const cells = line.slice(1, -1).split("|").map((c) => c.trim());
      out.push("<tr>" + cells.map((c) => `<td>${c}</td>`).join("") + "</tr>");
      continue;
    }
    if (out._tbl) { out.push("</table>"); out._tbl = false; }
    closeList();
    out.push(`<p>${line}</p>`);
  }
  if (out._tbl) out.push("</table>");
  closeList();
  h = out.join("\n");
  h = h.replace(/\u0000I(\d+)\u0000/g, (_m, i) => `<code>${esc(inline[+i])}</code>`);
  h = h.replace(/\u0000B(\d+)\u0000/g, (_m, i) => codeBlockHtml(blocks[+i].lang, blocks[+i].code));
  return h + artifactBar(blocks);
}

function highlight(text, q) {
  const safe = esc(text);
  if (!q) return safe;
  try { return safe.replace(new RegExp("(" + q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi"), "<mark>$1</mark>"); }
  catch { return safe; }
}

/* ------------------------------- sidebar -------------------------------- */
function timeLabel(ts) {
  const d = new Date(ts * 1000), now = new Date();
  if (d.toDateString() === now.toDateString()) return d.toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" });
  return d.toLocaleDateString("es", { day: "2-digit", month: "short" });
}

function renderSidebar() {
  const list = $("#chatList");
  const f = state.filter.toLowerCase();
  list.innerHTML = "";

  const chats = state.chats.filter((c) => !f || c.title.toLowerCase().includes(f) || (c.preview || "").toLowerCase().includes(f));
  const pinned = chats.filter((c) => c.pinned), rest = chats.filter((c) => !c.pinned);
  const group = (label, arr) => {
    if (!arr.length) return;
    const gl = document.createElement("div"); gl.className = "group-label"; gl.textContent = label;
    list.appendChild(gl); arr.forEach((c) => list.appendChild(chatItem(c)));
  };
  group("fijados", pinned);
  group("chats", rest);

  if (state.searchResults.length) {
    const gl = document.createElement("div"); gl.className = "group-label"; gl.textContent = t("messages_word");
    list.appendChild(gl);
    state.searchResults.forEach((r) => list.appendChild(resItem(r)));
  }
  if (!list.children.length) list.innerHTML = `<div class="group-label">sin resultados</div>`;
}

function chatItem(c) {
  const el = document.createElement("div");
  el.className = "chat-item" + (c.id === state.activeId ? " active" : "") + (c.pinned ? " pinned" : "");
  el.innerHTML = `
    <div class="ci-body">
      <div class="ci-title">${highlight(c.title, state.filter)}${c.agent ? `<span class="ci-agent">${t("mode_agent").toUpperCase()}</span>` : ""}</div>
      <div class="ci-prev">${c.preview ? esc(c.preview) : t("no_messages_yet")} · ${timeLabel(c.updated)}</div>
    </div>
    <div class="ci-actions">
      <button class="icon-btn" data-pin title="${c.pinned ? "Desfijar" : "Fijar"}">
        <svg viewBox="0 0 24 24"><path d="M12 3v9m0 0 4-4m-4 4-4-4M5 21h14" stroke="currentColor" stroke-width="1.7" fill="none"/></svg>
      </button>
      <button class="icon-btn" data-del title="Borrar">
        <svg viewBox="0 0 24 24"><path d="M5 7h14M9 7V5h6v2M7 7l1 13h8l1-13" stroke="currentColor" stroke-width="1.6" fill="none"/></svg>
      </button>
    </div>`;
  el.addEventListener("click", (e) => {
    if (e.target.closest("[data-pin]")) return togglePin(c);
    if (e.target.closest("[data-del]")) return removeChat(c);
    openChat(c.id);
  });
  return el;
}

function resItem(r) {
  const el = document.createElement("div");
  el.className = "res-item";
  el.innerHTML = `<div class="ri-role">${r.role === "user" ? "tú" : "ia"}</div>
    <div class="ri-body">
      <div class="ri-chat">${esc(r.chat_title)}</div>
      <div class="ri-text">${highlight(r.snippet, state.filter)}</div>
    </div>`;
  el.addEventListener("click", async () => {
    await openChat(r.chat_id);
    const node = $(`.msg[data-id="${r.message_id}"]`);
    if (node) { node.scrollIntoView({ behavior: "smooth", block: "center" }); node.classList.add("flash"); setTimeout(() => node.classList.remove("flash"), 1200); }
  });
  return el;
}

async function refreshChats() {
  const { chats } = await api("/api/chats");
  state.chats = chats;
  renderSidebar();
}

async function togglePin(c) {
  await api(`/api/chats/${c.id}`, { method: "PATCH", body: { pinned: c.pinned ? 0 : 1 } });
  await refreshChats();
}

async function removeChat(c) {
  if (!confirm(`¿Borrar "${c.title}"?`)) return;
  await api(`/api/chats/${c.id}`, { method: "DELETE" });
  if (state.activeId === c.id) { state.activeId = null; state.chat = null; state.messages = []; renderEmpty(); }
  await refreshChats();
  toast("Chat borrado");
}

/* ------------------------------- chats ---------------------------------- */
async function newChat(provider, model, agent) {
  const body = { provider, model };
  if (agent !== undefined) body.agent = agent;
  else if (LS.get("nexus_agentDefault", false)) body.agent = 1;
  const { chat } = await api("/api/chats", { method: "POST", body });
  await refreshChats();
  await openChat(chat.id);
  $("#input").focus();
}

async function openChat(id) {
  if (state.streaming) return toast(t("wait_response"));
  state.activeId = id;
  const data = await api(`/api/chats/${id}/messages`);
  state.chat = data.chat;
  state.messages = data.messages;
  clearAttachments();
  $("#chatTitle").value = state.chat.title;
  updateModelPill();
  updateAgentBtn();
  renderMessages();
  renderSidebar();
  if (isMobile()) $("#sidebar").classList.add("collapsed");
}

function chipsHtml() {
  const chips = (state.chips && state.chips.length) ? state.chips : [
    { title: "¿Qué puedes hacer?", body: "Explícame qué puedes hacer y cómo me ayudas en el día a día.", mode: "ambos" },
    { title: "Organizar mi día", body: "Ayúdame a organizar mi día y priorizar tareas.", mode: "ambos" },
    { title: "Escribir un script", body: "Escribe un script de bash para copia de seguridad de una carpeta.", mode: "ambos" },
  ];
  return chips.map((c) => {
    const marca = c.mode === "agente" ? '<span class="chip-mode" title="Necesita modo agente">◆</span>' : "";
    return `<button class="chip" data-q="${esc(c.body)}" data-mode="${esc(c.mode || "ambos")}">${marca}${esc(c.title)}</button>`;
  }).join("");
}

function renderEmpty() {
  $("#chatTitle").value = "NEXUS";
  $("#msgCount").textContent = "0";
  $("#statsInline").textContent = "—";
  const m = $("#messages");
  m.innerHTML = `
    <div class="empty">
      <div class="glyph">◈</div>
      <h2>${t("welcome_title")}</h2>
      <p>${t("welcome_text")}</p>
      <div class="modes">
        <div class="mode-card"><b>${t("mode_card_chat")}</b>${t("mode_card_chat_desc")}</div>
        <div class="mode-card"><b>${t("mode_card_agent")}</b>${t("mode_card_agent_desc")}</div>
      </div>
      <div class="chips">${chipsHtml()}</div>
    </div>`;
  m.querySelectorAll(".chip").forEach((c) => c.addEventListener("click", () => {
    const body = c.dataset.q || "";
    const modo = c.dataset.mode || "ambos";
    if (modo === "agente" && state.chat && !state.chat.agent) {
      toggleAgent();
      toast(t("chip_agent_on"));
    }
    // se rellena el campo para poder editarlo antes de enviar
    const inp = $("#input");
    inp.value = body;
    autoGrow();
    inp.focus();
    inp.setSelectionRange(inp.value.length, inp.value.length);
    toast(t("chip_ready"), 1600);
  }));
  updateModelPill();
  updateAgentBtn();
}

function renderMessages() {
  const box = $("#messages");
  box.innerHTML = "";
  if (!state.messages.length) return renderEmpty();
  state.messages.forEach((m) => box.appendChild(msgEl(m)));
  scrollBottom(true);
  updateCount();
  updateStatsInline();
}

function artifactsBarHtml(paths) {
  if (!paths || !paths.length) return "";
  const files = paths.map((p) => `<button class="ma-file" data-artifact="${esc(p)}" title="${esc(p)}">${esc(String(p).split("/").pop())}</button>`).join("");
  return `<div class="msg-artifacts"><span class="ma-tag">✎ tocado por el agente</span>${files}</div>`;
}

function updateArtifactsBar(el, paths) {
  if (!paths || !paths.length) return;
  const html = artifactsBarHtml(paths);
  const bar = el.querySelector(".msg-artifacts");
  if (bar) bar.outerHTML = html;
  else {
    const bubble = el.querySelector(".bubble");
    const actions = bubble.querySelector(".msg-actions");
    if (actions) actions.insertAdjacentHTML("beforebegin", html);
    else bubble.insertAdjacentHTML("beforeend", html);
  }
}

function autoPreviewFile(path) {
  if (!LS.get("nexus_autoPreview", true)) return;
  if (typeof window.previewProjectFile === "function") window.previewProjectFile(path);
}

/* ------------------- vista previa lateral (estilo artifacts) -------------- */
const SPLIT_IMG = /\.(png|jpe?g|gif|webp|svg|bmp|avif|ico)$/i;
const SPLIT_WEB = /\.(html?|xhtml|svg)$/i;
const SP = { mode: null, title: "", path: null, doc: "", text: "", live: false, timer: null, anim: null };

function splitEnabled() { return LS.get("nexus_splitView", true); }
function splitOpen() { const p = $("#splitPane"); return !!p && !p.classList.contains("hidden"); }
function stopSplitAnim() { if (SP.anim) { clearInterval(SP.anim); SP.anim = null; } }

function openSplit(opts) {
  const pane = $("#splitPane");
  if (!pane) return;
  pane.classList.remove("hidden");
  document.body.classList.add("split-open");
  Object.assign(SP, { mode: opts.mode || "doc", title: opts.title || "vista previa", path: opts.path || null });
  if (opts.doc != null) SP.doc = opts.doc;
  if (opts.text != null) SP.text = opts.text;
  $("#spTitle").textContent = SP.title;
  $("#spKind").textContent = SP.mode === "code" ? "⌘" : SP.mode === "img" ? "🖼" : "▤";
  setSplitLive(!!opts.live);
  paintSplit();
}

function closeSplit() {
  stopSplitAnim();
  if (SP.timer) { clearTimeout(SP.timer); SP.timer = null; }
  const pane = $("#splitPane");
  if (pane) pane.classList.add("hidden");
  document.body.classList.remove("split-open");
  setSplitLive(false);
}

function setSplitLive(on) {
  SP.live = !!on;
  const tag = $("#spLive");
  if (tag) tag.classList.toggle("hidden", !on);
}

/** Pinta el contenido actual del panel segun su modo. */
function paintSplit() {
  const body = $("#spBody");
  if (!body) return;
  if (SP.mode === "doc") {
    body.innerHTML = `<iframe sandbox="allow-scripts allow-forms allow-modals allow-popups" srcdoc="${esc(SP.doc || "")}"></iframe>`;
  } else if (SP.mode === "code") {
    body.innerHTML = `<pre class="sp-code">${esc(SP.text || "")}<span class="sp-cursor"></span></pre>`;
    const pre = body.querySelector("pre"); if (pre) pre.scrollTop = pre.scrollHeight;
  } else if (SP.mode === "img") {
    body.innerHTML = `<img class="sp-img" src="/preview${SP.path}" alt="">`;
  } else {
    body.innerHTML = `<iframe src="/preview${SP.path}"></iframe>`;
  }
}

/** Documento que se va escribiendo (chat en streaming o texto del agente). */
function liveSplitDoc(doc, title) {
  if (!splitEnabled() || !doc) return false;
  if (SP.mode !== "doc" || !splitOpen()) {
    openSplit({ mode: "doc", title: title || "vista previa", live: true });
    SP.doc = doc;
    paintSplit();
    return true;
  }
  SP.doc = doc;
  if (SP.timer) return true;
  SP.timer = setTimeout(() => {
    SP.timer = null;
    if (SP.mode === "doc" && splitOpen()) paintSplit();
  }, 550);
  return true;
}

/** Bloques ``` del markdown, incluido el que aun esta abierto (streaming). */
function blocksFromMarkdown(src) {
  const out = [];
  const re = /```([\w.+-]*)\n?([\s\S]*?)```/g;
  let m, last = 0;
  while ((m = re.exec(src))) { out.push({ lang: m[1], code: m[2] }); last = re.lastIndex; }
  const tail = src.slice(last);
  const open = tail.indexOf("```");
  if (open >= 0) {
    const head = tail.slice(open + 3);
    const nl = head.indexOf("\n");
    if (nl >= 0) out.push({ lang: head.slice(0, nl), code: head.slice(nl + 1) });
  }
  return out;
}

function liveSplitFromMarkdown(src) {
  if (!splitEnabled() || !src) return;
  const doc = composeArtifact(blocksFromMarkdown(src));
  if (doc) liveSplitDoc(doc, "código en vivo");
}

/** Escribe el contenido "al vuelo" en el panel (efecto de tecleo). */
function animateSplit(kind, text, title, lang) {
  stopSplitAnim();
  const mode = kind === "doc" ? "doc" : "code";
  openSplit({ mode, title, live: true });
  SP.text = ""; SP.doc = "";
  const lg = (lang || "html").replace(/^\./, "");
  const step = Math.max(60, Math.ceil(text.length / 24));
  let i = 0;
  SP.anim = setInterval(() => {
    i += step;
    const slice = text.slice(0, i);
    if (mode === "doc") SP.doc = composeArtifact([{ lang: lg, code: slice }]) || slice;
    else SP.text = slice;
    paintSplit();
    if (i >= text.length) { stopSplitAnim(); if (mode === "code") SP.text = text; else SP.doc = composeArtifact([{ lang: lg, code: text }]) || text; paintSplit(); }
  }, 55);
}

/** Evento del agente: archivo escrito. */
function handleSplitArtifact(d) {
  const path = d.path;
  if (!splitEnabled()) { autoPreviewFile(path); return; }
  const name = String(path).split("/").pop();
  const ext = (String(path).match(/\.[^./]+$/) || [""])[0].toLowerCase();
  if (d.content && SPLIT_WEB.test(ext) && !d.final) return void animateSplit("doc", d.content, name, ext);
  if (d.content && !d.final && ext !== ".svg") return void animateSplit("code", d.content, name, ext);
  setSplitLive(false);
  if (SPLIT_IMG.test(ext)) openSplit({ mode: "img", path, title: name });
  else if (SPLIT_WEB.test(ext)) openSplit({ mode: "file", path, title: name });
  else {
    if (SP.path !== path) SP.text = "";
    openSplit({ mode: "code", title: name, path });
    if (!SP.text) fetch("/preview" + path).then((r) => r.text()).then((txt) => { SP.text = txt.slice(0, 400000); paintSplit(); }).catch(() => {});
  }
  if (LS.get("nexus_autoPreview", false)) autoPreviewFile(path);
}

function initSplit() {
  const pane = $("#splitPane");
  if (!pane) return;
  const w = LS.get("nexus_splitW", 0);
  if (w) document.body.style.setProperty("--split-w", Math.round(w) + "px");
  $("#spClose").addEventListener("click", closeSplit);
  $("#spReload").addEventListener("click", () => {
    if (SP.mode === "doc") { const d = SP.doc; SP.doc = ""; paintSplit(); SP.doc = d; paintSplit(); }
    else paintSplit();
  });
  $("#spTab").addEventListener("click", () => {
    if (SP.mode === "doc" && SP.doc) return openDocInTab(SP.doc);
    if (SP.path) window.open("/preview" + SP.path, "_blank");
  });
  $("#spDock").addEventListener("click", () => { if (SP.path && window.previewProjectFile) window.previewProjectFile(SP.path); });
  const grip = $("#splitGrip");
  let dragging = false;
  grip.addEventListener("pointerdown", (e) => { dragging = true; try { grip.setPointerCapture(e.pointerId); } catch {} e.preventDefault(); });
  grip.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const w2 = Math.min(Math.max(window.innerWidth - e.clientX, 260), window.innerWidth * 0.72);
    document.body.style.setProperty("--split-w", Math.round(w2) + "px");
    LS.set("nexus_splitW", Math.round(w2));
  });
  ["pointerup", "pointercancel"].forEach((ev) => grip.addEventListener(ev, () => { dragging = false; }));
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape" || !splitOpen()) return;
    if ($("#settingsModal").classList.contains("hidden") && $("#palette").classList.contains("hidden")) closeSplit();
  });
}

function msgEl(m) {
  const wrap = document.createElement("div");
  wrap.className = "msg " + m.role + (m.meta && m.meta.error ? " error" : "");
  wrap.dataset.id = m.id;
  const isUser = m.role === "user";
  const mdl = m.model ? `<span class="mdl">${esc(m.model)}</span>` : "";
  const badge = (m.meta && m.meta.agent) ? `<span class="badge-agent">${t("mode_agent").toUpperCase()}</span>` : "";
  wrap.innerHTML = `
    <div class="avatar">${isUser ? "❯" : "◈"}</div>
    <div class="bubble">
      <div class="role">${isUser ? t("role_user") : t("role_assistant")} ${mdl} ${badge}</div>
      <div class="content">${isUser ? esc(m.content) : mdToHtml(m.content)}</div>
      ${attachmentsHtml(m.meta && m.meta.files)}
      ${metaLine(m)}
      ${artifactsBarHtml(m.meta && m.meta.artifacts)}
      <div class="msg-actions">
        <button data-act="copy">${t("act_copy")}</button>
        ${isUser ? `<button data-act="edit">${t("act_edit")}</button>` : `<button data-act="regen">${t("act_regen")}</button><button data-act="read">${t("act_read")}</button>`}
      </div>
    </div>`;
  wrap.querySelector('[data-act="copy"]').addEventListener("click", () => { navigator.clipboard.writeText(m.content); toast(t("copied")); });
  const regen = wrap.querySelector('[data-act="regen"]'); if (regen) regen.addEventListener("click", () => startTurn({ regenerate: true }));
  const read = wrap.querySelector('[data-act="read"]'); if (read) read.addEventListener("click", () => readAloud(m.content));
  const edit = wrap.querySelector('[data-act="edit"]'); if (edit) edit.addEventListener("click", () => editMessage(m, wrap));
  return wrap;
}

function editMessage(m, wrap) {
  if (state.streaming) return toast(t("wait_response"));
  const contentEl = wrap.querySelector(".content");
  const html = `<textarea class="edit-box" rows="3">${esc(m.content)}</textarea>
    <div class="edit-actions"><button class="mini-btn" data-e="save">Guardar y reenviar</button>
    <button class="mini-btn" data-e="cancel">Cancelar</button></div>`;
  const holder = document.createElement("div");
  holder.innerHTML = html;
  contentEl.replaceWith(holder);
  const ta = holder.querySelector(".edit-box"); ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length);
  holder.querySelector('[data-e="cancel"]').addEventListener("click", () => renderMessages());
  holder.querySelector('[data-e="save"]').addEventListener("click", () => {
    const text = ta.value.trim();
    if (!text) return;
    startTurn({ content: text, editId: m.id });
  });
}

function metaLine(m) {
  if (!m.meta) return "";
  const parts = [];
  if (m.meta.usage) {
    const u = m.meta.usage;
    const tot = u.total_tokens || (u.prompt_tokens || 0) + (u.completion_tokens || 0);
    if (tot) parts.push(`${tot} ${t("meta_tokens")}`);
    if (u.completion_tokens) parts.push(`${u.completion_tokens} ${t("meta_out")}`);
  }
  if (m.meta.latency_ms) parts.push(`${(m.meta.latency_ms / 1000).toFixed(1)}s`);
  if (m.meta.error) parts.push("↯ " + esc(m.meta.error));
  if (m.meta.interrupted) parts.push("⏹ " + t("meta_interrupted"));
  return parts.length ? `<div class="msg-meta">${parts.join(" · ")}</div>` : "";
}

function updateCount() { $("#msgCount").textContent = state.messages.length; }

function chatTokens() {
  let tin = 0, tout = 0;
  state.messages.forEach((m) => {
    const u = (m.meta && m.meta.usage) || {};
    tin += u.prompt_tokens || 0; tout += u.completion_tokens || 0;
  });
  return { tin, tout };
}
function updateStatsInline() {
  const { tin, tout } = chatTokens();
  $("#statsInline").textContent = (tin + tout) ? `${tin}↓ ${tout}↑ tok` : "—";
  $("#tokenHint").textContent = `${tin + tout} tok`;
}

/* ------------------------------ composer -------------------------------- */
function autoGrow() { const el = $("#input"); el.style.height = "auto"; el.style.height = Math.min(el.scrollHeight, 220) + "px"; }
function scrollBottom(instant) { const box = $("#messages"); box.scrollTo({ top: box.scrollHeight, behavior: instant ? "auto" : "smooth" }); }

/* --------------------------- adjuntos ----------------------------------- */
function peso(bytes) {
  const b = Number(bytes) || 0;
  if (b < 1024) return b + " B";
  if (b < 1024 * 1024) return (b / 1024).toFixed(1) + " KB";
  return (b / (1024 * 1024)).toFixed(1) + " MB";
}

// fichas de los adjuntos de un mensaje: imagenes con miniatura, documentos con su nombre
function attachmentsHtml(files) {
  const lista = (files || []).filter(Boolean);
  if (!lista.length) return "";
  const piezas = lista.map((f) => {
    const src = f.url || (f.file ? "/api/files/" + encodeURIComponent(f.file) : "");
    if (f.img && src) {
      return `<a class="att-img" href="${esc(src)}" target="_blank" title="${esc(f.name)}">
        <img src="${esc(src)}" alt="${esc(f.name)}" loading="lazy"></a>`;
    }
    const enlace = f.file ? `/api/files/${encodeURIComponent(f.file)}` : (f.url || "#");
    return `<a class="att-file" href="${esc(enlace)}" download="${esc(f.name)}" title="${esc(f.name)}">
        <span class="af-ico">📄</span><span class="af-name">${esc(f.name)}</span>
        <span class="af-size">${peso(f.size)}</span></a>`;
  }).join("");
  return `<div class="att-block">${piezas}</div>`;
}
function clearAttachments() { state.attachments = []; renderAttachChips(); }

function renderAttachChips() {
  const wrap = $("#attachChips");
  if (!state.attachments.length) { wrap.classList.add("hidden"); wrap.innerHTML = ""; return; }
  wrap.classList.remove("hidden");
  wrap.innerHTML = "";
  state.attachments.forEach((a, i) => {
    const chip = document.createElement("div");
    chip.className = "chip-file";
    chip.innerHTML = `${a.img ? `<img src="data:${a.mime};base64,${a.data}">` : "📄"} ${esc(a.name)}
      <span class="cf-x" title="Quitar">✕</span>`;
    chip.querySelector(".cf-x").addEventListener("click", () => { state.attachments.splice(i, 1); renderAttachChips(); });
    wrap.appendChild(chip);
  });
}

function addFiles(files) {
  Array.from(files).forEach((file) => {
    const reader = new FileReader();
    reader.onload = () => {
      const res = String(reader.result);
      const isImg = file.type.startsWith("image/");
      const data = isImg ? res.split(",")[1] : btoa(unescape(encodeURIComponent(res)));
      state.attachments.push({ name: file.name, mime: file.type || "text/plain", data, img: isImg });
      renderAttachChips();
    };
    if (file.type.startsWith("image/")) reader.readAsDataURL(file);
    else reader.readAsText(file);
  });
}

// junta lo que ya teniamos (miniatura local) con la ficha del servidor
function relink(locales, servidor) {
  return (servidor || []).map((f, i) => {
    const loc = (locales || [])[i] || {};
    return Object.assign({}, f, loc.url && f.img ? { url: loc.url } : {});
  });
}

// ficha local (para pintarla al momento); el servidor devuelve la definitiva
function vistazo(attachments) {
  return (attachments || []).map((a) => ({
    name: a.name, mime: a.mime, img: !!a.img, size: Math.round(a.data.length * 0.75),
    url: `data:${a.mime || "application/octet-stream"};base64,${a.data}`,
  }));
}

/* --------------------------- pedir al modelo ---------------------------- */
async function startTurn({ content = "", editId = null, regenerate = false }) {
  if (state.streaming) return;
  if (!state.activeId || !state.chat) {
    await newChat(state.defaults.provider, state.defaults.model);
    if (!state.activeId || !state.chat) return;
  }
  if (!regenerate && !editId && !content.trim()) return;

  const chatId = state.activeId;
  const provider = state.chat.provider, model = state.chat.model;
  const agent = state.chat.agent ? 1 : 0;
  const attachments = (editId || regenerate) ? [] : state.attachments.slice();
  const box = $("#messages");

  let userMsg = null;
  if (editId) {
    const idx = state.messages.findIndex((m) => m.id === editId);
    if (idx >= 0) state.messages.splice(idx);
    box.innerHTML = "";
    state.messages.forEach((m) => box.appendChild(msgEl(m)));
    userMsg = { id: "tmp_u", role: "user", content, model, meta: { files: vistazo(attachments) } };
    state.messages.push(userMsg); box.appendChild(msgEl(userMsg));
  } else if (!regenerate) {
    if (box.querySelector(".empty")) box.innerHTML = "";
    userMsg = { id: "tmp_u", role: "user", content, model, meta: { files: vistazo(attachments) } };
    state.messages.push(userMsg); box.appendChild(msgEl(userMsg));
  } else {
    const last = [...state.messages].reverse().find((m) => m.role === "assistant");
    if (last) { state.messages.splice(state.messages.indexOf(last), 1); const d = box.querySelector(`.msg[data-id="${last.id}"]`); if (d) d.remove(); }
  }
  if (box.querySelector(".empty")) box.innerHTML = "";
  updateCount(); scrollBottom();
  $("#input").value = ""; autoGrow(); clearAttachments();
  setStreaming(true);

  const asst = { id: "tmp_a", role: "assistant", content: "", model, meta: { agent: !!agent } };
  state.messages.push(asst);
  const el = msgEl(asst); box.appendChild(el);
  const contentEl = el.querySelector(".content");
  contentEl.innerHTML = '<span class="cursor"></span>';
  scrollBottom();

  let acc = "", raf = null;
  state.abort = new AbortController();
  const body = { chat_id: chatId, provider, model, agent };
  if (editId) body.edit_message_id = editId;
  else if (regenerate) body.regenerate = true;
  else { body.content = content; if (attachments.length) body.attachments = attachments; }

  try {
    await streamRequest(body, state.abort.signal, {
      onMeta: (d) => {
        asst.id = d.assistant_message_id; el.dataset.id = asst.id;
        if (userMsg) {
          userMsg.id = d.user_message_id;
          if (d.files && d.files.length) {
            userMsg.meta = Object.assign({}, userMsg.meta, { files: relink(userMsg.meta && userMsg.meta.files, d.files) });
          }
        }
      },
      onDelta: (piece) => {
        acc += piece;
        if (!raf) raf = requestAnimationFrame(() => {
          contentEl.innerHTML = mdToHtml(acc) + '<span class="cursor"></span>';
          liveSplitFromMarkdown(acc);
          raf = null;
        });
      },
      onDone: (d) => { asst.meta = Object.assign({ agent: !!agent }, d.meta || {}); },
      onSession: (d) => { if (state.chat) state.chat.agent_session = d.session_id; },
      onArtifact: (d) => {
        if (d.path && !(asst.meta.artifacts || []).includes(d.path)) {
          asst.meta.artifacts = (asst.meta.artifacts || []).concat([d.path]);
          updateArtifactsBar(el, asst.meta.artifacts);
        }
        handleSplitArtifact(d);
      },
      onError: (msg) => { asst.meta = { error: msg, agent: !!agent }; },
    });
  } catch (e) {
    asst.meta = e.name === "AbortError" ? { interrupted: true, agent: !!agent } : { error: e.message, agent: !!agent };
  }

  asst.content = acc;
  contentEl.innerHTML = mdToHtml(acc) || '<span style="color:var(--txt-faint)">(sin contenido)</span>';
  if (LS.get("nexus_autoView", true) && !splitEnabled()) {
    const vb = contentEl.querySelector(".artifact-bar [data-viewmsg]");
    if (vb && !contentEl.querySelector(".artifact-slot .cb-frame")) vb.click();
  }
  setSplitLive(false);
  const ml = el.querySelector(".msg-meta"); if (ml) ml.remove();
  el.insertAdjacentHTML("beforeend", metaLine(asst));
  el.className = "msg assistant" + (asst.meta.error ? " error" : "");
  setStreaming(false); scrollBottom(); updateCount(); updateStatsInline(); refreshChats();
  if (LS.get("nexus_autoRead", false) && acc) readAloud(acc);
  notifyDone(asst);
  if (state.chat && state.chat.title === "Nuevo chat" && userMsg) {
    state.chat.title = content.slice(0, 48) || "Nuevo chat";
    $("#chatTitle").value = state.chat.title;
  }
}

function setStreaming(on) {
  state.streaming = on;
  $("#sendBtn").classList.toggle("hidden", on);
  $("#stopBtn").classList.toggle("hidden", !on);
  $("#hintModel").textContent = state.chat ? `${state.chat.provider} · ${state.chat.model}` : "—";
  $("#modeHint").textContent = state.chat && state.chat.agent ? t("mode_agent_hint") : "";
}

/* --------------------------- streaming (SSE) ---------------------------- */
async function streamRequest(body, signal, cb) {
  const res = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal });
  if (!res.ok || !res.body) throw new Error("HTTP " + res.status);
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i;
    while ((i = buf.indexOf("\n\n")) >= 0) {
      const block = buf.slice(0, i); buf = buf.slice(i + 2);
      let ev = "message", data = "";
      for (const ln of block.split("\n")) {
        if (ln.startsWith("event:")) ev = ln.slice(6).trim();
        else if (ln.startsWith("data:")) data += ln.slice(5).trim();
      }
      if (!data) continue;
      let obj; try { obj = JSON.parse(data); } catch { continue; }
      if (ev === "meta") cb.onMeta(obj);
      else if (ev === "delta") cb.onDelta(obj.text);
      else if (ev === "session") { if (cb.onSession) cb.onSession(obj); }
      else if (ev === "artifact") { if (cb.onArtifact) cb.onArtifact(obj); }
      else if (ev === "done") cb.onDone(obj);
      else if (ev === "error") cb.onError(obj.message);
    }
  }
}

/* ----------------------------- selector modelo -------------------------- */
function updateModelPill() {
  $("#modelLabel").textContent = state.chat ? state.chat.model : (state.defaults.model || t("model_word"));
  $("#hintModel").textContent = state.chat ? `${state.chat.provider} · ${state.chat.model}` : "—";
}

function openModelPop() {
  const pop = $("#modelPop"), r = $("#modelBtn").getBoundingClientRect();
  pop.style.top = r.bottom + 8 + "px";
  pop.style.left = Math.max(10, r.right - 380) + "px";
  pop.classList.remove("hidden");
  renderModelList("");
  $("#modelSearch").value = ""; $("#modelSearch").focus();
}

function renderModelList(q) {
  const wrap = $("#modelList");
  wrap.innerHTML = "";
  q = q.toLowerCase();
  const current = state.chat ? `${state.chat.provider}::${state.chat.model}` : "";
  const favOnly = $("#favOnly").checked;
  for (const [pid, p] of Object.entries(state.providers)) {
    let models = p.models.filter((m) => !q || m.toLowerCase().includes(q));
    if (favOnly) models = models.filter((m) => state.favorites.includes(`${pid}::${m}`));
    if (!models.length) continue;
    const g = document.createElement("div"); g.className = "pop-group"; g.textContent = p.label; wrap.appendChild(g);
    models.slice(0, 400).forEach((m) => {
      const key = `${pid}::${m}`;
      const it = document.createElement("div");
      it.className = "pop-item" + (key === current ? " sel" : "");
      it.innerHTML = `<span>${esc(m)}</span><span class="pi-star ${state.favorites.includes(key) ? "on" : ""}" title="Favorito">★</span>`;
      it.querySelector(".pi-star").addEventListener("click", (e) => { e.stopPropagation(); toggleFav(key); renderModelList($("#modelSearch").value); });
      it.addEventListener("click", () => selectModel(pid, m));
      wrap.appendChild(it);
    });
  }
  if (!wrap.children.length) wrap.innerHTML = `<div class="pop-group">sin resultados</div>`;
}

function toggleFav(key) {
  const i = state.favorites.indexOf(key);
  if (i >= 0) state.favorites.splice(i, 1); else state.favorites.push(key);
  LS.set("nexus_favs", state.favorites);
}

async function selectModel(pid, model) {
  $("#modelPop").classList.add("hidden");
  if (!state.activeId) {
    state.defaults = { provider: pid, model }; state.chat = Object.assign({}, state.chat, { provider: pid, model });
    LS.set("nexus_default", state.defaults); updateModelPill(); toast(`Modelo: ${model}`); return;
  }
  await api(`/api/chats/${state.activeId}`, { method: "PATCH", body: { provider: pid, model } });
  state.chat.provider = pid; state.chat.model = model;
  updateModelPill(); toast(`Modelo: ${model}`); refreshChats();
}

/* ------------------------------- agente --------------------------------- */
function updateAgentBtn() {
  const on = state.chat && state.chat.agent;
  $("#agentBtn").classList.toggle("on", !!on);
  $("#agentLabel").textContent = on ? t("mode_agent") : t("mode_chat");
  $("#modeHint").textContent = on ? t("mode_agent_hint") : "";
}

async function toggleAgent() {
  if (!state.activeId) { await newChat(state.defaults.provider, state.defaults.model); }
  if (!state.activeId) return;
  const on = state.chat.agent ? 0 : 1;
  await api(`/api/chats/${state.activeId}`, { method: "PATCH", body: { agent: on } });
  state.chat.agent = on; updateAgentBtn(); refreshChats();
  toast(on ? "Modo agente activado — usa herramientas reales" : "Modo chat");
}

/* ------------------------------- plantillas ----------------------------- */
async function loadPresets() { state.presets = (await api("/api/presets")).presets; }

function openPresetPop() {
  const pop = $("#presetPop"), r = $("#presetBtn").getBoundingClientRect();
  pop.style.top = r.bottom + 8 + "px";
  pop.style.left = Math.max(10, r.right - 380) + "px";
  pop.classList.toggle("hidden");
  renderPresets();
}

function renderPresets() {
  const wrap = $("#presetList");
  wrap.innerHTML = "";
  if (!state.presets.length) {
    wrap.innerHTML = `<div class="pop-group">sin plantillas</div>` +
      `<div class="pop-foot"><button class="mini-btn" id="seedPresets">Cargar los prompts de ejemplo</button></div>`;
    const b = wrap.querySelector("#seedPresets");
    if (b) b.addEventListener("click", () => restoreExamplePrompts());
    return;
  }
  let catActual = null;
  state.presets.forEach((p) => {
    if ((p.cat || "") !== catActual) {
      catActual = p.cat || "";
      if (catActual) {
        const g = document.createElement("div");
        g.className = "pop-group";
        g.textContent = catActual;
        wrap.appendChild(g);
      }
    }
    const it = document.createElement("div");
    it.className = "preset-item";
    it.innerHTML = `<span class="pt-del" title="Borrar">✕</span><div class="pt-title">${esc(p.title)}</div><div class="pt-body">${esc(p.body)}</div>`;
    it.querySelector(".pt-del").addEventListener("click", async (e) => { e.stopPropagation(); await api(`/api/presets/${p.id}`, { method: "DELETE" }); await loadPresets(); renderPresets(); });
    it.addEventListener("click", () => {
      const inp = $("#input");
      inp.value = p.body; autoGrow(); inp.focus();
      $("#presetPop").classList.add("hidden");
    });
    wrap.appendChild(it);
  });
}

async function restoreExamplePrompts() {
  try {
    const r = await api("/api/prompts/seed", { method: "POST" });
    await loadPresets();
    renderPresets();
    toast(r.added ? t("examples_added", { n: r.added }) : t("examples_all"));
  } catch (e) { toast(t("install_failed", { error: e.message })); }
}

async function savePreset() {
  const body = $("#input").value.trim();
  if (!body) return toast(t("write_something"));
  const title = prompt("Nombre de la plantilla:", body.slice(0, 32));
  if (!title) return;
  await api("/api/presets", { method: "POST", body: { title, body } });
  await loadPresets(); renderPresets(); toast(t("preset_saved"));
}

/* -------------------------------- menú ---------------------------------- */
function openMore() {
  const pop = $("#morePop"), r = $("#menuMoreBtn").getBoundingClientRect();
  pop.style.top = r.bottom + 8 + "px";
  pop.style.left = r.right - 240 + "px";
  pop.classList.toggle("hidden");
}

async function moreAction(act) {
  $("#morePop").classList.add("hidden");
  if (!["exportAll", "presets"].includes(act)) { if (!state.activeId) return toast(t("open_chat_first")); }
  const id = state.activeId;
  if (act === "presets") { openPresetPop(); }
  else if (act === "rename") {
    const t = prompt("Nuevo título:", state.chat.title);
    if (t) { await api(`/api/chats/${id}`, { method: "PATCH", body: { title: t } }); state.chat.title = t; $("#chatTitle").value = t; await refreshChats(); }
  } else if (act === "duplicate") {
    const { chat } = await api(`/api/chats/${id}/duplicate`, { method: "POST" });
    await refreshChats(); await openChat(chat.id); toast("Chat duplicado");
  } else if (act === "system") {
    openSettings();
  } else if (act === "stats") {
    const s = await api(`/api/chats/${id}/stats`);
    toast(`${s.messages} mensajes · ${s.tokens_in}↓ ${s.tokens_out}↑ tok · ${Object.keys(s.models).length} modelos`, 4000);
  } else if (act === "read") {
    const last = [...state.messages].reverse().find((m) => m.role === "assistant");
    if (last) readAloud(last.content); else toast("Sin respuesta que leer");
  } else if (act === "export") {
    const md = `# ${state.chat.title}\n\n` + state.messages.map((m) => `**${m.role}** (${m.model || "-"}):\n\n${m.content}\n`).join("\n---\n\n");
    download(new Blob([md], { type: "text/markdown" }), state.chat.title.replace(/[^\w\-]+/g, "_") + ".md");
    toast("Exportado");
  } else if (act === "clear") {
    if (confirm(t("confirm_clear"))) { await api(`/api/chats/${id}/clear`, { method: "POST" }); state.messages = []; renderMessages(); refreshChats(); }
  } else if (act === "delete") {
    removeChat(state.chat);
  }
}

function download(blob, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
}

/* ------------------------------- voz ------------------------------------ */
let currentVoice = null;
function pickVoice() {
  const vs = window.speechSynthesis ? speechSynthesis.getVoices() : [];
  currentVoice = vs.find((v) => /^es/i.test(v.lang)) || vs[0] || null;
}
if (window.speechSynthesis) { pickVoice(); speechSynthesis.onvoiceschanged = pickVoice; }

function readAloud(text) {
  if (!window.speechSynthesis) return toast("Tu navegador no soporta voz");
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text.replace(/```[\s\S]*?```/g, " bloque de código ").slice(0, 4000));
  u.lang = "es-ES"; if (currentVoice) u.voice = currentVoice;
  speechSynthesis.speak(u);
}

let recognition = null;
function toggleMic() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return toast("Dictado no disponible en este navegador");
  const btn = $("#micBtn");
  if (recognition) { recognition.stop(); recognition = null; btn.classList.remove("rec"); return; }
  recognition = new SR();
  recognition.lang = "es-ES"; recognition.interimResults = true; recognition.continuous = true;
  const base = $("#input").value;
  recognition.onresult = (e) => {
    let txt = "";
    for (let i = e.resultIndex; i < e.results.length; i++) txt += e.results[i][0].transcript;
    $("#input").value = base + txt; autoGrow();
  };
  recognition.onend = () => { recognition = null; btn.classList.remove("rec"); };
  recognition.onerror = () => { recognition = null; btn.classList.remove("rec"); };
  recognition.start(); btn.classList.add("rec");
  toast("Dictado activo — habla");
}

/* ------------------------- notificación y sonido ------------------------ */
function notifyDone(asst) {
  if (document.hidden && $("#notifyChk").checked && window.Notification && Notification.permission === "granted") {
    try { new Notification("NEXUS", { body: (asst.content || "Respuesta lista").slice(0, 90), icon: "/assets/icon.svg" }); } catch {}
  }
  if ($("#soundChk").checked) beep();
}

let audioCtx = null;
function beep() {
  try {
    audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
    const o = audioCtx.createOscillator(), g = audioCtx.createGain();
    o.type = "sine"; o.frequency.value = 660;
    g.gain.setValueAtTime(0.0001, audioCtx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.06, audioCtx.currentTime + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.22);
    o.connect(g); g.connect(audioCtx.destination); o.start(); o.stop(audioCtx.currentTime + 0.24);
  } catch {}
}

/* --------------------------- paleta de comandos ------------------------- */
function paletteItems() {
  const items = [
    { ico: "＋", label: t("new_chat"), kind: "acción", run: () => newChat(state.defaults.provider, state.defaults.model) },
    { ico: "◈", label: t("help_change_model"), kind: "acción", run: openModelPop },
    { ico: "◆", label: t("mode_agent"), kind: "acción", run: toggleAgent },
    { ico: "▤", label: t("presets_title"), kind: "acción", run: openPresetPop },
    { ico: "◫", label: t("palette_split_toggle"), kind: "acción", run: () => {
        const on = !LS.get("nexus_splitView", true); LS.set("nexus_splitView", on);
        if (!on) closeSplit();
        toast(t("palette_split_toggle") + (on ? " ✓" : " ✗"));
      } },
    { ico: "◫", label: t("palette_split_close"), kind: "acción", run: closeSplit },
    { ico: "⚙", label: t("settings"), kind: "acción", run: openSettings },
    { ico: "🌐", label: t("language"), kind: "acción", run: openLangPop },
    { ico: "🔑", label: t("palette_providers"), kind: "acción", run: () => openSetup("manage") },
    { ico: "🧩", label: t("local_title"), kind: "acción", run: () => openLocal() },
    { ico: "★", label: t("palette_only_favs"), kind: "acción", run: () => { $("#favOnly").checked = true; openModelPop(); } },
    { ico: "⇩", label: t("act_export"), kind: "acción", run: () => moreAction("export") },
    { ico: "⇪", label: t("palette_export_all"), kind: "acción", run: exportAll },
    { ico: "⇧", label: t("palette_import"), kind: "acción", run: () => $("#importFile").click() },
    { ico: "∑", label: t("act_stats"), kind: "acción", run: () => moreAction("stats") },
    { ico: "🔊", label: t("act_read"), kind: "acción", run: () => moreAction("read") },
    { ico: "？", label: t("palette_help"), kind: "ayuda", run: openHelp },
    { ico: "▦", label: t("palette_panel_summary"), kind: "panel", run: () => openPanel("resumen") },
    { ico: "▶", label: t("palette_panel_tasks"), kind: "panel", run: () => openPanel("tareas") },
    { ico: "▤", label: t("palette_panel_project"), kind: "panel", run: () => openPanel("proyecto") },
    { ico: "≡", label: t("palette_panel_log"), kind: "panel", run: () => openPanel("registro") },
    { ico: "⇄", label: t("palette_panel_lan"), kind: "panel", run: () => openPanel("red") },
    { ico: "＋", label: t("palette_new_agent"), kind: "acción", run: () => newChat(state.defaults.provider, state.defaults.model, 1) },
  ];
  ["cyan", "violet", "emerald", "amber", "rose", "ice"].forEach((a) => items.push({ ico: "◐", label: t("palette_theme", { name: a }), kind: "tema", run: () => applyAccent(a) }));
  state.chats.slice(0, 40).forEach((c) => items.push({ ico: "❯", label: c.title, kind: "chat", run: () => openChat(c.id) }));
  return items;
}

let paletteSel = 0, paletteFiltered = [];
function openPalette() {
  $("#palette").classList.remove("hidden");
  $("#paletteInput").value = ""; paletteSel = 0;
  renderPalette("");
  $("#paletteInput").focus();
}
function renderPalette(q) {
  const list = $("#paletteList");
  const items = paletteItems();
  q = q.toLowerCase();
  paletteFiltered = items.filter((i) => !q || i.label.toLowerCase().includes(q));
  list.innerHTML = "";
  paletteFiltered.slice(0, 60).forEach((it, i) => {
    const el = document.createElement("div");
    el.className = "palette-item" + (i === paletteSel ? " sel" : "");
    el.innerHTML = `<span class="pi-ico">${it.ico}</span><span>${esc(it.label)}</span><span class="pi-kind">${it.kind}</span>`;
    el.addEventListener("click", () => runPalette(i));
    list.appendChild(el);
  });
  if (!paletteFiltered.length) list.innerHTML = `<div class="palette-item">sin resultados</div>`;
}
function runPalette(i) {
  const it = paletteFiltered[i];
  $("#palette").classList.add("hidden");
  if (it) setTimeout(it.run, 0);
}

/* ------------------------------- ajustes -------------------------------- */
function applyAccent(name) {
  document.body.className = "accent-" + name;
  LS.set("nexus_accent", name);
  $$(".accent-swatch").forEach((s) => s.classList.toggle("sel", s.dataset.accent === name));
}

function openSettings() {
  $("#settingsModal").classList.remove("hidden");
  $$(".accent-swatch").forEach((s) => s.classList.toggle("sel", s.dataset.accent === LS.get("nexus_accent", "cyan")));
  $("#systemPrompt").value = state.chat ? (state.chat.system || "") : "";
  $("#workdirInput").value = state.chat ? (state.chat.workdir || "") : "";
  $("#toolsetsInput").value = state.chat ? (state.chat.toolsets || "") : "";
  $("#agentDefault").checked = LS.get("nexus_agentDefault", false);
  $("#autoRead").checked = LS.get("nexus_autoRead", false);
  $("#autoView").checked = LS.get("nexus_autoView", true);
  $("#autoPreview").checked = LS.get("nexus_autoPreview", true);
  $("#splitView").checked = LS.get("nexus_splitView", true);
  $("#notifyChk").checked = LS.get("nexus_notify", true);
  $("#soundChk").checked = LS.get("nexus_sound", true);
}

async function saveSettings() {
  LS.set("nexus_agentDefault", $("#agentDefault").checked);
  LS.set("nexus_autoRead", $("#autoRead").checked);
  LS.set("nexus_autoView", $("#autoView").checked);
  LS.set("nexus_autoPreview", $("#autoPreview").checked);
  LS.set("nexus_splitView", $("#splitView").checked);
  LS.set("nexus_notify", $("#notifyChk").checked);
  LS.set("nexus_sound", $("#soundChk").checked);
  if (state.activeId) {
    const body = { system: $("#systemPrompt").value, workdir: $("#workdirInput").value, toolsets: $("#toolsetsInput").value };
    await api(`/api/chats/${state.activeId}`, { method: "PATCH", body });
    Object.assign(state.chat, body);
  }
  $("#settingsModal").classList.add("hidden");
  toast(t("settings_saved"));
}

async function exportAll() {
  const data = await api("/api/export");
  download(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }), "nexus-chats.json");
  toast("Exportado todo");
}

function importJson(file) {
  const reader = new FileReader();
  reader.onload = async () => {
    try {
      const data = JSON.parse(String(reader.result));
      const { imported } = await api("/api/import", { method: "POST", body: data });
      await refreshChats(); toast(`Importados ${imported} chats`);
    } catch (e) { toast("JSON no válido"); }
  };
  reader.readAsText(file);
}

/* --------------------------- colapsar / expandir ------------------------ */
function toggleSidebar(force) {
  const sb = $("#sidebar");
  sb.classList.toggle("collapsed", force === undefined ? !sb.classList.contains("collapsed") : !!force);
}
function orderedChatIds() { return state.chats.map((c) => c.id); }
function stepChat(delta) {
  const ids = orderedChatIds();
  if (!ids.length) return;
  let i = ids.indexOf(state.activeId);
  if (i < 0) i = 0;
  i = (i + delta + ids.length) % ids.length;
  openChat(ids[i]);
}
function jumpChat(idx) { const ids = orderedChatIds(); if (ids[idx]) openChat(ids[idx]); }
function openHelp() { $("#helpModal").classList.remove("hidden"); }

/* ---------------------------- barra redimensionable --------------------- */
function initDrag() {
  const handle = $("#dragHandle"), sb = $("#sidebar");
  const saved = LS.get("nexus_sidebarW", 290);
  sb.dataset.w = saved;
  if (!isMobile()) { sb.style.width = sb.style.flexBasis = saved + "px"; sb.style.marginLeft = ""; }
  let dragging = false;
  handle.addEventListener("mousedown", (e) => { dragging = true; document.body.classList.add("resizing"); e.preventDefault(); });
  document.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    const w = Math.min(520, Math.max(220, e.clientX));
    sb.style.width = sb.style.flexBasis = w + "px"; sb.dataset.w = w;
  });
  document.addEventListener("mouseup", () => {
    if (!dragging) return;
    dragging = false; document.body.classList.remove("resizing");
    LS.set("nexus_sidebarW", parseInt(sb.dataset.w, 10) || 290);
  });
  // el colapsado usa la anchura guardada y sincroniza icono/tab/cajon
  const sync = () => {
    const collapsed = sb.classList.contains("collapsed");
    const mobile = isMobile();
    document.body.classList.toggle("mobile", mobile);
    document.body.classList.toggle("sb-collapsed", collapsed);
    const bd = $("#drawerBackdrop");
    if (mobile) {
      sb.style.marginLeft = "";
      if (bd) bd.classList.toggle("show", !collapsed);
    } else {
      if (bd) bd.classList.remove("show");
      sb.style.marginLeft = collapsed ? "-" + (parseInt(sb.dataset.w, 10) || 290) + "px" : "";
    }
    const ic = $("#menuIcon");
    if (ic) ic.textContent = collapsed ? "›" : "‹";
    const mb = $("#menuBtn");
    if (mb) mb.title = collapsed ? "Mostrar historial (Ctrl+B)" : "Ocultar historial (Ctrl+B)";
    const bt = document.querySelector(".brand-text span");
    if (bt) bt.textContent = mobile ? t("brand_sub_mobile") : t("brand_sub");
  };
  window.__nexusSync = sync;
  window.addEventListener("resize", sync);
  window.addEventListener("orientationchange", () => setTimeout(sync, 160));
  const obs = new MutationObserver(sync);
  obs.observe(sb, { attributes: true, attributeFilter: ["class"] });
  sync();
}

/* -------------------------------- arranque ------------------------------ */
async function loadConfigState() {
  const s = await api("/api/state");
  state.chats = s.chats || [];
  state.providers = s.providers || {};
  state.presets = s.presets || [];
  state.chips = s.chips || [];
  state.defaults = LS.get("nexus_default", s.default || {});
  state.needsSetup = !!s.needs_setup;
  state.hermesInfo = s.hermes || {};
  state.configPath = s.config_path || "";
  state.home = s.home || "";
  return s;
}


/* ------------------------- idioma rapido (barra superior) ---------------- */
function updateLangPill() {
  const lbl = $("#langLabel");
  if (lbl) lbl.textContent = String(I18N.lang || "es").toUpperCase();
  const pop = $("#langPop");
  const btn = $("#langBtn");
  if (pop && !pop.classList.contains("hidden")) renderLangList();
  if (btn) btn.title = t("language") + " · " + I18N.name(I18N.lang);
}

function renderLangList() {
  const wrap = $("#langList");
  if (!wrap) return;
  wrap.innerHTML = "";
  (window.NEXUS_LANG_LIST || []).forEach((l) => {
    const it = document.createElement("div");
    it.className = "lang-item" + (l.code === I18N.lang ? " sel" : "");
    it.innerHTML = `<span>${esc(l.name)}</span><span class="lc">${esc(l.code)}${
      l.code === I18N.lang ? " ✓" : ""}</span>`;
    it.addEventListener("click", () => {
      setLang(l.code);
      $("#langPop").classList.add("hidden");
      $("#langBtn").classList.remove("on");
      toast(I18N.name(l.code));
    });
    wrap.appendChild(it);
  });
}

function openLangPop() {
  const pop = $("#langPop"), btn = $("#langBtn");
  if (!pop || !btn) return;
  const abierto = !pop.classList.contains("hidden");
  ["#modelPop", "#presetPop", "#morePop"].forEach((sel) => $(sel) && $(sel).classList.add("hidden"));
  if (abierto) {
    pop.classList.add("hidden");
    btn.classList.remove("on");
    return;
  }
  const r = btn.getBoundingClientRect();
  pop.style.top = r.bottom + 8 + "px";
  pop.style.left = Math.max(10, Math.min(r.right - 230, window.innerWidth - 250)) + "px";
  pop.classList.remove("hidden");
  btn.classList.add("on");
  renderLangList();
}

function fillLangSelect() {
  const sel = $("#langSelect");
  if (!sel) return;
  sel.innerHTML = "";
  (window.NEXUS_LANG_LIST || []).forEach((l) => {
    const o = document.createElement("option");
    o.value = l.code;
    o.textContent = l.name;
    if (l.code === I18N.lang) o.selected = true;
    sel.appendChild(o);
  });
  sel.addEventListener("change", () => {
    setLang(sel.value);
    toast(I18N.name(sel.value));
  });
}

/* al cambiar de idioma: aplicar al HTML y repintar lo que se genera en JS */
window.onLangChange = function () {
  I18N.apply(document);
  fillLangSelect();
  updateLangPill();
  try {
    renderSidebar();
    updateModelPill();
    updateAgentBtn();
    updateCount();
    if ($("#messages .empty")) renderEmpty();
    const panel = $("#panel");
    if (panel && !panel.classList.contains("hidden") && typeof window.setPanelTab === "function") {
      const activa = document.querySelector(".panel-tab.on");
      window.setPanelTab(activa ? activa.dataset.tab : "resumen");
    }
    if ($("#presetPop") && !$("#presetPop").classList.contains("hidden")) renderPresets();
    if ($("#setupModal") && !$("#setupModal").classList.contains("hidden")) renderSetupList();
    if ($("#localModal") && !$("#localModal").classList.contains("hidden")) renderLocal();
    renderHermes();
  } catch (e) {}
};

async function boot() {
  initLang();
  I18N.apply(document);
  fillLangSelect();
  updateLangPill();
  applyAccent(LS.get("nexus_accent", "cyan"));
  state.favorites = LS.get("nexus_favs", []);
  initDrag();
  initSplit();
  if (isMobile()) { $("#sidebar").classList.add("collapsed"); updateAgentBtn(); }
  try {
    await loadConfigState();
    const sinProveedor = state.needsSetup || !state.defaults.provider;
    $("#providerStatus").className = "status " + (sinProveedor ? "err" : "ok");
    $("#providerStatus").querySelector("span").textContent = sinProveedor ? t("status_no_provider") : t("status_online");
    renderSidebar(); updateModelPill();
    if (sinProveedor) openSetup("first");
    else if (state.chats.length) openChat(state.chats[0].id);
    else newChat(state.defaults.provider, state.defaults.model);
  } catch (e) {
    $("#providerStatus").className = "status err";
    $("#providerStatus").querySelector("span").textContent = t("status_no_server");
    toast(t("backend_down"));
  }
  updateCount();
  if (isMobile()) setTimeout(() => toast(t("brand_sub_mobile") + " · " + t("toggle_history"), 3200), 700);
}

/* -------------------------------- eventos ------------------------------- */
$("#input").addEventListener("input", autoGrow);
// en móvil el teclado tapa media pantalla: mantener el final a la vista al escribir
$("#input").addEventListener("focus", () => { if (isMobile()) setTimeout(() => scrollBottom(true), 350); });
if (window.visualViewport) {
  window.visualViewport.addEventListener("resize", () => { if (isMobile()) scrollBottom(true); });
}
$("#input").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); startTurn({ content: $("#input").value }); }
});
$("#sendBtn").addEventListener("click", () => startTurn({ content: $("#input").value }));
$("#stopBtn").addEventListener("click", () => {
  if (state.abort) state.abort.abort();
  if (state.activeId) fetch(`/api/chats/${state.activeId}/stop`, { method: "POST" }).catch(() => {});
});
$("#newChatBtn").addEventListener("click", () => newChat(state.defaults.provider, state.defaults.model));
$("#collapseBtn").addEventListener("click", () => toggleSidebar());
$("#menuBtn").addEventListener("click", () => toggleSidebar());
$("#expandTab").addEventListener("click", () => toggleSidebar(false));
$("#drawerBackdrop").addEventListener("click", () => $("#sidebar").classList.add("collapsed"));
// gestos en móvil: abrir desde el borde izquierdo, cerrar deslizando a la izquierda
let _tsx = 0, _tsy = 0, _tst = 0;
document.addEventListener("touchstart", (e) => {
  const toque = e.touches[0]; _tsx = toque.clientX; _tsy = toque.clientY; _tst = Date.now();
}, { passive: true });
document.addEventListener("touchend", (e) => {
  if (!isMobile()) return;
  const toque = e.changedTouches[0];
  const dx = toque.clientX - _tsx, dy = toque.clientY - _tsy;
  if (Date.now() - _tst > 600 || Math.abs(dy) > 60 || Math.abs(dx) < 60) return;
  const col = $("#sidebar").classList.contains("collapsed");
  if (dx > 0 && col && _tsx < 40) $("#sidebar").classList.remove("collapsed");
  else if (dx < 0 && !col) $("#sidebar").classList.add("collapsed");
}, { passive: true });
$("#closeHelp").addEventListener("click", () => $("#helpModal").classList.add("hidden"));
$("#helpModal").addEventListener("click", (e) => { if (e.target.id === "helpModal") $("#helpModal").classList.add("hidden"); });
$("#agentBtn").addEventListener("click", toggleAgent);
$("#presetBtn").addEventListener("click", (e) => { e.stopPropagation(); openPresetPop(); });
$("#savePresetBtn").addEventListener("click", savePreset);
$("#seedPresetBtn").addEventListener("click", restoreExamplePrompts);
$("#modelBtn").addEventListener("click", (e) => { e.stopPropagation(); const p = $("#modelPop"); p.classList.contains("hidden") ? openModelPop() : p.classList.add("hidden"); });
$("#modelSearch").addEventListener("input", (e) => renderModelList(e.target.value));
$("#favOnly").addEventListener("change", () => renderModelList($("#modelSearch").value));
$("#menuMoreBtn").addEventListener("click", (e) => { e.stopPropagation(); openMore(); });
$$("#morePop button").forEach((b) => b.addEventListener("click", () => moreAction(b.dataset.act)));
$("#settingsBtn").addEventListener("click", openSettings);
$("#panelBtn").addEventListener("click", () => openPanel("resumen"));
$("#closeSettings").addEventListener("click", () => $("#settingsModal").classList.add("hidden"));
$("#saveSettings").addEventListener("click", async () => {
  if ($("#notifyChk").checked && window.Notification && Notification.permission === "default") { try { await Notification.requestPermission(); } catch {} }
  saveSettings();
});
$("#exportAll").addEventListener("click", exportAll);
$("#importBtn").addEventListener("click", () => $("#importFile").click());
$("#importFile").addEventListener("change", (e) => { if (e.target.files[0]) importJson(e.target.files[0]); e.target.value = ""; });
$$(".accent-swatch").forEach((s) => s.addEventListener("click", () => applyAccent(s.dataset.accent)));
$("#scrollBtn").addEventListener("click", () => scrollBottom());

$("#attachBtn").addEventListener("click", () => $("#fileInput").click());
$("#langBtn").addEventListener("click", (e) => { e.stopPropagation(); openLangPop(); });

/* --- asistente de proveedor --- */
$("#setupTest").addEventListener("click", testSetup);
$("#setupSave").addEventListener("click", saveSetup);
$("#setupClose").addEventListener("click", () => $("#setupModal").classList.add("hidden"));
$("#setupModal").addEventListener("click", (e) => { if (e.target.id === "setupModal") $("#setupModal").classList.add("hidden"); });
$("#hermesInstall").addEventListener("click", startHermesInstall);
$("#hermesCheck").addEventListener("click", async () => { SETUP.hermes = await api("/api/hermes"); renderHermes(); });
$("#openProviders").addEventListener("click", () => { $("#settingsModal").classList.add("hidden"); openSetup("manage"); });
$("#spBase").addEventListener("keydown", (e) => { if (e.key === "Enter") testSetup(); });
$("#spKey").addEventListener("keydown", (e) => { if (e.key === "Enter") testSetup(); });
$("#fileInput").addEventListener("change", (e) => { addFiles(e.target.files); e.target.value = ""; });
$("#micBtn").addEventListener("click", toggleMic);

$("#chatSearch").addEventListener("input", debounce(async (e) => {
  state.filter = e.target.value.trim();
  if (state.filter.length >= 2) {
    try { state.searchResults = (await api("/api/search?q=" + encodeURIComponent(state.filter))).results; }
    catch { state.searchResults = []; }
  } else state.searchResults = [];
  renderSidebar();
}, 180));

$("#messages").addEventListener("scroll", () => {
  const box = $("#messages");
  const near = box.scrollHeight - box.scrollTop - box.clientHeight < 120;
  $("#scrollBtn").classList.toggle("show", !near);
});
$("#chatTitle").addEventListener("change", async (e) => {
  if (!state.activeId) return;
  const titulo = e.target.value.trim() || t("untitled");
  await api(`/api/chats/${state.activeId}`, { method: "PATCH", body: { title: titulo } });
  state.chat.title = titulo; refreshChats();
});
// bloques de codigo: copiar y previsualizar (delegado)
function blocksOf(scopeEl) {
  return Array.from(scopeEl.querySelectorAll(".code-block")).map((b) => ({
    lang: b.dataset.lang || "",
    code: (b.querySelector("pre code") || { textContent: "" }).textContent || "",
  }));
}
function toggleFrame(slot, doc, btn) {
  const open = slot.querySelector(".cb-frame");
  if (open) { open.remove(); if (btn) btn.classList.remove("on"); return false; }
  slot.insertAdjacentHTML("beforeend", frameHtml(doc));
  if (btn) btn.classList.add("on");
  return true;
}
function openDocInTab(doc) {
  const url = URL.createObjectURL(new Blob([doc], { type: "text/html" }));
  window.open(url, "_blank");
  setTimeout(() => URL.revokeObjectURL(url), 60000);
}
$("#messages").addEventListener("click", (e) => {
  const copy = e.target.closest("[data-copy]");
  if (copy) {
    const code = copy.closest(".code-block").querySelector("pre code");
    navigator.clipboard.writeText(code.textContent);
    copy.textContent = t("copied_blocks"); setTimeout(() => (copy.textContent = t("copy")), 1200);
    return;
  }
  const frameBtn = e.target.closest("[data-openframe]");
  if (frameBtn) {
    const fr = frameBtn.closest(".cb-frame").querySelector("iframe");
    if (fr) openDocInTab(fr.getAttribute("srcdoc") || "");
    return;
  }
  const closeBtn = e.target.closest("[data-closeframe]");
  if (closeBtn) {
    const block = closeBtn.closest(".code-block") || closeBtn.closest(".content");
    closeBtn.closest(".cb-frame").remove();
    const btn = block && block.querySelector("[data-view].on, [data-viewmsg].on");
    if (btn) btn.classList.remove("on");
    return;
  }
  const view = e.target.closest("[data-view]");
  if (view) {
    const block = view.closest(".code-block");
    const doc = composeArtifact(blocksOf(block));
    if (!doc) return;
    if (splitEnabled()) {
      openSplit({ mode: "doc", title: (block.dataset.lang || "html").toUpperCase() + " · bloque", doc, live: false });
    } else toggleFrame(block.querySelector(".cb-frame-slot"), doc, view);
    return;
  }
  const viewMsg = e.target.closest("[data-viewmsg]");
  if (viewMsg) {
    const msg = viewMsg.closest(".msg");
    const doc = composeArtifact(blocksOf(msg));
    if (!doc) return;
    if (splitEnabled()) {
      openSplit({ mode: "doc", title: "vista previa · respuesta", doc, live: false });
    } else toggleFrame(msg.querySelector(".artifact-slot"), doc, viewMsg);
    return;
  }
  const openTab = e.target.closest("[data-opentab]");
  if (openTab) {
    const doc = composeArtifact(blocksOf(openTab.closest(".msg")));
    if (doc) openDocInTab(doc);
    return;
  }
  const art = e.target.closest("[data-artifact]");
  if (art && window.previewProjectFile) window.previewProjectFile(art.dataset.artifact);
});

// arrastrar y soltar archivos
const composer = $("#composer");
["dragenter", "dragover"].forEach((ev) => composer.addEventListener(ev, (e) => { e.preventDefault(); composer.classList.add("dragover"); }));
["dragleave", "drop"].forEach((ev) => composer.addEventListener(ev, (e) => { e.preventDefault(); composer.classList.remove("dragover"); }));
composer.addEventListener("drop", (e) => { if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files); });
// pegar imagenes
$("#input").addEventListener("paste", (e) => {
  const items = e.clipboardData && e.clipboardData.files;
  if (items && items.length) { addFiles(items); }
});

// paleta
$("#paletteInput").addEventListener("input", (e) => { paletteSel = 0; renderPalette(e.target.value); });
$("#paletteInput").addEventListener("keydown", (e) => {
  if (e.key === "ArrowDown") { e.preventDefault(); paletteSel = Math.min(paletteFiltered.length - 1, paletteSel + 1); renderPalette(e.target.value); }
  else if (e.key === "ArrowUp") { e.preventDefault(); paletteSel = Math.max(0, paletteSel - 1); renderPalette(e.target.value); }
  else if (e.key === "Enter") { e.preventDefault(); runPalette(paletteSel); }
});
$("#palette").addEventListener("click", (e) => { if (e.target.id === "palette") $("#palette").classList.add("hidden"); });

document.addEventListener("click", (e) => {
  if (!e.target.closest("#modelPop") && !e.target.closest("#modelBtn")) $("#modelPop").classList.add("hidden");
  if (!e.target.closest("#morePop") && !e.target.closest("#menuMoreBtn")) $("#morePop").classList.add("hidden");
  if (!e.target.closest("#presetPop") && !e.target.closest("#presetBtn")) $("#presetPop").classList.add("hidden");
  if (!e.target.closest("#langPop") && !e.target.closest("#langBtn")) { $("#langPop").classList.add("hidden"); $("#langBtn").classList.remove("on"); }
});
$("#settingsModal").addEventListener("click", (e) => { if (e.target.id === "settingsModal") $("#settingsModal").classList.add("hidden"); });

document.addEventListener("keydown", (e) => {
  const mod = e.ctrlKey || e.metaKey;
  const k = e.key.toLowerCase();
  const typing = /^(input|textarea)$/i.test(e.target.tagName) || e.target.isContentEditable;
  if (mod && k === "n") { e.preventDefault(); newChat(state.defaults.provider, state.defaults.model); }
  else if (mod && k === "b") { e.preventDefault(); toggleSidebar(); }
  else if (mod && k === "k") { e.preventDefault(); openModelPop(); }
  else if (mod && k === "f") { e.preventDefault(); $("#chatSearch").focus(); }
  else if (mod && k === "p") { e.preventDefault(); openPalette(); }
  else if (mod && k === "d") { e.preventDefault(); const p = $("#panel"); p.classList.contains("hidden") ? openPanel("resumen") : closePanel(); }
  else if (e.altKey && (e.key === "ArrowUp" || e.key === "ArrowDown")) { e.preventDefault(); stepChat(e.key === "ArrowUp" ? -1 : 1); }
  else if (e.altKey && /^[1-9]$/.test(e.key)) { e.preventDefault(); jumpChat(parseInt(e.key, 10) - 1); }
  else if (!mod && e.key === "?" && !typing) { e.preventDefault(); openHelp(); }
  else if (e.key === "Escape") {
    if (window.speechSynthesis) speechSynthesis.cancel();
    if (!$("#panel").classList.contains("hidden")) { closePanel(); return; }
    $$(".pop").forEach((p) => p.classList.add("hidden"));
    $("#settingsModal").classList.add("hidden");
    $("#palette").classList.add("hidden");
    $("#helpModal").classList.add("hidden");
  }
});

boot();

/* ============ asistente de proveedor (primera vez) y gestion ============ */
const SETUP = { mode: "first", sel: "", info: null, hermes: null, poll: null, models: [] };


/* ======================= MODELOS LOCALES (Ollama / LM Studio) ============== */

const LOCAL = { info: null, poll: null, filtro: "", ligero: false, instalados: false, probando: "" };

function pesoMb(mb) {
  const n = Number(mb) || 0;
  return n >= 1024 ? (n / 1024).toFixed(1).replace(".", ",") + " GB" : Math.round(n) + " MB";
}

function etiquetaModelo(m) {
  const p = [];
  p.push(m.params);
  p.push(pesoMb(m.mb));
  if (m.sin_censura) p.push(t("local_uncensored"));
  p.push(m.herramientas ? t("local_tools_yes") : t("local_tools_no"));
  if (m.multilingue) p.push(t("local_multilang"));
  if (m.hf) p.push("Hugging Face");
  return p.join(" · ");
}

async function openLocal() {
  const modal = $("#localModal");
  if (!modal) return;
  modal.classList.remove("hidden");
  await loadLocal();
  if (LOCAL.poll) clearInterval(LOCAL.poll);
  LOCAL.poll = setInterval(() => {
    if (modal.classList.contains("hidden")) { clearInterval(LOCAL.poll); LOCAL.poll = null; return; }
    loadLocal(true);
  }, 2500);
}

async function loadLocal(silencioso) {
  try {
    LOCAL.info = await api("/api/local");
  } catch (e) {
    if (!silencioso) toast(t("backend_down") + ": " + e.message);
    return;
  }
  renderLocal();
}

function renderLocal() {
  const d = LOCAL.info || {};
  if (document.querySelector("#localModal").classList.contains("hidden")) return;
  const ollamaListo = d.ollama_bin && d.ollama_running;
  const estado = $("#localEstado");
  estado.innerHTML = "";
  const tarjeta = (titulo, sub, acciones) => {
    const div = document.createElement("div");
    div.className = "le-card";
    div.innerHTML = `<div class="le-tit">${titulo}</div><div class="le-sub">${sub}</div>`;
    const caja = document.createElement("div");
    caja.className = "le-acc";
    (acciones || []).forEach((a) => caja.appendChild(a));
    div.appendChild(caja);
    return div;
  };
  const boton = (texto, fn, clase) => {
    const b = document.createElement("button");
    b.className = clase || "mini-btn";
    b.textContent = texto;
    b.addEventListener("click", fn);
    return b;
  };

  // --- Ollama ---
  const accionesO = [];
  if (!d.ollama_bin) {
    accionesO.push(boton(d.instalando && d.instalacion === "ollama" ? t("local_installing") : t("local_install_ollama"),
                         () => instalarOllama(), "primary"));
    accionesO.push(boton(t("local_ollama_web"), () => abrirLocal("ollama_download")));
  } else {
    if (!d.ollama_running) accionesO.push(boton(t("local_start"), () => arrancarOllama(), "primary"));
    accionesO.push(boton(t("local_folder"), () => abrirLocal("modelos")));
  }
  const subO = d.ollama_bin
    ? `${d.ollama_version || "Ollama"} · ${d.ollama_running ? t("local_running") : t("local_stopped")} · ` +
      t("local_installed_n", { n: (d.ollama_instalados || []).length })
    : `${t("local_not_installed")} · ${t("local_free", { g: d.espacio_libre || "?" })}`;
  estado.appendChild(tarjeta("Ollama", subO, accionesO));

  // --- LM Studio ---
  const accionesL = [];
  if (!d.lmstudio_instalado) {
    accionesL.push(boton(t("local_lm_download"), () => abrirLocal("lmstudio_download"), "primary"));
  } else {
    if (!d.lmstudio_running) accionesL.push(boton(t("local_start"), () => arrancarLmStudio()));
    accionesL.push(boton(t("local_lm_docs"), () => abrirLocal("lmstudio_docs")));
  }
  const subL = d.lmstudio_instalado
    ? `${d.lms_bin ? "lms" : "LM Studio"} · ${d.lmstudio_running ? t("local_running") : t("local_stopped")} · ` +
      t("local_installed_n", { n: (d.lmstudio_modelos || []).length })
    : t("local_not_installed");
  estado.appendChild(tarjeta("LM Studio", subL, accionesL));

  // --- progreso de descarga ---
  const pull = d.pull || {};
  const caja = $("#localProgreso");
  if (pull.running || (pull.model && (pull.done || pull.error))) {
    caja.classList.remove("hidden");
    $("#lpModelo").textContent = pull.model || "—";
    $("#lpPct").textContent = (pull.percent || 0) + "%";
    $("#lpRelleno").style.width = (pull.percent || 0) + "%";
    $("#lpLinea").textContent = pull.error ? "✕ " + pull.error : (pull.line || "");
    $("#localCancelar").classList.toggle("hidden", !pull.running);
  } else {
    caja.classList.add("hidden");
  }

  // --- catalogo ---
  const lista = $("#localLista");
  const filtro = (LOCAL.filtro || "").trim().toLowerCase();
  const modelos = (d.catalogo || []).filter((m) => {
    if (LOCAL.ligero && m.mb > 1024) return false;
    if (LOCAL.instalados && !m.instalado) return false;
    if (!filtro) return true;
    return (m.id + " " + m.nombre + " " + (m.familia || "") + " " + (m.resumen || "")).toLowerCase().includes(filtro);
  });
  $("#localCuenta").textContent = t("local_count", { n: modelos.length, total: (d.catalogo || []).length });
  lista.innerHTML = "";
  if (!modelos.length) {
    lista.innerHTML = `<p class="modal-note">${t("setup_models_empty")}</p>`;
  }
  modelos.forEach((m) => {
    const card = document.createElement("div");
    card.className = "lm-card" + (m.instalado ? " instalado" : "");
    card.innerHTML = `
      <div class="lc-cabeza">
        <b>${esc(m.nombre)}</b>
        ${m.sin_censura ? `<span class="lc-tag sin">${t("local_uncensored")}</span>` : ""}
        ${m.herramientas ? `<span class="lc-tag herr">${t("local_tools_yes")}</span>` : ""}
        ${m.hf ? `<span class="lc-tag hf">HF</span>` : ""}
        ${m.instalado ? `<span class="lc-tag ok">${t("local_installed")}</span>` : ""}
      </div>
      <div class="lc-meta">${esc(etiquetaModelo(m))}</div>
      <div class="lc-desc">${esc(m.resumen || "")}</div>
      <div class="lc-detalle"><b>${t("local_can")}:</b> ${esc((m.sabe || []).join(", "))}
        · <b>${t("local_cant")}:</b> ${esc((m.no_sabe || []).join(", "))}</div>
      ${m.recomendado ? `<div class="lc-uso">▸ ${esc(m.recomendado)}</div>` : ""}
      <div class="lc-acc"></div>`;
    const acc = card.querySelector(".lc-acc");
    const mk = (texto, fn, clase) => {
      const b = document.createElement("button");
      b.className = clase || "mini-btn";
      b.textContent = texto;
      b.addEventListener("click", fn);
      return b;
    };
    if (m.instalado) {
      acc.appendChild(mk(t("local_use"), () => usarLocal(m), "primary"));
      acc.appendChild(mk(t("local_probar"), () => probarLocal(m)));
      acc.appendChild(mk(t("local_remove"), () => borrarLocal(m)));
    } else {
      const descargando = pull.running && pull.model === m.id;
      const b = mk(descargando ? t("local_downloading") : t("local_download"), () => descargarLocal(m), "primary");
      b.disabled = !!pull.running || !ollamaListo;
      if (!ollamaListo) b.title = t("local_need_ollama");
      acc.appendChild(b);
      if (m.hf) acc.appendChild(mk("Hugging Face", () => abrirLocal("ollama_docs")));
    }
    if (LOCAL.probando === m.id) {
      const r = document.createElement("div");
      r.className = "lc-resultado";
      r.textContent = t("local_probing");
      card.appendChild(r);
    }
    lista.appendChild(card);
  });

  // --- LM Studio: catalogo ---
  const lmInfo = $("#localLmEstado");
  if (lmInfo) {
    lmInfo.textContent = d.lmstudio_instalado
      ? (d.lmstudio_running ? t("local_running") : t("local_stopped")) + " · " + (d.lms_bin || "lms")
      : t("local_lm_missing");
  }
  const lmLista = $("#localLmLista");
  if (lmLista) {
    lmLista.innerHTML = "";
    (d.lmstudio_catalogo || []).forEach((m) => {
      const card = document.createElement("div");
      card.className = "lm-card";
      card.innerHTML = `<div class="lc-cabeza"><b>${esc(m.nombre)}</b>
        ${m.sin_censura ? `<span class="lc-tag sin">${t("local_uncensored")}</span>` : ""}
        ${m.herramientas ? `<span class="lc-tag herr">${t("local_tools_yes")}</span>` : ""}</div>
        <div class="lc-meta">${esc(m.params)} · ${pesoMb(m.mb)} · ${esc(m.quant || "Q4_K_M")} · ${esc(m.repo)}</div>
        <div class="lc-desc">${esc(m.resumen || "")}</div>`;
      const acc = document.createElement("div");
      acc.className = "lc-acc";
      const b = document.createElement("button");
      b.className = "mini-btn";
      b.textContent = d.lms_bin ? t("local_download") : t("local_lm_download");
      b.disabled = !d.lms_bin;
      b.addEventListener("click", () => (d.lms_bin ? descargarLocal(m, "lmstudio") : abrirLocal("lmstudio_download")));
      acc.appendChild(b);
      card.appendChild(acc);
      lmLista.appendChild(card);
    });
  }
}

async function instalarOllama() {
  if (!confirm(t("local_confirm_install"))) return;
  try {
    const r = await api("/api/local/install", { method: "POST", body: { backend: "ollama" } });
    toast(r.message || (r.ok ? t("local_install_ok") : t("local_install_fail")));
    LOCAL.info = r.status || LOCAL.info;
    renderLocal();
    const log = $("#localLog");
    log.classList.remove("hidden");
    log.textContent = t("local_installing") + "...";
    const ver = setInterval(async () => {
      try {
        const l = await api("/api/local/log");
        $("#localLog").textContent = l.log || "";
        $("#localLog").scrollTop = $("#localLog").scrollHeight;
        await loadLocal(true);
        if (!l.running && l.code !== null && l.code !== undefined) {
          clearInterval(ver);
          toast(l.code === 0 ? t("local_install_ok") : t("local_install_fail"));
          await loadLocal();
        }
      } catch (e) { clearInterval(ver); }
    }, 2500);
  } catch (e) { toast(t("local_install_fail") + ": " + e.message); }
}

async function arrancarOllama() {
  try {
    const r = await api("/api/local/start", { method: "POST", body: { backend: "ollama" } });
    toast(r.message || "ok");
    LOCAL.info = r.status || LOCAL.info;
    renderLocal();
  } catch (e) { toast(e.message); }
}

async function arrancarLmStudio() {
  try {
    const r = await api("/api/local/start", { method: "POST", body: { backend: "lmstudio" } });
    toast(r.message || "ok");
    setTimeout(() => loadLocal(true), 1500);
  } catch (e) { toast(e.message); }
}

async function descargarLocal(m, backend) {
  try {
    const r = await api("/api/local/pull", { method: "POST", body: { model: m.id, backend: backend || "ollama" } });
    toast(r.message || (r.ok ? t("local_pull_start") : t("local_pull_fail")));
    await loadLocal(true);
  } catch (e) { toast(t("local_pull_fail") + ": " + e.message); }
}

async function cancelarDescarga() {
  try { const r = await api("/api/local/cancel", { method: "POST", body: {} }); toast(r.message || ""); await loadLocal(true); }
  catch (e) { toast(e.message); }
}

async function usarLocal(m, backend) {
  try {
    const r = await api("/api/local/use", { method: "POST", body: { model: m.id, backend: backend || "ollama" } });
    if (!r.ok) return toast(r.message || "error");
    await loadConfigState();
    refreshChats();
    updateModelPill();
    toast(t("local_use_ok", { model: m.nombre || m.id }));
    const modal = $("#localModal");
    if (modal) modal.classList.add("hidden");
    if (LOCAL.poll) { clearInterval(LOCAL.poll); LOCAL.poll = null; }
    await newChat();
    const inp = $("#input");
    if (inp && !inp.value.trim()) { inp.value = t("local_try_msg"); autoGrow(); inp.focus(); }
  } catch (e) { toast(e.message); }
}

async function probarLocal(m, backend) {
  LOCAL.probando = m.id;
  renderLocal();
  try {
    const r = await api("/api/config/test", { method: "POST", body: { provider: backend === "lmstudio" ? "lmstudio" : "ollama", model: m.id } });
    LOCAL.probando = "";
    renderLocal();
    toast(r.ok ? t("local_test_ok", { reply: (r.reply || "").slice(0, 80) }) : t("local_test_fail", { error: (r.error || "?").slice(0, 120) }),
          r.ok ? 5000 : 7000);
  } catch (e) {
    LOCAL.probando = "";
    renderLocal();
    toast(t("local_test_fail", { error: e.message }), 7000);
  }
}

async function borrarLocal(m, backend) {
  if (!confirm(t("local_confirm_remove", { model: m.id }))) return;
  try {
    const r = await api("/api/local/remove", { method: "POST", body: { model: m.id, backend: backend || "ollama" } });
    toast(r.message || "");
    LOCAL.info = r.status || LOCAL.info;
    renderLocal();
  } catch (e) { toast(e.message); }
}

async function abrirLocal(que) {
  try { await api("/api/local/open", { method: "POST", body: { what: que } }); } catch (e) { toast(e.message); }
}

async function loadSetupInfo() {
  try { SETUP.info = await api("/api/config"); } catch { SETUP.info = { catalog: {}, providers: {} }; }
  try { SETUP.hermes = await api("/api/hermes"); } catch { SETUP.hermes = {}; }
  return SETUP.info;
}

async function openSetup(mode = "manage") {
  SETUP.mode = mode;
  const info = await loadSetupInfo();
  const modal = $("#setupModal");
  if (!modal) return;
  modal.classList.remove("hidden");
  $("#setupTitle").textContent = mode === "first" ? t("setup_title") : t("providers_btn");
  const ruta = info.config_path || "~/.config/nexus/config.json";
  $("#setupPath").textContent = ruta;
  if ($("#settingsCfgPath")) $("#settingsCfgPath").textContent = ruta;
  const grid = $("#setupGrid");
  grid.innerHTML = "";
  const cat = info.catalog || {};
  const items = Object.keys(cat).map((pid) => ({ pid, label: cat[pid].label || pid, url: cat[pid].base_url || "" }));
  items.push({ pid: "__custom", label: "Otro (personalizado)", url: "Cualquier API compatible con OpenAI" });
  items.forEach((it) => {
    const b = document.createElement("button");
    b.className = "setup-opt";
    b.dataset.pid = it.pid;
    b.innerHTML = `${esc(it.label)}<small>${esc(it.url)}</small>`;
    b.addEventListener("click", () => selectSetupProvider(it.pid));
    grid.appendChild(b);
  });
  const preferido = SETUP.mode === "first" ? (Object.keys(cat)[0] || "__custom") : (SETUP.sel || Object.keys(cat)[0] || "__custom");
  selectSetupProvider(preferido);
  renderSetupList();
  renderHermes();
}

function selectSetupProvider(pid) {
  SETUP.sel = pid;
  SETUP.models = [];
  $$("#setupGrid .setup-opt").forEach((b) => b.classList.toggle("sel", b.dataset.pid === pid));
  const cat = (SETUP.info && SETUP.info.catalog) || {};
  const spec = cat[pid] || {};
  const guardado = ((SETUP.info && SETUP.info.providers) || {})[pid] || {};
  $("#spLabel").value = spec.label || guardado.label || (pid === "__custom" ? "Mi proveedor" : pid);
  $("#spBase").value = guardado.base_url || spec.base_url || "";
  $("#spKey").value = "";
  $("#spModel").value = guardado.models && guardado.models[0] ? guardado.models[0] : "";
  const docs = $("#spDocs");
  if (spec.docs) { docs.href = spec.docs; docs.classList.remove("hidden"); } else docs.classList.add("hidden");
  $("#setupResult").classList.add("hidden");
  const necesita = spec.requires_key === false ? false : true;
  $("#spKey").disabled = pid !== "__custom" && spec.requires_key === false;
  $("#spKey").placeholder = necesita ? "sk-..." : "no hace falta (servidor local)";
  if (guardado.has_key) $("#spKey").placeholder = "guardada ✓ (escribe otra para cambiarla)";
  SETUP.models = (guardado.models || spec.models || []).slice();
  renderSetupModels();
  loadSetupModels();
}


/* --- lista de modelos del asistente (elegir con el raton, no a mano) ------ */

async function loadSetupModels() {
  const lista = $("#spModelList");
  if (!lista) return;
  const spec = setupFormSpec();
  if (!spec.base_url) {
    lista.innerHTML = `<div class="ml-hint">${t("setup_need_url")}</div>`;
    return;
  }
  lista.innerHTML = `<div class="ml-hint">${t("setup_models_loading")}</div>`;
  $("#spModelsLoad").disabled = true;
  try {
    const r = await api("/api/config/models", { method: "POST", body: { provider: spec.id, spec, refresh: true }, timeout: 45000 });
    SETUP.models = r.models || [];
    renderSetupModels();
    if (!SETUP.models.length) {
      lista.innerHTML = `<div class="ml-hint">${t("setup_models_none")}${r.error ? " · " + esc(r.error) : ""}</div>`;
    }
  } catch (e) {
    lista.innerHTML = `<div class="ml-hint">${t("setup_models_none")} · ${esc(e.message)}</div>`;
  } finally {
    $("#spModelsLoad").disabled = false;
  }
}

function renderSetupModels() {
  const lista = $("#spModelList");
  if (!lista) return;
  const filtro = ($("#spBuscar").value || "").trim().toLowerCase();
  const elegido = ($("#spModel").value || "").trim();
  const todos = SETUP.models || [];
  const modelos = todos.filter((m) => !filtro || m.toLowerCase().includes(filtro));
  lista.innerHTML = "";
  if (!modelos.length) {
    lista.innerHTML = `<div class="ml-hint">${t("setup_models_empty")}</div>`;
    return;
  }
  modelos.slice(0, 500).forEach((m) => {
    const b = document.createElement("button");
    b.className = "ml-item" + (m === elegido ? " sel" : "");
    b.textContent = m;
    b.addEventListener("click", () => {
      $("#spModel").value = m;
      renderSetupModels();
      setupShow(t("setup_model_picked", { model: m }), "");
    });
    lista.appendChild(b);
  });
}

function setupFormSpec() {
  const pid = SETUP.sel === "__custom" ? ($("#spLabel").value.trim().toLowerCase().replace(/[^a-z0-9_-]+/g, "-") || "custom") : SETUP.sel;
  return { id: pid, label: $("#spLabel").value.trim() || pid, base_url: $("#spBase").value.trim(),
           api_key: $("#spKey").value.trim(), models: SETUP.models };
}

function setupShow(texto, clase) {
  const box = $("#setupResult");
  box.textContent = texto;
  box.className = "setup-result " + (clase || "");
  box.classList.remove("hidden");
}

async function testSetup() {
  const spec = setupFormSpec();
  const modelo = $("#spModel").value.trim();
  setupShow(t("setup_testing"), "");
  $("#setupTest").disabled = true;
  try {
    const r = await api("/api/config/test", { method: "POST", body: { provider: spec.id, spec, model: modelo } });
    if (r.ok) {
      if (!modelo && r.model) $("#spModel").value = r.model;
      setupShow(t("setup_ok", { n: r.models || 0, reply: r.reply || "-", model: r.model || modelo }), "ok");
      loadSetupModels();
      $("#setupSave").focus();
    } else {
      setupShow(t("setup_fail", { error: r.error || "?" }), "err");
    }
  } catch (e) {
    setupShow(t("backend_down") + ": " + e.message, "err");
  } finally {
    $("#setupTest").disabled = false;
  }
}

async function saveSetup() {
  const spec = setupFormSpec();
  if (!spec.base_url) return setupShow(t("setup_need_url"), "err");
  $("#setupSave").disabled = true;
  try {
    const r = await api("/api/config", { method: "POST",
      body: { provider: Object.assign({}, spec, { model: $("#spModel").value.trim() }), make_default: true } });
    if (r.error) { setupShow(r.error, "err"); return; }
    await loadConfigState();
    refreshChats();
    updateModelPill();
    setupShow(t("setup_saved"), "ok");
    toast(t("setup_ready", { name: spec.label || spec.id }));
    setTimeout(() => { $("#setupModal").classList.add("hidden"); }, 700);
  } catch (e) {
    setupShow(t("setup_save_failed", { error: e.message }), "err");
  } finally {
    $("#setupSave").disabled = false;
  }
}

function renderSetupList() {
  const box = $("#setupList");
  const provs = (SETUP.info && SETUP.info.providers) || {};
  const ids = Object.keys(provs);
  if (!ids.length) { box.innerHTML = `<p class="modal-note">${t("setup_no_providers")}</p>`; return; }
  const porDefecto = ((SETUP.info && SETUP.info.default) || {}).provider || "";
  box.innerHTML = "";
  ids.forEach((pid) => {
    const p = provs[pid];
    const row = document.createElement("div");
    row.className = "setup-row";
    row.innerHTML = `<span class="sr-name">${esc(p.label || pid)}</span>` +
      `<span class="sr-tag">${p.has_key ? "clave ✓" : (p.requires_key ? "sin clave" : "local")}` +
      `${p.models && p.models.length ? " · " + p.models.length + " modelos" : ""}` +
      `${pid === porDefecto ? " · " + t("setup_default") : ""}</span>`;
    const usar = document.createElement("button");
    usar.className = "mini-btn"; usar.textContent = t("setup_use");
    usar.addEventListener("click", () => makeDefault(pid));
    const del = document.createElement("button");
    del.className = "mini-btn"; del.textContent = t("setup_remove");
    del.addEventListener("click", () => removeProvider(pid));
    row.appendChild(usar); row.appendChild(del);
    box.appendChild(row);
  });
}

async function makeDefault(pid) {
  try {
    await api("/api/config", { method: "POST", body: { provider: { id: pid }, make_default: true } });
    await loadConfigState();
    await loadSetupInfo();
    renderSetupList();
    toast(t("setup_default_now", { id: pid }));
  } catch (e) { toast(t("setup_save_failed", { error: e.message })); }
}

async function removeProvider(pid) {
  if (!confirm(t("setup_confirm_remove", { id: pid }))) return;
  try {
    await api("/api/config", { method: "POST", body: { delete: pid } });
    await loadConfigState();
    await loadSetupInfo();
    renderSetupList();
    toast(t("setup_removed"));
  } catch (e) { toast(t("setup_save_failed", { error: e.message })); }
}

function renderHermes() {
  const h = SETUP.hermes || {};
  const estado = $("#hermesState");
  if (h.installed) estado.textContent = t("agent_installed");
  else if (h.running) estado.textContent = t("agent_installing");
  else estado.textContent = t("agent_missing");
  if ($("#hermesDocs")) $("#hermesDocs").href = h.docs || "https://hermes-agent.nousresearch.com/docs";
  if ($("#hermesInstall")) {
    $("#hermesInstall").disabled = !!h.installed || !!h.running;
    $("#hermesInstall").textContent = h.installed ? t("already_installed") : (h.running ? t("installing") : t("install_hermes"));
  }
  const log = $("#hermesLog");
  if (h.tail) { log.textContent = h.tail; log.classList.remove("hidden"); }
}

async function startHermesInstall() {
  const h = SETUP.hermes || {};
  const cmd = h.command || "curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash";
  if (!confirm(t("confirm_install", { cmd }))) return;
  try {
    const r = await api("/api/hermes/install", { method: "POST" });
    SETUP.hermes = r.status || SETUP.hermes;
    renderHermes();
    if (SETUP.poll) clearInterval(SETUP.poll);
    SETUP.poll = setInterval(async () => {
      try { SETUP.hermes = await api("/api/hermes"); } catch {}
      renderHermes();
      if (SETUP.hermes && !SETUP.hermes.running && SETUP.hermes.exit_code !== null) {
        clearInterval(SETUP.poll); SETUP.poll = null;
        const info = SETUP.hermes;
        toast(info.installed ? t("hermes_installed_ok") : t("hermes_finished", { code: info.exit_code }));
        loadConfigState();
      }
    }, 3000);
  } catch (e) { toast(t("install_failed", { error: e.message })); }
}

/* --- enganches de los modelos locales --- */
$("#localBtn").addEventListener("click", () => openLocal());
$("#quickKey").addEventListener("click", () => openSetup("manage"));
$("#setupLocalBtn").addEventListener("click", () => { $("#setupModal").classList.add("hidden"); openLocal(); });
$("#localClose").addEventListener("click", () => { $("#localModal").classList.add("hidden"); if (LOCAL.poll) { clearInterval(LOCAL.poll); LOCAL.poll = null; } });
$("#localModal").addEventListener("click", (e) => { if (e.target.id === "localModal") { $("#localModal").classList.add("hidden"); } });
$("#localRefresh").addEventListener("click", () => loadLocal());
$("#localCancelar").addEventListener("click", cancelarDescarga);
$("#localCarpeta").addEventListener("click", () => abrirLocal("modelos"));
$("#localOllamaWeb").addEventListener("click", () => abrirLocal("ollama_download"));
$("#localLmDescargar").addEventListener("click", () => abrirLocal("lmstudio_download"));
$("#localLmDocs").addEventListener("click", () => abrirLocal("lmstudio_docs"));
$("#localBuscar").addEventListener("input", (e) => { LOCAL.filtro = e.target.value; renderLocal(); });
$("#localLigero").addEventListener("change", (e) => { LOCAL.ligero = e.target.checked; renderLocal(); });
$("#localInstalados").addEventListener("change", (e) => { LOCAL.instalados = e.target.checked; renderLocal(); });
$("#spModelsLoad").addEventListener("click", () => loadSetupModels());
$("#spBuscar").addEventListener("input", renderSetupModels);
$("#spKey").addEventListener("change", () => { if (($("#spKey").value || "").trim()) loadSetupModels(); });
window.openLocal = openLocal;
