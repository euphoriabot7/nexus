/* ============================================================
   NEXUS · panel de control (resumen, tareas, proyecto, registro, red)
   ============================================================ */
(function () {
  const P = { tab: "resumen", days: 30, a: null, tasks: [], poll: null, projPath: "", projFile: "" };

  const nf = (n) => (n || 0).toLocaleString("es-ES");
  const compact = (n) => {
    n = n || 0;
    if (n >= 1e9) return (n / 1e9).toFixed(2) + "G";
    if (n >= 1e6) return (n / 1e6).toFixed(2) + "M";
    if (n >= 1e3) return (n / 1e3).toFixed(1) + "k";
    return String(n);
  };
  const money = (v) => "$" + (v || 0).toFixed(v >= 1 ? 2 : 4);
  const bytes = (n) => {
    if (!n) return "";
    if (n < 1024) return n + " B";
    if (n < 1048576) return (n / 1024).toFixed(1) + " KB";
    return (n / 1048576).toFixed(1) + " MB";
  };
  const dt = (ts) => new Date(ts * 1000).toLocaleString("es-ES", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
  const IMG = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".avif", ".ico"];
  const CODE = [".html", ".htm", ".css", ".js", ".json", ".md", ".txt", ".py", ".sh", ".yml", ".yaml", ".toml", ".csv", ".ts", ".jsx", ".tsx", ".vue", ".sql", ".xml", ".ini", ".conf", ".log", ".env"];

  /* ---------------------------- abrir / cerrar --------------------------- */
  window.openPanel = function (tab) {
    $("#panel").classList.remove("hidden");
    if (tab) setTab(tab);
    else loadTab(P.tab);
    applyRain();
  };
  window.closePanel = function () {
    $("#panel").classList.add("hidden");
    stopRain();
    if (P.poll) { clearInterval(P.poll); P.poll = null; }
  };

  function setTab(tab) {
    P.tab = tab;
    document.querySelectorAll(".panel-tab").forEach((s) => s.classList.toggle("on", s.dataset.tab === tab));
    document.querySelectorAll(".ptab").forEach((b) => b.classList.toggle("on", b.dataset.tab === tab));
    loadTab(tab);
  }

  window.setPanelTab = setTab;
  window.openProject = openProject;

  /** Previsualiza un archivo absoluto desde fuera del panel (lo usa el chat). */
  window.previewProjectFile = async function (path) {
    if (!path) return;
    path = String(path);
    const dir = path.replace(/\/[^/]*$/, "") || "/";
    const ext = (path.match(/\.[^./]+$/) || [""])[0].toLowerCase();
    if (P.projPath !== dir) {
      P.projPath = dir;  // antes de abrir el panel: evita que loadTab cargue otra carpeta
      window.openPanel("proyecto");
      const ok = await openProject(dir);
      if (ok === false) { if (P.projPath === dir) P.projPath = ""; return; }
    } else {
      window.openPanel("proyecto");
    }
    previewFile(path, ext);
  };

  function loadTab(tab) {
    if (tab === "resumen") loadAnalytics();
    else if (tab === "tareas") { fillTaskSelects(); loadTasks(); startTaskPoll(); }
    else if (tab === "proyecto") { if (!P.projPath) { $("#projPath").value = (state.chat && state.chat.workdir) || state.home || ""; openProject($("#projPath").value); } }
    else if (tab === "registro") loadLog();
    else if (tab === "red") loadLan();
  }

  /* ------------------------------- resumen ------------------------------- */
  async function loadAnalytics() {
    try { P.a = await api("/api/analytics?days=" + P.days); }
    catch (e) { $("#kpis").innerHTML = `<div class="empty-note">No se pudo cargar la analítica</div>`; return; }
    renderKpis(P.a); renderDaily(P.a.per_day); renderModels(P.a.per_model); renderHour(P.a.per_hour); renderWeek(P.a.per_weekday);
  }

  function kpi(val, lab) { return `<div class="kpi"><div class="k-val">${val}</div><div class="k-lab">${lab}</div></div>`; }

  function renderKpis(a) {
    const t = a.totals;
    $("#kpis").innerHTML =
      kpi(compact(t.tokens_total), t("kpi_tokens")) +
      kpi(compact(t.tokens_in) + " / " + compact(t.tokens_out), t("kpi_in_out")) +
      kpi(nf(t.calls), t("kpi_calls")) +
      kpi(money(t.cost_api), t("kpi_cost")) +
      kpi(t.hours_agent + " h", t("kpi_agent_hours")) +
      kpi(t.hours_app + " h", t("kpi_app_hours")) +
      kpi(nf(t.tool_calls), t("kpi_tools")) +
      kpi(nf(t.models), t("kpi_models"));
  }

  function renderDaily(series) {
    const w = 720, h = 190, pad = { l: 40, r: 10, t: 12, b: 22 };
    const n = series.length || 1;
    const max = Math.max(1, ...series.map((d) => d.tokens_in + d.tokens_out));
    const iw = (w - pad.l - pad.r) / n;
    const bw = Math.max(2, iw * 0.66);
    let bars = "";
    const grid = [0.25, 0.5, 0.75, 1].map((f) => {
      const y = pad.t + (1 - f) * (h - pad.t - pad.b);
      return `<line class="bar-grid" x1="${pad.l}" y1="${y.toFixed(1)}" x2="${w - pad.r}" y2="${y.toFixed(1)}"/>`
        + `<text class="axis" x="4" y="${(y + 3).toFixed(1)}">${compact(max * f)}</text>`;
    }).join("");
    series.forEach((d, i) => {
      const x = pad.l + i * iw + (iw - bw) / 2;
      const total = h - pad.t - pad.b;
      const hIn = (d.tokens_in / max) * total;
      const hOut = (d.tokens_out / max) * total;
      const yOut = pad.t + total - hIn - hOut;
      const yIn = pad.t + total - hIn;
      if (hIn > 0) bars += `<rect class="bar-in" x="${x.toFixed(1)}" y="${yIn.toFixed(1)}" width="${bw.toFixed(1)}" height="${hIn.toFixed(1)}"><title>${d.date}: ${nf(d.tokens_in)} entrada</title></rect>`;
      if (hOut > 0) bars += `<rect class="bar-out" x="${x.toFixed(1)}" y="${yOut.toFixed(1)}" width="${bw.toFixed(1)}" height="${hOut.toFixed(1)}"><title>${d.date}: ${nf(d.tokens_out)} salida</title></rect>`;
      if (hIn + hOut === 0) bars += `<rect x="${x.toFixed(1)}" y="${(pad.t + total - 1).toFixed(1)}" width="${bw.toFixed(1)}" height="1" fill="var(--p-line)"/>`;
    });
    const step = Math.max(1, Math.ceil(n / 7));
    let labels = "";
    series.forEach((d, i) => {
      if (i % step) return;
      const x = pad.l + i * iw + iw / 2;
      labels += `<text class="axis" x="${x.toFixed(1)}" y="${h - 6}" text-anchor="middle">${d.date.slice(5)}</text>`;
    });
    $("#chartDaily").innerHTML = `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">${grid}${bars}${labels}</svg>
      <div class="wb-lab"><span>■ entrada</span><span style="flex:none;width:auto">■ salida</span></div>`;
  }

  function renderModels(list) {
    if (!list.length) { $("#modelTable").innerHTML = `<div class="empty-note">Sin uso registrado todavía</div>`; return; }
    const max = Math.max(1, ...list.map((m) => m.tokens_total));
    let rows = "";
    list.forEach((m) => {
      const pct = Math.round((m.tokens_total / max) * 100);
      rows += `<tr>
        <td><div class="mname">${esc(m.model)}</div><div class="prov">${esc(m.provider || "—")} · ${(m.sources || []).join("+")}</div>
          <div class="share"><i style="width:${pct}%"></i></div></td>
        <td class="num">${nf(m.calls)}</td>
        <td class="num">${compact(m.tokens_in)}</td>
        <td class="num">${compact(m.tokens_out)}</td>
        <td class="num">${m.cache_read ? compact(m.cache_read) : "—"}</td>
        <td class="num">${money(m.cost_api)}</td>
      </tr>`;
    });
    $("#modelTable").innerHTML = `<table class="mtbl"><thead><tr>
      <th>modelo</th><th class="num">llamadas</th><th class="num">entrada</th><th class="num">salida</th><th class="num">caché</th><th class="num">coste</th>
      </tr></thead><tbody>${rows}</tbody></table>`;
  }

  function renderHour(hour) {
    const max = Math.max(1, ...hour);
    let cells = "";
    for (let i = 0; i < 24; i++) {
      const a = hour[i] / max;
      const bg = a ? `rgba(var(--p-accent-rgb),${(0.15 + a * 0.85).toFixed(2)})` : "var(--p-line)";
      cells += `<div style="background:${a ? "" : "var(--p-line)"};${a ? `background:color-mix(in srgb,var(--p-accent) ${Math.round(15 + a * 85)}%, transparent)` : ""}" title="${i}:00 — ${hour[i]}"></div>`;
    }
    let labs = "";
    for (let i = 0; i < 24; i++) labs += `<span>${i % 3 === 0 ? i : ""}</span>`;
    $("#hourHeat").innerHTML = `<div class="hint" style="margin-bottom:6px">mensajes por hora del día</div><div class="heat">${cells}</div><div class="heat-lab">${labs}</div>`;
  }

  function renderWeek(wd) {
    const names = ["L", "M", "X", "J", "V", "S", "D"];
    const max = Math.max(1, ...wd);
    let bars = "", labs = "";
    for (let i = 0; i < 7; i++) {
      const h = Math.max(3, Math.round((wd[i] / max) * 84));
      bars += `<div class="wb" style="height:${h}px" title="${wd[i]}"></div>`;
      labs += `<span>${names[i]}</span>`;
    }
    $("#weekBars").innerHTML = `<div class="hint" style="margin-bottom:6px">por día de la semana</div><div class="weekbars">${bars}</div><div class="wb-lab">${labs}</div>`;
  }

  function exportCsv() {
    if (!P.a) return;
    const head = "modelo,proveedor,llamadas,tokens_entrada,tokens_salida,cache,fuentes,coste_api_usd\n";
    const rows = P.a.per_model.map((m) => [m.model, m.provider, m.calls, m.tokens_in, m.tokens_out,
      m.cache_read, (m.sources || []).join("+"), m.cost_api.toFixed(6)].join(",")).join("\n");
    const blob = new Blob([head + rows], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = "nexus-gasto-modelos.csv"; a.click();
  }

  /* -------------------------------- tareas ------------------------------- */
  function fillTaskSelects() {
    const prov = $("#taskProvider"), mod = $("#taskModel");
    if (prov.options.length) return;
    prov.innerHTML = "";
    Object.entries(state.providers).forEach(([pid, p]) => {
      const o = document.createElement("option"); o.value = pid; o.textContent = p.label; prov.appendChild(o);
    });
    const fill = () => {
      const p = state.providers[prov.value];
      mod.innerHTML = "";
      (p ? p.models : []).forEach((m) => { const o = document.createElement("option"); o.value = m; o.textContent = m; mod.appendChild(o); });
      if (state.chat && state.chat.model) mod.value = state.chat.model;
    };
    prov.addEventListener("change", fill);
    fill();
    $("#taskWorkdir").value = (state.chat && state.chat.workdir) || "";
    $("#taskToolsets").value = (state.chat && state.chat.toolsets) || "";
  }

  async function createTask() {
    const prompt = $("#taskPrompt").value.trim();
    if (!prompt) return toast("Escribe el encargo");
    const body = { title: $("#taskTitle").value.trim(), prompt, workdir: $("#taskWorkdir").value.trim(),
      provider: $("#taskProvider").value, model: $("#taskModel").value, toolsets: $("#taskToolsets").value.trim() };
    $("#taskCreate").disabled = true;
    try { await api("/api/tasks", { method: "POST", body }); $("#taskPrompt").value = ""; $("#taskTitle").value = ""; toast("Trabajo encargado"); await loadTasks(); }
    catch (e) { toast("No se pudo encargar"); }
    $("#taskCreate").disabled = false;
  }

  async function loadTasks() {
    try { P.tasks = (await api("/api/tasks")).tasks; } catch { return; }
    const box = $("#taskList");
    if (!P.tasks.length) { box.innerHTML = `<div class="empty-note">Sin trabajos todavía. Encarga uno arriba.</div>`; return; }
    box.innerHTML = "";
    for (const t of P.tasks) {
      const el = document.createElement("div");
      el.className = "task-item";
      const running = t.status === "running" || t.status === "queued";
      let out = "";
      if (running) { try { out = ((await api(`/api/tasks/${t.id}`)).task || {}).output || ""; } catch {} }
      else { try { out = ((await api(`/api/tasks/${t.id}`)).task || {}).output || ""; } catch {} }
      el.innerHTML = `
        <div class="task-head">
          <span class="t-title">${esc(t.title)}</span>
          <span class="st ${t.status}">${t.status}</span>
          <span class="task-meta" style="margin:0 0 0 auto">${esc(t.model || "")} ${t.tokens ? "· " + compact(t.tokens) + " tok" : ""}</span>
        </div>
        <div class="task-meta">${esc(t.workdir || "")} · ${dt(t.created)}${t.finished ? " · " + Math.round(t.finished - t.created) + "s" : ""}${t.error ? " · ↯ " + esc(t.error) : ""}</div>
        ${out ? `<div class="task-out">${esc(out.slice(-4000))}</div>` : ""}
        <div class="task-actions">
          ${running ? `<button class="mini-btn" data-a="cancel">■ ${t("t_stop")}</button>` : ""}
          <button class="mini-btn" data-a="del">Borrar</button>
        </div>`;
      el.querySelector('[data-a="cancel"]')?.addEventListener("click", async () => { await api(`/api/tasks/${t.id}/cancel`, { method: "POST" }); loadTasks(); });
      el.querySelector('[data-a="del"]').addEventListener("click", async () => { await api(`/api/tasks/${t.id}`, { method: "DELETE" }); loadTasks(); });
      box.appendChild(el);
    }
  }

  function startTaskPoll() {
    if (P.poll) clearInterval(P.poll);
    P.poll = setInterval(() => { if (P.tab === "tareas" && !$("#panel").classList.contains("hidden")) loadTasks(); }, 2500);
  }

  /* ------------------------------- proyecto ------------------------------ */
  async function openProject(path) {
    const req = (P.projReq = (P.projReq || 0) + 1);
    let d;
    try { d = await api("/api/project?path=" + encodeURIComponent(path)); }
    catch { toast("No se pudo abrir esa carpeta"); return false; }
    if (req !== P.projReq) return false;  // una peticion mas nueva gano
    P.projPath = d.path; $("#projPath").value = d.path;
    const box = $("#projList");
    box.innerHTML = "";
    if (d.parent) {
      const up = document.createElement("div"); up.className = "proj-item";
      up.innerHTML = `<span class="pi-ico">↑</span> ..`;
      up.addEventListener("click", () => openProject(d.parent));
      box.appendChild(up);
    }
    (d.entries || []).forEach((e) => {
      const el = document.createElement("div"); el.className = "proj-item";
      const ico = e.type === "dir" ? "▸" : (IMG.includes(e.ext) ? "🖼" : "▫");
      if (e.type === "file") el.dataset.path = d.path + "/" + e.name;
      el.innerHTML = `<span class="pi-ico">${ico}</span> ${esc(e.name)} <span class="pi-size">${e.type === "file" ? bytes(e.size) : ""}</span>`;
      el.addEventListener("click", () => { if (e.type === "dir") openProject(d.path + "/" + e.name); else previewFile(d.path + "/" + e.name, e.ext); });
      box.appendChild(el);
    });
    if (!(d.entries || []).length) box.innerHTML += `<div class="empty-note">carpeta vacía</div>`;
  }

  function previewFile(path, ext) {
    P.projFile = path;
    $("#projFile").textContent = path;
    document.querySelectorAll("#projList .proj-item").forEach((it) => it.classList.toggle("sel", it.dataset.path === path));
    const url = "/preview" + path;
    const box = $("#projPreview");
    if (ext === ".html" || ext === ".htm") {
      box.innerHTML = `<iframe src="${url}"></iframe>`;
    } else if (IMG.includes(ext)) {
      box.innerHTML = `<img src="${url}" alt="">`;
    } else if (CODE.includes(ext) || true) {
      fetch(url).then((r) => r.text()).then((txt) => {
        box.innerHTML = `<pre>${esc(txt.slice(0, 400000))}</pre>`;
      }).catch(() => { box.innerHTML = `<div class="proj-empty">No se puede mostrar</div>`; });
    }
  }

  /* -------------------------------- registro ----------------------------- */
  async function loadLog() {
    const kind = $("#logFilter").value;
    let evs = [];
    try { evs = (await api("/api/log?limit=300" + (kind ? "&kind=" + encodeURIComponent(kind) : ""))).events; } catch {}
    const box = $("#logList");
    if (!evs.length) { box.innerHTML = `<div class="empty-note">${t("no_activity")}</div>`; return; }
    box.innerHTML = evs.map((e) => `<div class="log-row">
        <span class="lt">${dt(e.ts)}</span>
        <span class="lk">${esc(e.kind)}</span>
        <span class="ld" title="${esc(e.detail)}">${esc(e.detail || "—")}${e.model ? " · " + esc(e.model) : ""}</span>
        <span class="lc">${e.tokens ? compact(e.tokens) + " tok" : ""}${e.cost ? " " + money(e.cost) : ""}</span>
      </div>`).join("");
  }

  /* ---------------------------------- red -------------------------------- */
  async function loadLan() {
    let d;
    try { d = await api("/api/lan"); } catch { return; }
    const ips = d.addresses || [];
    const urls = ips.map((ip) => `http://${ip}:${d.port}`).join("  ·  ") || "sin IP de red detectada";
    const first = ips[0] ? `http://${ips[0]}:${d.port}` : "";
    $("#lanInfo").innerHTML = `
      <div><span class="hint">dirección en la red</span><div class="lan-url">${urls}</div></div>
      <div><span class="hint">enlace con acceso directo</span><div class="lan-url" id="lanFull">${first ? first + "/login?token=" + d.token : "—"}</div></div>
      <div><span class="hint">token</span><div class="lan-token">${d.token}</div></div>
      <div><span class="hint">estado</span><div>${d.enabled ? "activo" : "desactivado (NEXUS_LAN=0)"}</div></div>`;
    $("#lanLink").textContent = first ? first + "/login?token=" + d.token.slice(0, 10) + "…" : "—";
    $("#lanCopy").onclick = () => {
      if (!first) return toast("Sin IP de red");
      navigator.clipboard.writeText(first + "/login?token=" + d.token);
      toast("Enlace copiado — ábrelo en el otro dispositivo");
    };
  }

  /* ----------------------------- temas + lluvia -------------------------- */
  function applyTheme(name) {
    $("#panel").setAttribute("data-theme", name);
    LS.set("nexus_dashTheme", name);
    $("#dashTheme").value = name;
    applyRain();
  }

  let rainRAF = null;
  function stopRain() { if (rainRAF) cancelAnimationFrame(rainRAF); rainRAF = null; }
  function applyRain() {
    const c = $("#rainCanvas");
    const want = $("#panel").getAttribute("data-theme") === "matrix" && !$("#panel").classList.contains("hidden");
    c.classList.toggle("hidden", !want);
    stopRain();
    if (!want) return;
    const ctx = c.getContext("2d");
    const fit = () => { c.width = c.clientWidth; c.height = c.clientHeight; };
    fit();
    const cols = Math.floor(c.width / 14) || 1;
    const drops = Array.from({ length: cols }, () => Math.random() * c.height);
    const glyphs = "アイウエオカキクケコサシスセソタチツテトナニヌネノ01ハヒフヘホ";
    const draw = () => {
      ctx.fillStyle = "rgba(1,4,2,0.09)";
      ctx.fillRect(0, 0, c.width, c.height);
      ctx.fillStyle = "#00ff7b";
      ctx.font = "12px monospace";
      for (let i = 0; i < drops.length; i++) {
        ctx.fillText(glyphs[(Math.random() * glyphs.length) | 0], i * 14, drops[i]);
        drops[i] = drops[i] > c.height && Math.random() > 0.975 ? 0 : drops[i] + 14;
      }
      rainRAF = requestAnimationFrame(draw);
    };
    draw();
  }

  /* -------------------------------- eventos ------------------------------ */
  document.querySelectorAll(".ptab").forEach((b) => b.addEventListener("click", () => setTab(b.dataset.tab)));
  $("#panelClose").addEventListener("click", closePanel);
  $("#dashTheme").addEventListener("change", (e) => applyTheme(e.target.value));
  $("#daysSel").addEventListener("change", (e) => { P.days = parseInt(e.target.value, 10) || 30; loadAnalytics(); });
  $("#refreshAnalytics").addEventListener("click", loadAnalytics);
  $("#exportCsv").addEventListener("click", exportCsv);
  $("#taskCreate").addEventListener("click", createTask);
  $("#projOpen").addEventListener("click", () => openProject($("#projPath").value.trim()));
  $("#projUp").addEventListener("click", () => P.projPath && openProject(P.projPath.replace(/\/[^/]*$/, "") || "/"));
  $("#projRefresh").addEventListener("click", () => P.projPath && openProject(P.projPath));
  $("#projPath").addEventListener("keydown", (e) => { if (e.key === "Enter") openProject(e.target.value.trim()); });
  $("#projReload").addEventListener("click", () => { if (P.projFile) previewFile(P.projFile, P.projFile.slice(P.projFile.lastIndexOf("."))); });
  $("#projNewTab").addEventListener("click", () => { if (P.projFile) window.open("/preview" + P.projFile, "_blank"); });
  $("#logFilter").addEventListener("change", loadLog);
  $("#logRefresh").addEventListener("click", loadLog);

  /* arranque del panel */
  applyTheme(LS.get("nexus_dashTheme", "default"));

  // latido para medir el tiempo de uso de la app
  const ping = () => fetch("/api/ping", { method: "POST" }).catch(() => {});
  ping();
  setInterval(ping, 60000);
})();
