/* ============================================================
   NEXUS · motor de idiomas
   Los ficheros de app/lang/<codigo>.js registran su diccionario y aqui se
   resuelve el idioma activo, se aplican las traducciones al HTML y se
   reacciona al cambio (incluido el sentido de lectura RTL).
   ============================================================ */
(function () {
  const LANGS = [
    { code: "en", name: "English", dir: "ltr" },
    { code: "es", name: "Español", dir: "ltr" },
    { code: "zh", name: "中文", dir: "ltr" },
    { code: "ja", name: "日本語", dir: "ltr" },
    { code: "ko", name: "한국어", dir: "ltr" },
    { code: "ar", name: "العربية", dir: "rtl" },
    { code: "id", name: "Bahasa Indonesia", dir: "ltr" },
  ];
  const BASE = "es";          // idioma de referencia si falta una clave
  const STORE = "nexus_lang";

  window.NEXUS_LANGS = window.NEXUS_LANGS || {};
  window.NEXUS_LANG_LIST = LANGS;
  window.NEXUS_ADD_LANG = function (obj) {
    if (obj && obj.code) window.NEXUS_LANGS[obj.code] = obj;
  };

  function detect() {
    try {
      const guardado = localStorage.getItem(STORE);
      if (guardado && window.NEXUS_LANGS[guardado]) return guardado;
    } catch (e) {}
    const nav = (navigator.languages && navigator.languages[0]) || navigator.language || "";
    const l = String(nav).toLowerCase();
    if (l.startsWith("es")) return "es";
    if (l.startsWith("zh")) return "zh";
    if (l.startsWith("ja")) return "ja";
    if (l.startsWith("ko")) return "ko";
    if (l.startsWith("ar")) return "ar";
    if (l.startsWith("id") || l.startsWith("in")) return "id";
    if (l.startsWith("en")) return "en";
    return "en";
  }

  const I18N = {
    lang: null,
    langs: LANGS,
    t(key, vars) {
      const dic = (window.NEXUS_LANGS[I18N.lang] || {}).strings || {};
      const base = (window.NEXUS_LANGS[BASE] || {}).strings || {};
      let txt = dic[key];
      if (txt === undefined) txt = base[key];
      if (txt === undefined) txt = key;
      if (vars) {
        txt = String(txt).replace(/\{(\w+)\}/g, (m, k) => (vars[k] !== undefined ? vars[k] : m));
      }
      return txt;
    },
    setLang(code, opts) {
      if (!window.NEXUS_LANGS[code]) code = BASE;
      I18N.lang = code;
      try { localStorage.setItem(STORE, code); } catch (e) {}
      const info = LANGS.find((x) => x.code === code) || LANGS[0];
      document.documentElement.lang = code;
      document.documentElement.dir = info.dir;
      document.body.classList.toggle("rtl", info.dir === "rtl");
      I18N.apply(document);
      if (!opts || !opts.silent) {
        const sel = document.querySelector("#langSelect");
        if (sel) sel.value = code;
      }
      if (typeof window.onLangChange === "function") window.onLangChange(code);
      return code;
    },
    apply(root) {
      const r = root || document;
      r.querySelectorAll("[data-i18n]").forEach((el) => {
        el.textContent = I18N.t(el.dataset.i18n);
      });
      r.querySelectorAll("[data-i18n-html]").forEach((el) => {
        el.innerHTML = I18N.t(el.dataset.i18nHtml);
      });
      r.querySelectorAll("[data-i18n-ph]").forEach((el) => {
        el.placeholder = I18N.t(el.dataset.i18nPh);
      });
      r.querySelectorAll("[data-i18n-title]").forEach((el) => {
        el.title = I18N.t(el.dataset.i18nTitle);
      });
    },
    name(code) {
      const l = LANGS.find((x) => x.code === (code || I18N.lang));
      return l ? l.name : code;
    },
  };

  window.I18N = I18N;
  window.t = (k, v) => I18N.t(k, v);
  window.setLang = (c, o) => I18N.setLang(c, o);
  window.initLang = function () {
    return I18N.setLang(detect());
  };
})();
