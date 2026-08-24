(() => {
  "use strict";
  const OPT_IN_KEY = "eea-europa-overload";
  const CATALOG_URL = "/wallpapers.json";
  const VOTES_URL = "/api/wallpaper-votes";
  const stream = document.getElementById("wallpaper-stream");
  if (!stream) return;

  const imageUrl = (file, width) => `https://commons.wikimedia.org/wiki/Special:Redirect/file/${encodeURIComponent(file)}?width=${width}`;
  const sourceUrl = wallpaper => `https://commons.wikimedia.org/wiki/File:${encodeURIComponent(wallpaper.file)}`;
  const icon = path => `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="${path}" fill="currentColor"></path></svg>`;
  const icons = Object.freeze({
    up: icon("M9 21H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h4m0 11V10m0 11h8.1a2 2 0 0 0 1.96-1.61l1.2-6A2 2 0 0 0 18.3 11H15l.55-3.2A3.2 3.2 0 0 0 12.4 4L9 10"),
    down: icon("M15 3h4a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-4M15 3v11m0-11H6.9a2 2 0 0 0-1.96 1.61l-1.2 6A2 2 0 0 0 5.7 13H9l-.55 3.2A3.2 3.2 0 0 0 11.6 20l3.4-6"),
    previous: icon("M14.7 5.3 8 12l6.7 6.7-1.4 1.4L5.2 12l8.1-8.1z"),
    next: icon("m9.3 18.7 6.7-6.7-6.7-6.7 1.4-1.4 8.1 8.1-8.1 8.1z"),
  });
  const readOptIn = () => { try { return localStorage.getItem(OPT_IN_KEY) === "true"; } catch (_error) { return false; } };
  const persistOptIn = enabled => { try { localStorage.setItem(OPT_IN_KEY, String(enabled)); } catch (_error) {} };
  const randomIndex = maximum => globalThis.crypto?.getRandomValues ? crypto.getRandomValues(new Uint32Array(1))[0] % maximum : Math.floor(Math.random() * maximum);
  function shuffled(items) {
    const result = [...items];
    for (let index = result.length - 1; index > 0; index -= 1) {
      const target = randomIndex(index + 1);
      [result[index], result[target]] = [result[target], result[index]];
    }
    return result;
  }

  let catalog = [], sequence = [], active = false, starting = null, votesAvailable = false, votePending = false, voteError = "";
  let activeIndex = null, focusBeforeLightbox = null, lockedScrollY = 0, bodyStyles = null;
  let viewportHeight = Math.max(1, window.innerHeight), scrollFrame = null, layoutTimer = null, resizeObserver = null;
  const voteStates = new Map(), panels = [], preloadedHighResolution = new Set();

  const lightbox = document.createElement("section");
  lightbox.id = "wallpaper-lightbox";
  lightbox.className = "wallpaper-lightbox";
  lightbox.hidden = true;
  lightbox.tabIndex = -1;
  lightbox.setAttribute("role", "dialog");
  lightbox.setAttribute("aria-modal", "true");
  lightbox.setAttribute("aria-labelledby", "wallpaper-lightbox-title");
  const card = document.createElement("div"); card.className = "wallpaper-lightbox-card";
  const button = (className, label, markup) => {
    const element = document.createElement("button");
    element.type = "button"; element.className = className; element.setAttribute("aria-label", label); element.innerHTML = markup;
    return element;
  };
  const closeButton = button("wallpaper-lightbox-close", "Bildergalerie schließen", '<img src="/assets/europe-star.svg" alt="">');
  const previousButton = button("wallpaper-gallery-previous", "Vorheriges Bild", icons.previous);
  const nextButton = button("wallpaper-gallery-next", "Nächstes Bild", icons.next);
  const image = document.createElement("img"); image.className = "wallpaper-lightbox-image";
  const info = document.createElement("div"); info.className = "wallpaper-lightbox-info";
  const title = document.createElement("h2"); title.id = "wallpaper-lightbox-title";
  const position = document.createElement("p"); position.className = "wallpaper-gallery-position";
  const details = document.createElement("p"); details.className = "wallpaper-lightbox-details";
  const attribution = document.createElement("p"); attribution.className = "wallpaper-lightbox-attribution";
  const source = document.createElement("a"); source.className = "wallpaper-lightbox-source"; source.target = "_blank"; source.rel = "noopener noreferrer"; source.textContent = "Quelle auf Wikimedia Commons";
  const voteSummary = document.createElement("p"); voteSummary.className = "wallpaper-vote-summary"; voteSummary.setAttribute("role", "status");
  const reactions = document.createElement("div"); reactions.className = "wallpaper-reactions"; reactions.setAttribute("aria-label", "Öffentliche Abstimmung");
  const upButton = button("wallpaper-vote-up", "Daumen hoch vergeben", icons.up); upButton.dataset.reaction = "up";
  const downButton = button("wallpaper-vote-down", "Daumen runter vergeben", icons.down); downButton.dataset.reaction = "down";
  reactions.append(voteSummary, upButton, downButton);
  info.append(title, position, details, attribution, source, reactions);
  card.append(closeButton, previousButton, nextButton, image, info); lightbox.append(card); document.body.append(lightbox);

  async function loadCatalog() {
    if (catalog.length) return catalog;
    const response = await fetch(CATALOG_URL, {credentials: "same-origin"});
    const payload = await response.json();
    if (!response.ok || !Array.isArray(payload) || payload.length !== 250 || payload.some(item => !item?.id || !item.file)) throw new Error("Der Bilderkatalog konnte nicht geladen werden.");
    catalog = payload; return catalog;
  }
  async function loadVotes() {
    const response = await fetch(VOTES_URL, {credentials: "same-origin"});
    const payload = await response.json();
    if (!response.ok || !Array.isArray(payload.wallpapers)) throw new Error(payload.error || "Abstimmung nicht erreichbar");
    voteStates.clear(); payload.wallpapers.forEach(state => voteStates.set(state.wallpaper_id, state)); votesAvailable = true;
  }
  const scoreLabel = score => score > 0 ? `+${score}` : String(score || 0);
  function updateVoteUi() {
    const wallpaper = activeIndex === null ? null : sequence[activeIndex];
    const state = wallpaper && voteStates.get(wallpaper.id), own = state?.own_vote || null;
    upButton.setAttribute("aria-pressed", String(own === 1)); downButton.setAttribute("aria-pressed", String(own === -1));
    upButton.disabled = !votesAvailable || votePending; downButton.disabled = !votesAvailable || votePending;
    voteSummary.hidden = false;
    if (!votesAvailable) { voteSummary.textContent = "Öffentliche Abstimmung derzeit nicht erreichbar."; return; }
    if (!state) { voteSummary.textContent = "Abstimmung wird geladen …"; return; }
    if (!own) {
      voteSummary.hidden = !voteError;
      voteSummary.textContent = voteError ? `Nicht gespeichert: ${voteError}` : "";
      return;
    }
    voteSummary.textContent = `${state.upvotes} 👍 · ${state.downvotes} 👎 · Score ${scoreLabel(state.score)} · Platz ${state.rank}${state.rank_shared ? " (geteilt)" : ""} von ${catalog.length}${voteError ? ` · Nicht gespeichert: ${voteError}` : ""}`;
  }
  function preloadGalleryImages() {
    if (activeIndex === null || !sequence.length) return;
    for (const offset of [-1, 0, 1]) {
      const wallpaper = sequence[(activeIndex + offset + sequence.length) % sequence.length];
      if (!wallpaper || preloadedHighResolution.has(wallpaper.id)) continue;
      preloadedHighResolution.add(wallpaper.id);
      const preload = new Image(); preload.decoding = "async"; preload.src = imageUrl(wallpaper.file, 3840);
    }
  }
  function lockScroll() {
    lockedScrollY = window.scrollY;
    bodyStyles = {overflow: document.body.style.overflow, position: document.body.style.position, top: document.body.style.top, width: document.body.style.width};
    document.body.classList.add("overload-lightbox-open"); Object.assign(document.body.style, {overflow: "hidden", position: "fixed", top: `-${lockedScrollY}px`, width: "100%"});
  }
  function unlockScroll() {
    if (bodyStyles) Object.assign(document.body.style, bodyStyles);
    bodyStyles = null; document.body.classList.remove("overload-lightbox-open"); window.scrollTo({top: lockedScrollY, behavior: "auto"});
  }
  function renderLightbox() {
    const wallpaper = activeIndex === null ? null : sequence[activeIndex]; if (!wallpaper) return;
    title.textContent = wallpaper.title; position.textContent = `${activeIndex + 1} / ${sequence.length}`; details.textContent = wallpaper.country;
    attribution.textContent = `${wallpaper.author} · ${wallpaper.license}`; source.href = sourceUrl(wallpaper); image.src = imageUrl(wallpaper.file, 3840); image.alt = wallpaper.title;
    updateVoteUi(); preloadGalleryImages();
  }
  function showIndex(index) { if (sequence.length) { activeIndex = (index + sequence.length) % sequence.length; renderLightbox(); } }
  function closeLightbox({restoreFocus = true} = {}) {
    if (activeIndex === null) return;
    lightbox.classList.remove("is-open"); lightbox.hidden = true; image.removeAttribute("src"); activeIndex = null; unlockScroll();
    if (restoreFocus && focusBeforeLightbox?.isConnected) focusBeforeLightbox.focus({preventScroll: true}); focusBeforeLightbox = null;
  }
  function openLightbox(index, panel) {
    if (!active || !sequence[index]) return;
    focusBeforeLightbox = panel; lockScroll(); lightbox.hidden = false; showIndex(index); requestAnimationFrame(() => lightbox.classList.add("is-open")); closeButton.focus({preventScroll: true});
  }
  async function submitVote(action) {
    const wallpaper = activeIndex === null ? null : sequence[activeIndex]; if (!wallpaper || !votesAvailable || votePending) return;
    const current = voteStates.get(wallpaper.id); const requested = current?.own_vote === (action === "up" ? 1 : -1) ? "clear" : action;
    voteError = ""; votePending = true; updateVoteUi();
    try {
      const response = await fetch(VOTES_URL, {method: "POST", credentials: "same-origin", headers: {"Content-Type": "application/json"}, body: JSON.stringify({wallpaper_id: wallpaper.id, vote: requested})});
      const payload = await response.json(); if (!response.ok || !payload.wallpaper) throw new Error(payload.error || "Stimme konnte nicht gespeichert werden");
      voteStates.set(payload.wallpaper.wallpaper_id, payload.wallpaper);
    } catch (error) {
      voteError = error.message;
    } finally { votePending = false; updateVoteUi(); }
  }
  function handleLightboxKeydown(event) {
    if (activeIndex === null) return;
    if (event.key === "Escape") { event.preventDefault(); closeLightbox(); return; }
    if (event.key === "ArrowLeft") { event.preventDefault(); showIndex(activeIndex - 1); return; }
    if (event.key === "ArrowRight") { event.preventDefault(); showIndex(activeIndex + 1); return; }
    if (event.key !== "Tab") return;
    const focusable = [...lightbox.querySelectorAll("button, a[href]")].filter(item => !item.disabled), first = focusable[0], last = focusable.at(-1);
    if (!first || !last) return;
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
  function postcardStep() { return Math.max(220, viewportHeight * .28); }
  function createPanel(index) {
    const panel = document.createElement("div"), wallpaper = sequence[index];
    panel.className = "wallpaper-panel"; panel.dataset.wallpaperIndex = String(index); panel.tabIndex = 0; panel.setAttribute("role", "button"); panel.setAttribute("aria-label", `Postkarte öffnen: ${wallpaper.title}`);
    panel.style.top = `${index * postcardStep() + Math.max(24, viewportHeight * .06)}px`; panel.style.setProperty("--postcard-index", String(index));
    const caption = document.createElement("div"); caption.className = "wallpaper-caption"; caption.innerHTML = `<strong></strong><span></span>`; caption.querySelector("strong").textContent = wallpaper.title; caption.querySelector("span").textContent = `${wallpaper.country} · ${wallpaper.author}`; panel.append(caption);
    panel.addEventListener("click", () => openLightbox(index, panel)); panel.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); openLightbox(index, panel); } });
    stream.append(panel); panels.push(panel); return panel;
  }
  function loadPanel(panel) {
    if (!active || panel.dataset.loaded || panel.dataset.loading) return;
    const wallpaper = sequence[Number(panel.dataset.wallpaperIndex)]; if (!wallpaper) return; panel.dataset.loading = "true";
    const preview = new Image(); preview.decoding = "async";
    preview.onload = () => { if (!active || !panel.isConnected) return; panel.style.backgroundImage = `url("${imageUrl(wallpaper.file, 960)}")`; panel.dataset.loaded = "true"; delete panel.dataset.loading; panel.classList.add("is-loaded"); };
    preview.onerror = () => { delete panel.dataset.loading; panel.classList.add("is-unavailable"); };
    preview.src = imageUrl(wallpaper.file, 960);
  }
  function centeredIndex() { return Math.min(panels.length - 1, Math.max(0, Math.floor((window.scrollY + viewportHeight / 2) / postcardStep()))); }
  function updateForScroll() { if (!active) return; scrollFrame = null; const index = centeredIndex(); [index - 1, index, index + 1].forEach(nearby => { if (panels[nearby]) loadPanel(panels[nearby]); }); }
  function scheduleScroll() { if (active && scrollFrame === null) scrollFrame = requestAnimationFrame(updateForScroll); }
  function layoutWallpapers() {
    if (!active) return; viewportHeight = Math.max(1, window.innerHeight); const main = document.querySelector("main");
    const height = Math.max(viewportHeight, main ? main.offsetTop + main.offsetHeight : document.documentElement.scrollHeight), needed = Math.min(sequence.length, Math.max(1, Math.ceil(height / postcardStep())));
    while (panels.length < needed) createPanel(panels.length);
    panels.forEach((panel, index) => { panel.style.top = `${index * postcardStep() + Math.max(24, viewportHeight * .06)}px`; panel.style.setProperty("--postcard-index", String(index)); }); stream.style.height = `${height}px`; updateForScroll();
  }
  function scheduleLayout() { if (active) { clearTimeout(layoutTimer); layoutTimer = setTimeout(layoutWallpapers, 120); } }
  function notifyState() { document.dispatchEvent(new CustomEvent("atlas-overload-change", {detail: {enabled: active}})); }
  async function start() {
    if (active || starting) return starting;
    starting = (async () => { try {
      await loadCatalog(); if (!readOptIn()) return; active = true; sequence = shuffled(catalog);
      try { await loadVotes(); } catch (_error) { votesAvailable = false; }
      layoutWallpapers(); window.addEventListener("scroll", scheduleScroll, {passive: true}); window.addEventListener("resize", scheduleLayout, {passive: true});
      if ("ResizeObserver" in window) { resizeObserver = new ResizeObserver(scheduleLayout); resizeObserver.observe(document.querySelector("main")); }
    } finally { starting = null; notifyState(); } })();
    return starting;
  }
  function stop() {
    closeLightbox({restoreFocus: false}); active = false; window.removeEventListener("scroll", scheduleScroll); window.removeEventListener("resize", scheduleLayout);
    if (scrollFrame !== null) cancelAnimationFrame(scrollFrame); scrollFrame = null; clearTimeout(layoutTimer); layoutTimer = null; resizeObserver?.disconnect(); resizeObserver = null;
    panels.splice(0).forEach(panel => panel.remove()); stream.replaceChildren(); stream.style.height = ""; sequence = []; preloadedHighResolution.clear(); notifyState();
  }
  function setEnabled(enabled) { persistOptIn(Boolean(enabled)); if (enabled) void start(); else stop(); }
  closeButton.addEventListener("click", () => closeLightbox()); previousButton.addEventListener("click", () => showIndex(activeIndex - 1)); nextButton.addEventListener("click", () => showIndex(activeIndex + 1));
  upButton.addEventListener("click", () => void submitVote("up")); downButton.addEventListener("click", () => void submitVote("down")); lightbox.addEventListener("click", event => { if (event.target === lightbox) closeLightbox(); }); document.addEventListener("keydown", handleLightboxKeydown);
  const controller = Object.freeze({setEnabled, isEnabled: () => active}); window.__atlasWallpaper = controller;
  window.__atlasWallpaperTest = {catalog: () => catalog, shuffled, imageUrl, showIndex, controller};
  if (readOptIn()) void start();
})();
