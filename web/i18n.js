/* Local, version-pinned i18next. No translation network calls or third-party CDN. */
(() => {
  "use strict";
  const language = document.documentElement.lang === "en" ? "en" : "de";
  const instance = window.i18next.createInstance();
  instance.init({
    lng: language, fallbackLng: "en", supportedLngs: ["de", "en"],
    resources: window.ATLAS_TRANSLATIONS, initImmediate: false,
    keySeparator: false, nsSeparator: false,
    // Callers use textContent or explicitly escape values at the HTML boundary.
    interpolation: {escapeValue: false}, returnEmptyString: false,
  });
  const t = (key, values = {}) => instance.t(key, values);
  const apiFetch = (path, options) => {
    const url = new URL(path, window.location.href);
    url.searchParams.set("lang", language);
    return fetch(url.pathname + url.search, options);
  };
  const stateKey = "eea-language-state";
  window.AtlasI18n = {language, locale: language === "en" ? "en-GB" : "de-DE", t, apiFetch};
  window.AtlasI18n.restoreState = () => {
    try {
      const saved = JSON.parse(sessionStorage.getItem(stateKey) || "null");
      sessionStorage.removeItem(stateKey);
      if (saved?.url === window.location.href && Date.now() - saved.time < 60_000) return saved.state;
    } catch (_) { /* Storage may be disabled; links still work. */ }
    return null;
  };
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-language]").forEach(link => {
      link.addEventListener("click", event => {
        if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        const nextLanguage = link.dataset.language;
        const url = new URL(window.location.href);
        url.searchParams.set("lang", nextLanguage);
        document.cookie = `eea_language=${nextLanguage}; Path=/; Max-Age=15552000; SameSite=Lax${location.protocol === "https:" ? "; Secure" : ""}`;
        try {
          sessionStorage.setItem(stateKey, JSON.stringify({
            url: url.href, time: Date.now(), state: window.AtlasI18n.captureState?.(),
          }));
        } catch (_) { /* Preference storage is optional. */ }
        event.preventDefault();
        window.location.assign(url.href);
      });
    });
  });
})();
