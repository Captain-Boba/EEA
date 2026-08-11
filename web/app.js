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
const STORAGE_METRIC_IDS = ["storage_power_gw", "storage_energy_gwh", "storage_duration_hours"];
const NE_TO_ATLAS = {
  "AUT": "AT", "BEL": "BE", "BGR": "BG", "CHE": "CH", "CZE": "CZ", "DEU": "DE", "DNK": "DK",
  "ESP": "ES", "EST": "EE", "FIN": "FI", "FRA": "FR", "GBR": "UK", "GRC": "GR", "HRV": "HR",
  "HUN": "HU", "IRL": "IE", "ITA": "IT", "LTU": "LT", "LUX": "LU", "LVA": "LV", "MNE": "ME",
  "MKD": "MK", "NLD": "NL", "NOR": "NO", "POL": "PL", "PRT": "PT", "ROU": "RO", "SRB": "RS",
  "SVK": "SK", "SVN": "SI", "SWE": "SE"
};
const MAP_PALETTES = {
  teal: ["#e7f2f2", "#a8d3d1", "#5badaf", "#247f8f", "#07566f"],
  amber: ["#fff3d7", "#f5d18a", "#dfa653", "#b8752f", "#78461f"],
  purple: ["#f0edf6", "#cbbddb", "#9c83b5", "#71518f", "#48266c"],
  "orange-purple": ["#b35806", "#f1a340", "#f7f7f7", "#998ec3", "#542788"],
};

let metricCatalog = new Map();
let data = [];
let sortKey = "country_name";
let sortDirection = 1;
let comparisonData = [];
let compareSortKey = "country_name";
let compareSortDirection = 1;
let storageData = [];
let storageSnapshot = null;
let storageSourceLabel = "";
let storageSortKey = "storage_power_gw";
let storageSortDirection = -1;
let mapSvg = null;
let mapMetricId = "generation_twh";
const selected = new Set();

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

function formatMetricValue(value, metric, compact = false) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
  const decimals = metric?.map_config?.decimals ?? 2;
  return new Intl.NumberFormat("de-DE", {
    maximumFractionDigits: decimals,
    minimumFractionDigits: 0,
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
  const arrow = activeSort ? (direction > 0 ? " ↑" : " ↓") : "";
  const ariaSort = activeSort ? ` aria-sort="${direction > 0 ? "ascending" : "descending"}"` : "";
  const unit = metric.unit ? `<span class="unit">${escapeHtml(metric.unit)}</span>` : "";
  const mapAction = allowMap && metric.map
    ? `<button type="button" class="map-column-action${mapMetricId === id ? " active" : ""}" data-map-metric="${id}" aria-label="${escapeAttribute(metric.label_de)} auf Karte anzeigen">Auf Karte anzeigen</button>`
    : "";
  return `<th scope="col" data-key="${id}"${ariaSort} class="${mapMetricId === id ? "map-column-active" : ""}">
    <button type="button" class="sort-action" data-sort-key="${id}" aria-label="${escapeAttribute(metric.label_de)} sortieren">${escapeHtml(metric.label_de)}${arrow}${unit}</button>
    ${mapAction}
  </th>`;
}

function countryHeader(activeKey, direction) {
  const active = activeKey === "country_name";
  const arrow = active ? (direction > 0 ? " ↑" : " ↓") : "";
  const ariaSort = active ? ` aria-sort="${direction > 0 ? "ascending" : "descending"}"` : "";
  return `<th scope="col" data-key="country_name"${ariaSort}><button type="button" class="sort-action" data-sort-key="country_name">Land${arrow}</button></th>`;
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

function bindSort(selector, callback) {
  document.querySelectorAll(selector).forEach(button => button.addEventListener("click", () => callback(button.dataset.sortKey)));
}

function bindMapColumnActions() {
  document.querySelectorAll("#summary-head [data-map-metric]").forEach(button => button.addEventListener("click", () => {
    setMapMetric(button.dataset.mapMetric, true);
  }));
}

function renderHead() {
  $("summary-head").innerHTML = '<th scope="col">Auswahl</th>'
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
  renderHead();
  const sorted = sortRows(data, sortKey, sortDirection);
  $("summary-body").innerHTML = sorted.map(row => `<tr data-country-row="${row.country_code}">
    <td><input type="checkbox" aria-label="${escapeAttribute(row.country_name)} auswählen" data-country="${row.country_code}" ${selected.has(row.country_code) ? "checked" : ""}></td>
    <th scope="row"><span class="country-name">${escapeHtml(row.country_name)}</span>${statusBadge(row)}</th>
    ${TABLE_METRIC_IDS.map(id => `<td data-metric="${id}" class="${mapMetricId === id ? "map-column-active" : ""}">${format(row[id])}</td>`).join("")}
  </tr>`).join("");
  document.querySelectorAll("input[data-country]").forEach(input => input.addEventListener("change", event => {
    const changed = toggleCountry(event.target.dataset.country, event.target.checked);
    if (!changed) event.target.checked = false;
  }));
  updateSelection();
}

function renderComparison() {
  $("compare-head").innerHTML = countryHeader(compareSortKey, compareSortDirection)
    + TABLE_METRIC_IDS.map(id => metricHeader(id, compareSortKey, compareSortDirection)).join("");
  bindSort("#compare-head [data-sort-key]", key => {
    if (compareSortKey === key) compareSortDirection *= -1;
    else { compareSortKey = key; compareSortDirection = -1; }
    renderComparison();
  });
  const sorted = sortRows(comparisonData, compareSortKey, compareSortDirection);
  $("compare-body").innerHTML = sorted.map(row =>
    `<tr><th scope="row"><span class="country-name">${escapeHtml(row.country_name)}</span>${statusBadge(row)}</th>${TABLE_METRIC_IDS.map(id => `<td>${format(row[id])}</td>`).join("")}</tr>`
  ).join("");
}

function renderStorage() {
  $("storage-head").innerHTML = countryHeader(storageSortKey, storageSortDirection)
    + STORAGE_METRIC_IDS.map(id => metricHeader(id, storageSortKey, storageSortDirection)).join("");
  bindSort("#storage-head [data-sort-key]", key => {
    if (storageSortKey === key) storageSortDirection *= -1;
    else { storageSortKey = key; storageSortDirection = -1; }
    renderStorage();
  });
  const sorted = sortRows(storageData, storageSortKey, storageSortDirection);
  $("storage-body").innerHTML = sorted.map(row => `<tr>
    <th scope="row">${escapeHtml(row.country_name)}${row.quality_status === "missing" ? '<span class="status-badge missing">fehlend</span>' : ""}</th>
    ${STORAGE_METRIC_IDS.map(id => `<td>${format(row[id])}</td>`).join("")}
  </tr>`).join("");
}

function toggleCountry(code, shouldSelect = !selected.has(code)) {
  if (shouldSelect && !selected.has(code) && selected.size >= 4) {
    $("status").textContent = "Maximal vier Länder können gleichzeitig verglichen werden.";
    return false;
  }
  shouldSelect ? selected.add(code) : selected.delete(code);
  updateSelection();
  return true;
}

function updateSelection() {
  $("selected-count").textContent = selected.size;
  $("compare").disabled = selected.size < 2 || selected.size > 4;
  document.querySelectorAll("input[data-country]").forEach(input => {
    input.checked = selected.has(input.dataset.country);
  });
  if (mapSvg) {
    mapSvg.querySelectorAll("[data-country-code]").forEach(path => {
      const active = selected.has(path.dataset.countryCode);
      path.classList.toggle("selected", active);
      path.setAttribute("aria-pressed", String(active));
    });
  }
}

function mapMetrics() {
  return [...metricCatalog.values()].filter(metric => metric.map);
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
      const disabled = variants.some(metricAvailable) ? "" : " disabled";
      return `<option value="${escapeAttribute(`${group}::${family}`)}"${disabled}>${escapeHtml(family)}</option>`;
    }).join("")}</optgroup>`
  ).join("");
  $("map-family").value = familyKey(activeMetric);

  const variants = metrics.filter(metric => familyKey(metric) === familyKey(activeMetric));
  $("map-representation").innerHTML = variants.map(metric => {
    const disabled = metricAvailable(metric) ? "" : " disabled";
    const unit = metric.unit ? ` (${metric.unit})` : "";
    return `<option value="${metric.id}"${disabled}>${escapeHtml(metric.representation)}${escapeHtml(unit)}</option>`;
  }).join("");
  $("map-representation").value = mapMetricId;

  if (metricAvailable(activeMetric)) {
    $("map-availability").textContent = activeMetric.temporal_availability.snapshot
      ? "Speicherkennzahlen verwenden den separat ausgewiesenen JRC-Snapshot; Jahr und Monat gelten hier nicht."
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

function setMapMetric(metricId, scrollToMap = false) {
  const metric = metricCatalog.get(metricId);
  if (!metric?.map) return;
  mapMetricId = metricId;
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
  if (metric.temporal_availability.snapshot) return storageSnapshot ? `Snapshot ${storageSnapshot}` : "Kein Snapshot";
  const period = row?.period || (isMonthView() ? `${selectedYear()}-${String($("month").value).padStart(2, "0")}` : String(selectedYear()));
  const status = row?.period_status === "ytd" ? " · YTD" : (row?.period_status === "provisional_current_month" ? " · vorläufig" : "");
  return `${period}${status}`;
}

function statusLabel(row, metric) {
  if (!row) return "fehlend";
  const value = row[metric.id];
  if (value === null || value === undefined) return "fehlend";
  if (metric.temporal_availability.snapshot) {
    return row.quality_status === "observed_with_estimates" ? "mit Schätzwerten" : (row.quality_status || "vorhanden");
  }
  return {complete: "vollständig", partial: "teilweise", missing: "fehlend"}[row.data_status] || row.data_status || "vorhanden";
}

function countryDetail(code, metric) {
  const row = mapRow(code, metric);
  const value = metricAvailable(metric) && row ? row[metric.id] : null;
  const formatted = formatMetricValue(value, metric);
  const unit = formatted === "—" ? "" : ` ${metric.unit}`;
  return {
    html: `<strong>${escapeHtml(countryName(code))}</strong>
      <span>${escapeHtml(metric.label_de)}</span>
      <b>${escapeHtml(formatted + unit)}</b>
      <span>${escapeHtml(periodLabel(metric, row))}</span>
      <span>Datenstatus: ${escapeHtml(statusLabel(row, metric))}</span>
      <span>Quelle: ${escapeHtml(metric.source)}</span>`,
    label: `${countryName(code)}, ${metric.label_de}: ${formatted}${unit}, ${periodLabel(metric, row)}, Datenstatus ${statusLabel(row, metric)}, Quelle ${metric.source}`,
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
  const colors = MAP_PALETTES[palette] || MAP_PALETTES.teal;
  const bounded = Math.max(0, Math.min(1, position));
  const scaled = bounded * (colors.length - 1);
  const index = Math.min(colors.length - 2, Math.floor(scaled));
  return interpolateColor(colors[index], colors[index + 1], scaled - index);
}

function mapScale(metric, values) {
  const config = metric.map_config || {};
  if (Array.isArray(config.domain)) return {min: config.domain[0], max: config.domain[1], midpoint: config.midpoint};
  const finite = values.filter(value => Number.isFinite(value));
  if (!finite.length) return {min: 0, max: 1, midpoint: config.midpoint};
  let min = Math.min(...finite), max = Math.max(...finite);
  if (config.scale === "diverging") {
    const midpoint = config.midpoint ?? 0;
    const distance = Math.max(Math.abs(min - midpoint), Math.abs(max - midpoint), 1e-9);
    return {min: midpoint - distance, max: midpoint + distance, midpoint};
  }
  if (min === max) {
    if (min === 0) max = 1;
    else if (min > 0) min = 0;
    else max = 0;
  }
  return {min, max, midpoint: config.midpoint};
}

function colorForValue(value, metric, scale) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return null;
  const position = (Number(value) - scale.min) / (scale.max - scale.min || 1);
  return paletteColor(metric.map_config?.palette || "teal", position);
}

function renderLegend(metric, scale) {
  const colors = MAP_PALETTES[metric.map_config?.palette] || MAP_PALETTES.teal;
  const gradient = `linear-gradient(90deg, ${colors.join(", ")})`;
  const midpoint = scale.midpoint;
  $("map-legend").innerHTML = `<div class="legend-ramp" style="background:${gradient}" aria-hidden="true"></div>
    <div class="legend-values"><span>${escapeHtml(formatMetricValue(scale.min, metric))}</span>${midpoint !== null && midpoint !== undefined ? `<span>${escapeHtml(formatMetricValue(midpoint, metric))}</span>` : ""}<span>${escapeHtml(formatMetricValue(scale.max, metric))}</span></div>
    <p>${escapeHtml(metric.unit || "ohne Einheit")} · Grau = kein Wert</p>`;
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

function showCountryDetail(path, pointerEvent = null) {
  const metric = metricDefinition(mapMetricId);
  const detail = countryDetail(path.dataset.countryCode, metric);
  $("map-detail").innerHTML = detail.html;
  $("map-tooltip").innerHTML = detail.html;
  $("map-tooltip").hidden = false;
  positionTooltip(path, pointerEvent);
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
    path.setAttribute("aria-pressed", "false");
    path.addEventListener("mouseenter", event => showCountryDetail(path, event));
    path.addEventListener("mousemove", event => positionTooltip(path, event));
    path.addEventListener("mouseleave", hideMapTooltip);
    path.addEventListener("focus", () => showCountryDetail(path));
    path.addEventListener("blur", hideMapTooltip);
    path.addEventListener("click", () => toggleCountry(code));
    path.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        toggleCountry(code);
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
    path.setAttribute("aria-label", countryDetail(path.dataset.countryCode, metric).label);
  });
  $("map-metric-title").textContent = `${metric.family}: ${metric.representation}`;
  $("map-period").textContent = periodLabel(metric, mapRow("DE", metric));
  renderLegend(metric, scale);
  renderMapLabels(metric);
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

async function compare() {
  const params = periodQuery();
  params.set("countries", [...selected].join(","));
  const response = await fetch(`/api/compare?${params}`);
  const comparison = await response.json();
  if (!response.ok) { $("status").textContent = `Fehler: ${comparison.error}`; return; }
  comparisonData = comparison;
  renderComparison();
  $("comparison").hidden = false;
  $("comparison").scrollIntoView({behavior: "smooth"});
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
      ? ` Ohne Exportwert: ${storage.countries_missing.join(", ")}.`
      : "";
    $("storage-note").textContent = `Snapshot ${storage.snapshot_date} · ${storage.countries_with_values}/${storage.countries.length} Länder · ${storageSourceLabel}.${missingNote}`;
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
  renderMapControls();
  renderMap();
}

$("period-type").addEventListener("change", syncPeriodControls);
$("year").max = String(currentYear);
$("load").addEventListener("click", loadSummary);
$("compare").addEventListener("click", compare);
$("map-family").addEventListener("change", event => {
  const variants = mapMetrics().filter(metric => familyKey(metric) === event.target.value);
  const next = variants.find(metricAvailable) || variants[0];
  if (next) setMapMetric(next.id);
});
$("map-representation").addEventListener("change", event => setMapMetric(event.target.value));
$("map-values").addEventListener("change", () => renderMapLabels(metricDefinition(mapMetricId)));

window.__atlasMapTest = {colorForValue, mapScale, NE_TO_ATLAS};

syncPeriodControls();
loadCoverage();
loadMetricCatalog()
  .then(() => Promise.all([loadMapAsset(), loadSummary(), loadStorage()]))
  .catch(error => {
    $("status").textContent = `Fehler: ${error.message}`;
    $("status").className = "error";
  });
