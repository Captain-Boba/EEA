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
const CHART_HOVER_THROTTLE_MS = 120;
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
  generation: ["#cadbf0", "#b9c9e2", "#7f9dc6", "#466f9f", "#234a76"],
  consumption: ["#c8e3e8", "#b7d5dc", "#78b2bf", "#3d8999", "#1b5e6d"],
  renewables: ["#c6e0c8", "#b8dcb8", "#7fbe83", "#459e58", "#216b37"],
  wind: ["#cfe4f7", "#c2dcf4", "#8cbde4", "#5197cd", "#276da6"],
  solar: ["#f6e9b6", "#f7e6a8", "#ebcc67", "#d7a72d", "#9e7314"],
  hydro: ["#c7e7f5", "#b7dff1", "#75c4e5", "#369fcb", "#15719b"],
  bioenergy: ["#dce7b6", "#ccd7a3", "#a2b66d", "#758f3d", "#4a6124"],
  "other-renewables": ["#c8e6d9", "#b9dfcf", "#82c6aa", "#4aa481", "#276e58"],
  fossil: ["#efd2c5", "#edc0aa", "#db8d6a", "#bb573b", "#7d2f24"],
  coal: ["#d2d3d0", "#c7c7c3", "#989891", "#686861", "#3d3d39"],
  gas: ["#f4d4b4", "#f7c89e", "#e99458", "#ca6130", "#8d351f"],
  "other-fossil": ["#e6d0c4", "#dfc1b2", "#bf927a", "#95634e", "#643f32"],
  nuclear: ["#e1d2ec", "#d5c0e4", "#ad91ca", "#805eaa", "#58377e"],
  trade: ["#2a6fbb", "#80b1d3", "#d8e3ed", "#ef8a62", "#b2182b"],
  price: ["#efd1e1", "#e8bad3", "#cf80ad", "#ad4f85", "#7c2f5d"],
  carbon: ["#ecd0c6", "#e7c1b5", "#ce8d7d", "#aa584b", "#71312d"],
  population: ["#ddd7ed", "#cfc2e2", "#aa95ca", "#7b65ae", "#4c3b7e"],
  gdp: ["#cde5d8", "#bfdcc9", "#8bc09e", "#519972", "#2c6a4d"],
  "gdp-per-capita": ["#e4d9b5", "#dccb9f", "#bea66d", "#927c40", "#65552a"],
  battery: ["#d8ddf4", "#c8cef4", "#98a3e2", "#6975c6", "#414b91"],
  "pumped-storage": ["#c6e5e2", "#b2dfdc", "#72c4bf", "#39a19d", "#1f716f"],
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
let mapData = [];
let mapDataContext = null;
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
let chartHoverThrottle = null;
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
  if (compact && Math.abs(value) >= 1_000_000) {
    return `${new Intl.NumberFormat("de-DE", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value / 1_000_000)} Mio.`;
  }
  return new Intl.NumberFormat("de-DE", {
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals,
    notation: compact && Math.abs(value) >= 10000 ? "compact" : "standard",
  }).format(value);
}

function metricDefinition(id) {
  return metricCatalog.get(id) || {
    id,
    label_de: id,
    group: "Kennzahl",
    unit: "",
    display_topic: "Kennzahl",
    display_metric: id,
    display_basis: "",
    map: false,
  };
}

function metricLabels(metric) {
  return {
    topic: metric.display_topic || metric.group || "Kennzahl",
    metric: metric.display_metric || metric.label_de || metric.id,
    basis: metric.display_basis || metric.representation || metric.unit || "",
  };
}

function compactMetricLabel(metric) {
  const labels = metricLabels(metric);
  return labels.basis ? `${labels.metric} · ${labels.basis}` : labels.metric;
}

function metricLabelHtml(metric, className = "metric-labeling") {
  const labels = metricLabels(metric);
  return `<span class="${className}">
    <span class="metric-label-topic">${escapeHtml(labels.topic)}</span>
    <span class="metric-label-metric">${escapeHtml(labels.metric)}</span>
    ${labels.basis ? `<span class="metric-label-basis">${escapeHtml(labels.basis)}</span>` : ""}
  </span>`;
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

function metricHeader(id, activeKey, direction, allowMap = true) {
  const metric = metricDefinition(id);
  const activeSort = activeKey === id;
  const ariaSort = activeSort ? ` aria-sort="${direction > 0 ? "ascending" : "descending"}"` : "";
  // Table columns need a concise, unique domain label.  The three-level
  // presentation labels belong to selectors and detail views; using only
  // their middle line here would turn several columns into just "Anteil".
  const label = tableHeaderText(metric.label_de);
  const unitLabel = tableHeaderText(metric.unit);
  const unit = unitLabel ? `<span class="unit">${escapeHtml(unitLabel)}</span>` : "";
  const mapAction = allowMap && metric.map
    ? `<button type="button" class="map-column-action${mapMetricId === id ? " active" : ""}" data-map-metric="${id}" aria-label="${escapeAttribute(label)} auf Karte anzeigen">Karte</button>`
    : "";
  const descending = `<button type="button" class="sort-indicator${activeSort && direction < 0 ? " active" : ""}" data-sort-key="${id}" data-sort-direction="-1" aria-label="${escapeAttribute(label)} absteigend sortieren" aria-pressed="${activeSort && direction < 0}">↓</button>`;
  const ascending = `<button type="button" class="sort-indicator${activeSort && direction > 0 ? " active" : ""}" data-sort-key="${id}" data-sort-direction="1" aria-label="${escapeAttribute(label)} aufsteigend sortieren" aria-pressed="${activeSort && direction > 0}">↑</button>`;
  const headerActions = `<span class="table-header-actions">${descending}${mapAction}${ascending}</span>`;
  return `<th scope="col" data-key="${id}"${ariaSort} class="${activeSort ? "sort-column-active" : ""}">
    <button type="button" class="sort-action" data-sort-key="${id}" aria-label="${escapeAttribute(label)} sortieren">
      <span class="table-header-copy"><span class="sort-label">${escapeHtml(label)}</span>${unit}</span>
    </button>
    ${headerActions}
  </th>`;
}

function fitTableHeaderText(headId) {
  const head = $(headId);
  if (!head?.querySelectorAll) return;
  const apply = () => head.querySelectorAll(".table-header-copy").forEach(copy => {
    copy.classList.remove("is-condensed");
    copy.style.removeProperty("--header-text-scale");
    const unit = copy.querySelector(".unit");
    if (!unit) return;
    unit.classList.remove("is-condensed");
    unit.style.removeProperty("--unit-text-scale");
    const availableWidth = Math.max(copy.clientWidth, 1);
    const requiredWidth = unit.scrollWidth;
    if (requiredWidth <= availableWidth) return;
    const scale = Math.max(.7, Math.min(1, availableWidth / requiredWidth));
    unit.style.setProperty("--unit-text-scale", scale.toFixed(3));
    unit.classList.add("is-condensed");
  });
  if (typeof requestAnimationFrame === "function") requestAnimationFrame(apply);
  else apply();
}

function tableHeaderText(value) {
  return String(value ?? "").replace(/\s+im\s+Ranking\b/gi, "").trim();
}

function leadingTableHeader(withSelection = false) {
  const label = withSelection
    ? "Rang, Land und Länder für den Zeitvergleich auswählen"
    : "Rang und Land";
  return `<th scope="colgroup" colspan="2" class="table-leading-spacer"><span class="sr-only">${label}</span></th>`;
}

function tableCountry(row) {
  return `<button type="button" class="table-country profile-open" data-country-profile="${row.country_code}" aria-label="Steckbrief für ${escapeAttribute(row.country_name)} öffnen">
    <img src="/assets/flags/${flagCode(row.country_code)}.svg" alt="" loading="lazy">
    <span class="table-country-copy"><span class="country-name">${escapeHtml(row.country_name)}</span><small>${escapeHtml(row.country_code)}</small></span>
  </button>`;
}

function bindProfileTriggers(scope = document) {
  scope?.querySelectorAll?.("[data-country-profile]").forEach(button => {
    if (button.dataset.profileBound) return;
    button.dataset.profileBound = "true";
    button.addEventListener("click", () => openCountryProfile(button.dataset.countryProfile));
  });
}

function updateTableDisclosure(kind, expanded, total) {
  const button = $(`${kind}-toggle`);
  const state = $(`${kind}-table-state`);
  const count = $(`${kind}-count`);
  if (!button) return;
  const card = button.closest?.(".table-card");
  card?.classList.toggle("table-card-expanded", expanded);
  button.hidden = total <= TABLE_PREVIEW_LIMIT;
  button.setAttribute("aria-expanded", String(expanded));
  button.querySelector(".table-toggle-label").textContent = expanded
    ? "Auf Top 10 reduzieren"
    : `Alle ${total} Länder anzeigen`;
  if (state) state.textContent = expanded ? "Vollständige Rangliste" : "Top 10 nach aktueller Sortierung";
  if (count) count.textContent = `${expanded ? total : Math.min(TABLE_PREVIEW_LIMIT, total)} von ${total} Ländern`;
}

function syncStickyHeaderOffset() {
  const controls = document.querySelector?.(".controls");
  if (!controls || typeof controls.getBoundingClientRect !== "function") return;
  const height = Math.ceil(controls.getBoundingClientRect().height);
  document.documentElement?.style?.setProperty("--atlas-controls-height", `${height}px`);
}

let tableDisclosureAnchorLocks = 0;

function lockTableDisclosureScrollAnchoring() {
  tableDisclosureAnchorLocks += 1;
  document.documentElement.classList.add("table-disclosure-updating");
  return () => {
    tableDisclosureAnchorLocks = Math.max(0, tableDisclosureAnchorLocks - 1);
    if (tableDisclosureAnchorLocks === 0) document.documentElement.classList.remove("table-disclosure-updating");
  };
}

function animateTableDisclosure(kind, renderTable, collapsing) {
  const region = $(`${kind}-table-region`);
  const unlockScrollAnchoring = lockTableDisclosureScrollAnchoring();
  if (!region || !motionAllowed()) {
    renderTable();
    if (collapsing) scrollTableCardHeading(kind);
    requestAnimationFrame(unlockScrollAnchoring);
    return;
  }
  const startHeight = region.getBoundingClientRect().height;
  region.style.height = `${startHeight}px`;
  region.classList.add("table-disclosure-animating");
  renderTable();
  if (collapsing) scrollTableCardHeading(kind);
  region.style.height = "auto";
  const endHeight = region.scrollHeight;
  region.style.height = `${startHeight}px`;
  if (Math.abs(startHeight - endHeight) < 1) {
    region.style.height = "";
    region.classList.remove("table-disclosure-animating");
    unlockScrollAnchoring();
    return;
  }
  requestAnimationFrame(() => {
    region.style.height = `${endHeight}px`;
  });
  let finished = false;
  const finish = () => {
    if (finished) return;
    finished = true;
    region.style.height = "";
    region.classList.remove("table-disclosure-animating");
    requestAnimationFrame(unlockScrollAnchoring);
  };
  region.addEventListener("transitionend", finish, {once: true});
  setTimeout(finish, 900);
}

function scrollTableCardHeading(kind) {
  const heading = $(`${kind}-toggle`)?.closest?.(".table-card")?.querySelector?.(".table-card-header");
  heading?.scrollIntoView?.({behavior: motionAllowed() ? "smooth" : "auto", block: "start"});
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

function bindSortDirection(selector, callback) {
  document.querySelectorAll(selector).forEach(button => button.addEventListener("click", () => {
    callback(button.dataset.sortKey, Number(button.dataset.sortDirection));
  }));
}

function bindMapColumnActions(scope) {
  scope?.querySelectorAll?.("[data-map-metric]").forEach(button => button.addEventListener("click", async () => {
    await setMapMetric(button.dataset.mapMetric, true);
  }));
}

function renderHead() {
  $("summary-head").innerHTML = leadingTableHeader(true)
    + TABLE_METRIC_IDS.map(id => metricHeader(id, sortKey, sortDirection, true)).join("");
  bindSort("#summary-head .sort-action", key => {
    if (sortKey === key) sortDirection *= -1;
    else { sortKey = key; sortDirection = -1; }
    render();
  });
  bindSortDirection("#summary-head [data-sort-direction]", (key, direction) => {
    sortKey = key;
    sortDirection = direction;
    render();
  });
  bindMapColumnActions($("summary-head"));
  fitTableHeaderText("summary-head");
}

function render() {
  const previousPositions = rowPositions("#summary-body [data-country-row]");
  renderHead();
  const sorted = sortRows(data, sortKey, sortDirection);
  const visibleRows = summaryExpanded ? sorted : sorted.slice(0, TABLE_PREVIEW_LIMIT);
  $("summary-body").innerHTML = visibleRows.map((row, index) => {
    const isSelected = selected.has(row.country_code);
    return `<tr data-country-row="${row.country_code}" style="--row-index:${index}">
    <td class="selection-cell${isSelected ? " is-selected" : ""}"><button type="button" class="table-rank selection-toggle${isSelected ? " is-selected" : ""}" aria-label="${escapeAttribute(row.country_name)} ${isSelected ? "abwählen" : "auswählen"}" aria-pressed="${isSelected}" data-country="${row.country_code}">${index + 1}</button></td>
    <th scope="row">${tableCountry(row)}</th>
    ${TABLE_METRIC_IDS.map(id => `<td data-metric="${id}" class="${sortKey === id ? "sort-column-active" : ""}">${formatTableValue(row[id], id)}</td>`).join("")}
  </tr>`;
  }).join("");
  updateTableDisclosure("summary", summaryExpanded, sorted.length);
  animateRowReorder("#summary-body [data-country-row]", previousPositions, row => row.dataset.countryRow);
  document.querySelectorAll("button.selection-toggle[data-country]").forEach(button => button.addEventListener("click", () => {
    toggleCountry(button.dataset.country);
  }));
  bindProfileTriggers($("summary-body"));
  updateSelection();
}

function renderStorage() {
  const previousPositions = rowPositions("#storage-body tr");
  $("storage-head").innerHTML = leadingTableHeader()
    + STORAGE_METRIC_IDS.map(id => metricHeader(id, storageSortKey, storageSortDirection, true)).join("");
  bindSort("#storage-head .sort-action", key => {
    if (storageSortKey === key) storageSortDirection *= -1;
    else { storageSortKey = key; storageSortDirection = -1; }
    renderStorage();
  });
  bindSortDirection("#storage-head [data-sort-direction]", (key, direction) => {
    storageSortKey = key;
    storageSortDirection = direction;
    renderStorage();
  });
  bindMapColumnActions($("storage-head"));
  fitTableHeaderText("storage-head");
  const sorted = sortRows(storageData, storageSortKey, storageSortDirection);
  const visibleRows = storageExpanded ? sorted : sorted.slice(0, TABLE_PREVIEW_LIMIT);
  $("storage-body").innerHTML = visibleRows.map((row, index) => `<tr data-storage-row="${row.country_code}" style="--row-index:${index}">
    <td class="rank-column"><span class="table-rank${selected.has(row.country_code) ? " is-selected" : ""}" data-country="${row.country_code}">${index + 1}</span></td>
    <th scope="row">${tableCountry(row)}${row.quality_status === "missing" ? '<span class="status-badge missing">fehlend</span>' : ""}</th>
    ${STORAGE_METRIC_IDS.map(id => storageCell(row, id, storageSortKey === id)).join("")}
  </tr>`).join("");
  updateTableDisclosure("storage", storageExpanded, sorted.length);
  bindProfileTriggers($("storage-body"));
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
    if (state) state.textContent = "Nur in der Jahresansicht verfügbar";
    if (count) count.textContent = "Jahresansicht erforderlich";
    $("ev-note").textContent = "Elektromobilitätswerte sind jährliche Eurostat-Daten. In der Monatsansicht werden keine Jahreswerte eingeblendet.";
    return;
  }

  region.hidden = false;
  $("ev-note").textContent = `Eurostat-Jahreswerte für ${selectedYear()}. Fehlende Land-Jahr-Werte bleiben leer und werden nicht aus Vorjahren fortgeschrieben.`;
  head.innerHTML = leadingTableHeader()
    + EV_METRIC_IDS.map(id => metricHeader(id, evSortKey, evSortDirection, true)).join("");
  bindSort("#ev-head .sort-action", key => {
    if (evSortKey === key) evSortDirection *= -1;
    else { evSortKey = key; evSortDirection = -1; }
    renderElectromobility();
  });
  bindSortDirection("#ev-head [data-sort-direction]", (key, direction) => {
    evSortKey = key;
    evSortDirection = direction;
    renderElectromobility();
  });
  bindMapColumnActions($("ev-head"));
  fitTableHeaderText("ev-head");
  const sorted = sortRows(data, evSortKey, evSortDirection);
  const visibleRows = electromobilityRowsForView(data, false, evSortKey, evSortDirection, evExpanded);
  $("ev-body").innerHTML = visibleRows.map((row, index) => `<tr data-ev-row="${row.country_code}" style="--row-index:${index}">
    <td class="rank-column"><span class="table-rank${selected.has(row.country_code) ? " is-selected" : ""}" data-country="${row.country_code}">${index + 1}</span></td>
    <th scope="row">${tableCountry(row)}</th>
    ${EV_METRIC_IDS.map(id => `<td data-metric="${id}" class="${evSortKey === id ? "sort-column-active" : ""}">${formatTableValue(row[id], id)}</td>`).join("")}
  </tr>`).join("");
  updateTableDisclosure("ev", evExpanded, sorted.length);
  bindProfileTriggers($("ev-body"));
}

function storageCell(row, metricId, isSortColumn = false) {
  const provenance = row.metric_provenance?.[metricId];
  const activeClass = isSortColumn ? "sort-column-active" : "";
  if (!provenance) {
    if (isSortColumn) return `<td class="${activeClass}">${formatTableValue(null, metricId)}</td>`;
    return `<td>${formatTableValue(null, metricId)}</td>`;
  }
  const coverageLabels = {
    national_registry_total: "nationaler Register-Gesamtbestand",
    tracked_project_inventory: "erfasster Projektbestand",
  };
  const qualityLabel = storageQualityLabel(provenance.quality_status);
  const quality = qualityLabel === "vorhanden" ? "" : ` · ${qualityLabel}`;
  const title = `${provenance.source_label} · Stichtag ${provenance.date} · ${coverageLabels[provenance.coverage_type] || provenance.coverage_type}${quality}`;
  if (isSortColumn) return `<td class="${activeClass}" title="${escapeAttribute(title)}">${formatTableValue(row[metricId], metricId)}</td>`;
  return `<td title="${escapeAttribute(title)}">${formatTableValue(row[metricId], metricId)}</td>`;
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
    $("status").textContent = "Maximal zehn Länder können gleichzeitig im Zeitvergleich ausgewählt werden.";
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
  document.querySelectorAll(".table-rank[data-country]").forEach(rank => {
    rank.classList.toggle("is-selected", selected.has(rank.dataset.country));
  });
  document.querySelectorAll("button.selection-toggle[data-country]").forEach(button => {
    const isSelected = selected.has(button.dataset.country);
    button.classList.toggle("is-selected", isSelected);
    button.closest(".selection-cell")?.classList.toggle("is-selected", isSelected);
    button.setAttribute("aria-pressed", String(isSelected));
    const country = countryName(button.dataset.country);
    button.setAttribute("aria-label", `${country} ${isSelected ? "abwählen" : "auswählen"}`);
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
  return [...metrics].sort((first, second) => {
    const firstRank = metricVariantRank(first);
    const secondRank = metricVariantRank(second);
    return firstRank - secondRank;
  });
}

function metricVariantRank(metric) {
  const storageRank = STORAGE_VARIANT_ORDER.get(metric.id);
  if (storageRank !== undefined) return storageRank;
  if (metric.id.includes("_gdp_") || metric.id === "household_wholesale_price_gap_ct_kwh") return 30;
  if (metric.id.includes("_per_capita") || metric.representation.includes("je Einwohner")) return 20;
  if (metric.unit === "%" || metric.representation.startsWith("Anteil")) return 10;
  return 0;
}

function familyKey(metric) {
  // The first selector is the user-facing category.  Keep the technical
  // family for internal grouping elsewhere, but never expose its abbreviated
  // legacy wording (for example "Erzeugung") as the category label.
  return `${metric.group}::${metricLabels(metric).topic}`;
}

function usesLatestAvailableMapYear(metric) {
  return Boolean(metric?.map_config?.latest_available_year) && !metric.temporal_availability.snapshot;
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
    const key = familyKey(metric);
    if (!families.has(key)) families.set(key, []);
    families.get(key).push(metric);
  });
  $("map-family").innerHTML = [...groups.entries()].map(([group, families]) =>
    `<optgroup label="${escapeAttribute(group)}">${[...families.entries()].map(([key, variants]) => {
      const selectable = variants.some(metric => metricAvailable(metric)
        || (isMonthView() && metric.temporal_availability.yearly));
      const disabled = selectable ? "" : " disabled";
      return `<option value="${escapeAttribute(key)}"${disabled}>${escapeHtml(metricLabels(variants[0]).topic)}</option>`;
    }).join("")}</optgroup>`
  ).join("");
  $("map-family").value = familyKey(activeMetric);

  const variants = orderedMetricVariants(metrics.filter(metric => familyKey(metric) === familyKey(activeMetric)));
  $("map-representation").innerHTML = variants.map(metric => {
    const selectable = metricAvailable(metric) || (isMonthView() && metric.temporal_availability.yearly);
    const disabled = selectable ? "" : " disabled";
    return `<option value="${metric.id}"${disabled}>${escapeHtml(compactMetricLabel(metric))}</option>`;
  }).join("");
  $("map-representation").value = mapMetricId;

  if (usesLatestAvailableMapYear(activeMetric) && mapDataContext?.metric_id === activeMetric.id) {
    $("map-availability").textContent = mapDataContext.data_year === null
      ? `Ausgewähltes Jahr ${mapDataContext.requested_year}: kein Leistungsdatenstand verfügbar.`
      : mapDataContext.data_year === mapDataContext.requested_year
        ? `Datenstand ${mapDataContext.data_year}.`
        : `Ausgewähltes Jahr ${mapDataContext.requested_year} ohne Werte · angezeigt wird Datenstand ${mapDataContext.data_year}.`;
  } else if (metricAvailable(activeMetric)) {
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
  syncEnhancedSelectMenus(["map-family", "map-representation"]);
}

async function selectMapMetricForPeriod(metricId) {
  const metric = metricCatalog.get(metricId);
  if (!metric?.map) return;
  const requiresYearView = isMonthView()
    && !metric.temporal_availability.monthly
    && metric.temporal_availability.yearly;
  if (!requiresYearView) {
    await setMapMetric(metric.id);
    return;
  }
  mapMetricId = metric.id;
  $("period-type").value = "year";
  syncPeriodControls();
  await loadSummary();
  $("map-availability").textContent = "Jahresansicht für diese Kennzahl automatisch aktiviert.";
}

async function setMapMetric(metricId, scrollToMap = false) {
  const metric = metricCatalog.get(metricId);
  if (!metric?.map) return;
  mapMetricId = metricId;
  await loadMapData(metric);
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
  if (mapUrlState()) writeMapUrl();
  if (scrollToMap) $("atlas-map-section").scrollIntoView({behavior: "smooth", block: "start"});
}

function highlightMapColumn() {
  // The table highlight represents the active sort. The map relation is shown
  // exclusively by the selected "Karte" action in each column header.
}

function mapRow(code, metric) {
  const rows = metric.temporal_availability.snapshot ? storageData : mapData;
  return rows.find(row => row.country_code === code) || null;
}

async function loadMapData(metric = metricDefinition(mapMetricId)) {
  if (!metric || metric.temporal_availability.snapshot) return;
  if (!usesLatestAvailableMapYear(metric)) {
    mapData = data;
    mapDataContext = {
      metric_id: metric.id,
      requested_year: selectedYear(),
      data_year: selectedYear(),
    };
    return;
  }
  const response = await fetch(`/api/map-data?metric=${encodeURIComponent(metric.id)}&year=${selectedYear()}`);
  if (!response.ok) throw new Error((await response.json()).error || response.statusText);
  const payload = await response.json();
  if (payload.metric_id !== metric.id || payload.requested_year !== selectedYear()) return;
  mapData = payload.rows || [];
  mapDataContext = payload;
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
  if (usesLatestAvailableMapYear(metric) && mapDataContext?.metric_id === metric.id) {
    if (mapDataContext.data_year === null) return `Ausgewähltes Jahr ${mapDataContext.requested_year} · kein Datenstand verfügbar`;
    if (mapDataContext.data_year !== mapDataContext.requested_year) return `Ausgewähltes Jahr ${mapDataContext.requested_year} · Datenstand ${mapDataContext.data_year}`;
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
  const labels = metricLabels(metric);
  const value = metricAvailable(metric) && row ? row[metric.id] : null;
  const formatted = formatMetricValue(value, metric);
  const unit = formatted === "—" ? "" : ` ${metric.unit}`;
  const provenance = metric.temporal_availability.snapshot ? row?.metric_provenance?.[metric.id] : null;
  const source = provenance?.source_label || metric.source;
  const coverage = provenance?.coverage_type ? `<span>Coverage: ${escapeHtml(provenance.coverage_type)}</span>` : "";
  return {
    html: `<strong>${escapeHtml(countryName(code))}</strong>
      ${metricLabelHtml(metric, "metric-labeling detail-metric-labeling")}
      <b>${escapeHtml(formatted + unit)}</b>
      <span>${escapeHtml(periodLabel(metric, row))}</span>
      <span>Datenstatus: ${escapeHtml(statusLabel(row, metric))}</span>
      ${coverage}
      <span>Quelle: ${escapeHtml(source)}</span>
      <button type="button" class="profile-open map-profile-open" data-country-profile="${escapeAttribute(code)}">Steckbrief öffnen</button>`,
    label: `${countryName(code)}, ${labels.topic}: ${labels.metric}, ${labels.basis}; ${formatted}${unit}, ${periodLabel(metric, row)}, Datenstatus ${statusLabel(row, metric)}, Quelle ${source}`,
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
  if (!finite.length) return null;
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

function mapLegendSummaries(metric) {
  const rows = (metric.temporal_availability.snapshot ? storageData : mapData)
    .map(row => ({...row, value: row[metric.id]}))
    .filter(row => Number.isFinite(row.value))
    .sort((first, second) => first.value - second.value || first.country_code.localeCompare(second.country_code));
  if (!rows.length) return null;
  const minimum = rows[0];
  const maximum = rows.at(-1);
  const average = rows.reduce((sum, row) => sum + row.value, 0) / rows.length;
  return {minimum, maximum, average};
}

function mapLegendCountrySummary(label, row, metric) {
  return `<div class="map-legend-summary">
    <span class="map-legend-summary-label">${escapeHtml(label)}</span>
    <img src="/assets/flags/${flagCode(row.country_code)}.svg" alt="" width="24" height="18">
    <span class="map-legend-summary-country">${escapeHtml(row.country_name || countryName(row.country_code))}</span>
    <b>${formatMetricValue(row.value, metric)}</b>
  </div>`;
}

function renderLegend(metric, scale) {
  if (!scale) {
    $("map-legend").innerHTML = "<p>Keine Werte für den ausgewählten Datenstand verfügbar.</p>";
    $("map-sign-note").hidden = true;
    return;
  }
  const colors = MAP_PALETTES[mapPaletteName(metric)];
  const gradient = `linear-gradient(90deg, ${colors.join(", ")})`;
  const midpoint = scale.midpoint;
  const summaries = mapLegendSummaries(metric);
  const summaryMarkup = summaries ? `<div class="map-legend-summaries">
    ${mapLegendCountrySummary("Minimum", summaries.minimum, metric)}
    ${mapLegendCountrySummary("Maximum", summaries.maximum, metric)}
    <div class="map-legend-summary map-legend-average">
      <span class="map-legend-summary-label">Atlas-Durchschnitt</span>
      <b>${formatMetricValue(summaries.average, metric)}</b>
    </div>
  </div>` : "";
  $("map-legend").innerHTML = `<div class="legend-ramp" style="background:${gradient}" aria-hidden="true"></div>
    <div class="legend-values"><span>${escapeHtml(formatMetricValue(scale.min, metric))}</span>${midpoint !== null && midpoint !== undefined ? `<span>${escapeHtml(formatMetricValue(midpoint, metric))}</span>` : ""}<span>${escapeHtml(formatMetricValue(scale.max, metric))}</span></div>
    <p>${escapeHtml(metric.unit || "ohne Einheit")} · Grau = kein Wert</p>${summaryMarkup}`;
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

function focusMapCountry(path, syncUrl = true) {
  focusedMapCountry = path.dataset.countryCode;
  mapSvg.querySelectorAll(".atlas-country").forEach(country => country.classList.toggle("selected", country === path));
  const detail = countryDetail(focusedMapCountry, metricDefinition(mapMetricId));
  const panel = $("map-detail");
  panel.innerHTML = detail.html;
  bindProfileTriggers(panel);
  hideMapTooltip();
  if (motionAllowed()) {
    path.classList.remove("map-focus-pulse");
    panel.classList.remove("detail-enter");
    void path.getBBox();
    path.classList.add("map-focus-pulse");
    panel.classList.add("detail-enter");
    path.addEventListener("animationend", () => path.classList.remove("map-focus-pulse"), {once: true});
  }
  if (syncUrl && mapUrlState()) writeMapUrl();
}

function clearMapCountryFocus(syncUrl = true) {
  if (!focusedMapCountry) return;
  focusedMapCountry = null;
  mapSvg?.querySelectorAll(".atlas-country.selected").forEach(country => country.classList.remove("selected"));
  $("map-detail").textContent = "Ein Land fokussieren, um Details anzuzeigen.";
  hideMapTooltip();
  if (syncUrl && mapUrlState()) writeMapUrl();
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
  mapSvg.addEventListener("click", event => {
    if (event.target.closest?.(".map-country")) return;
    clearMapCountryFocus();
  });
  updateSelection();
}

function renderMap() {
  if (!mapSvg || !metricCatalog.size) return;
  const metric = metricDefinition(mapMetricId);
  const available = metricAvailable(metric);
  const values = mapSvg.querySelectorAll(".atlas-country");
  const numericValues = available
    ? [...values].map(path => mapRow(path.dataset.countryCode, metric)?.[metric.id]).filter(Number.isFinite)
    : [];
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
  $("map-metric-title").innerHTML = metricLabelHtml(metric);
  $("map-period").textContent = periodLabel(metric, mapRow("DE", metric));
  renderLegend(metric, scale);
  renderMapLabels(metric);
  if (focusedMapCountry) {
    $("map-detail").innerHTML = countryDetail(focusedMapCountry, metric).html;
    bindProfileTriggers($("map-detail"));
  }
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
    await loadMapData();
    render();
    renderElectromobility();
    renderCountryControls();
    renderMapControls();
    renderMap();
    if (activeProfileCountry) await refreshActiveCountryProfile();
    const periodStatus = data[0]?.period_status;
    const periodNote = periodStatus === "provisional_current_month"
      ? " Laufender Monat: vorläufig."
      : (periodStatus === "ytd" ? " Laufendes Jahr: YTD." : "");
    const hasSummaryValues = data.some(row => Object.values(row).some(value => typeof value === "number"));
    $("status").textContent = hasSummaryValues ? "" : `Noch keine Daten importiert.${periodNote}`;
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
      <b>${escapeHtml(code)}</b>
      <button type="button" data-remove-country="${code}" aria-label="${escapeAttribute(name)} entfernen"><img class="europe-star" src="/assets/europe-star.svg" alt=""></button>
    </span>`;
  }).join("");
  document.querySelectorAll("[data-remove-country]").forEach(button => button.addEventListener("click", () => {
    toggleCountry(button.dataset.removeCountry, false);
  }));
  syncEnhancedSelectMenus(["compare-country-add"]);
}

function renderComparisonControls(metricId = null) {
  const allMetrics = [...metricCatalog.values()].filter(metric => metric.compare);
  if (!allMetrics.length) return;
  const activeMetric = metricCatalog.get(metricId || $("compare-metric").value)
    || metricCatalog.get(DEFAULT_COMPARISON_METRIC)
    || timeseriesMetrics()[0];
  const groups = new Map();
  allMetrics.forEach(metric => {
    if (!groups.has(metric.group)) groups.set(metric.group, new Map());
    const families = groups.get(metric.group);
    const key = familyKey(metric);
    if (!families.has(key)) families.set(key, []);
    families.get(key).push(metric);
  });
  $("compare-family").innerHTML = [...groups].map(([group, families]) =>
    `<optgroup label="${escapeAttribute(group)}">${[...families].map(([key, variants]) => {
      const available = variants.some(metric => metric.temporal_availability.monthly || metric.temporal_availability.yearly);
      return `<option value="${escapeAttribute(key)}"${available ? "" : " disabled"}>${escapeHtml(metricLabels(variants[0]).topic)}</option>`;
    }).join("")}</optgroup>`
  ).join("");
  const activeFamily = familyKey(activeMetric);
  $("compare-family").value = activeFamily;
  renderComparisonFamilyPicker(groups, activeFamily);
  renderComparisonMetricOptions(activeFamily, activeMetric.id);
  syncEnhancedSelectMenus(["compare-metric", "compare-axis-mode"]);
  renderCountryControls();
}

function renderComparisonFamilyPicker(groups, activeFamily) {
  let activeGroup = "";
  let activeLabel = "";
  const menu = $("compare-family-menu");
  const triggerValue = $("compare-family-value");
  const menuGroups = [...groups].map(([group, families]) => {
    const options = [...families].map(([key, variants]) => {
      const available = variants.some(metric => metric.temporal_availability.monthly || metric.temporal_availability.yearly);
      if (key === activeFamily) {
        activeGroup = group;
        activeLabel = metricLabels(variants[0]).topic;
      }
      return `<button type="button" class="metric-family-option${key === activeFamily ? " active" : ""}" data-comparison-family="${escapeAttribute(key)}" data-comparison-group="${escapeAttribute(group)}" aria-pressed="${key === activeFamily}"${available ? "" : " disabled"}>${escapeHtml(metricLabels(variants[0]).topic)}</button>`;
    }).join("");
    return `<section class="metric-family-group" aria-label="${escapeAttribute(group)}"><h3>${escapeHtml(group)}</h3><div class="metric-family-options">${options}</div></section>`;
  }).join("");
  triggerValue.innerHTML = `<span class="metric-family-selected-group">${escapeHtml(activeGroup)}</span><span class="metric-family-selected-label">${escapeHtml(activeLabel)}</span>`;
  menu.innerHTML = `<p class="metric-family-menu-intro">Kennzahlenfamilie wählen</p><div class="metric-family-groups">${menuGroups}</div>`;
  menu.querySelectorAll("[data-comparison-family]").forEach(button => button.addEventListener("click", () => {
    if (button.disabled) return;
    menu.querySelectorAll("[data-comparison-family]").forEach(option => {
      option.classList.toggle("active", option === button);
      option.setAttribute("aria-pressed", String(option === button));
    });
    triggerValue.innerHTML = `<span class="metric-family-selected-group">${escapeHtml(button.dataset.comparisonGroup)}</span><span class="metric-family-selected-label">${escapeHtml(button.textContent)}</span>`;
    $("compare-family").value = button.dataset.comparisonFamily;
    $("compare-family").dispatchEvent(new Event("change", {bubbles: true}));
    closeComparisonFamilyPicker(true);
  }));
}

function setComparisonFamilyPickerOpen(open) {
  const picker = $("compare-family-picker");
  const trigger = $("compare-family-trigger");
  const menu = $("compare-family-menu");
  picker.classList.toggle("is-open", open);
  trigger.setAttribute("aria-expanded", String(open));
  menu.hidden = !open;
}

function closeComparisonFamilyPicker(restoreFocus = false) {
  const menu = $("compare-family-menu");
  if (menu.hidden) return;
  setComparisonFamilyPickerOpen(false);
  if (restoreFocus) $("compare-family-trigger").focus();
}

const ENHANCED_SELECT_IDS = Object.freeze([
  "period-type", "month", "map-family", "map-representation",
  "compare-country-add", "compare-metric", "compare-axis-mode",
]);

function selectControlLabel(select) {
  return select.closest(".select-field")?.querySelector(".field-label")?.textContent.trim()
    || select.getAttribute("aria-label")
    || "Auswahl";
}

function enhancedSelectControl(select) {
  return select?.closest?.(".select-field")?.querySelector(".enhanced-select") || null;
}

function renderEnhancedSelectMenu(select) {
  const control = enhancedSelectControl(select);
  if (!control) return;
  const trigger = control.querySelector(".enhanced-select-trigger");
  const menu = control.querySelector(".enhanced-select-menu");
  const selectedOption = select.selectedOptions[0];
  trigger.querySelector(".enhanced-select-value").textContent = selectedOption?.textContent.trim() || "Auswählen …";
  trigger.disabled = select.disabled;
  const grouped = [...select.children].filter(child => child.tagName === "OPTGROUP");
  const optionButton = option => {
    const disabled = option.disabled || !option.value;
    return `<button type="button" class="enhanced-select-option${option.value === select.value ? " active" : ""}" data-select-option="${escapeAttribute(option.value)}" aria-pressed="${option.value === select.value}"${disabled ? " disabled" : ""}>${escapeHtml(option.textContent.trim())}</button>`;
  };
  menu.innerHTML = grouped.length
    ? `<div class="enhanced-select-groups">${grouped.map(group => `<section class="enhanced-select-group" aria-label="${escapeAttribute(group.label)}"><h3>${escapeHtml(group.label)}</h3><div class="enhanced-select-options">${[...group.children].map(optionButton).join("")}</div></section>`).join("")}</div>`
    : `<div class="enhanced-select-options is-list">${[...select.options].map(optionButton).join("")}</div>`;
  menu.classList.toggle("has-groups", Boolean(grouped.length));
  menu.querySelectorAll("[data-select-option]").forEach(button => button.addEventListener("click", () => {
    if (button.disabled) return;
    select.value = button.dataset.selectOption;
    select.dispatchEvent(new Event("change", {bubbles: true}));
    closeEnhancedSelectMenu(select, true);
  }));
}

function setEnhancedSelectMenuOpen(select, open) {
  const control = enhancedSelectControl(select);
  const trigger = control.querySelector(".enhanced-select-trigger");
  const menu = control.querySelector(".enhanced-select-menu");
  if (open) {
    closeComparisonFamilyPicker();
    document.querySelectorAll(".enhanced-select-menu:not([hidden])").forEach(other => {
      if (other !== menu) closeEnhancedSelectMenu(other.closest(".enhanced-select").parentElement.querySelector("select"));
    });
    renderEnhancedSelectMenu(select);
    menu.hidden = false;
  } else {
    menu.hidden = true;
  }
  control.classList.toggle("is-open", open);
  trigger.setAttribute("aria-expanded", String(open));
}

function closeEnhancedSelectMenu(select, restoreFocus = false) {
  const control = select ? enhancedSelectControl(select) : null;
  const menu = control?.querySelector(".enhanced-select-menu");
  if (!menu || menu.hidden) return;
  setEnhancedSelectMenuOpen(select, false);
  if (restoreFocus) control.querySelector(".enhanced-select-trigger").focus();
}

function syncEnhancedSelectMenus(ids = ENHANCED_SELECT_IDS) {
  ids.forEach(id => {
    const select = $(id);
    if (enhancedSelectControl(select)) renderEnhancedSelectMenu(select);
  });
}

function configureEnhancedSelectMenus() {
  if (typeof document.createElement !== "function") return;
  ENHANCED_SELECT_IDS.forEach(id => {
    const select = $(id);
    if (!select || select.closest(".enhanced-select")) return;
    const field = select.closest(".select-field");
    if (!field) return;
    const caption = selectControlLabel(select);
    const control = document.createElement("div");
    const trigger = document.createElement("button");
    const menu = document.createElement("div");
    control.className = "enhanced-select";
    trigger.type = "button";
    trigger.className = "enhanced-select-trigger";
    trigger.setAttribute("aria-label", `${caption} auswählen`);
    trigger.setAttribute("aria-haspopup", "dialog");
    trigger.setAttribute("aria-expanded", "false");
    menu.className = "enhanced-select-menu";
    menu.setAttribute("role", "dialog");
    menu.setAttribute("aria-label", `${caption} auswählen`);
    menu.hidden = true;
    trigger.innerHTML = '<span class="enhanced-select-value"></span><span class="enhanced-select-chevron" aria-hidden="true"></span>';
    control.append(trigger, menu);
    select.classList.add("sr-only");
    select.tabIndex = -1;
    select.setAttribute("aria-hidden", "true");
    select.insertAdjacentElement("afterend", control);
    trigger.addEventListener("click", () => setEnhancedSelectMenuOpen(select, menu.hidden));
    trigger.addEventListener("keydown", event => {
      if (!["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) return;
      event.preventDefault();
      setEnhancedSelectMenuOpen(select, true);
    });
    select.addEventListener("change", () => renderEnhancedSelectMenu(select));
    if (typeof MutationObserver === "function") new MutationObserver(() => renderEnhancedSelectMenu(select)).observe(select, {childList: true, subtree: true, characterData: true});
    renderEnhancedSelectMenu(select);
  });
}

function renderComparisonMetricOptions(family, metricId = null) {
  const variants = orderedMetricVariants([...metricCatalog.values()].filter(metric => metric.compare && familyKey(metric) === family));
  $("compare-metric").innerHTML = variants.map(metric => {
    const availability = metric.temporal_availability;
    const available = availability.monthly || availability.yearly;
    const suffix = available ? "" : " · kein Zeitverlauf";
    return `<option value="${metric.id}"${available ? "" : " disabled"}>${escapeHtml(compactMetricLabel(metric) + suffix)}</option>`;
  }).join("");
  const next = variants.find(metric => metric.id === metricId && (metric.temporal_availability.monthly || metric.temporal_availability.yearly))
    || variants.find(metric => metric.temporal_availability.monthly || metric.temporal_availability.yearly);
  if (!next) return;
  $("compare-metric").value = next.id;
  configureComparisonRange(next);
  configureComparisonAxisMode(next);
  syncEnhancedSelectMenus(["compare-metric", "compare-axis-mode"]);
}

function isPercentagePlotMetric(metric) {
  return metric?.unit === "%" && metric.map_config?.scale !== "diverging";
}

function isBoundedPercentagePlotMetric(metric) {
  // Shares are naturally bounded by 0–100 %.  Self-sufficiency is a ratio of
  // generation to consumption and can legitimately exceed 100 %.
  return isPercentagePlotMetric(metric) && metric?.id !== "self_sufficiency_pct";
}

function configureComparisonAxisMode(metric) {
  const input = $("compare-axis-mode");
  const options = [...input.options];
  const boundedPercentage = isBoundedPercentagePlotMetric(metric);
  const diverging = metric?.map_config?.scale === "diverging";
  options.find(option => option.value === "full").textContent = boundedPercentage
    ? "0 bis 100 %"
    : diverging
      ? "Symmetrisch um 0"
      : "0 bis Maximum";
  options.find(option => option.value === "data-range").textContent = boundedPercentage
    ? "Minimum bis Maximum"
    : "Minimum bis Maximum";
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

async function applyComparisonPreset(preset, {updateUrl = true} = {}) {
  const metric = metricDefinition($("compare-metric").value);
  const range = comparisonPresetRange(preset, metric, $("compare-end").value, null);
  if (!range) return;
  $("compare-start").value = range.start;
  $("compare-end").value = range.end;
  setActiveComparisonPreset(preset);
  await loadTimeseries({scroll: false, updateUrl, availabilityPreset: preset});
}

function comparisonQuery() {
  const params = new URLSearchParams({
    metric: $("compare-metric").value,
    countries: [...selected].join(","),
    start: $("compare-start").value,
    end: $("compare-end").value,
  });
  params.set("axis", $("compare-axis-mode").value);
  return params;
}

function mapUrlState() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("view") !== "map") return null;
  const year = Number.parseInt(params.get("year"), 10);
  const period = params.get("period") === "month" ? "month" : "year";
  const month = Number.parseInt(params.get("month"), 10);
  const country = (params.get("country") || "").toUpperCase();
  return {
    metric: params.get("map_metric") || "",
    year: Number.isInteger(year) && year >= MIN_YEAR && year <= currentYear ? year : null,
    period,
    month: Number.isInteger(month) && month >= 1 && month <= 12 ? month : null,
    values: params.get("map_values") !== "0",
    country: /^[A-Z]{2}$/.test(country) ? country : null,
  };
}

function writeMapUrl() {
  const metric = metricDefinition(mapMetricId);
  const url = new URL(window.location.href);
  url.search = "";
  url.searchParams.set("view", "map");
  url.searchParams.set("year", String(selectedYear()));
  url.searchParams.set("period", isMonthView() ? "month" : "year");
  if (isMonthView()) url.searchParams.set("month", $("month").value);
  url.searchParams.set("map_metric", metric.id);
  url.searchParams.set("map_values", $("map-values").checked ? "1" : "0");
  if (focusedMapCountry) url.searchParams.set("country", focusedMapCountry);
  history.replaceState(null, "", url);
  return url.href;
}

function syncControlsFromMapUrl() {
  const state = mapUrlState();
  if (!state) return;
  if (state.year !== null) $("year").value = String(state.year);
  $("period-type").value = state.period;
  if (state.month !== null) $("month").value = String(state.month);
}

async function restoreMapState() {
  const state = mapUrlState();
  if (!state) return false;
  const metric = metricCatalog.get(state.metric);
  if (!metric?.map) {
    $("status").textContent = "Der Karten-Direktlink enthält eine ungültige Kennzahl und wurde nicht vollständig übernommen.";
    return false;
  }
  mapMetricId = metric.id;
  $("map-values").checked = state.values;
  await loadMapData(metric);
  renderMapControls();
  renderMap();
  if (state.country && data.some(row => row.country_code === state.country)) {
    const path = mapSvg?.querySelector(`.atlas-country[data-country-code="${state.country}"]`);
    if (path) focusMapCountry(path, false);
  }
  setDocumentTitle("map");
  return true;
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
  const axisMode = ["data-range", "minimum-to-100"].includes(params.get("axis"))
    ? "data-range"
    : "full";
  return {valid: true, codes, metric, start, end, axisMode};
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
  $("compare-axis-mode").value = parsed.axisMode;
  syncComparisonPresetFromFields(parsed.metric);
  updateSelection();
  $("comparison").hidden = false;
  await loadTimeseries({scroll: false, updateUrl: false});
  setDocumentTitle("comparison");
  return true;
}

async function initializeDefaultComparison() {
  selected.clear();
  DEFAULT_COMPARISON_COUNTRIES.forEach(code => selected.add(code));
  renderComparisonControls(DEFAULT_COMPARISON_METRIC);
  updateSelection();
  $("comparison").hidden = false;
  await applyComparisonPreset("10y", {updateUrl: false});
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
  configureComparisonAxisMode(payload.metric);
  await prepareTimeseriesColors(payload);
  clearChartHoverThrottle();
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
  const right = width - 150;
  return {
    width, height, left, right,
    top: 90,
    bottom: 535,
    legendY: 600,
    legendColumns: 6,
    legendColumnWidth: (right - left) / 6,
    connectorX: right + 20,
    flagX: right + 30,
    tagX: right + 70,
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
  const useDataRange = $("compare-axis-mode")?.value === "data-range";
  const boundedPercentage = isBoundedPercentagePlotMetric(metric);
  if (boundedPercentage) {
    // The explicit data-range mode must use both observed bounds.  Keeping
    // 100 % as the upper bound here would make a narrow range needlessly
    // flat and contradict the selector label.
    minimum = useDataRange ? Math.max(0, minimum) : 0;
    maximum = useDataRange ? maximum : 100;
  } else if (diverging) {
    if (!useDataRange) {
      const extent = Math.max(Math.abs(minimum), Math.abs(maximum), 1);
      minimum = -extent;
      maximum = extent;
    }
  } else {
    if (!useDataRange) {
      minimum = Math.min(0, minimum);
      maximum = Math.max(maximum, minimum + 1);
    }
  }
  if (minimum === maximum) maximum = minimum + 1;
  // Both explicit range modes are literal: no visual headroom above the
  // reported maximum.  Bounded percentage shares already use their intended
  // fixed 0–100 % scale above; all other metrics end at their actual maximum.
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
  const labels = metricLabels(metric);
  svg.appendChild(svgElement("text", {class: "chart-title", x: geometry.left, y: 30}, labels.topic));
  const axisNote = $("compare-axis-mode")?.value === "data-range"
    ? ` · Y-Achse ${formatMetricValue(scale.minimum, metric)} bis ${formatMetricValue(scale.maximum, metric)}${metric.unit ? ` ${metric.unit}` : ""}`
    : "";
  svg.appendChild(svgElement("text", {class: "chart-subtitle", x: geometry.left, y: 51}, `${labels.metric} · ${labels.basis}`));
  svg.appendChild(svgElement("text", {class: "chart-period", x: geometry.left, y: 71}, `${payload.start} bis ${payload.end}${axisNote}`));

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

function createLeadingTrailingThrottle(callback, wait, clock = () => performance.now(), timers = window) {
  let lastInvocation = -Infinity;
  let pendingValue;
  let timer = null;
  const flush = () => {
    timer = null;
    if (pendingValue === undefined) return;
    const value = pendingValue;
    pendingValue = undefined;
    lastInvocation = clock();
    callback(value);
  };
  return {
    push(value) {
      pendingValue = value;
      const delay = Math.max(0, wait - (clock() - lastInvocation));
      if (timer === null && delay === 0) flush();
      else if (timer === null) timer = timers.setTimeout(flush, delay);
    },
    cancel() {
      if (timer !== null) timers.clearTimeout(timer);
      timer = null;
      pendingValue = undefined;
    },
  };
}

function clearChartHoverThrottle() {
  chartHoverThrottle?.cancel();
  chartHoverThrottle = null;
}

function scheduleChartHoverIndex(index) {
  if (!chartHoverThrottle) {
    chartHoverThrottle = createLeadingTrailingThrottle(nextIndex => {
      if (nextIndex === chartHoverIndex) return;
      chartHoverIndex = nextIndex;
      renderTimeseriesChart();
    }, CHART_HOVER_THROTTLE_MS);
  }
  chartHoverThrottle.push(index);
}

function bindChartInteraction(svg, scale, geometry) {
  const overlay = svg.querySelector(".chart-interaction");
  overlay.addEventListener("pointermove", event => {
    const count = timeseriesData.atlas_average.values.length;
    const index = chartIndexFromClientX(event.clientX, overlay.getBoundingClientRect(), count);
    scheduleChartHoverIndex(index);
  });
  overlay.addEventListener("pointerleave", () => {
    clearChartHoverThrottle();
    if (chartPinnedIndex === null && chartHoverIndex !== null) {
      chartHoverIndex = null;
      renderTimeseriesChart();
    }
  });
  overlay.addEventListener("click", event => {
    clearChartHoverThrottle();
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
    chartScale,
    orderedMetricVariants,
    chartIndexFromClientX,
    createLeadingTrailingThrottle,
    comparisonBaselineYear,
    latestCompleteComparisonIndex,
    latestCompleteComparisonPeriod,
    metricLabels,
    compactMetricLabel,
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

const EXPORT_THEME = Object.freeze({
  background: "#070d18",
  surface: "#0d1a2a",
  panel: "#0a1726",
  panelRaised: "#13243a",
  border: "#29445f",
  text: "#edf7ff",
  muted: "#91a9bd",
  accent: "#57d7ff",
  signal: "#ffffff",
});

function exportText(root, x, y, value, attributes = {}) {
  const text = svgElement("text", {x, y, "font-family": 'Calibri,"Segoe UI",sans-serif', ...attributes}, value);
  root.appendChild(text);
  return text;
}

function appendExportCard(root, x, y, width, height, attributes = {}) {
  root.appendChild(svgElement("rect", {
    x, y, width, height, rx: 16, class: "export-card", ...attributes,
  }));
}

function exportCreationTimestamp(now = new Date()) {
  const formatted = new Intl.DateTimeFormat("de-DE", {
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", hourCycle: "h23",
  }).format(now);
  return `Erstellt am ${formatted} Uhr`;
}

function createMidnightExportRoot(width, height, ariaLabel) {
  const root = svgElement("svg", {
    xmlns: "http://www.w3.org/2000/svg",
    viewBox: `0 0 ${width} ${height}`,
    width,
    height,
    role: "img",
    "aria-label": ariaLabel,
  });
  const defs = svgElement("defs");
  const glow = svgElement("radialGradient", {id: "eea-export-glow", cx: "22%", cy: "-10%", r: "72%"});
  glow.appendChild(svgElement("stop", {offset: "0%", "stop-color": "#183654", "stop-opacity": ".92"}));
  glow.appendChild(svgElement("stop", {offset: "55%", "stop-color": EXPORT_THEME.background, "stop-opacity": ".88"}));
  glow.appendChild(svgElement("stop", {offset: "100%", "stop-color": EXPORT_THEME.background}));
  const grid = svgElement("pattern", {id: "eea-export-grid", width: 48, height: 48, patternUnits: "userSpaceOnUse"});
  grid.appendChild(svgElement("path", {d: "M 48 0 L 0 0 0 48", fill: "none", stroke: "#5a97c7", "stroke-opacity": ".12", "stroke-width": 1}));
  defs.append(glow, grid);
  root.appendChild(defs);
  root.appendChild(svgElement("rect", {width, height, fill: "url(#eea-export-glow)"}));
  root.appendChild(svgElement("rect", {width, height, fill: "url(#eea-export-grid)"}));
  root.appendChild(svgElement("style", {}, `
    text{font-family:Calibri,"Segoe UI",sans-serif}.export-card{fill:${EXPORT_THEME.surface};stroke:${EXPORT_THEME.border};stroke-width:1.25}
    .export-brand{fill:${EXPORT_THEME.text};font-size:28px;font-weight:750}.export-title{fill:${EXPORT_THEME.text};font-size:23px;font-weight:750}
    .export-label{fill:${EXPORT_THEME.text};font-size:15px;font-weight:700}.export-subtitle,.export-small{fill:${EXPORT_THEME.muted};font-size:13px}
    .export-rule{stroke:#b89a5a;stroke-opacity:.55}.export-ranking-row{fill:${EXPORT_THEME.panelRaised};stroke:${EXPORT_THEME.border};stroke-width:1}
    .export-ranking-average{fill:${EXPORT_THEME.panel};stroke:#52657c;stroke-width:1;stroke-dasharray:3 3}
  `));
  return root;
}

function appendExportBranding(root, metric, period, width, {includeMetricHeading = true} = {}) {
  const labels = metricLabels(metric);
  root.appendChild(svgElement("image", {href: "/assets/eea-mark.svg", x: 34, y: 28, width: 58, height: 58}));
  exportText(root, 108, 68, "European Electricity Atlas", {class: "export-brand"});
  if (includeMetricHeading) {
    exportText(root, 108, 94, labels.topic, {class: "export-label"});
    exportText(root, 108, 115, `${labels.metric} · ${labels.basis || "ohne Einheit"} · ${period}`, {class: "export-subtitle"});
  }
  exportText(root, width - 34, 54, exportCreationTimestamp(), {class: "export-small", "font-weight": 700, "text-anchor": "end"});
  const ruleY = includeMetricHeading ? 132 : 118;
  root.appendChild(svgElement("line", {class: "export-rule", x1: 34, x2: width - 34, y1: ruleY, y2: ruleY}));
}

function exportSvgDimensions(source) {
  const root = new DOMParser().parseFromString(source, "image/svg+xml").documentElement;
  const values = root.getAttribute("viewBox")?.trim().split(/\s+/).map(Number) || [];
  if (values.length !== 4 || !values.every(Number.isFinite)) throw new Error("Export-SVG hat keine gültige ViewBox.");
  return {width: values[2], height: values[3]};
}

async function rasterizeExportSvg(source, scale = 2) {
  const {width, height} = exportSvgDimensions(source);
  const url = URL.createObjectURL(new Blob([source], {type: "image/svg+xml;charset=utf-8"}));
  try {
    const image = new Image();
    await new Promise((resolve, reject) => {
      image.onload = resolve;
      image.onerror = reject;
      image.src = url;
    });
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(width * scale);
    canvas.height = Math.round(height * scale);
    const context = canvas.getContext("2d");
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    return new Promise(resolve => canvas.toBlob(resolve, "image/png"));
  } finally {
    URL.revokeObjectURL(url);
  }
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
    .chart-background{fill:transparent}.chart-title{fill:${EXPORT_THEME.text};font:750 24px Calibri,"Segoe UI",sans-serif}
    .chart-subtitle,.chart-period,.axis-label,.legend-label,.average-endpoint-tag{fill:${EXPORT_THEME.muted};font:13px Calibri,"Segoe UI",sans-serif}
    .chart-grid{stroke:#34495f;stroke-width:1}.chart-grid.vertical{stroke-opacity:.45}
    .chart-zero{stroke:#b89a5a;stroke-width:1.5}.chart-line{fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
    .atlas-average-line{stroke:${EXPORT_THEME.text};stroke-width:1.7;stroke-dasharray:10 7;opacity:.85}
    .chart-guide{stroke:#dbe8f6;stroke-width:1.2;stroke-dasharray:4 5}.chart-point{stroke:#08101c;stroke-width:2}
    .endpoint-connector{fill:none;stroke-width:1;opacity:.8}.average-endpoint-connector{stroke-dasharray:6 5}.endpoint-tag{font:800 14px Calibri,"Segoe UI",sans-serif}
    .average-endpoint-tag{font-weight:750;fill:${EXPORT_THEME.text}}.legend-line{stroke-width:3}.legend-line.average{stroke-dasharray:7 5}
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
  return serializedComparisonExportSvg();
}

async function serializedComparisonExportSvg() {
  const chartSource = await serializedChartSvg();
  const chart = new DOMParser().parseFromString(chartSource, "image/svg+xml").documentElement;
  const [, , chartWidth, chartHeight] = chart.getAttribute("viewBox").split(/\s+/).map(Number);
  const panelWidth = 390;
  const padding = 30;
  const headerHeight = 132;
  const gap = 20;
  const chartCardWidth = chartWidth + 20;
  const rankingEntries = liveRankingExportEntries();
  const panelHeight = Math.max(chartHeight + 20, 182 + rankingEntries.length * 52);
  const rootWidth = padding * 2 + chartCardWidth + gap + panelWidth;
  const rootHeight = headerHeight + panelHeight + padding;
  const panelX = padding + chartCardWidth + gap;
  const contentY = headerHeight;
  const root = createMidnightExportRoot(rootWidth, rootHeight, `Zeitvergleich: ${compactMetricLabel(timeseriesData.metric)}, ${timeseriesData.start} bis ${timeseriesData.end}`);
  appendExportBranding(root, timeseriesData.metric, `${timeseriesData.start} bis ${timeseriesData.end}`, rootWidth, {includeMetricHeading: false});
  appendExportCard(root, padding, contentY, chartCardWidth, panelHeight);
  appendExportCard(root, panelX, contentY, panelWidth, panelHeight);
  const chartCopy = document.importNode(chart, true);
  chartCopy.setAttribute("x", String(padding + 10));
  chartCopy.setAttribute("y", String(contentY + 10));
  chartCopy.setAttribute("width", chartWidth);
  chartCopy.setAttribute("height", chartHeight);
  chartCopy.setAttribute("preserveAspectRatio", "xMidYMid meet");
  root.appendChild(chartCopy);
  exportText(root, panelX + 22, contentY + 35, "Live-Ranking", {class: "export-title"});
  exportText(root, panelX + panelWidth - 22, contentY + 35, $("ranking-period").textContent.trim(), {class: "export-small", "font-weight": 700, "text-anchor": "end"});
  root.appendChild(svgElement("rect", {class: "export-ranking-average", x: panelX + 18, y: contentY + 52, width: panelWidth - 36, height: 42, rx: 8}));
  exportText(root, panelX + 30, contentY + 78, $("atlas-average-value").textContent.trim(), {fill: EXPORT_THEME.text, "font-size": 14, "font-weight": 750});
  exportText(root, panelX + 22, contentY + 117, $("ranking-baseline-note").textContent.trim(), {class: "export-small", "font-size": 12});
  rankingEntries.forEach((entry, index) => {
    const y = contentY + 130 + index * 52;
    root.appendChild(svgElement("rect", {class: "export-ranking-row", x: panelX + 18, y, width: panelWidth - 36, height: 45, rx: 8}));
    exportText(root, panelX + 35, y + 28, entry.rank, {fill: EXPORT_THEME.muted, "font-size": 14, "font-weight": 750, "text-anchor": "middle"});
    root.appendChild(svgElement("image", {href: `/assets/flags/${flagCode(entry.code)}.svg`, x: panelX + 52, y: y + 12, width: 22, height: 16}));
    exportText(root, panelX + 84, y + 20, entry.code, {fill: EXPORT_THEME.text, "font-size": 14, "font-weight": 800});
    exportText(root, panelX + 84, y + 34, entry.name, {fill: EXPORT_THEME.muted, "font-size": 9});
    const valueX = panelX + panelWidth - 100;
    exportText(root, valueX, y + 20, entry.value, {fill: EXPORT_THEME.text, "font-size": 14, "font-weight": 800, "text-anchor": "middle"});
    exportText(root, valueX, y + 34, entry.unit, {fill: EXPORT_THEME.muted, "font-size": 9, "text-anchor": "middle"});
    exportText(root, panelX + panelWidth - 28, y + 28, entry.change, {fill: "#8ba2bd", "font-size": 11, "font-weight": 700, "text-anchor": "end"});
  });
  await inlineSvgImages(root);
  return `<?xml version="1.0" encoding="UTF-8"?>\n${new XMLSerializer().serializeToString(root)}`;
}

async function exportSvg() {
  downloadBlob(new Blob([await serializedComparisonExportSvg()], {type: "image/svg+xml;charset=utf-8"}), comparisonFilename("svg"));
  pulseExportFrame($("comparison-stage"));
}

async function exportPng() {
  const blob = await buildChartPngBlob();
  downloadBlob(blob, comparisonFilename("png"));
  pulseExportFrame($("comparison-stage"));
}

async function buildChartPngBlob() {
  return rasterizeExportSvg(await serializedComparisonExportSvg());
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
    setDocumentTitle("map");
    await stage.requestFullscreen();
  } else {
    $("map-availability").textContent = "Dieser Browser unterstützt die Vollbildansicht nicht.";
  }
}

const PROFILE_SECTION_ORDER = Object.freeze([
  "Stromsystem", "Erneuerbare", "Fossile", "Kernenergie", "Installierte Leistung",
  "Handel", "Preise", "Endkundenpreise", "Klima", "Sozioökonomie", "Elektromobilität",
  "Kapazitäten und Speicher", "Wasserkraftinventar",
]);
const PROFILE_SECTION_LABELS = Object.freeze({
  Handel: "Stromhandel und Preise", Preise: "Stromhandel und Preise", Endkundenpreise: "Stromhandel und Preise",
  "Kapazitäten und Speicher": "Speicher", Wasserkraftinventar: "JRC-Wasserkraftinventar",
});
const PROFILE_SECTION_MERGES = Object.freeze({
  Handel: "Stromhandel und Preise", Preise: "Stromhandel und Preise", Endkundenpreise: "Stromhandel und Preise",
});
let activeProfileCountry = null;

function profileUrlState() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("view") !== "country") return null;
  const code = (params.get("country") || "").toUpperCase();
  return /^[A-Z]{2}$/.test(code) ? code : null;
}

function syncControlsFromProfileUrl() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("view") !== "country") return;
  const year = Number.parseInt(params.get("year"), 10);
  if (Number.isFinite(year)) $("year").value = String(year);
  const month = Number.parseInt(params.get("month"), 10);
  const monthly = params.get("period") === "month" || Number.isFinite(month);
  $("period-type").value = monthly ? "month" : "year";
  if (Number.isFinite(month) && month >= 1 && month <= 12) $("month").value = String(month);
}

function profileUrl(code) {
  const params = new URLSearchParams(window.location.search);
  params.set("view", "country");
  params.set("country", code);
  params.set("year", String(selectedYear()));
  params.set("period", isMonthView() ? "month" : "year");
  if (isMonthView()) params.set("month", $("month").value);
  else params.delete("month");
  return `${window.location.pathname}?${params.toString()}`;
}

function profileMetricSort(first, second) {
  const firstRank = STORAGE_VARIANT_ORDER.get(first.id) ?? metricVariantRank(first);
  const secondRank = STORAGE_VARIANT_ORDER.get(second.id) ?? metricVariantRank(second);
  return first.family.localeCompare(second.family, "de") || firstRank - secondRank || first.label.localeCompare(second.label, "de");
}

function profileSourceYear(metric) {
  const period = String(metric.actual_period || selectedYear());
  return period.match(/\b\d{4}\b/)?.[0] || "";
}

function profileMetricCard(metric) {
  const catalogMetric = metricDefinition(metric.id);
  const displayed = formatMetricValue(metric.value, catalogMetric);
  const unit = displayed === "—" ? "" : ` ${metric.unit}`;
  const labels = metricLabels(metric);
  const source = [metric.source, profileSourceYear(metric)].filter(Boolean).join(" · ");
  return `<article class="profile-metric${metric.value === null ? " is-missing" : ""}">
    <p class="profile-topic">${escapeHtml(labels.topic)}</p>
    <h4>${escapeHtml(labels.metric)}</h4>
    <p class="profile-representation">${escapeHtml(labels.basis)}</p>
    <p class="profile-value">${escapeHtml(displayed)}<small>${escapeHtml(unit)}</small></p>
    <p class="profile-source">${escapeHtml(source)}</p>
  </article>`;
}

function profileSectionHtml(section) {
  const families = new Map();
  [...section.metrics].sort(profileMetricSort).forEach(metric => {
    const key = section.id === "Kapazitäten und Speicher" ? metric.family : "";
    if (!families.has(key)) families.set(key, []);
    families.get(key).push(metric);
  });
  const heading = PROFILE_SECTION_LABELS[section.id] || section.label;
  return `<section class="profile-section" aria-labelledby="profile-section-${escapeAttribute(section.id)}">
    <h3 id="profile-section-${escapeAttribute(section.id)}">${escapeHtml(heading)}</h3>
    ${[...families].map(([family, metrics]) => `${family ? `<h4 class="profile-subsection-title">${escapeHtml(family)}</h4>` : ""}<div class="profile-grid">${metrics.map(profileMetricCard).join("")}</div>`).join("")}
  </section>`;
}

function renderCountryProfile(profile) {
  const country = profile.country;
  const highlightIds = ["generation_twh", "consumption_twh", "renewable_share_pct", "carbon_intensity_gco2eq_kwh", "price_avg_eur_mwh"];
  const metrics = new Map(profile.sections.flatMap(section => section.metrics.map(metric => [metric.id, metric])));
  const highlights = highlightIds.map(id => metrics.get(id)).filter(Boolean);
  const mergedSections = new Map();
  profile.sections.forEach(section => {
    const id = PROFILE_SECTION_MERGES[section.id] || section.id;
    const existing = mergedSections.get(id);
    if (existing) existing.metrics.push(...section.metrics);
    else mergedSections.set(id, {id, label: PROFILE_SECTION_LABELS[id] || section.label, metrics: [...section.metrics]});
  });
  const sections = [...mergedSections.values()].sort((first, second) => PROFILE_SECTION_ORDER.indexOf(first.id) - PROFILE_SECTION_ORDER.indexOf(second.id));
  $("country-profile").innerHTML = `<header class="country-profile-header">
    <div class="country-profile-title"><img src="/assets/flags/${flagCode(country.code)}.svg" alt="" width="44" height="33"><div><h2 id="country-profile-title">${escapeHtml(country.name)} <small>${escapeHtml(country.code)}</small></h2></div></div>
    <div class="profile-actions tool-actions"><button id="profile-back" type="button">Zurück zum Atlas</button><button id="profile-compare" type="button">Im Zeitvergleich öffnen</button></div>
  </header>
  <section class="profile-highlights" aria-label="Hauptkennzahlen">${highlights.map(profileMetricCard).join("")}</section>
  <p class="profile-time-note">Monats-, Jahres- und Snapshotwerte sind anhand von Zeitbasis und tatsächlichem Datenstand getrennt ausgewiesen. Fehlende Werte bleiben leer.</p>
  <div class="profile-sections">${sections.map(profileSectionHtml).join("")}</div>`;
  $("profile-back").addEventListener("click", () => leaveCountryProfile(true));
  $("profile-compare").addEventListener("click", openProfileInComparison);
  setDocumentTitle("country");
}

async function loadCountryProfile({scroll = true} = {}) {
  const code = profileUrlState();
  if (!code) return;
  activeProfileCountry = code;
  $("atlas-content").hidden = true;
  $("country-profile").hidden = false;
  $("country-profile").innerHTML = `<p class="hint" role="status">Steckbrief wird geladen …</p>`;
  if (scroll) $("country-profile").scrollIntoView({behavior: motionAllowed() ? "smooth" : "auto", block: "start"});
  setDocumentTitle("country");
  try {
    const response = await fetch(`/api/country-profile?country=${encodeURIComponent(code)}&${periodQuery()}`);
    if (!response.ok) throw new Error((await response.json()).error || response.statusText);
    renderCountryProfile(await response.json());
  } catch (error) {
    $("country-profile").innerHTML = `<p class="error">Steckbrief konnte nicht geladen werden: ${escapeHtml(error.message)}</p><button id="profile-back" type="button">Zurück zum Atlas</button>`;
    $("profile-back").addEventListener("click", () => leaveCountryProfile(true));
  }
}

async function refreshActiveCountryProfile() {
  if (!activeProfileCountry) return;
  const params = new URLSearchParams(window.location.search);
  params.set("view", "country");
  params.set("country", activeProfileCountry);
  params.set("year", String(selectedYear()));
  params.set("period", isMonthView() ? "month" : "year");
  if (isMonthView()) params.set("month", $("month").value);
  else params.delete("month");
  window.history.replaceState({}, "", `${window.location.pathname}?${params.toString()}`);
  await loadCountryProfile({scroll: false});
}

function leaveCountryProfile(pushHistory = false) {
  if (pushHistory) {
    const params = new URLSearchParams(window.location.search);
    params.delete("view"); params.delete("country"); params.delete("period");
    window.history.pushState({}, "", `${window.location.pathname}${params.toString() ? `?${params}` : ""}`);
  }
  activeProfileCountry = null;
  $("country-profile").hidden = true;
  $("atlas-content").hidden = false;
  updateDynamicDocumentTitle();
}

function openCountryProfile(code) {
  if (!code) return;
  window.history.pushState({}, "", profileUrl(code));
  void loadCountryProfile();
}

async function openProfileInComparison() {
  const code = activeProfileCountry;
  if (!code) return;
  if (!selected.has(code) && selected.size >= 10) {
    $("country-profile").querySelector(".profile-time-note").textContent = "Maximal zehn Länder können gleichzeitig im Zeitvergleich ausgewählt werden.";
    return;
  }
  selected.add(code);
  updateSelection();
  leaveCountryProfile(false);
  const params = new URLSearchParams(window.location.search);
  params.set("view", "compare"); params.delete("country"); params.delete("period");
  window.history.pushState({}, "", `${window.location.pathname}?${params.toString()}`);
  await loadTimeseries({scroll: false, updateUrl: true});
  $("comparison").scrollIntoView({behavior: motionAllowed() ? "smooth" : "auto", block: "start"});
  setDocumentTitle("comparison");
}

function configureCountryProfileNavigation() {
  syncControlsFromMapUrl();
  syncControlsFromProfileUrl();
  window.addEventListener("popstate", () => {
    if (profileUrlState()) void loadCountryProfile();
    else {
      leaveCountryProfile(false);
      if (mapUrlState()) void restoreMapState();
    }
  });
}

const TITLE_BY_SECTION = Object.freeze({
  map: "EEA · Karte",
  comparison: "EEA · Zeitvergleich",
  summary: "EEA · Stromsysteme",
  electromobility: "EEA · E-Mobilität",
  storage: "EEA · Speicher",
  sources: "EEA · Quellen",
  country: "EEA",
});
let activeTitleSection = null;
let titleUpdateFrame = null;

function setDocumentTitle(section = null) {
  activeTitleSection = section;
  document.title = section === "country" && activeProfileCountry
    ? `EEA · ${countryName(activeProfileCountry)}`
    : (TITLE_BY_SECTION[section] || "European Electricity Atlas");
}

function visibleTitleSection() {
  if (mapIsFullscreen()) return "map";
  if (comparisonIsFullscreen()) return "comparison";
  const referenceY = Math.min(180, Math.max(96, window.innerHeight * .18));
  const sections = [
    ["map", $("atlas-map-section")], ["comparison", $("comparison")], ["summary", $("summary-section")],
    ["electromobility", $("electromobility")], ["storage", $("storage")], ["sources", document.querySelector?.(".source-details")],
  ].filter(([, section]) => section && !section.hidden);
  const containing = sections.find(([, section]) => {
    const rect = section.getBoundingClientRect();
    return rect.top <= referenceY && rect.bottom > referenceY;
  });
  if (containing) return containing[0];
  const passed = sections.filter(([, section]) => section.getBoundingClientRect().top <= referenceY);
  return passed.at(-1)?.[0] || null;
}

function updateDynamicDocumentTitle() {
  const section = visibleTitleSection();
  if (section !== activeTitleSection) setDocumentTitle(section);
}

function scheduleDynamicDocumentTitle() {
  if (titleUpdateFrame !== null) return;
  titleUpdateFrame = requestAnimationFrame(() => {
    titleUpdateFrame = null;
    updateDynamicDocumentTitle();
  });
}

function configureDynamicDocumentTitle() {
  const targets = [
    $("atlas-map-section"), $("comparison"), $("summary-section"), $("electromobility"), $("storage"),
    document.querySelector?.(".source-details"),
  ].filter(Boolean);
  if (typeof IntersectionObserver === "function") {
    const observer = new IntersectionObserver(() => scheduleDynamicDocumentTitle(), {
      rootMargin: "-18% 0px -55% 0px",
      threshold: [0, .1, .5],
    });
    targets.forEach(target => observer.observe(target));
  }
  window.addEventListener("scroll", scheduleDynamicDocumentTitle, {passive: true});
  window.addEventListener("resize", scheduleDynamicDocumentTitle);
  if (profileUrlState()) setDocumentTitle("country");
  else if (mapUrlState()) setDocumentTitle("map");
  else if (new URLSearchParams(window.location.search).get("view") === "compare") setDocumentTitle("comparison");
  else updateDynamicDocumentTitle();
}

function updateEuropeOverloadButton() {
  const button = $("europe-overload");
  if (!button) return;
  const enabled = Boolean(window.__atlasWallpaper?.isEnabled?.());
  button.setAttribute("aria-pressed", String(enabled));
  button.classList.toggle("active", enabled);
}

function configureEuropeOverload() {
  const button = $("europe-overload");
  button?.addEventListener("click", () => {
    window.__atlasWallpaper?.setEnabled?.(!window.__atlasWallpaper.isEnabled());
    updateEuropeOverloadButton();
  });
  document.addEventListener?.("atlas-overload-change", updateEuropeOverloadButton);
  updateEuropeOverloadButton();
}

function mapFilename(extension) {
  return `eea-map-${mapMetricId}-${periodLabel(metricDefinition(mapMetricId)).replace(/[^0-9a-z-]+/gi, "-").toLowerCase()}.${extension}`;
}

function appendMapExportSummary(root, x, y, width, label, value, metric, country = null) {
  root.appendChild(svgElement("rect", {class: "export-ranking-row", x, y, width, height: 44, rx: 8}));
  exportText(root, x + 14, y + 16, label, {class: "export-small", "font-size": 10, "font-weight": 700});
  if (country) {
    root.appendChild(svgElement("image", {href: `/assets/flags/${flagCode(country.country_code)}.svg`, x: x + 14, y: y + 22, width: 22, height: 16}));
    exportText(root, x + 45, y + 35, country.country_name || countryName(country.country_code), {class: "export-small", "font-size": 10});
  }
  exportText(root, x + width - 14, y + 35, formatMetricValue(value, metric), {fill: EXPORT_THEME.text, "font-size": 13, "font-weight": 800, "text-anchor": "end"});
}

async function serializedMapSvg() {
  if (!mapSvg) throw new Error("Karte ist noch nicht geladen.");
  const metric = metricDefinition(mapMetricId);
  const values = [...mapSvg.querySelectorAll(".atlas-country")]
    .map(path => mapRow(path.dataset.countryCode, metric)?.[metric.id])
    .filter(Number.isFinite);
  const scale = mapScale(metric, values);
  const colors = MAP_PALETTES[mapPaletteName(metric)];
  const width = 1600;
  const height = 1000;
  const contentY = 140;
  const mapCardX = 30;
  const mapCardWidth = 1110;
  const panelX = 1170;
  const panelWidth = 400;
  const panelHeight = 830;
  const root = createMidnightExportRoot(width, height, `Europakarte: ${compactMetricLabel(metric)}, ${periodLabel(metric)}`);
  root.appendChild(svgElement("style", {}, `
    .map-country{vector-effect:non-scaling-stroke;stroke:#52657a;stroke-width:1}.background-country{fill:#182638;opacity:.84}
    .background-country[data-clipped=true]{stroke:transparent}.atlas-country{stroke:#94b0c9;stroke-width:1.35}
    .atlas-country.no-data{fill:#657486}.atlas-country.selected{stroke:${EXPORT_THEME.signal};stroke-width:4}
    .map-value-label{fill:#fff;stroke:#070d18;stroke-width:3px;paint-order:stroke;text-anchor:middle;dominant-baseline:middle;font-size:13px;font-weight:750}
  `));
  appendExportBranding(root, metric, periodLabel(metric, mapRow("DE", metric)), width);
  appendExportCard(root, mapCardX, contentY, mapCardWidth, panelHeight);
  appendExportCard(root, panelX, contentY, panelWidth, panelHeight);
  const mapClone = mapSvg.cloneNode(true);
  mapClone.setAttribute("x", "46");
  mapClone.setAttribute("y", "158");
  mapClone.setAttribute("width", "1078");
  mapClone.setAttribute("height", "794");
  mapClone.setAttribute("preserveAspectRatio", "xMidYMid meet");
  mapClone.removeAttribute("tabindex");
  mapClone.querySelectorAll("[tabindex]").forEach(element => element.removeAttribute("tabindex"));
  root.appendChild(mapClone);
  exportText(root, panelX + 28, contentY + 42, "Legende", {class: "export-title"});
  exportText(root, panelX + 28, contentY + 67, compactMetricLabel(metric), {class: "export-small"});
  let detailY = contentY + 210;
  if (scale) {
    const legendX = panelX + 30;
    const legendY = contentY + 95;
    const legendWidth = panelWidth - 60;
    colors.forEach((color, index) => {
      root.appendChild(svgElement("rect", {x: legendX + index * legendWidth / colors.length, y: legendY, width: legendWidth / colors.length + 1, height: 18, fill: color}));
    });
    exportText(root, legendX, legendY + 42, formatMetricValue(scale.min, metric), {class: "export-small"});
    if (scale.midpoint !== null && scale.midpoint !== undefined) exportText(root, legendX + legendWidth / 2, legendY + 42, formatMetricValue(scale.midpoint, metric), {class: "export-small", "text-anchor": "middle"});
    exportText(root, legendX + legendWidth, legendY + 42, formatMetricValue(scale.max, metric), {class: "export-small", "text-anchor": "end"});
    exportText(root, legendX, legendY + 68, `${metric.unit || "ohne Einheit"} · Grau = kein Wert`, {class: "export-small"});
    const summaries = mapLegendSummaries(metric);
    if (summaries) {
      const summaryX = panelX + 28;
      const summaryWidth = panelWidth - 56;
      const summaryY = legendY + 92;
      appendMapExportSummary(root, summaryX, summaryY, summaryWidth, "Minimum", summaries.minimum.value, metric, summaries.minimum);
      appendMapExportSummary(root, summaryX, summaryY + 52, summaryWidth, "Maximum", summaries.maximum.value, metric, summaries.maximum);
      appendMapExportSummary(root, summaryX, summaryY + 104, summaryWidth, "Atlas-Durchschnitt", summaries.average, metric);
      detailY = summaryY + 164;
    }
  } else {
    exportText(root, panelX + 28, contentY + 118, "Keine Werte für den ausgewählten Datenstand verfügbar.", {class: "export-small"});
  }
  if (focusedMapCountry) {
    const focusY = detailY;
    root.appendChild(svgElement("rect", {class: "export-ranking-average", x: panelX + 24, y: focusY, width: panelWidth - 48, height: 124, rx: 12}));
    exportText(root, panelX + 42, focusY + 30, "Länderfokus", {class: "export-label"});
    exportText(root, panelX + 42, focusY + 61, countryName(focusedMapCountry), {class: "export-title", "font-size": 20});
    const row = mapRow(focusedMapCountry, metric);
    const value = row?.[metric.id];
    exportText(root, panelX + 42, focusY + 94, `${formatMetricValue(value, metric)} ${Number.isFinite(value) ? metric.unit : ""}`.trim(), {class: "export-label"});
  }
  exportText(root, panelX + 28, contentY + panelHeight - 28, "Lokaler, eigenständiger Export", {class: "export-small"});
  await inlineSvgImages(root);
  return `<?xml version="1.0" encoding="UTF-8"?>\n${new XMLSerializer().serializeToString(root)}`;
}

async function exportMapSvg() {
  downloadBlob(new Blob([await serializedMapSvg()], {type: "image/svg+xml;charset=utf-8"}), mapFilename("svg"));
  $("map-availability").textContent = "SVG-Kartenexport mit Legende wurde erstellt.";
  pulseExportFrame($("map-stage"));
}

async function buildMapPngBlob() {
  return rasterizeExportSvg(await serializedMapSvg());
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
  syncEnhancedSelectMenus(["period-type", "month"]);
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
    setDocumentTitle("comparison");
    await stage.requestFullscreen();
  } else {
    $("comparison-status").textContent = "Dieser Browser unterstützt die Vollbildansicht nicht.";
  }
}

$("period-type").addEventListener("change", syncPeriodControls);
$("year").max = String(currentYear);
$("load").addEventListener("click", async () => {
  await loadSummary();
  if (mapUrlState()) writeMapUrl();
});
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
$("compare-family-trigger").addEventListener("click", () => {
  const menu = $("compare-family-menu");
  document.querySelectorAll?.(".select-field select").forEach(select => closeEnhancedSelectMenu(select));
  setComparisonFamilyPickerOpen(menu.hidden);
});
$("compare-family-trigger").addEventListener("keydown", event => {
  if (!["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) return;
  event.preventDefault();
  setComparisonFamilyPickerOpen(true);
});
document.addEventListener?.("click", event => {
  const picker = $("compare-family-picker");
  const menu = $("compare-family-menu");
  if (picker?.contains?.(event.target) || menu?.contains?.(event.target) || event.target.closest?.(".enhanced-select")) return;
  closeComparisonFamilyPicker();
  document.querySelectorAll?.(".select-field select").forEach(select => closeEnhancedSelectMenu(select));
});
document.addEventListener?.("keydown", event => {
  if (event.key === "Escape") closeComparisonFamilyPicker(true);
});
$("compare-metric").addEventListener("change", async event => {
  configureComparisonRange(metricDefinition(event.target.value));
  await loadTimeseries({scroll: false, updateUrl: true});
});
$("compare-axis-mode").addEventListener("change", () => {
  renderTimeseriesChart();
  writeComparisonUrl();
});
$("comparison-fullscreen").addEventListener("click", toggleComparisonFullscreen);
$("unpin-time").addEventListener("click", () => {
  clearChartHoverThrottle();
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
$("map-representation").addEventListener("change", async event => {
  await selectMapMetricForPeriod(event.target.value);
});
$("map-values").addEventListener("change", () => {
  renderMapLabels(metricDefinition(mapMetricId));
  if (mapUrlState()) writeMapUrl();
});
$("map-copy-link").addEventListener("click", async () => {
  const url = writeMapUrl();
  await navigator.clipboard.writeText(url);
  $("map-availability").textContent = "Karten-Direktlink wurde kopiert.";
});
$("map-fullscreen").addEventListener("click", toggleMapFullscreen);
$("map-export-svg").addEventListener("click", exportMapSvg);
$("map-export-png").addEventListener("click", exportMapPng);
document.addEventListener?.("fullscreenchange", () => {
  clearChartHoverThrottle();
  updateComparisonFullscreenButton();
  updateMapFullscreenButton();
  updateDynamicDocumentTitle();
  renderTimeseriesChart();
});
document.addEventListener?.("keydown", event => {
  if (event.key === "Escape") {
    if (comparisonIsFullscreen() || mapIsFullscreen()) document.exitFullscreen();
    else if (activeInfoTrigger) closeInfoPanel(true);
  }
});

window.__atlasMapTest = {
  colorForValue, mapScale, NE_TO_ATLAS, serializedMapSvg, buildMapPngBlob,
  mapUrlState, writeMapUrl,
};
window.__atlasCompareTest = {
  availableComparisonRange,
  buildComparisonCsv,
  colorDistance,
  comparisonPresetRange,
  chartIndexFromClientX,
  createLeadingTrailingThrottle,
  clearChartHoverThrottle,
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

if (typeof window.addEventListener === "function") configureCountryProfileNavigation();
else {
  syncControlsFromMapUrl();
  syncControlsFromProfileUrl();
}
syncPeriodControls();
configureEnhancedSelectMenus();
loadCoverage();
configureInfoPanels();
if (typeof document.querySelector === "function") {
  configureDynamicDocumentTitle();
  configureEuropeOverload();
}
loadMetricCatalog()
  .then(() => Promise.all([loadMapAsset(), loadSummary(), loadStorage()]))
  .then(async () => {
    // A country profile is a self-contained direct view.  Do not let the
    // comparison initializer replace its URL with the default plot state.
    if (profileUrlState()) {
      await loadCountryProfile();
      return;
    }
    if (await restoreMapState()) return;
    const restored = await restoreComparisonState();
    if (!restored) await initializeDefaultComparison();
  })
  .catch(error => {
    $("status").textContent = `Fehler: ${error.message}`;
    $("status").className = "error";
  });
