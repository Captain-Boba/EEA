const TABLE_METRIC_IDS = [
  "generation_twh",
  "consumption_twh",
  "consumption_per_capita_mwh",
  "renewable_share_pct",
  "fossil_share_pct",
  "nuclear_share_pct",
  "net_import_share_pct",
  "carbon_intensity_gco2eq_kwh",
  "price_avg_eur_mwh",
];
const STORAGE_METRIC_IDS = [
  "battery_energy_gwh",
  "battery_power_gw",
  "battery_duration_hours",
  "pumped_storage_energy_gwh",
  "pumped_storage_power_gw",
  "pumped_storage_duration_hours",
];
const EV_METRIC_IDS = [
  "bev_stock",
  "bev_new_registrations",
  "ev_battery_nominal_capacity_est_gwh",
];
const COMPARISON_PRESETS = ["ytd", "1y", "3y", "5y", "10y", "max"];
const DEFAULT_COMPARISON_METRIC = "low_carbon_share_pct";
const DEFAULT_COMPARISON_COUNTRIES = ["FR", "DE", "ES", "UK", "IT"];
const SHOW_RANKING_DATA_QUALITY_NOTICES = false;
const STORAGE_VARIANT_ORDER = new Map([
  ["battery_energy_gwh", 0], ["battery_power_gw", 1], ["battery_duration_hours", 2],
  ["pumped_storage_energy_gwh", 0], ["pumped_storage_power_gw", 1], ["pumped_storage_duration_hours", 2],
]);
const NE_TO_ATLAS = {
  "AUT": "AT", "BEL": "BE", "BGR": "BG", "CHE": "CH", "CZE": "CZ", "DEU": "DE", "DNK": "DK",
  "ESP": "ES", "EST": "EE", "FIN": "FI", "FRA": "FR", "GBR": "UK", "GRC": "GR", "HRV": "HR",
  "HUN": "HU", "IRL": "IE", "ITA": "IT", "LTU": "LT", "LUX": "LU", "LVA": "LV", "MNE": "ME",
  "MKD": "MK", "NLD": "NL", "NOR": "NO", "POL": "PL", "PRT": "PT", "ROU": "RO", "SRB": "RS",
  "SVK": "SK", "SVN": "SI", "SWE": "SE"
};
const MAP_PALETTES = {
  generation: ["#e8eef8", "#b9c9e2", "#7f9dc6", "#466f9f", "#234a76"],
  consumption: ["#e6f1f4", "#b7d5dc", "#78b2bf", "#3d8999", "#1b5e6d"],
  renewables: ["#e8f4e8", "#b8dcb8", "#7fbe83", "#459e58", "#216b37"],
  wind: ["#edf5ff", "#c2dcf4", "#8cbde4", "#5197cd", "#276da6"],
  solar: ["#fff8df", "#f7e6a8", "#ebcc67", "#d7a72d", "#9e7314"],
  hydro: ["#e5f4fb", "#b7dff1", "#75c4e5", "#369fcb", "#15719b"],
  bioenergy: ["#edf1df", "#ccd7a3", "#a2b66d", "#758f3d", "#4a6124"],
  "other-renewables": ["#e8f5ef", "#b9dfcf", "#82c6aa", "#4aa481", "#276e58"],
  fossil: ["#f8e9e1", "#edc0aa", "#db8d6a", "#bb573b", "#7d2f24"],
  coal: ["#eeeeed", "#c7c7c3", "#989891", "#686861", "#3d3d39"],
  gas: ["#fff0e5", "#f7c89e", "#e99458", "#ca6130", "#8d351f"],
  "other-fossil": ["#f4e9e3", "#dfc1b2", "#bf927a", "#95634e", "#643f32"],
  nuclear: ["#f1eaf7", "#d5c0e4", "#ad91ca", "#805eaa", "#58377e"],
  trade: ["#2a6fbb", "#80b1d3", "#f7f7f7", "#ef8a62", "#b2182b"],
  price: ["#f8e9f2", "#e8bad3", "#cf80ad", "#ad4f85", "#7c2f5d"],
  carbon: ["#f6ebe7", "#e7c1b5", "#ce8d7d", "#aa584b", "#71312d"],
  population: ["#eeeaf6", "#cfc2e2", "#aa95ca", "#7b65ae", "#4c3b7e"],
  gdp: ["#e8f3ed", "#bfdcc9", "#8bc09e", "#519972", "#2c6a4d"],
  "gdp-per-capita": ["#f3eedf", "#dccb9f", "#bea66d", "#927c40", "#65552a"],
  battery: ["#eef0ff", "#c8cef4", "#98a3e2", "#6975c6", "#414b91"],
  "pumped-storage": ["#e3f4f3", "#b2dfdc", "#72c4bf", "#39a19d", "#1f716f"],
};
const MAP_PALETTE_BY_FAMILY = {
  "Erzeugung": "generation",
  "Verbrauch": "consumption",
  "Erneuerbare gesamt": "renewables",
  "Wind": "wind",
  "Solar": "solar",
  "Wasserkraft": "hydro",
  "Bioenergie": "bioenergy",
  "Sonstige Erneuerbare": "other-renewables",
  "Fossile gesamt": "fossil",
  "Kohle": "coal",
  "Gas": "gas",
  "Sonstige Fossile": "other-fossil",
  "Kernenergie": "nuclear",
  "Nettoimporte": "trade",
  "Großhandelspreis": "price",
  "CO₂-Intensität": "carbon",
  "Bevölkerung": "population",
  "BIP": "gdp",
  "BIP pro Kopf": "gdp-per-capita",
  "Batteriespeicher": "battery",
  "Pumpspeicher": "pumped-storage",
};

let metricCatalog = new Map();
let data = [];
const TABLE_PREVIEW_LIMIT = 10;
let sortKey = "generation_twh";
let sortDirection = -1;
let summaryExpanded = false;
let storageData = [];
let storageSnapshot = null;
let storageSourceLabel = "";
let storageSortKey = "battery_energy_gwh";
let storageSortDirection = -1;
let storageExpanded = false;
let evSortKey = "bev_stock";
let evSortDirection = -1;
let evExpanded = false;
let mapSvg = null;
let mapMetricId = "generation_twh";
let focusedMapCountry = null;
let animateChartNextRender = false;
const selected = new Set(DEFAULT_COMPARISON_COUNTRIES);
let timeseriesData = null;
let timeseriesColors = new Map();
let chartHoverIndex = null;
let chartPinnedIndex = null;
let activeComparisonPreset = null;
let knownMaximumComparisonRange = null;
const FLAG_COLOR_CACHE = new Map();
const CHART_FALLBACK_COLORS = [
  "#c0e040", "#e04000", "#4090ff", "#e020e0", "#00e000",
  "#00a080", "#60a000", "#00e0e0", "#8040e0", "#e04080",
];
const MIN_CHART_COLOR_DISTANCE = 96;

const $ = id => document.getElementById(id);
const MIN_YEAR = 2015;
const currentYear = new Date().getFullYear();

function selectedYear() {
  const input = $("year");
  input.min = String(MIN_YEAR);
  input.max = String(currentYear);
  const parsed = Number.parseInt(input.value, 10);
  const year = Number.isFinite(parsed) ? Math.min(currentYear, Math.max(MIN_YEAR, parsed)) : 2025;
  input.value = String(year);
  return year;
}

function isMonthView() {
  return $("period-type").value === "month";
}

function periodQuery() {
  const params = new URLSearchParams({year: selectedYear()});
  if (isMonthView()) params.set("month", $("month").value);
  return params;
}

function format(value) {
  if (value === null || value === undefined) return '<span class="missing">—</span>';
  if (typeof value === "number") {
    return new Intl.NumberFormat("de-DE", {maximumFractionDigits: 2}).format(value);
  }
  return escapeHtml(value);
}

function formatTableValue(value, metricId) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return '<span class="missing">—</span>';
  const decimals = metricDefinition(metricId)?.map_config?.decimals ?? 2;
  return new Intl.NumberFormat("de-DE", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(Number(value));
}

function formatMetricValue(value, metric, compact = false) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
  const decimals = metric?.map_config?.decimals ?? 2;
  return new Intl.NumberFormat("de-DE", {
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals,
    notation: compact && Math.abs(value) >= 10000 ? "compact" : "standard",
  }).format(value);
}

function metricDefinition(id) {
  return metricCatalog.get(id) || {id, label_de: id, unit: "", map: false};
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
  return escapeHtml(value);
}

function metricHeader(id, activeKey, direction, allowMap = false) {
  const metric = metricDefinition(id);
  const activeSort = activeKey === id;
  const arrow = activeSort ? (direction > 0 ? "↑" : "↓") : "";
  const ariaSort = activeSort ? ` aria-sort="${direction > 0 ? "ascending" : "descending"}"` : "";
  const label = tableHeaderText(metric.label_de);
  const unitLabel = tableHeaderText(metric.unit);
  const unit = unitLabel ? `<span class="unit">${escapeHtml(unitLabel)}</span>` : "";
  const mapAction = allowMap && metric.map
    ? `<button type="button" class="map-column-action${mapMetricId === id ? " active" : ""}" data-map-metric="${id}" aria-label="${escapeAttribute(label)} auf Karte anzeigen">Karte</button>`
    : "";
  return `<th scope="col" data-key="${id}"${ariaSort} class="${mapMetricId === id ? "map-column-active" : ""}">
    <button type="button" class="sort-action" data-sort-key="${id}" aria-label="${escapeAttribute(label)} sortieren">
      <span class="sort-label">${escapeHtml(label)}</span>${unit}<span class="sort-indicator" aria-hidden="true">${arrow}</span>
    </button>
    ${mapAction}
  </th>`;
}

function tableHeaderText(value) {
  return String(value ?? "").replace(/\s+im\s+Ranking\b/gi, "").trim();
}

function countryHeader(activeKey, direction) {
  const active = activeKey === "country_name";
  const arrow = active ? (direction > 0 ? "↑" : "↓") : "";
  const ariaSort = active ? ` aria-sort="${direction > 0 ? "ascending" : "descending"}"` : "";
  return `<th scope="col" data-key="country_name"${ariaSort}><button type="button" class="sort-action" data-sort-key="country_name"><span class="sort-label">Land</span><span class="sort-indicator" aria-hidden="true">${arrow}</span></button></th>`;
}

function rankHeader(withSelection = false) {
  const selection = withSelection ? '<span class="sr-only">Länder für den Zeitreihenvergleich auswählen</span>' : "";
  return `<th scope="col" class="rank-column"><span aria-hidden="true">#</span>${selection}</th>`;
}

function tableCountry(row) {
  return `<span class="table-country">
    <img src="/assets/flags/${flagCode(row.country_code)}.svg" alt="" loading="lazy">
    <span class="table-country-copy"><span class="country-name">${escapeHtml(row.country_name)}</span><small>${escapeHtml(row.country_code)}</small></span>
  </span>`;
}

function updateTableDisclosure(kind, expanded, total) {
  const visible = expanded ? total : Math.min(TABLE_PREVIEW_LIMIT, total);
  const button = $(`${kind}-toggle`);
  const state = $(`${kind}-table-state`);
  const count = $(`${kind}-count`);
  if (!button || !state || !count) return;
  const card = button.closest?.(".table-card");
  card?.classList.toggle("table-card-expanded", expanded);
  button.hidden = total <= TABLE_PREVIEW_LIMIT;
  button.setAttribute("aria-expanded", String(expanded));
  button.querySelector(".table-toggle-label").textContent = expanded
    ? "Auf Top 10 reduzieren"
    : `Alle ${total} Länder anzeigen`;
  state.textContent = expanded ? "Vollständige Rangliste" : "Top 10 nach aktueller Sortierung";
  count.textContent = `${visible} von ${total} Ländern`;
}

function syncStickyHeaderOffset() {
  const controls = document.querySelector?.(".controls");
  if (!controls || typeof controls.getBoundingClientRect !== "function") return;
  const height = Math.ceil(controls.getBoundingClientRect().height);
  document.documentElement?.style?.setProperty("--atlas-controls-height", `${height}px`);
}

function animateTableDisclosure(kind, renderTable, collapsing) {
  const region = $(`${kind}-table-region`);
  if (!region || !motionAllowed()) {
    renderTable();
    return;
  }
  const startHeight = region.getBoundingClientRect().height;
  renderTable();
  const endHeight = region.scrollHeight;
  if (Math.abs(startHeight - endHeight) < 1) return;
  region.style.height = `${startHeight}px`;
  region.classList.add("table-disclosure-animating");
  requestAnimationFrame(() => {
    region.style.height = `${endHeight}px`;
    if (collapsing) window.scrollBy?.({top: endHeight - startHeight, behavior: "smooth"});
  });
  const finish = () => {
    region.style.height = "";
    region.classList.remove("table-disclosure-animating");
  };
  region.addEventListener("transitionend", finish, {once: true});
  setTimeout(finish, 900);
}

function statusBadge(row) {
  const labels = {complete: "vollständig", partial: "teilweise", missing: "fehlend"};
  const periodLabels = {provisional_current_month: "vorläufig", ytd: "YTD"};
  const details = [
    `Datenstatus: ${labels[row.data_status] || row.data_status}`,
    `Zeitraum: ${row.period}`,
    `Preisabdeckung: ${row.price_coverage || "fehlend"}`,
    ...(row.quality_issues || []).map(issue => issue.details),
  ].join("\n");
  const period = periodLabels[row.period_status]
    ? `<span class="period-flag ${row.period_status === "ytd" ? "ytd" : "provisional"}">${periodLabels[row.period_status]}</span>`
    : "";
  return `<span class="status-badge ${row.data_status}" title="${escapeAttribute(details)}" aria-label="${escapeAttribute(details)}">${labels[row.data_status] || row.data_status}</span>${period}`;
}

function sortRows(rows, key, direction) {
  return [...rows].sort((a, b) => {
    const av = a[key], bv = b[key];
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    return (typeof av === "string" ? av.localeCompare(bv, "de") : av - bv) * direction;
  });
}

function motionAllowed() {
  return !window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
}

function rowPositions(selector) {
  return new Map([...document.querySelectorAll(selector)].map(row => [
    row.dataset.countryRow || row.dataset.storageRow,
    row.getBoundingClientRect().top,
  ]));
}

function animateRowReorder(selector, positions, keyForRow) {
  if (!positions.size || !motionAllowed()) return;
  document.querySelectorAll(selector).forEach(row => {
    const previousTop = positions.get(keyForRow(row));
    if (previousTop === undefined) return;
    const distance = previousTop - row.getBoundingClientRect().top;
    if (Math.abs(distance) < 1) return;
    row.animate(
      [{transform: `translateY(${distance}px)`}, {transform: "translateY(0)"}],
      {duration: 320, easing: "cubic-bezier(.22,.8,.24,1)"},
    );
  });
}

function bindSort(selector, callback) {
  document.querySelectorAll(selector).forEach(button => button.addEventListener("click", () => callback(button.dataset.sortKey)));
}

function bindMapColumnActions() {
  document.querySelectorAll("#summary-head [data-map-metric]").forEach(button => button.addEventListener("click", () => {
    setMapMetric(button.dataset.mapMetric, true);
  }));
}

function renderHead() {
  $("summary-head").innerHTML = rankHeader(true)
    + countryHeader(sortKey, sortDirection)
    + TABLE_METRIC_IDS.map(id => metricHeader(id, sortKey, sortDirection, true)).join("");
  bindSort("#summary-head [data-sort-key]", key => {
    if (sortKey === key) sortDirection *= -1;
    else { sortKey = key; sortDirection = -1; }
    render();
  });
  bindMapColumnActions();
}

function render() {
  const previousPositions = rowPositions("#summary-body [data-country-row]");
  renderHead();
  const sorted = sortRows(data, sortKey, sortDirection);
  const visibleRows = summaryExpanded ? sorted : sorted.slice(0, TABLE_PREVIEW_LIMIT);
  $("summary-body").innerHTML = visibleRows.map((row, index) => `<tr data-country-row="${row.country_code}" style="--row-index:${index}">
    <td class="selection-cell"><span class="table-rank">${index + 1}</span><input type="checkbox" aria-label="${escapeAttribute(row.country_name)} auswählen" data-country="${row.country_code}" ${selected.has(row.country_code) ? "checked" : ""}></td>
    <th scope="row">${tableCountry(row)}${statusBadge(row)}</th>
    ${TABLE_METRIC_IDS.map(id => `<td data-metric="${id}" class="${mapMetricId === id ? "map-column-active" : ""}">${formatTableValue(row[id], id)}</td>`).join("")}
  </tr>`).join("");
  updateTableDisclosure("summary", summaryExpanded, sorted.length);
  animateRowReorder("#summary-body [data-country-row]", previousPositions, row => row.dataset.countryRow);
  document.querySelectorAll("input[data-country]").forEach(input => input.addEventListener("change", event => {
    const changed = toggleCountry(event.target.dataset.country, event.target.checked);
    if (!changed) event.target.checked = false;
  }));
  updateSelection();
}

function renderStorage() {
  const previousPositions = rowPositions("#storage-body tr");
  $("storage-head").innerHTML = rankHeader()
    + countryHeader(storageSortKey, storageSortDirection)
    + STORAGE_METRIC_IDS.map(id => metricHeader(id, storageSortKey, storageSortDirection)).join("");
  bindSort("#storage-head [data-sort-key]", key => {
    if (storageSortKey === key) storageSortDirection *= -1;
    else { storageSortKey = key; storageSortDirection = -1; }
    renderStorage();
  });
  const sorted = sortRows(storageData, storageSortKey, storageSortDirection);
  const visibleRows = storageExpanded ? sorted : sorted.slice(0, TABLE_PREVIEW_LIMIT);
  $("storage-body").innerHTML = visibleRows.map((row, index) => `<tr data-storage-row="${row.country_code}" style="--row-index:${index}">
    <td class="rank-column"><span class="table-rank">${index + 1}</span></td>
    <th scope="row">${tableCountry(row)}${row.quality_status === "missing" ? '<span class="status-badge missing">fehlend</span>' : ""}</th>
    ${STORAGE_METRIC_IDS.map(id => storageCell(row, id)).join("")}
  </tr>`).join("");
  updateTableDisclosure("storage", storageExpanded, sorted.length);
  animateRowReorder("#storage-body tr", previousPositions, row => row.dataset.storageRow);
}

function electromobilityRowsForView(rows, monthly, key, direction, expanded) {
  if (monthly) return [];
  const sorted = sortRows(rows, key, direction);
  return expanded ? sorted : sorted.slice(0, TABLE_PREVIEW_LIMIT);
}

function renderElectromobility() {
  const head = $("ev-head");
  if (!head || typeof head.querySelectorAll !== "function") return;
  const monthly = isMonthView();
  const region = $("ev-table-region");
  const toggle = $("ev-toggle");
  const state = $("ev-table-state");
  const count = $("ev-count");
  if (monthly) {
    region.hidden = true;
    toggle.hidden = true;
    toggle.setAttribute("aria-expanded", "false");
    state.textContent = "Nur in der Jahresansicht verfügbar";
    count.textContent = "Jahresansicht erforderlich";
    $("ev-note").textContent = "Elektromobilitätswerte sind jährliche Eurostat-Daten. In der Monatsansicht werden keine Jahreswerte eingeblendet.";
    return;
  }

  region.hidden = false;
  $("ev-note").textContent = `Eurostat-Jahreswerte für ${selectedYear()}. Fehlende Land-Jahr-Werte bleiben leer und werden nicht aus Vorjahren fortgeschrieben.`;
  head.innerHTML = rankHeader()
    + countryHeader(evSortKey, evSortDirection)
    + EV_METRIC_IDS.map(id => metricHeader(id, evSortKey, evSortDirection)).join("");
  bindSort("#ev-head [data-sort-key]", key => {
    if (evSortKey === key) evSortDirection *= -1;
    else { evSortKey = key; evSortDirection = -1; }
    renderElectromobility();
  });
  const sorted = sortRows(data, evSortKey, evSortDirection);
  const visibleRows = electromobilityRowsForView(data, false, evSortKey, evSortDirection, evExpanded);
  $("ev-body").innerHTML = visibleRows.map((row, index) => `<tr data-ev-row="${row.country_code}" style="--row-index:${index}">
    <td class="rank-column"><span class="table-rank">${index + 1}</span></td>
    <th scope="row">${tableCountry(row)}</th>
    ${EV_METRIC_IDS.map(id => `<td data-metric="${id}">${formatTableValue(row[id], id)}</td>`).join("")}
  </tr>`).join("");
  updateTableDisclosure("ev", evExpanded, sorted.length);
}

function storageCell(row, metricId) {
  const provenance = row.metric_provenance?.[metricId];
  if (!provenance) return `<td>${formatTableValue(null, metricId)}</td>`;
  const coverageLabels = {
    national_registry_total: "nationaler Register-Gesamtbestand",
    tracked_project_inventory: "erfasster Projektbestand",
  };
  const sourceName = provenance.source === "battery_charts" ? "Battery-Charts" : "JRC";
  const qualityLabel = storageQualityLabel(provenance.quality_status);
  const quality = qualityLabel === "vorhanden" ? "" : ` · ${qualityLabel}`;
  const title = `${provenance.source_label} · Stichtag ${provenance.date} · ${coverageLabels[provenance.coverage_type] || provenance.coverage_type}${quality}`;
  return `<td title="${escapeAttribute(title)}">${formatTableValue(row[metricId], metricId)}<small class="cell-provenance">${escapeHtml(sourceName)} · ${escapeHtml(provenance.date)}${escapeHtml(quality)}</small></td>`;
}

function storageQualityLabel(quality) {
  return {
    observed: "vorhanden",
    derived: "abgeleitet",
    provisional_current_month: "vorläufig",
    derived_provisional: "abgeleitet, vorläufig",
    observed_with_estimates: "mit Schätzwerten",
    derived_with_estimates: "abgeleitet, mit Schätzwerten",
  }[quality] || quality || "vorhanden";
}

function toggleCountry(code, shouldSelect = !selected.has(code)) {
  if (shouldSelect && !selected.has(code) && selected.size >= 10) {
    $("status").textContent = "Maximal zehn Länder können gleichzeitig verglichen werden.";
    return false;
  }
  shouldSelect ? selected.add(code) : selected.delete(code);
  knownMaximumComparisonRange = null;
  const row = document.querySelector(`[data-country-row="${code}"]`);
  if (row && motionAllowed()) {
    row.classList.remove("selection-pulse");
    void row.offsetWidth;
    row.classList.add("selection-pulse");
    row.addEventListener("animationend", () => row.classList.remove("selection-pulse"), {once: true});
  }
  updateSelection();
  if (shouldSelect) animateSelectionToCompare(code);
  if (timeseriesData && selected.size) void loadTimeseries({scroll: false, updateUrl: true});
  else if (timeseriesData) $("comparison-status").textContent = "Mindestens ein Land auswählen.";
  return true;
}

function clearSelection() {
  if (!selected.size) return;
  selected.clear();
  updateSelection();
  if (timeseriesData) {
    $("comparison-status").textContent = "Länderauswahl aufgehoben. Neue Länder wählen.";
  }
  $("status").textContent = "Gesamte Länderauswahl aufgehoben.";
}

function updateSelection() {
  const counter = $("selected-count");
  counter.textContent = selected.size;
  if (motionAllowed()) {
    counter.classList.remove("count-pulse");
    void counter.offsetWidth;
    counter.classList.add("count-pulse");
  }
  $("compare").disabled = selected.size < 1 || selected.size > 10;
  $("clear-selection").disabled = selected.size === 0;
  document.querySelectorAll("input[data-country]").forEach(input => {
    input.checked = selected.has(input.dataset.country);
  });
  renderCountryControls();
}

function animateSelectionToCompare(code) {
  if (!motionAllowed()) return;
  const row = document.querySelector(`[data-country-row="${code}"]`);
  const target = $("compare");
  if (!row || !target || target.disabled) return;
  const start = row.getBoundingClientRect();
  const end = target.getBoundingClientRect();
  const pulse = document.createElement("span");
  pulse.className = "selection-energy-pulse";
  pulse.style.left = `${start.left + Math.min(start.width * .55, 280)}px`;
  pulse.style.top = `${start.top + start.height / 2}px`;
  document.body.appendChild(pulse);
  const dx = end.left + end.width / 2 - (start.left + Math.min(start.width * .55, 280));
  const dy = end.top + end.height / 2 - (start.top + start.height / 2);
  pulse.animate(
    [
      {transform: "translate(-50%, -50%) scale(.6)", opacity: 0},
      {transform: "translate(-50%, -50%) scale(1)", opacity: 1, offset: .16},
      {transform: `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px)) scale(.35)`, opacity: 0},
    ],
    {duration: 560, easing: "cubic-bezier(.22,.8,.24,1)"},
  ).addEventListener("finish", () => {
    pulse.remove();
    target.classList.remove("comparison-arrival-pulse");
    void target.offsetWidth;
    target.classList.add("comparison-arrival-pulse");
    target.addEventListener("animationend", () => target.classList.remove("comparison-arrival-pulse"), {once: true});
  }, {once: true});
}

function mapMetrics() {
  return [...metricCatalog.values()].filter(metric => metric.map);
}

function orderedMetricVariants(metrics) {
  return [...metrics].sort((first, second) => (
    (STORAGE_VARIANT_ORDER.get(first.id) ?? 99) - (STORAGE_VARIANT_ORDER.get(second.id) ?? 99)
  ));
}

function familyKey(metric) {
  return `${metric.group}::${metric.family}`;
}

function metricAvailable(metric) {
  if (metric.temporal_availability.snapshot) return storageSnapshot !== null;
  return isMonthView()
    ? metric.temporal_availability.monthly
    : metric.temporal_availability.yearly;
}

function renderMapControls() {
  const metrics = mapMetrics();
  if (!metrics.length) return;
  if (!metricCatalog.has(mapMetricId) || !metricCatalog.get(mapMetricId).map) mapMetricId = metrics[0].id;
  const activeMetric = metricDefinition(mapMetricId);
  const groups = new Map();
  metrics.forEach(metric => {
    if (!groups.has(metric.group)) groups.set(metric.group, new Map());
    const families = groups.get(metric.group);
    if (!families.has(metric.family)) families.set(metric.family, []);
    families.get(metric.family).push(metric);
  });
  $("map-family").innerHTML = [...groups.entries()].map(([group, families]) =>
    `<optgroup label="${escapeAttribute(group)}">${[...families.entries()].map(([family, variants]) => {
      const selectable = variants.some(metric => metricAvailable(metric)
        || (isMonthView() && metric.temporal_availability.yearly));
      const disabled = selectable ? "" : " disabled";
      return `<option value="${escapeAttribute(`${group}::${family}`)}"${disabled}>${escapeHtml(family)}</option>`;
    }).join("")}</optgroup>`
  ).join("");
  $("map-family").value = familyKey(activeMetric);

  const variants = orderedMetricVariants(metrics.filter(metric => familyKey(metric) === familyKey(activeMetric)));
  $("map-representation").innerHTML = variants.map(metric => {
    const selectable = metricAvailable(metric) || (isMonthView() && metric.temporal_availability.yearly);
    const disabled = selectable ? "" : " disabled";
    const unit = metric.unit ? ` (${metric.unit})` : "";
    return `<option value="${metric.id}"${disabled}>${escapeHtml(metric.representation)}${escapeHtml(unit)}</option>`;
  }).join("");
  $("map-representation").value = mapMetricId;

  if (metricAvailable(activeMetric)) {
    $("map-availability").textContent = activeMetric.temporal_availability.snapshot
      ? "Snapshot-Kennzahlen verwenden ihren jeweils ausgewiesenen Datenstand; Jahr und Monat gelten hier nicht."
      : "";
  } else if (activeMetric.temporal_availability.yearly && isMonthView()) {
    $("map-availability").textContent = "Nur in der Jahresansicht verfügbar.";
  } else if (activeMetric.temporal_availability.snapshot) {
    $("map-availability").textContent = "Noch kein Speichersnapshot verfügbar.";
  } else {
    $("map-availability").textContent = "Für diese Darstellung und diesen Zeitraum nicht verfügbar.";
  }
  highlightMapColumn();
}

async function selectMapMetricForPeriod(metricId) {
  const metric = metricCatalog.get(metricId);
  if (!metric?.map) return;
  const requiresYearView = isMonthView()
    && !metric.temporal_availability.monthly
    && metric.temporal_availability.yearly;
  if (!requiresYearView) {
    setMapMetric(metric.id);
    return;
  }
  mapMetricId = metric.id;
  $("period-type").value = "year";
  syncPeriodControls();
  await loadSummary();
  $("map-availability").textContent = "Jahresansicht für diese Kennzahl automatisch aktiviert.";
}

function setMapMetric(metricId, scrollToMap = false) {
  const metric = metricCatalog.get(metricId);
  if (!metric?.map) return;
  mapMetricId = metricId;
  if (motionAllowed()) {
    const frame = $("map-frame");
    frame.classList.remove("grid-sweep");
    void frame.offsetWidth;
    frame.classList.add("grid-sweep");
    frame.addEventListener("animationend", () => frame.classList.remove("grid-sweep"), {once: true});
  }
  renderMapControls();
  renderMap();
  renderHead();
  highlightMapColumn();
  if (scrollToMap) $("atlas-map-section").scrollIntoView({behavior: "smooth", block: "start"});
}

function highlightMapColumn() {
  document.querySelectorAll(".map-column-active").forEach(element => element.classList.remove("map-column-active"));
  document.querySelectorAll(`[data-key="${mapMetricId}"], [data-metric="${mapMetricId}"]`).forEach(element => element.classList.add("map-column-active"));
}

function mapRow(code, metric) {
  const rows = metric.temporal_availability.snapshot ? storageData : data;
  return rows.find(row => row.country_code === code) || null;
}

function countryName(code) {
  return data.find(row => row.country_code === code)?.country_name
    || storageData.find(row => row.country_code === code)?.country_name
    || code;
}

function periodLabel(metric, row = null) {
  if (metric.temporal_availability.snapshot) {
    const date = row?.metric_provenance?.[metric.id]?.date || storageSnapshot;
    return date ? `Snapshot ${date}` : "Kein Snapshot";
  }
  const period = row?.period || (isMonthView() ? `${selectedYear()}-${String($("month").value).padStart(2, "0")}` : String(selectedYear()));
  const status = row?.period_status === "ytd" ? " · YTD" : (row?.period_status === "provisional_current_month" ? " · vorläufig" : "");
  return `${period}${status}`;
}

function statusLabel(row, metric) {
  if (!row) return "fehlend";
  const value = row[metric.id];
  if (value === null || value === undefined) return "fehlend";
  if (metric.temporal_availability.snapshot) {
    const quality = row.metric_provenance?.[metric.id]?.quality_status || row.quality_status;
    return storageQualityLabel(quality);
  }
  return {complete: "vollständig", partial: "teilweise", missing: "fehlend"}[row.data_status] || row.data_status || "vorhanden";
}

function countryDetail(code, metric) {
  const row = mapRow(code, metric);
  const value = metricAvailable(metric) && row ? row[metric.id] : null;
  const formatted = formatMetricValue(value, metric);
  const unit = formatted === "—" ? "" : ` ${metric.unit}`;
  const provenance = metric.temporal_availability.snapshot ? row?.metric_provenance?.[metric.id] : null;
  const source = provenance?.source_label || metric.source;
  const coverage = provenance?.coverage_type ? `<span>Coverage: ${escapeHtml(provenance.coverage_type)}</span>` : "";
  return {
    html: `<strong>${escapeHtml(countryName(code))}</strong>
      <span>${escapeHtml(metric.label_de)}</span>
      <b>${escapeHtml(formatted + unit)}</b>
      <span>${escapeHtml(periodLabel(metric, row))}</span>
      <span>Datenstatus: ${escapeHtml(statusLabel(row, metric))}</span>
      ${coverage}
      <span>Quelle: ${escapeHtml(source)}</span>`,
    label: `${countryName(code)}, ${metric.label_de}: ${formatted}${unit}, ${periodLabel(metric, row)}, Datenstatus ${statusLabel(row, metric)}, Quelle ${source}`,
  };
}

function hexToRgb(color) {
  const value = color.replace("#", "");
  return [0, 2, 4].map(index => Number.parseInt(value.slice(index, index + 2), 16));
}

function interpolateColor(start, end, amount) {
  const a = hexToRgb(start), b = hexToRgb(end);
  const values = a.map((value, index) => Math.round(value + (b[index] - value) * amount));
  return `rgb(${values.join(", ")})`;
}

function paletteColor(palette, position) {
  const colors = MAP_PALETTES[palette] || MAP_PALETTES.generation;
  const bounded = Math.max(0, Math.min(1, position));
  const scaled = bounded * (colors.length - 1);
  const index = Math.min(colors.length - 2, Math.floor(scaled));
  return interpolateColor(colors[index], colors[index + 1], scaled - index);
}

function mapPaletteName(metric) {
  const familyPalette = MAP_PALETTE_BY_FAMILY[metric?.family];
  if (familyPalette && MAP_PALETTES[familyPalette]) return familyPalette;
  const configuredPalette = metric?.map_config?.palette;
  return MAP_PALETTES[configuredPalette] ? configuredPalette : "generation";
}

function mapScale(metric, values) {
  const config = metric.map_config || {};
  const finite = values.filter(value => Number.isFinite(value));
  if (!finite.length) return {min: 0, max: 1, midpoint: config.midpoint};
  const min = Math.min(...finite), max = Math.max(...finite);
  return {min, max, midpoint: config.midpoint};
}

function mapScalePosition(value, metric, scale) {
  const numeric = Number(value);
  if (scale.min === scale.max) return .5;
  const midpoint = scale.midpoint;
  const diverging = metric.map_config?.scale === "diverging";
  if (diverging && Number.isFinite(midpoint) && midpoint > scale.min && midpoint < scale.max) {
    if (numeric <= midpoint) return .5 * ((numeric - scale.min) / (midpoint - scale.min));
    return .5 + .5 * ((numeric - midpoint) / (scale.max - midpoint));
  }
  return (numeric - scale.min) / (scale.max - scale.min);
}

function colorForValue(value, metric, scale) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return null;
  const position = mapScalePosition(value, metric, scale);
  return paletteColor(mapPaletteName(metric), position);
}

function renderLegend(metric, scale) {
  const colors = MAP_PALETTES[mapPaletteName(metric)];
  const gradient = `linear-gradient(90deg, ${colors.join(", ")})`;
  const midpoint = scale.midpoint;
  $("map-legend").innerHTML = `<div class="legend-ramp" style="background:${gradient}" aria-hidden="true"></div>
    <div class="legend-values"><span>${escapeHtml(formatMetricValue(scale.min, metric))}</span>${midpoint !== null && midpoint !== undefined ? `<span>${escapeHtml(formatMetricValue(midpoint, metric))}</span>` : ""}<span>${escapeHtml(formatMetricValue(scale.max, metric))}</span></div>
    <p>${escapeHtml(metric.unit || "ohne Einheit")} · Grau = kein Wert</p>`;
  if (motionAllowed()) {
    const legend = $("map-legend");
    legend.classList.remove("legend-morph");
    void legend.offsetWidth;
    legend.classList.add("legend-morph");
  }
  $("map-sign-note").hidden = metric.map_config?.scale !== "diverging";
}

function renderMapLabels(metric) {
  if (!mapSvg) return;
  const layer = mapSvg.querySelector("#map-value-labels");
  if (!layer) return;
  layer.replaceChildren();
  if (!$("map-values").checked || !metricAvailable(metric)) return;
  mapSvg.querySelectorAll(".map-country.atlas-country").forEach(path => {
    const row = mapRow(path.dataset.countryCode, metric);
    const value = row?.[metric.id];
    if (!Number.isFinite(value) || !path.dataset.labelX || !path.dataset.labelY) return;
    const bounds = path.getBBox();
    if (bounds.width * bounds.height < 1100) return;
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", path.dataset.labelX);
    text.setAttribute("y", path.dataset.labelY);
    text.setAttribute("class", "map-value-label");
    text.textContent = formatMetricValue(value, metric, true);
    layer.appendChild(text);
  });
}

function positionTooltip(path, pointerEvent = null) {
  const tooltip = $("map-tooltip");
  const frame = $("map-frame").getBoundingClientRect();
  if (pointerEvent) {
    tooltip.style.left = `${pointerEvent.clientX - frame.left + 12}px`;
    tooltip.style.top = `${pointerEvent.clientY - frame.top + 12}px`;
    return;
  }
  const svgRect = mapSvg.getBoundingClientRect();
  const viewBox = mapSvg.viewBox.baseVal;
  const labelX = Number(path.dataset.labelX || path.getBBox().x + path.getBBox().width / 2);
  const labelY = Number(path.dataset.labelY || path.getBBox().y + path.getBBox().height / 2);
  tooltip.style.left = `${svgRect.left - frame.left + (labelX - viewBox.x) / viewBox.width * svgRect.width + 10}px`;
  tooltip.style.top = `${svgRect.top - frame.top + (labelY - viewBox.y) / viewBox.height * svgRect.height + 10}px`;
}

function showCountryTooltip(path, pointerEvent = null) {
  const metric = metricDefinition(mapMetricId);
  const detail = countryDetail(path.dataset.countryCode, metric);
  $("map-tooltip").innerHTML = detail.html;
  $("map-tooltip").hidden = false;
  positionTooltip(path, pointerEvent);
}

function focusMapCountry(path) {
  focusedMapCountry = path.dataset.countryCode;
  mapSvg.querySelectorAll(".atlas-country").forEach(country => country.classList.toggle("selected", country === path));
  const detail = countryDetail(focusedMapCountry, metricDefinition(mapMetricId));
  const panel = $("map-detail");
  panel.innerHTML = detail.html;
  hideMapTooltip();
  if (motionAllowed()) {
    path.classList.remove("map-focus-pulse");
    panel.classList.remove("detail-enter");
    void path.getBBox();
    path.classList.add("map-focus-pulse");
    panel.classList.add("detail-enter");
    path.addEventListener("animationend", () => path.classList.remove("map-focus-pulse"), {once: true});
  }
}

function hideMapTooltip() {
  $("map-tooltip").hidden = true;
}

function configureMapCountries() {
  mapSvg.querySelectorAll(".map-country").forEach(path => {
    const code = NE_TO_ATLAS[path.dataset.neCode];
    if (!code) {
      path.classList.add("background-country");
      path.setAttribute("aria-hidden", "true");
      return;
    }
    path.classList.add("atlas-country");
    path.dataset.countryCode = code;
    path.setAttribute("tabindex", "0");
    path.setAttribute("role", "button");
    path.addEventListener("mouseenter", event => showCountryTooltip(path, event));
    path.addEventListener("mousemove", event => positionTooltip(path, event));
    path.addEventListener("mouseleave", hideMapTooltip);
    path.addEventListener("focus", () => showCountryTooltip(path));
    path.addEventListener("blur", hideMapTooltip);
    path.addEventListener("click", () => focusMapCountry(path));
    path.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        focusMapCountry(path);
      }
    });
  });
  updateSelection();
}

function renderMap() {
  if (!mapSvg || !metricCatalog.size) return;
  const metric = metricDefinition(mapMetricId);
  const available = metricAvailable(metric);
  const values = mapSvg.querySelectorAll(".atlas-country");
  const numericValues = [...values].map(path => mapRow(path.dataset.countryCode, metric)?.[metric.id]).filter(Number.isFinite);
  const scale = mapScale(metric, numericValues);
  values.forEach(path => {
    const row = mapRow(path.dataset.countryCode, metric);
    const value = available && row ? row[metric.id] : null;
    const color = colorForValue(value, metric, scale);
    path.style.fill = color || "";
    path.classList.toggle("no-data", color === null);
    path.classList.toggle("selected", path.dataset.countryCode === focusedMapCountry);
    path.setAttribute("aria-label", countryDetail(path.dataset.countryCode, metric).label);
  });
  $("map-metric-title").textContent = `${metric.family}: ${metric.representation}`;
  $("map-period").textContent = periodLabel(metric, mapRow("DE", metric));
  renderLegend(metric, scale);
  renderMapLabels(metric);
  if (focusedMapCountry) $("map-detail").innerHTML = countryDetail(focusedMapCountry, metric).html;
  highlightMapColumn();
}

async function loadMapAsset() {
  try {
    const response = await fetch("/assets/europe.svg");
    if (!response.ok) throw new Error(response.statusText);
    const documentNode = new DOMParser().parseFromString(await response.text(), "image/svg+xml");
    if (documentNode.querySelector("parsererror")) throw new Error("Ungültiges SVG");
    mapSvg = document.importNode(documentNode.documentElement, true);
    mapSvg.id = "atlas-map";
    mapSvg.classList.add("atlas-map");
    $("map-canvas").replaceChildren(mapSvg);
    configureMapCountries();
    $("map-frame").setAttribute("aria-busy", "false");
    $("map-export-svg").disabled = false;
    $("map-export-png").disabled = false;
    renderMap();
  } catch (error) {
    $("map-frame").setAttribute("aria-busy", "false");
    $("map-canvas").innerHTML = `<p class="error">Kartengrundlage konnte nicht geladen werden: ${escapeHtml(error.message)}</p>`;
  }
}

async function loadMetricCatalog() {
  const response = await fetch("/api/metrics");
  if (!response.ok) throw new Error((await response.json()).error || response.statusText);
  metricCatalog = new Map((await response.json()).map(metric => [metric.id, metric]));
  renderMapControls();
  renderComparisonControls();
}

async function loadSummary() {
  $("status").textContent = "Daten werden geladen …";
  $("status").className = "";
  try {
    if (!metricCatalog.size) await loadMetricCatalog();
    const response = await fetch(`/api/summary?${periodQuery()}`);
    if (!response.ok) throw new Error((await response.json()).error || response.statusText);
    data = await response.json();
    render();
    renderElectromobility();
    renderCountryControls();
    renderMapControls();
    renderMap();
    const periodStatus = data[0]?.period_status;
    const periodNote = periodStatus === "provisional_current_month"
      ? " Laufender Monat: vorläufig."
      : (periodStatus === "ytd" ? " Laufendes Jahr: YTD." : "");
    $("status").textContent = data.some(row => Object.values(row).some(value => typeof value === "number"))
      ? `Atlas-Daten geladen.${periodNote}` : `Noch keine Daten importiert.${periodNote}`;
  } catch (error) {
    $("status").textContent = `Fehler: ${error.message}`;
    $("status").className = "error";
  }
}

function timeseriesMetrics() {
  return [...metricCatalog.values()].filter(metric => {
    const availability = metric.temporal_availability;
    return metric.compare && (availability.monthly || availability.yearly);
  });
}

function flagCode(code) {
  return code === "UK" ? "gb" : code.toLowerCase();
}

const NAMED_FLAG_COLORS = {
  red: "#ff0000", blue: "#0000ff", green: "#008000", yellow: "#ffff00",
  gold: "#ffd700", orange: "#ff8c00", white: "#ffffff", black: "#000000",
};

function normalizedHexColor(value) {
  let color = value.trim().toLowerCase();
  color = NAMED_FLAG_COLORS[color] || color;
  if (/^#[0-9a-f]{3}$/.test(color)) {
    color = `#${color[1]}${color[1]}${color[2]}${color[2]}${color[3]}${color[3]}`;
  }
  return /^#[0-9a-f]{6}$/.test(color) ? color : null;
}

function rgbColor(color) {
  const value = normalizedHexColor(color);
  if (!value) return null;
  return [1, 3, 5].map(index => Number.parseInt(value.slice(index, index + 2), 16));
}

function usefulFlagColor(color) {
  const rgb = rgbColor(color);
  if (!rgb) return false;
  const [red, green, blue] = rgb.map(channel => channel / 255);
  const luminance = .2126 * red + .7152 * green + .0722 * blue;
  const saturation = Math.max(red, green, blue) - Math.min(red, green, blue);
  return luminance >= .17 && luminance <= .9 && saturation >= .18;
}

function extractFlagColors(svgText) {
  const colors = [...svgText.matchAll(/\bfill=["']([^"']+)["']/gi)]
    .map(match => normalizedHexColor(match[1]))
    .filter(color => color && usefulFlagColor(color));
  return [...new Set(colors)];
}

function colorDistance(first, second) {
  const a = rgbColor(first);
  const b = rgbColor(second);
  if (!a || !b) return 0;
  return Math.sqrt(a.reduce((sum, channel, index) => sum + (channel - b[index]) ** 2, 0));
}

function assignCountryColors(countryCodes, candidatesByCode) {
  const colors = countryCodes.map((_code, index) => CHART_FALLBACK_COLORS[index % CHART_FALLBACK_COLORS.length]);
  countryCodes.forEach((code, index) => {
    const preferred = (candidatesByCode.get(code) || []).find(candidate => colors.every((other, otherIndex) => (
      otherIndex === index || colorDistance(candidate, other) >= MIN_CHART_COLOR_DISTANCE
    )));
    if (preferred) colors[index] = preferred;
  });
  return new Map(countryCodes.map((code, index) => [code, colors[index]]));
}

async function prepareTimeseriesColors(payload) {
  const candidates = new Map();
  await Promise.all(payload.countries.map(async country => {
    const code = country.country_code;
    if (!FLAG_COLOR_CACHE.has(code)) {
      try {
        const response = await fetch(`/assets/flags/${flagCode(code)}.svg`);
        FLAG_COLOR_CACHE.set(code, response.ok ? extractFlagColors(await response.text()) : []);
      } catch (_error) {
        FLAG_COLOR_CACHE.set(code, []);
      }
    }
    candidates.set(code, FLAG_COLOR_CACHE.get(code));
  }));
  timeseriesColors = assignCountryColors(payload.countries.map(country => country.country_code), candidates);
}

function chartColor(countryCode, index) {
  return timeseriesColors.get(countryCode) || CHART_FALLBACK_COLORS[index % CHART_FALLBACK_COLORS.length];
}

function renderCountryControls() {
  if (!$("compare-country-add")) return;
  const rows = [...data].sort((a, b) => a.country_name.localeCompare(b.country_name, "de"));
  $("compare-country-add").innerHTML = '<option value="">Land auswählen …</option>'
    + rows.map(row => `<option value="${row.country_code}"${selected.has(row.country_code) ? " disabled" : ""}>${escapeHtml(row.country_name)} (${row.country_code})</option>`).join("");
  $("compare-chips").innerHTML = [...selected].map(code => {
    const name = countryName(code);
    return `<span class="country-chip">
      <img src="/assets/flags/${flagCode(code)}.svg" alt="" width="24" height="18">
      <span>${escapeHtml(name)} <b>${code}</b></span>
      <button type="button" data-remove-country="${code}" aria-label="${escapeAttribute(name)} entfernen"><img class="europe-star" src="/assets/europe-star.svg" alt=""></button>
    </span>`;
  }).join("");
  document.querySelectorAll("[data-remove-country]").forEach(button => button.addEventListener("click", () => {
    toggleCountry(button.dataset.removeCountry, false);
  }));
}

function renderComparisonControls(metricId = null) {
  const allMetrics = [...metricCatalog.values()].filter(metric => metric.compare);
  if (!allMetrics.length) return;
  const activeMetric = metricCatalog.get(metricId || $("compare-metric").value)
    || metricCatalog.get(DEFAULT_COMPARISON_METRIC)
    || timeseriesMetrics()[0];
  const families = new Map();
  allMetrics.forEach(metric => {
    const key = familyKey(metric);
    if (!families.has(key)) families.set(key, []);
    families.get(key).push(metric);
  });
  $("compare-family").innerHTML = [...families].map(([key, variants]) => {
    const available = variants.some(metric => metric.temporal_availability.monthly || metric.temporal_availability.yearly);
    const label = `${variants[0].group} · ${variants[0].family}${available ? "" : " · kein Zeitverlauf"}`;
    return `<option value="${escapeAttribute(key)}"${available ? "" : " disabled"}>${escapeHtml(label)}</option>`;
  }).join("");
  const activeFamily = familyKey(activeMetric);
  $("compare-family").value = activeFamily;
  renderComparisonMetricOptions(activeFamily, activeMetric.id);
  renderCountryControls();
}

function renderComparisonMetricOptions(family, metricId = null) {
  const variants = orderedMetricVariants([...metricCatalog.values()].filter(metric => metric.compare && familyKey(metric) === family));
  $("compare-metric").innerHTML = variants.map(metric => {
    const availability = metric.temporal_availability;
    const available = availability.monthly || availability.yearly;
    const suffix = available ? ` (${metric.unit})` : " · kein Zeitverlauf";
    return `<option value="${metric.id}"${available ? "" : " disabled"}>${escapeHtml(metric.representation + suffix)}</option>`;
  }).join("");
  const next = variants.find(metric => metric.id === metricId && (metric.temporal_availability.monthly || metric.temporal_availability.yearly))
    || variants.find(metric => metric.temporal_availability.monthly || metric.temporal_availability.yearly);
  if (!next) return;
  $("compare-metric").value = next.id;
  configureComparisonRange(next);
}

function configureComparisonRange(metric) {
  const monthly = metric.temporal_availability.monthly;
  const startInput = $("compare-start");
  const endInput = $("compare-end");
  const previousStart = startInput.value;
  const previousEnd = endInput.value;
  if (monthly) {
    const maximum = `${currentYear}-${String(new Date().getMonth() + 1).padStart(2, "0")}`;
    for (const input of [startInput, endInput]) {
      input.type = "month";
      input.min = `${MIN_YEAR}-01`;
      input.max = maximum;
    }
    startInput.value = /^\d{4}-\d{2}$/.test(previousStart) ? previousStart : `${previousStart.slice(0, 4) || MIN_YEAR}-01`;
    endInput.value = /^\d{4}-\d{2}$/.test(previousEnd) ? previousEnd : maximum;
    if (!startInput.value) startInput.value = `${MIN_YEAR}-01`;
    if (!endInput.value) endInput.value = maximum;
  } else {
    for (const input of [startInput, endInput]) {
      input.type = "number";
      input.min = String(MIN_YEAR);
      input.max = String(currentYear);
      input.step = "1";
    }
    startInput.value = previousStart.slice(0, 4) || String(MIN_YEAR);
    endInput.value = previousEnd.slice(0, 4) || String(currentYear);
  }
  knownMaximumComparisonRange = null;
  syncComparisonPresetFromFields(metric);
}

function comparisonPresetRange(preset, metric, end, availableRange = null) {
  const monthly = Boolean(metric?.temporal_availability?.monthly);
  if (monthly) {
    const maximum = `${currentYear}-${String(new Date().getMonth() + 1).padStart(2, "0")}`;
    const normalizedEnd = /^\d{4}-\d{2}$/.test(end) ? end : maximum;
    const [endYear, endMonth] = normalizedEnd.split("-").map(Number);
    if (preset === "ytd") return {start: `${endYear}-01`, end: normalizedEnd};
    if (preset === "max") return {
      start: availableRange?.start || `${MIN_YEAR}-01`,
      end: availableRange?.end || normalizedEnd,
    };
    const years = Number.parseInt(preset, 10);
    if (!Number.isFinite(years)) return null;
    const startYear = Math.max(MIN_YEAR, endYear - years);
    return {start: `${startYear}-${String(endMonth).padStart(2, "0")}`, end: normalizedEnd};
  }

  if (preset === "ytd") return null;
  const normalizedEnd = /^\d{4}$/.test(end) ? end : String(currentYear);
  const endYear = Number(normalizedEnd);
  if (preset === "max") return {
    start: availableRange?.start || String(MIN_YEAR),
    end: availableRange?.end || normalizedEnd,
  };
  const years = Number.parseInt(preset, 10);
  if (!Number.isFinite(years)) return null;
  return {start: String(Math.max(MIN_YEAR, endYear - years + 1)), end: normalizedEnd};
}

function availableComparisonRange(payload) {
  const countryPoints = (payload?.countries || []).flatMap(country => country.values || []);
  const source = countryPoints.some(point => Number.isFinite(point.value))
    ? countryPoints
    : (payload?.atlas_average?.values || []);
  const periods = source.filter(point => Number.isFinite(point.value)).map(point => point.period).sort();
  return periods.length ? {start: periods[0], end: periods[periods.length - 1]} : null;
}

function latestCompleteComparisonIndex(payload) {
  const countries = payload?.countries || [];
  if (!countries.length) return null;
  const periodCount = Math.max(...countries.map(country => country.values?.length || 0));
  for (let index = periodCount - 1; index >= 0; index -= 1) {
    const points = countries.map(country => country.values?.[index]);
    if (points.every(point => point?.period && Number.isFinite(point.value))) return index;
  }
  return null;
}

function latestCompleteComparisonPeriod(payload) {
  const index = latestCompleteComparisonIndex(payload);
  return index === null ? null : payload.countries[0].values[index].period;
}

function setActiveComparisonPreset(preset) {
  activeComparisonPreset = preset;
  const container = $("comparison-presets");
  const buttons = [...container.querySelectorAll("[data-range-preset]")];
  const index = COMPARISON_PRESETS.indexOf(preset);
  container.dataset.hasActive = String(index >= 0);
  container.style.setProperty("--preset-index", String(Math.max(index, 0)));
  buttons.forEach(button => {
    const active = button.dataset.rangePreset === preset;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

function syncComparisonPresetFromFields(metric = metricDefinition($("compare-metric").value)) {
  const monthly = Boolean(metric?.temporal_availability?.monthly);
  const ytdButton = document.querySelector('[data-range-preset="ytd"]');
  ytdButton.disabled = !monthly;
  ytdButton.setAttribute("aria-disabled", String(!monthly));
  const start = $("compare-start").value;
  const end = $("compare-end").value;
  const match = COMPARISON_PRESETS.find(preset => {
    const range = comparisonPresetRange(preset, metric, end, knownMaximumComparisonRange);
    return range && range.start === start && range.end === end;
  }) || null;
  setActiveComparisonPreset(match);
}

async function applyComparisonPreset(preset) {
  const metric = metricDefinition($("compare-metric").value);
  const range = comparisonPresetRange(preset, metric, $("compare-end").value, null);
  if (!range) return;
  $("compare-start").value = range.start;
  $("compare-end").value = range.end;
  setActiveComparisonPreset(preset);
  await loadTimeseries({scroll: false, updateUrl: true, availabilityPreset: preset});
}

function comparisonQuery() {
  const params = new URLSearchParams({
    metric: $("compare-metric").value,
    countries: [...selected].join(","),
    start: $("compare-start").value,
    end: $("compare-end").value,
  });
  return params;
}

function writeComparisonUrl() {
  const url = new URL(window.location.href);
  url.search = "";
  url.searchParams.set("view", "compare");
  for (const [key, value] of comparisonQuery()) url.searchParams.set(key, value);
  history.replaceState(null, "", url);
  return url.href;
}

function parseComparisonUrl(search, validCodes, catalog, now = new Date()) {
  const params = new URLSearchParams(search);
  if (params.get("view") !== "compare") return null;
  const codes = (params.get("countries") || "").split(",").filter(Boolean).map(code => code.toUpperCase());
  const metric = catalog.get(params.get("metric"));
  if (
    !codes.length || codes.length > 10 || new Set(codes).size !== codes.length
    || codes.some(code => !validCodes.has(code))
    || !metric || !(metric.temporal_availability.monthly || metric.temporal_availability.yearly)
  ) return {valid: false};

  const monthly = metric.temporal_availability.monthly;
  const start = params.get("start") || "";
  const end = params.get("end") || "";
  const pattern = monthly ? /^\d{4}-(0[1-9]|1[0-2])$/ : /^\d{4}$/;
  const maximum = monthly
    ? `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`
    : String(now.getFullYear());
  const minimum = monthly ? `${MIN_YEAR}-01` : String(MIN_YEAR);
  if (!pattern.test(start) || !pattern.test(end) || start < minimum || end > maximum || start > end) {
    return {valid: false};
  }
  return {valid: true, codes, metric, start, end};
}

async function restoreComparisonState() {
  const validCodes = new Set(data.map(row => row.country_code));
  const parsed = parseComparisonUrl(window.location.search, validCodes, metricCatalog);
  if (parsed === null) return false;
  if (!parsed.valid) {
    $("comparison").hidden = false;
    $("comparison-status").textContent = "Der Direktlink enthält ungültige Vergleichswerte und wurde nicht übernommen.";
    return false;
  }
  selected.clear();
  parsed.codes.forEach(code => selected.add(code));
  renderComparisonControls(parsed.metric.id);
  $("compare-start").value = parsed.start;
  $("compare-end").value = parsed.end;
  syncComparisonPresetFromFields(parsed.metric);
  updateSelection();
  $("comparison").hidden = false;
  await loadTimeseries({scroll: false, updateUrl: false});
  return true;
}

async function initializeDefaultComparison() {
  selected.clear();
  DEFAULT_COMPARISON_COUNTRIES.forEach(code => selected.add(code));
  renderComparisonControls(DEFAULT_COMPARISON_METRIC);
  updateSelection();
  $("comparison").hidden = false;
  await applyComparisonPreset("max");
}

async function compare() {
  $("comparison").hidden = false;
  renderComparisonControls();
  await loadTimeseries({scroll: true, updateUrl: true});
}

async function loadTimeseries({scroll = false, updateUrl = true, availabilityPreset = null, availabilityAdjusted = false} = {}) {
  if (!selected.size) {
    $("comparison-status").textContent = "Mindestens ein Land auswählen.";
    return;
  }
  $("comparison-status").textContent = "Zeitreihe wird geladen …";
  const response = await fetch(`/api/timeseries?${comparisonQuery()}`);
  const payload = await response.json();
  if (!response.ok) {
    $("comparison-status").textContent = `Fehler: ${payload.error}`;
    return;
  }
  const payloadAvailableRange = availableComparisonRange(payload);
  const completeEnd = latestCompleteComparisonPeriod(payload);
  const maximumRange = payloadAvailableRange && completeEnd ? {...payloadAvailableRange, end: completeEnd} : payloadAvailableRange;
  if (availabilityPreset === "max" && maximumRange) knownMaximumComparisonRange = maximumRange;
  if (availabilityPreset && !availabilityAdjusted && payloadAvailableRange) {
    let adjusted = null;
    if (availabilityPreset === "max") adjusted = maximumRange;
    if (availabilityPreset === "ytd" && payload.granularity === "monthly") {
      const requestedYear = $("compare-end").value.slice(0, 4);
      if (payloadAvailableRange.end.startsWith(requestedYear)) {
        adjusted = {start: `${requestedYear}-01`, end: payloadAvailableRange.end};
      }
    }
    if (adjusted && (adjusted.start !== $("compare-start").value || adjusted.end !== $("compare-end").value)) {
      $("compare-start").value = adjusted.start;
      $("compare-end").value = adjusted.end;
      return loadTimeseries({scroll, updateUrl, availabilityPreset, availabilityAdjusted: true});
    }
  }
  timeseriesData = payload;
  await prepareTimeseriesColors(payload);
  chartHoverIndex = null;
  chartPinnedIndex = null;
  animateChartNextRender = true;
  renderTimeseriesChart();
  for (const id of ["export-csv", "export-svg", "export-png", "copy-link"]) $(id).disabled = false;
  $("comparison-status").textContent = `${payload.countries.length} Länder · ${payload.granularity === "monthly" ? "Monatswerte" : "Jahreswerte"} · fehlende Werte bleiben als Linienlücken sichtbar.`;
  syncComparisonPresetFromFields(payload.metric);
  if (updateUrl) writeComparisonUrl();
  if (scroll) $("comparison").scrollIntoView({behavior: "smooth"});
}

function svgElement(name, attributes = {}, text = null) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, String(value)));
  if (text !== null) element.textContent = text;
  return element;
}

function comparisonIsFullscreen() {
  return document.fullscreenElement === $("comparison-stage");
}

function chartGeometry() {
  const height = 640;
  const chartRect = $("timeseries-chart").getBoundingClientRect();
  const ratio = chartRect.height > 0 ? chartRect.width / chartRect.height : 2.1;
  const width = Math.max(1180, Math.round(height * ratio));
  const left = 100;
  const right = width - 230;
  return {
    width, height, left, right,
    top: 76,
    bottom: 510,
    legendY: 575,
    legendColumns: 6,
    legendColumnWidth: (right - left) / 6,
    connectorX: right + 30,
    flagX: right + 40,
    tagX: right + 80,
    endpointGap: 30,
  };
}

function chartScale(payload, geometry) {
  const values = [
    ...payload.countries.flatMap(country => country.values.map(point => point.value)),
    ...payload.atlas_average.values.map(point => point.value),
  ].filter(Number.isFinite);
  let minimum = values.length ? Math.min(...values) : 0;
  let maximum = values.length ? Math.max(...values) : 1;
  const metric = payload.metric;
  const diverging = metric.map_config?.scale === "diverging";
  if (metric.unit === "%" && !diverging) {
    minimum = 0;
    maximum = 100;
  } else if (diverging) {
    const extent = Math.max(Math.abs(minimum), Math.abs(maximum), 1);
    minimum = -extent;
    maximum = extent;
  } else {
    minimum = Math.min(0, minimum);
    maximum = Math.max(maximum, minimum + 1);
  }
  if (minimum === maximum) maximum = minimum + 1;
  const padding = diverging || metric.unit === "%" ? 0 : (maximum - minimum) * 0.06;
  maximum += padding;
  const x = index => geometry.left + index / Math.max(1, payload.atlas_average.values.length - 1) * (geometry.right - geometry.left);
  const y = value => geometry.bottom - (value - minimum) / (maximum - minimum) * (geometry.bottom - geometry.top);
  return {minimum, maximum, x, y};
}

function linePath(points, scale) {
  let path = "";
  let drawing = false;
  points.forEach((point, index) => {
    if (!Number.isFinite(point.value)) {
      drawing = false;
      return;
    }
    path += `${drawing ? "L" : "M"}${scale.x(index).toFixed(2)},${scale.y(point.value).toFixed(2)} `;
    drawing = true;
  });
  return path.trim();
}

function endpointPositions(payload, scale, geometry) {
  const endpoints = payload.countries.map((country, countryIndex) => {
    let pointIndex = country.values.length - 1;
    while (pointIndex >= 0 && !Number.isFinite(country.values[pointIndex].value)) pointIndex -= 1;
    if (pointIndex < 0) return null;
    return {
      country,
      countryIndex,
      pointIndex,
      x: scale.x(pointIndex),
      targetY: scale.y(country.values[pointIndex].value),
      y: scale.y(country.values[pointIndex].value),
    };
  }).filter(Boolean);
  const averagePoint = [...payload.atlas_average.values]
    .map((point, index) => ({point, index}))
    .reverse()
    .find(item => Number.isFinite(item.point.value));
  if (averagePoint) {
    endpoints.push({
      average: true,
      x: scale.x(averagePoint.index),
      targetY: scale.y(averagePoint.point.value),
      y: scale.y(averagePoint.point.value),
    });
  }
  endpoints.sort((a, b) => a.targetY - b.targetY);
  const gap = geometry.endpointGap;
  endpoints.forEach((endpoint, index) => {
    endpoint.y = Math.max(endpoint.targetY, geometry.top + 10, index ? endpoints[index - 1].y + gap : -Infinity);
  });
  for (let index = endpoints.length - 1; index >= 0; index -= 1) {
    const maximum = index === endpoints.length - 1 ? geometry.bottom - 10 : endpoints[index + 1].y - gap;
    endpoints[index].y = Math.min(endpoints[index].y, maximum);
  }
  return endpoints;
}

function renderTimeseriesChart() {
  if (!timeseriesData) return;
  const svg = $("timeseries-chart");
  const payload = timeseriesData;
  const metric = payload.metric;
  const geometry = chartGeometry();
  const scale = chartScale(payload, geometry);
  const periods = payload.atlas_average.values.map(point => point.period);
  const activeIndex = chartPinnedIndex ?? chartHoverIndex;
  const animateThisRender = animateChartNextRender && motionAllowed();
  animateChartNextRender = false;
  svg.replaceChildren();
  svg.setAttribute("viewBox", `0 0 ${geometry.width} ${geometry.height}`);
  svg.appendChild(svgElement("rect", {class: "chart-background", x: 0, y: 0, width: geometry.width, height: geometry.height, rx: 12}));
  svg.appendChild(svgElement("text", {class: "chart-title", x: geometry.left, y: 34}, metric.label_de));
  svg.appendChild(svgElement("text", {class: "chart-subtitle", x: geometry.left, y: 57}, `${metric.representation} · ${metric.unit} · ${payload.start} bis ${payload.end}`));

  for (let tick = 0; tick <= 5; tick += 1) {
    const value = scale.minimum + (scale.maximum - scale.minimum) * tick / 5;
    const y = scale.y(value);
    svg.appendChild(svgElement("line", {class: "chart-grid", x1: geometry.left, x2: geometry.right, y1: y, y2: y}));
    svg.appendChild(svgElement("text", {class: "axis-label y-axis-label", x: geometry.left - 12, y: y + 4}, formatMetricValue(value, metric)));
  }
  const tickStep = Math.max(1, Math.ceil(periods.length / 8));
  periods.forEach((period, index) => {
    if (index % tickStep !== 0 && index !== periods.length - 1) return;
    const x = scale.x(index);
    svg.appendChild(svgElement("line", {class: "chart-grid vertical", x1: x, x2: x, y1: geometry.top, y2: geometry.bottom}));
    svg.appendChild(svgElement("text", {class: "axis-label x-axis-label", x, y: geometry.bottom + 28}, period));
  });
  if (scale.minimum < 0 && scale.maximum > 0) {
    const zeroY = scale.y(0);
    svg.appendChild(svgElement("line", {class: "chart-zero", x1: geometry.left, x2: geometry.right, y1: zeroY, y2: zeroY}));
  }
  if (activeIndex !== null) {
    const guideX = scale.x(activeIndex);
    svg.appendChild(svgElement("line", {class: "chart-guide", x1: guideX, x2: guideX, y1: geometry.top, y2: geometry.bottom}));
  }

  const averagePath = linePath(payload.atlas_average.values, scale);
  if (averagePath) svg.appendChild(svgElement("path", {class: `chart-line atlas-average-line${animateThisRender ? " draw-once" : ""}`, d: averagePath, pathLength: 1}));
  payload.countries.forEach((country, index) => {
    const path = linePath(country.values, scale);
    if (!path) return;
    const color = chartColor(country.country_code, index);
    svg.appendChild(svgElement("path", {
      class: `chart-line country-line${animateThisRender ? " draw-once" : ""}`,
      d: path,
      pathLength: 1,
      stroke: color,
      "data-country-line": country.country_code,
    }));
    if (activeIndex !== null && Number.isFinite(country.values[activeIndex]?.value)) {
      svg.appendChild(svgElement("circle", {
        class: "chart-point",
        cx: scale.x(activeIndex),
        cy: scale.y(country.values[activeIndex].value),
        r: 3.5,
        fill: color,
      }));
    }
  });

  endpointPositions(payload, scale, geometry).forEach(endpoint => {
    if (endpoint.average) {
      svg.appendChild(svgElement("path", {
        class: "endpoint-connector average-endpoint-connector",
        d: `M${endpoint.x},${endpoint.targetY} L${geometry.connectorX},${endpoint.y}`,
        stroke: "#edf3fb",
      }));
      svg.appendChild(svgElement("text", {
        class: `average-endpoint-tag${animateThisRender ? " chart-enter" : ""}`,
        x: geometry.flagX,
        y: endpoint.y + 5,
      }, "Atlas Ø"));
      return;
    }
    const color = chartColor(endpoint.country.country_code, endpoint.countryIndex);
    svg.appendChild(svgElement("path", {
      class: "endpoint-connector",
      d: `M${endpoint.x},${endpoint.targetY} L${geometry.connectorX},${endpoint.y}`,
      stroke: color,
    }));
    svg.appendChild(svgElement("image", {
      class: `endpoint-flag${animateThisRender ? " chart-enter" : ""}`,
      href: `/assets/flags/${flagCode(endpoint.country.country_code)}.svg`,
      x: geometry.flagX,
      y: endpoint.y - 11,
      width: 30,
      height: 22,
    }));
    svg.appendChild(svgElement("text", {class: `endpoint-tag${animateThisRender ? " chart-enter" : ""}`, x: geometry.tagX, y: endpoint.y + 5, fill: color}, endpoint.country.country_code));
  });
  [...payload.countries.map((country, index) => ({label: country.country_code, color: chartColor(country.country_code, index)})), {label: "Atlas-Durchschnitt", color: "#edf3fb", average: true}]
    .forEach((item, index) => {
      const column = index % geometry.legendColumns;
      const row = Math.floor(index / geometry.legendColumns);
      const x = geometry.left + column * geometry.legendColumnWidth;
      const y = geometry.legendY + row * 28;
      const line = svgElement("line", {class: item.average ? "legend-line average" : "legend-line", x1: x, x2: x + 24, y1: y, y2: y, stroke: item.color});
      svg.appendChild(line);
      svg.appendChild(svgElement("text", {class: "legend-label", x: x + 32, y: y + 4}, item.label));
    });

  svg.appendChild(svgElement("rect", {
    class: "chart-interaction",
    x: geometry.left,
    y: geometry.top,
    width: geometry.right - geometry.left,
    height: geometry.bottom - geometry.top,
  }));
  bindChartInteraction(svg, scale, geometry);
  renderRanking(activeIndex ?? latestCompleteComparisonIndex(payload) ?? periods.length - 1);
  $("unpin-time").hidden = chartPinnedIndex === null;
}

function chartIndexFromClientX(clientX, rect, pointCount) {
  const ratio = (clientX - rect.left) / Math.max(rect.width, 1);
  return Math.max(0, Math.min(pointCount - 1, Math.round(ratio * Math.max(1, pointCount - 1))));
}

function bindChartInteraction(svg, scale, geometry) {
  const overlay = svg.querySelector(".chart-interaction");
  overlay.addEventListener("pointermove", event => {
    const count = timeseriesData.atlas_average.values.length;
    const index = chartIndexFromClientX(event.clientX, overlay.getBoundingClientRect(), count);
    if (index !== chartHoverIndex) {
      chartHoverIndex = index;
      renderTimeseriesChart();
    }
  });
  overlay.addEventListener("pointerleave", () => {
    if (chartPinnedIndex === null && chartHoverIndex !== null) {
      chartHoverIndex = null;
      renderTimeseriesChart();
    }
  });
  overlay.addEventListener("click", event => {
    const count = timeseriesData.atlas_average.values.length;
    const index = chartIndexFromClientX(event.clientX, overlay.getBoundingClientRect(), count);
    chartPinnedIndex = chartPinnedIndex === index ? null : index;
    chartHoverIndex = index;
    renderTimeseriesChart();
  });
}

function comparisonBaselineYear(payload = timeseriesData) {
  const year = Number(payload?.comparison_baseline?.year);
  return Number.isInteger(year) ? year : MIN_YEAR;
}

function comparisonBaselinePoint(country, period, granularity, baselineYear = MIN_YEAR) {
  const baselinePeriod = granularity === "monthly" ? `${baselineYear}-${period.slice(5, 7)}` : String(baselineYear);
  return country.baseline_values?.find(point => point.period === baselinePeriod) || null;
}

function rankingFallbackDetails(country, index) {
  const period = country.values[index]?.period || "";
  const granularity = timeseriesData?.granularity || (period.includes("-") ? "monthly" : "yearly");
  const baselineYear = comparisonBaselineYear();
  const baselinePoint = comparisonBaselinePoint(country, period, granularity, baselineYear);
  const incomplete = country.values.some(point => !Number.isFinite(point.value));
  const reasons = [];
  if (incomplete) reasons.push("Datenreihe unvollständig");
  if (!Number.isFinite(baselinePoint?.value)) reasons.push(`Vergleichswert ${baselineYear} fehlt`);
  return {
    active: reasons.length > 0,
    text: reasons.length ? `${country.country_name}: ${reasons.join("; ")}` : "",
  };
}

function relativeBaselineChange(country, index, granularity, baselineYear = MIN_YEAR) {
  const current = country.values[index]?.value;
  const period = country.values[index]?.period || "";
  const baseline = comparisonBaselinePoint(country, period, granularity, baselineYear)?.value;
  if (!Number.isFinite(current) || !Number.isFinite(baseline) || baseline === 0) return null;
  return (current - baseline) / baseline * 100;
}

function rankingChange(country, index) {
  const change = relativeBaselineChange(country, index, timeseriesData.granularity, comparisonBaselineYear());
  if (!Number.isFinite(change)) return "—";
  return `${change >= 0 ? "+" : ""}${new Intl.NumberFormat("de-DE", {maximumFractionDigits: 1}).format(change)} %`;
}

function renderRanking(index) {
  const previous = new Map([...$("ranking-list").children].map(item => [item.dataset.country, item.getBoundingClientRect().top]));
  const previousValues = new Map([...$("ranking-list").children].map(item => {
    const raw = item.querySelector(".ranking-number")?.dataset.numeric;
    return [item.dataset.country, raw ? Number(raw) : null];
  }));
  const previousAverageRaw = $("atlas-average-value").dataset.numeric;
  const previousAverage = previousAverageRaw ? Number(previousAverageRaw) : null;
  const period = timeseriesData.atlas_average.values[index].period;
  const entries = timeseriesData.countries.map((country, countryIndex) => {
    const fallback = rankingFallbackDetails(country, index);
    return {country, countryIndex, value: country.values[index]?.value, fallback};
  }).sort((a, b) => {
    if (!Number.isFinite(a.value) && !Number.isFinite(b.value)) return a.country.country_name.localeCompare(b.country.country_name, "de");
    if (!Number.isFinite(a.value)) return 1;
    if (!Number.isFinite(b.value)) return -1;
    return b.value - a.value || a.country.country_name.localeCompare(b.country.country_name, "de");
  });
  let rank = 0;
  let previousValue = null;
  entries.forEach((entry, position) => {
    if (Number.isFinite(entry.value) && entry.value !== previousValue) rank = position + 1;
    entry.rank = Number.isFinite(entry.value) ? rank : null;
    previousValue = entry.value;
  });
  const periodStatus = timeseriesData.atlas_average.values[index].period_status;
  $("ranking-period").textContent = `${period}${periodStatus === "ytd" ? " · YTD" : periodStatus === "provisional_current_month" ? " · vorläufig" : ""}`;
  const average = timeseriesData.atlas_average.values[index].value;
  $("atlas-average-value").dataset.numeric = Number.isFinite(average) ? String(average) : "";
  $("atlas-average-value").innerHTML = `Atlas-Durchschnitt · <span class="ranking-average-number" data-numeric="${Number.isFinite(average) ? average : ""}">${formatMetricValue(average, timeseriesData.metric)}</span> ${escapeHtml(timeseriesData.metric.unit)}`;
  const baselineYear = comparisonBaselineYear();
  $("ranking-baseline-note").textContent = timeseriesData.granularity === "monthly"
    ? `Veränderung gegenüber demselben Kalendermonat ${baselineYear}`
    : `Veränderung gegenüber dem Jahreswert ${baselineYear}`;
  $("ranking-list").innerHTML = entries.map(entry => {
    return `<li data-country="${entry.country.country_code}" class="ranking-item${Number.isFinite(entry.value) ? "" : " missing-value"}">
      <span class="ranking-rank">${entry.rank || "—"}</span>
      <img src="/assets/flags/${flagCode(entry.country.country_code)}.svg" alt="" width="24" height="18">
      <span class="ranking-country"><b>${entry.country.country_code}${SHOW_RANKING_DATA_QUALITY_NOTICES && entry.fallback.active ? '<sup class="ranking-fallback-marker" aria-label="Hinweis">*</sup>' : ""}</b><small>${escapeHtml(entry.country.country_name)}</small></span>
      <span class="ranking-value"><span class="ranking-number" data-numeric="${Number.isFinite(entry.value) ? entry.value : ""}">${formatMetricValue(entry.value, timeseriesData.metric)}</span><small>${Number.isFinite(entry.value) ? timeseriesData.metric.unit : ""}</small></span>
      <span class="ranking-change">${rankingChange(entry.country, index)}</span>
    </li>`;
  }).join("");
  const fallbackNotes = SHOW_RANKING_DATA_QUALITY_NOTICES
    ? entries.filter(entry => entry.fallback.active).map(entry => `<span class="ranking-footnote-star" aria-hidden="true">*</span> ${escapeHtml(entry.fallback.text)}`)
    : [];
  $("ranking-footnotes").hidden = fallbackNotes.length === 0;
  $("ranking-footnotes").innerHTML = fallbackNotes.join("<br>");
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    animateMetricNumber($("atlas-average-value").querySelector(".ranking-average-number"), previousAverage, average, timeseriesData.metric);
    $("ranking-list").querySelectorAll(".ranking-item").forEach(item => {
      const raw = item.querySelector(".ranking-number")?.dataset.numeric;
      const next = raw ? Number(raw) : null;
      animateMetricNumber(item.querySelector(".ranking-number"), previousValues.get(item.dataset.country), next, timeseriesData.metric);
    });
    requestAnimationFrame(() => {
      [...$("ranking-list").children].forEach(item => {
        const oldTop = previous.get(item.dataset.country);
        if (oldTop === undefined) return;
        const delta = oldTop - item.getBoundingClientRect().top;
        if (!delta) return;
        item.style.transform = `translateY(${delta}px)`;
        item.style.transition = "none";
        requestAnimationFrame(() => {
          item.style.transition = "transform .24s ease";
          item.style.transform = "translateY(0)";
        });
      });
    });
  }
}

function animateMetricNumber(element, from, to, metric) {
  if (!element || !Number.isFinite(from) || !Number.isFinite(to) || from === to) return;
  const started = performance.now();
  const duration = 420;
  const frame = now => {
    const progress = Math.min(1, (now - started) / duration);
    const eased = 1 - Math.pow(1 - progress, 3);
    element.textContent = formatMetricValue(from + (to - from) * eased, metric);
    if (progress < 1 && element.isConnected) requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
}

function buildComparisonCsv(payload) {
  const header = ["period", ...payload.countries.map(country => country.country_code), "atlas_average"];
  const rows = payload.atlas_average.values.map((average, index) => [
    average.period,
    ...payload.countries.map(country => country.values[index].value ?? ""),
    average.value ?? "",
  ]);
  return [header, ...rows].map(row => row.map(value => {
    const text = String(value);
    return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  }).join(",")).join("\r\n");
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    assignCountryColors,
    buildComparisonCsv,
    colorDistance,
    electromobilityRowsForView,
    extractFlagColors,
    flagCode,
    formatTableValue,
    availableComparisonRange,
    comparisonPresetRange,
    chartIndexFromClientX,
    comparisonBaselineYear,
    latestCompleteComparisonIndex,
    latestCompleteComparisonPeriod,
    parseComparisonUrl,
    comparisonBaselinePoint,
    rankingFallbackDetails,
    relativeBaselineChange,
  };
}

function downloadBlob(blob, filename) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.hidden = true;
  document.body.appendChild(link);
  link.click();
  const href = link.href;
  link.remove();
  setTimeout(() => URL.revokeObjectURL(href), 1000);
}

function pulseExportFrame(element) {
  if (!motionAllowed() || !element) return;
  element.classList.remove("export-success-pulse");
  void element.offsetWidth;
  element.classList.add("export-success-pulse");
  element.addEventListener("animationend", () => element.classList.remove("export-success-pulse"), {once: true});
}

function comparisonFilename(extension) {
  return `eea-${timeseriesData.metric.id}-${timeseriesData.start}-${timeseriesData.end}.${extension}`;
}

async function serializedChartSvg() {
  const clone = $("timeseries-chart").cloneNode(true);
  clone.querySelectorAll(".chart-interaction").forEach(element => element.remove());
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  const viewBox = clone.getAttribute("viewBox").split(/\s+/).map(Number);
  clone.setAttribute("width", String(viewBox[2]));
  clone.setAttribute("height", String(viewBox[3]));
  const style = document.createElementNS("http://www.w3.org/2000/svg", "style");
  style.textContent = `
    .chart-background{fill:#0a1422}.chart-title{fill:#f7f5f0;font:750 24px Calibri,"Segoe UI",sans-serif}
    .chart-subtitle,.axis-label,.legend-label,.average-endpoint-tag{fill:#b6c1cc;font:13px Calibri,"Segoe UI",sans-serif}
    .chart-grid{stroke:#34495f;stroke-width:1}.chart-grid.vertical{stroke-opacity:.45}
    .chart-zero{stroke:#b89a5a;stroke-width:1.5}.chart-line{fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
    .atlas-average-line{stroke:#edf3fb;stroke-width:1.7;stroke-dasharray:10 7;opacity:.85}
    .chart-guide{stroke:#dbe8f6;stroke-width:1.2;stroke-dasharray:4 5}.chart-point{stroke:#08101c;stroke-width:2}
    .endpoint-connector{fill:none;stroke-width:1;opacity:.8}.average-endpoint-connector{stroke-dasharray:6 5}.endpoint-tag{font:800 14px Calibri,"Segoe UI",sans-serif}
    .average-endpoint-tag{font-weight:750;fill:#edf3fb}.legend-line{stroke-width:3}.legend-line.average{stroke-dasharray:7 5}
    .x-axis-label{text-anchor:middle}.y-axis-label{text-anchor:end}
  `;
  clone.prepend(style);
  await inlineSvgImages(clone);
  return `<?xml version="1.0" encoding="UTF-8"?>\n${new XMLSerializer().serializeToString(clone)}`;
}

async function inlineSvgImages(root) {
  for (const image of root.querySelectorAll("image")) {
    const href = image.getAttribute("href");
    if (!href || href.startsWith("data:")) continue;
    const response = await fetch(href);
    const source = await response.text();
    image.setAttribute("href", `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(source)))}`);
  }
}

function liveRankingExportEntries() {
  return [...$("ranking-list").querySelectorAll(".ranking-item")].map(item => ({
    rank: item.querySelector(".ranking-rank")?.textContent.trim() || "—",
    code: item.dataset.country,
    name: item.querySelector(".ranking-country small")?.textContent.trim() || "",
    value: item.querySelector(".ranking-number")?.textContent.trim() || "—",
    unit: item.querySelector(".ranking-value small")?.textContent.trim() || "",
    change: item.querySelector(".ranking-change")?.textContent.trim() || "—",
  }));
}

async function serializedChartPngSvg() {
  const chartSource = await serializedChartSvg();
  const chart = new DOMParser().parseFromString(chartSource, "image/svg+xml").documentElement;
  const [, , chartWidth, chartHeight] = chart.getAttribute("viewBox").split(/\s+/).map(Number);
  const panelWidth = 390;
  const gap = 18;
  const panelX = chartWidth + gap;
  const root = svgElement("svg", {
    xmlns: "http://www.w3.org/2000/svg",
    viewBox: `0 0 ${chartWidth + gap + panelWidth} ${chartHeight}`,
    width: chartWidth + gap + panelWidth,
    height: chartHeight,
  });
  root.appendChild(svgElement("rect", {width: chartWidth + gap + panelWidth, height: chartHeight, fill: "#070d18"}));
  const chartCopy = document.importNode(chart, true);
  chartCopy.setAttribute("x", "0");
  chartCopy.setAttribute("y", "0");
  chartCopy.setAttribute("width", chartWidth);
  chartCopy.setAttribute("height", chartHeight);
  root.appendChild(chartCopy);
  root.appendChild(svgElement("rect", {x: panelX, y: 0, width: panelWidth, height: chartHeight, rx: 12, fill: "#0d1626", stroke: "#2b3b52"}));
  const text = (x, y, value, attributes = {}) => root.appendChild(svgElement("text", {x, y, "font-family": 'Calibri,"Segoe UI",sans-serif', ...attributes}, value));
  text(panelX + 22, 35, "Live-Ranking", {fill: "#f7f5f0", "font-size": 22, "font-weight": 750});
  text(panelX + panelWidth - 22, 35, $("ranking-period").textContent.trim(), {fill: "#b6c1cc", "font-size": 14, "font-weight": 700, "text-anchor": "end"});
  root.appendChild(svgElement("rect", {x: panelX + 18, y: 52, width: panelWidth - 36, height: 42, rx: 8, fill: "#111d2e", stroke: "#52657c", "stroke-dasharray": "3 3"}));
  text(panelX + 30, 78, $("atlas-average-value").textContent.trim(), {fill: "#edf3fb", "font-size": 14, "font-weight": 750});
  text(panelX + 22, 117, $("ranking-baseline-note").textContent.trim(), {fill: "#b6c1cc", "font-size": 12});
  liveRankingExportEntries().forEach((entry, index) => {
    const y = 130 + index * 36;
    root.appendChild(svgElement("rect", {x: panelX + 18, y, width: panelWidth - 36, height: 31, rx: 7, fill: "#152238"}));
    text(panelX + 35, y + 20, entry.rank, {fill: "#b6c1cc", "font-size": 14, "font-weight": 750, "text-anchor": "middle"});
    root.appendChild(svgElement("image", {href: `/assets/flags/${flagCode(entry.code)}.svg`, x: panelX + 52, y: y + 6, width: 22, height: 16}));
    text(panelX + 84, y + 15, entry.code, {fill: "#f7f5f0", "font-size": 14, "font-weight": 800});
    text(panelX + 84, y + 27, entry.name, {fill: "#b6c1cc", "font-size": 9});
    text(panelX + panelWidth - 94, y + 15, entry.value, {fill: "#f7f5f0", "font-size": 14, "font-weight": 800, "text-anchor": "end"});
    text(panelX + panelWidth - 94, y + 27, entry.unit, {fill: "#b6c1cc", "font-size": 9, "text-anchor": "end"});
    text(panelX + panelWidth - 28, y + 20, entry.change, {fill: "#8ba2bd", "font-size": 11, "font-weight": 700, "text-anchor": "end"});
  });
  await inlineSvgImages(root);
  return `<?xml version="1.0" encoding="UTF-8"?>\n${new XMLSerializer().serializeToString(root)}`;
}

async function exportSvg() {
  downloadBlob(new Blob([await serializedChartSvg()], {type: "image/svg+xml;charset=utf-8"}), comparisonFilename("svg"));
  pulseExportFrame($("comparison-stage"));
}

async function exportPng() {
  const blob = await buildChartPngBlob();
  downloadBlob(blob, comparisonFilename("png"));
  pulseExportFrame($("comparison-stage"));
}

async function buildChartPngBlob() {
  const source = await serializedChartPngSvg();
  const url = URL.createObjectURL(new Blob([source], {type: "image/svg+xml;charset=utf-8"}));
  const image = new Image();
  await new Promise((resolve, reject) => {
    image.onload = resolve;
    image.onerror = reject;
    image.src = url;
  });
  const canvas = document.createElement("canvas");
  const chartBox = $("timeseries-chart").viewBox.baseVal;
  canvas.width = chartBox.width * 2;
  canvas.height = chartBox.height * 2;
  const context = canvas.getContext("2d");
  context.fillStyle = "#070d18";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.drawImage(image, 0, 0, canvas.width, canvas.height);
  URL.revokeObjectURL(url);
  return new Promise(resolve => canvas.toBlob(resolve, "image/png"));
}

function mapIsFullscreen() {
  return document.fullscreenElement === $("map-stage");
}

function updateMapFullscreenButton() {
  const active = mapIsFullscreen();
  const button = $("map-fullscreen");
  button.textContent = active ? "Vollbild verlassen" : "Vollbild";
  button.setAttribute("aria-pressed", String(active));
}

async function toggleMapFullscreen() {
  const stage = $("map-stage");
  if (mapIsFullscreen()) {
    await document.exitFullscreen();
  } else if (stage.requestFullscreen) {
    await stage.requestFullscreen();
  } else {
    $("map-availability").textContent = "Dieser Browser unterstützt die Vollbildansicht nicht.";
  }
}

function mapFilename(extension) {
  return `eea-map-${mapMetricId}-${periodLabel(metricDefinition(mapMetricId)).replace(/[^0-9a-z-]+/gi, "-").toLowerCase()}.${extension}`;
}

function appendExportText(root, text, x, y, className) {
  root.appendChild(svgElement("text", {x, y, class: className}, text));
}

async function serializedMapSvg() {
  if (!mapSvg) throw new Error("Karte ist noch nicht geladen.");
  const metric = metricDefinition(mapMetricId);
  const values = [...mapSvg.querySelectorAll(".atlas-country")]
    .map(path => mapRow(path.dataset.countryCode, metric)?.[metric.id])
    .filter(Number.isFinite);
  const scale = mapScale(metric, values);
  const colors = MAP_PALETTES[mapPaletteName(metric)];
  const root = svgElement("svg", {xmlns: "http://www.w3.org/2000/svg", viewBox: "0 0 1200 760", width: 1200, height: 760, role: "img", "aria-label": `${metric.label_de}, ${periodLabel(metric)}`});
  root.appendChild(svgElement("rect", {width: 1200, height: 760, fill: "#070d18"}));
  const style = svgElement("style", {}, `
    text{font-family:Calibri,"Segoe UI",sans-serif}.export-title{fill:#edf7ff;font-size:28px;font-weight:750}
    .export-subtitle{fill:#b6c1cc;font-size:16px}.export-label{fill:#f7f5f0;font-size:17px;font-weight:700}
    .export-small{fill:#b6c1cc;font-size:14px}.map-country{vector-effect:non-scaling-stroke;stroke:#52657a;stroke-width:1}
    .background-country{fill:#182638;opacity:.84}.background-country[data-clipped=true]{stroke:transparent}
    .atlas-country{stroke:#c5d0da;stroke-width:1.1}.atlas-country.no-data{fill:#657486}.atlas-country.selected{stroke:#ffffff;stroke-width:4}
    .map-value-label{fill:#fff;stroke:#070d18;stroke-width:3px;paint-order:stroke;text-anchor:middle;dominant-baseline:middle;font-size:13px;font-weight:750}
  `);
  root.appendChild(style);
  appendExportText(root, "European Electricity Atlas", 36, 45, "export-title");
  appendExportText(root, `${metric.family}: ${metric.representation}`, 36, 76, "export-label");
  appendExportText(root, `${metric.unit || "ohne Einheit"} · ${periodLabel(metric, mapRow("DE", metric))}`, 36, 101, "export-subtitle");
  const mapClone = mapSvg.cloneNode(true);
  mapClone.setAttribute("x", "30");
  mapClone.setAttribute("y", "120");
  mapClone.setAttribute("width", "820");
  mapClone.setAttribute("height", "585");
  mapClone.removeAttribute("tabindex");
  mapClone.querySelectorAll("[tabindex]").forEach(element => element.removeAttribute("tabindex"));
  root.appendChild(mapClone);
  appendExportText(root, "Legende", 900, 165, "export-title");
  colors.forEach((color, index) => {
    root.appendChild(svgElement("rect", {x: 900 + index * 48, y: 190, width: 50, height: 18, fill: color}));
  });
  appendExportText(root, formatMetricValue(scale.min, metric), 900, 232, "export-small");
  if (scale.midpoint !== null && scale.midpoint !== undefined) appendExportText(root, formatMetricValue(scale.midpoint, metric), 1000, 232, "export-small");
  appendExportText(root, formatMetricValue(scale.max, metric), 1140, 232, "export-small");
  appendExportText(root, `${metric.unit || "ohne Einheit"} · Grau = kein Wert`, 900, 260, "export-small");
  if (focusedMapCountry) {
    appendExportText(root, "Fokus", 900, 320, "export-label");
    appendExportText(root, countryName(focusedMapCountry), 900, 350, "export-title");
    const row = mapRow(focusedMapCountry, metric);
    const value = row?.[metric.id];
    appendExportText(root, `${formatMetricValue(value, metric)} ${Number.isFinite(value) ? metric.unit : ""}`.trim(), 900, 382, "export-label");
  }
  appendExportText(root, "Lokaler Export · ohne externe Dienste", 900, 695, "export-small");
  return `<?xml version="1.0" encoding="UTF-8"?>\n${new XMLSerializer().serializeToString(root)}`;
}

async function exportMapSvg() {
  downloadBlob(new Blob([await serializedMapSvg()], {type: "image/svg+xml;charset=utf-8"}), mapFilename("svg"));
  $("map-availability").textContent = "SVG-Kartenexport mit Legende wurde erstellt.";
  pulseExportFrame($("map-stage"));
}

async function buildMapPngBlob() {
  const source = await serializedMapSvg();
  const url = URL.createObjectURL(new Blob([source], {type: "image/svg+xml;charset=utf-8"}));
  const image = new Image();
  await new Promise((resolve, reject) => {
    image.onload = resolve;
    image.onerror = reject;
    image.src = url;
  });
  const canvas = document.createElement("canvas");
  canvas.width = 2400;
  canvas.height = 1520;
  const context = canvas.getContext("2d");
  context.fillStyle = "#070d18";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.drawImage(image, 0, 0, canvas.width, canvas.height);
  URL.revokeObjectURL(url);
  return new Promise(resolve => canvas.toBlob(resolve, "image/png"));
}

async function exportMapPng() {
  downloadBlob(await buildMapPngBlob(), mapFilename("png"));
  $("map-availability").textContent = "PNG-Kartenexport mit Legende wurde erstellt.";
  pulseExportFrame($("map-stage"));
}

let activeInfoTrigger = null;

function closeInfoPanel(returnFocus = true) {
  if (!activeInfoTrigger) return;
  const panel = $(activeInfoTrigger.dataset.infoTarget);
  panel.hidden = true;
  activeInfoTrigger.setAttribute("aria-expanded", "false");
  const trigger = activeInfoTrigger;
  activeInfoTrigger = null;
  if (returnFocus) trigger.focus();
}

function configureInfoPanels() {
  document.querySelectorAll?.("[data-info-target]")?.forEach(trigger => trigger.addEventListener("click", () => {
    const wasOpen = activeInfoTrigger === trigger;
    closeInfoPanel(false);
    if (wasOpen) return;
    activeInfoTrigger = trigger;
    const panel = $(trigger.dataset.infoTarget);
    panel.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
    panel.querySelector(".info-close")?.focus();
  }));
  document.querySelectorAll?.(".info-close")?.forEach(button => button.addEventListener("click", () => closeInfoPanel(true)));
  document.addEventListener?.("click", event => {
    if (activeInfoTrigger && !activeInfoTrigger.contains(event.target) && !$(activeInfoTrigger.dataset.infoTarget).contains(event.target)) closeInfoPanel(false);
  });
}

async function loadStorage() {
  try {
    if (!metricCatalog.size) await loadMetricCatalog();
    const response = await fetch("/api/storage");
    if (!response.ok) throw new Error((await response.json()).error || response.statusText);
    const storage = await response.json();
    storageSnapshot = storage.snapshot_date;
    storageSourceLabel = storage.source_label;
    storageData = storage.countries || [];
    renderMapControls();
    renderMap();
    if (!storage.snapshot_date) return;
    const missingNote = storage.countries_missing?.length
      ? ` Ohne Speicherwert: ${storage.countries_missing.join(", ")}.`
      : "";
    const dates = storage.snapshot_dates?.length ? storage.snapshot_dates.join(", ") : storage.snapshot_date;
    $("storage-note").textContent = `Datenstände ${dates} · ${storage.countries_with_values}/${storage.countries.length} Länder · ${storageSourceLabel}.${missingNote}`;
    $("storage").hidden = false;
    renderStorage();
  } catch (error) {
    $("storage").hidden = false;
    $("storage-note").textContent = `Speicherdaten konnten nicht geladen werden: ${error.message}`;
    $("storage-note").className = "error";
  }
}

function loadCoverage() {
  $("coverage").innerHTML = "<p>Fehlende Werte bleiben leer. Jahreswerte pro Kopf kombinieren ausschließlich Ember-Stromdaten und Eurostat-Bevölkerung desselben Kalenderjahres.</p>";
}

function syncPeriodControls() {
  const showMonth = isMonthView();
  $("month-label").hidden = !showMonth;
  $("month").disabled = !showMonth;
  renderElectromobility();
  renderMapControls();
  renderMap();
}

function updateComparisonFullscreenButton() {
  const active = comparisonIsFullscreen();
  const button = $("comparison-fullscreen");
  button.textContent = active ? "Vollbild verlassen" : "Vollbild";
  button.setAttribute("aria-pressed", String(active));
}

async function toggleComparisonFullscreen() {
  const stage = $("comparison-stage");
  if (comparisonIsFullscreen()) {
    await document.exitFullscreen();
  } else if (stage.requestFullscreen) {
    await stage.requestFullscreen();
  } else {
    $("comparison-status").textContent = "Dieser Browser unterstützt die Vollbildansicht nicht.";
  }
}

$("period-type").addEventListener("change", syncPeriodControls);
$("year").max = String(currentYear);
$("load").addEventListener("click", loadSummary);
$("compare").addEventListener("click", compare);
$("clear-selection").addEventListener("click", clearSelection);
$("summary-toggle").addEventListener("click", () => {
  const collapsing = summaryExpanded;
  summaryExpanded = !summaryExpanded;
  animateTableDisclosure("summary", render, collapsing);
});
$("ev-toggle").addEventListener("click", () => {
  const collapsing = evExpanded;
  evExpanded = !evExpanded;
  animateTableDisclosure("ev", renderElectromobility, collapsing);
});
$("storage-toggle").addEventListener("click", () => {
  const collapsing = storageExpanded;
  storageExpanded = !storageExpanded;
  animateTableDisclosure("storage", renderStorage, collapsing);
});
document.querySelectorAll?.("[data-range-preset]")?.forEach(button => button.addEventListener("click", () => applyComparisonPreset(button.dataset.rangePreset)));
syncStickyHeaderOffset();
window.addEventListener?.("resize", syncStickyHeaderOffset);
if (typeof ResizeObserver === "function") {
  const controls = document.querySelector?.(".controls");
  if (controls) new ResizeObserver(syncStickyHeaderOffset).observe(controls);
}
for (const id of ["compare-start", "compare-end"]) {
  $(id).addEventListener("input", () => {
    knownMaximumComparisonRange = null;
    syncComparisonPresetFromFields();
  });
  $(id).addEventListener("change", () => loadTimeseries({scroll: false, updateUrl: true}));
}
$("compare-country-add").addEventListener("change", event => {
  if (event.target.value) toggleCountry(event.target.value, true);
  event.target.value = "";
});
$("compare-family").addEventListener("change", async event => {
  renderComparisonMetricOptions(event.target.value);
  await loadTimeseries({scroll: false, updateUrl: true});
});
$("compare-metric").addEventListener("change", async event => {
  configureComparisonRange(metricDefinition(event.target.value));
  await loadTimeseries({scroll: false, updateUrl: true});
});
$("comparison-fullscreen").addEventListener("click", toggleComparisonFullscreen);
$("unpin-time").addEventListener("click", () => {
  chartPinnedIndex = null;
  chartHoverIndex = null;
  renderTimeseriesChart();
});
$("export-csv").addEventListener("click", () => {
  downloadBlob(new Blob([buildComparisonCsv(timeseriesData)], {type: "text/csv;charset=utf-8"}), comparisonFilename("csv"));
  pulseExportFrame($("comparison-stage"));
});
$("export-svg").addEventListener("click", exportSvg);
$("export-png").addEventListener("click", exportPng);
$("copy-link").addEventListener("click", async () => {
  const url = writeComparisonUrl();
  await navigator.clipboard.writeText(url);
  $("comparison-status").textContent = "Direktlink wurde kopiert.";
});
$("map-family").addEventListener("change", async event => {
  const variants = orderedMetricVariants(mapMetrics().filter(metric => familyKey(metric) === event.target.value));
  const next = variants.find(metricAvailable)
    || variants.find(metric => isMonthView() && metric.temporal_availability.yearly)
    || variants[0];
  if (next) await selectMapMetricForPeriod(next.id);
});
$("map-representation").addEventListener("change", event => selectMapMetricForPeriod(event.target.value));
$("map-values").addEventListener("change", () => renderMapLabels(metricDefinition(mapMetricId)));
$("map-fullscreen").addEventListener("click", toggleMapFullscreen);
$("map-export-svg").addEventListener("click", exportMapSvg);
$("map-export-png").addEventListener("click", exportMapPng);
document.addEventListener?.("fullscreenchange", () => {
  updateComparisonFullscreenButton();
  updateMapFullscreenButton();
  renderTimeseriesChart();
});
document.addEventListener?.("keydown", event => {
  if (event.key === "Escape") {
    if (comparisonIsFullscreen() || mapIsFullscreen()) document.exitFullscreen();
    else if (activeInfoTrigger) closeInfoPanel(true);
  }
});

window.__atlasMapTest = {colorForValue, mapScale, NE_TO_ATLAS, serializedMapSvg, buildMapPngBlob};
window.__atlasCompareTest = {
  availableComparisonRange,
  buildComparisonCsv,
  colorDistance,
  comparisonPresetRange,
  chartIndexFromClientX,
  assignCountryColors,
  extractFlagColors,
  flagCode,
  latestCompleteComparisonIndex,
  latestCompleteComparisonPeriod,
  parseComparisonUrl,
  comparisonBaselineYear,
  comparisonBaselinePoint,
  rankingFallbackDetails,
  relativeBaselineChange,
  serializedChartSvg,
  buildChartPngBlob,
};

syncPeriodControls();
loadCoverage();
configureInfoPanels();
loadMetricCatalog()
  .then(() => Promise.all([loadMapAsset(), loadSummary(), loadStorage()]))
  .then(async () => {
    const restored = await restoreComparisonState();
    if (!restored) await initializeDefaultComparison();
  })
  .catch(error => {
    $("status").textContent = `Fehler: ${error.message}`;
    $("status").className = "error";
  });
