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
  "battery_power_gw",
  "battery_energy_gwh",
  "battery_duration_hours",
  "pumped_storage_power_gw",
  "pumped_storage_energy_gwh",
  "pumped_storage_duration_hours",
];
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
let storageData = [];
let storageSnapshot = null;
let storageSourceLabel = "";
let storageSortKey = "battery_power_gw";
let storageSortDirection = -1;
let mapSvg = null;
let mapMetricId = "generation_twh";
const selected = new Set();
let timeseriesData = null;
let chartHoverIndex = null;
let chartPinnedIndex = null;
let chartHoverCountry = null;
const CHART_COLORS = [
  "#4da3ff", "#ffb454", "#53d39b", "#d38cff", "#ff718b",
  "#64d7e8", "#d6d957", "#a6a1ff", "#ff9466", "#72c06a",
];

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
    ${STORAGE_METRIC_IDS.map(id => storageCell(row, id)).join("")}
  </tr>`).join("");
}

function storageCell(row, metricId) {
  const provenance = row.metric_provenance?.[metricId];
  if (!provenance) return `<td>${format(null)}</td>`;
  const coverageLabels = {
    national_registry_total: "nationaler Register-Gesamtbestand",
    tracked_project_inventory: "erfasster Projektbestand",
  };
  const sourceName = provenance.source === "battery_charts" ? "Battery-Charts" : "JRC";
  const qualityLabel = storageQualityLabel(provenance.quality_status);
  const quality = qualityLabel === "vorhanden" ? "" : ` · ${qualityLabel}`;
  const title = `${provenance.source_label} · Stichtag ${provenance.date} · ${coverageLabels[provenance.coverage_type] || provenance.coverage_type}${quality}`;
  return `<td title="${escapeAttribute(title)}">${format(row[metricId])}<small class="cell-provenance">${escapeHtml(sourceName)} · ${escapeHtml(provenance.date)}${escapeHtml(quality)}</small></td>`;
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
  updateSelection();
  if (timeseriesData) {
    $("comparison-status").textContent = "Länderauswahl geändert. Plot aktualisieren, um den neuen Stand zu laden.";
  }
  return true;
}

function updateSelection() {
  $("selected-count").textContent = selected.size;
  $("compare").disabled = selected.size < 1 || selected.size > 10;
  document.querySelectorAll("input[data-country]").forEach(input => {
    input.checked = selected.has(input.dataset.country);
  });
  renderCountryControls();
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
      ? "Speicherkennzahlen verwenden getrennte Battery-Charts- und JRC-Snapshots; Jahr und Monat gelten hier nicht."
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
    path.addEventListener("mouseenter", event => showCountryDetail(path, event));
    path.addEventListener("mousemove", event => positionTooltip(path, event));
    path.addEventListener("mouseleave", hideMapTooltip);
    path.addEventListener("focus", () => showCountryDetail(path));
    path.addEventListener("blur", hideMapTooltip);
    path.addEventListener("click", () => showCountryDetail(path));
    path.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        showCountryDetail(path);
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
      <button type="button" data-remove-country="${code}" aria-label="${escapeAttribute(name)} entfernen">×</button>
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
    || metricCatalog.get("renewable_share_pct")
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
  const variants = [...metricCatalog.values()].filter(metric => metric.compare && familyKey(metric) === family);
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
  updateSelection();
  $("comparison").hidden = false;
  await loadTimeseries({scroll: false, updateUrl: false});
  return true;
}

async function compare() {
  $("comparison").hidden = false;
  renderComparisonControls();
  await loadTimeseries({scroll: true, updateUrl: true});
}

async function loadTimeseries({scroll = false, updateUrl = true} = {}) {
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
  timeseriesData = payload;
  chartHoverIndex = null;
  chartPinnedIndex = null;
  chartHoverCountry = null;
  renderTimeseriesChart();
  for (const id of ["export-csv", "export-svg", "export-png", "copy-link"]) $(id).disabled = false;
  $("comparison-status").textContent = `${payload.countries.length} Länder · ${payload.granularity === "monthly" ? "Monatswerte" : "Jahreswerte"} · fehlende Werte bleiben als Linienlücken sichtbar.`;
  if (updateUrl) writeComparisonUrl();
  if (scroll) $("comparison").scrollIntoView({behavior: "smooth"});
}

function svgElement(name, attributes = {}, text = null) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, String(value)));
  if (text !== null) element.textContent = text;
  return element;
}

function chartGeometry() {
  return {width: 1040, height: 620, left: 82, right: 850, top: 82, bottom: 490};
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
  }).filter(Boolean).sort((a, b) => a.targetY - b.targetY);
  const gap = 25;
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
  svg.replaceChildren();
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
  if (averagePath) svg.appendChild(svgElement("path", {class: "chart-line atlas-average-line", d: averagePath}));
  payload.countries.forEach((country, index) => {
    const path = linePath(country.values, scale);
    if (!path) return;
    const muted = chartHoverCountry && chartHoverCountry !== country.country_code;
    svg.appendChild(svgElement("path", {
      class: `chart-line country-line${muted ? " muted" : ""}${chartHoverCountry === country.country_code ? " active" : ""}`,
      d: path,
      stroke: CHART_COLORS[index],
      "data-country-line": country.country_code,
    }));
    if (activeIndex !== null && Number.isFinite(country.values[activeIndex]?.value)) {
      svg.appendChild(svgElement("circle", {
        class: "chart-point",
        cx: scale.x(activeIndex),
        cy: scale.y(country.values[activeIndex].value),
        r: chartHoverCountry === country.country_code ? 6 : 4,
        fill: CHART_COLORS[index],
      }));
    }
  });

  endpointPositions(payload, scale, geometry).forEach(endpoint => {
    const color = CHART_COLORS[endpoint.countryIndex];
    svg.appendChild(svgElement("path", {
      class: "endpoint-connector",
      d: `M${endpoint.x},${endpoint.targetY} L870,${endpoint.y}`,
      stroke: color,
    }));
    svg.appendChild(svgElement("image", {
      class: "endpoint-flag",
      href: `/assets/flags/${flagCode(endpoint.country.country_code)}.svg`,
      x: 878,
      y: endpoint.y - 9,
      width: 24,
      height: 18,
    }));
    svg.appendChild(svgElement("text", {class: "endpoint-tag", x: 910, y: endpoint.y + 5, fill: color}, endpoint.country.country_code));
  });
  const averageEndpoint = [...payload.atlas_average.values].map((point, index) => ({point, index})).reverse().find(item => Number.isFinite(item.point.value));
  if (averageEndpoint) {
    svg.appendChild(svgElement("text", {
      class: "average-endpoint-tag",
      x: Math.min(geometry.right + 8, scale.x(averageEndpoint.index) + 8),
      y: scale.y(averageEndpoint.point.value) - 8,
    }, "Atlas Ø"));
  }

  const legendY = 548;
  [...payload.countries.map((country, index) => ({label: country.country_code, color: CHART_COLORS[index]})), {label: "Atlas-Durchschnitt", color: "#edf3fb", average: true}]
    .forEach((item, index) => {
      const column = index % 6;
      const row = Math.floor(index / 6);
      const x = geometry.left + column * 145;
      const y = legendY + row * 28;
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
  renderRanking(activeIndex ?? periods.length - 1);
  $("unpin-time").hidden = chartPinnedIndex === null;
}

function pointerInSvg(svg, event) {
  const point = svg.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;
  return point.matrixTransform(svg.getScreenCTM().inverse());
}

function bindChartInteraction(svg, scale, geometry) {
  const overlay = svg.querySelector(".chart-interaction");
  overlay.addEventListener("pointermove", event => {
    const point = pointerInSvg(svg, event);
    const count = timeseriesData.atlas_average.values.length;
    const index = Math.max(0, Math.min(count - 1, Math.round((point.x - geometry.left) / (geometry.right - geometry.left) * Math.max(1, count - 1))));
    let closest = null;
    let distance = Infinity;
    timeseriesData.countries.forEach(country => {
      const value = country.values[index]?.value;
      if (!Number.isFinite(value)) return;
      const candidate = Math.abs(scale.y(value) - point.y);
      if (candidate < distance) {
        closest = country.country_code;
        distance = candidate;
      }
    });
    if (index !== chartHoverIndex || closest !== chartHoverCountry) {
      chartHoverIndex = index;
      chartHoverCountry = distance <= 24 ? closest : null;
      renderTimeseriesChart();
    }
  });
  overlay.addEventListener("pointerleave", () => {
    if (chartPinnedIndex === null && (chartHoverIndex !== null || chartHoverCountry !== null)) {
      chartHoverIndex = null;
      chartHoverCountry = null;
      renderTimeseriesChart();
    }
  });
  overlay.addEventListener("click", event => {
    const point = pointerInSvg(svg, event);
    const count = timeseriesData.atlas_average.values.length;
    const index = Math.max(0, Math.min(count - 1, Math.round((point.x - geometry.left) / (geometry.right - geometry.left) * Math.max(1, count - 1))));
    chartPinnedIndex = chartPinnedIndex === index ? null : index;
    chartHoverIndex = index;
    renderTimeseriesChart();
  });
}

function rankingChange(country, index) {
  const current = country.values[index]?.value;
  const start = country.values[0]?.value;
  if (!Number.isFinite(current) || !Number.isFinite(start)) return "—";
  const metric = timeseriesData.metric;
  const delta = current - start;
  if (metric.unit === "%") return `${delta >= 0 ? "+" : ""}${formatMetricValue(delta, {...metric, map_config: {...metric.map_config, decimals: 1}})} pp`;
  if (metric.map_config?.scale === "diverging") return `${delta >= 0 ? "+" : ""}${formatMetricValue(delta, metric)} ${metric.unit}`;
  if (start === 0) return "—";
  const change = delta / Math.abs(start) * 100;
  return `${change >= 0 ? "+" : ""}${new Intl.NumberFormat("de-DE", {maximumFractionDigits: 1}).format(change)} %`;
}

function renderRanking(index) {
  const previous = new Map([...$("ranking-list").children].map(item => [item.dataset.country, item.getBoundingClientRect().top]));
  const entries = timeseriesData.countries.map((country, countryIndex) => ({
    country,
    countryIndex,
    value: country.values[index]?.value,
  })).sort((a, b) => {
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
  const period = timeseriesData.atlas_average.values[index].period;
  const periodStatus = timeseriesData.atlas_average.values[index].period_status;
  $("ranking-period").textContent = `${period}${periodStatus === "ytd" ? " · YTD" : periodStatus === "provisional_current_month" ? " · vorläufig" : ""}`;
  const average = timeseriesData.atlas_average.values[index].value;
  $("atlas-average-value").textContent = `Atlas-Durchschnitt · ${formatMetricValue(average, timeseriesData.metric)} ${timeseriesData.metric.unit}`;
  $("ranking-list").innerHTML = entries.map(entry => {
    const active = chartHoverCountry === entry.country.country_code;
    return `<li data-country="${entry.country.country_code}" class="ranking-item${active ? " active" : ""}${Number.isFinite(entry.value) ? "" : " missing-value"}">
      <span class="ranking-rank">${entry.rank || "—"}</span>
      <img src="/assets/flags/${flagCode(entry.country.country_code)}.svg" alt="" width="24" height="18">
      <span class="ranking-country"><b>${entry.country.country_code}</b><small>${escapeHtml(entry.country.country_name)}</small></span>
      <span class="ranking-value">${formatMetricValue(entry.value, timeseriesData.metric)}<small>${Number.isFinite(entry.value) ? timeseriesData.metric.unit : ""}</small></span>
      <span class="ranking-change">${rankingChange(entry.country, index)}</span>
    </li>`;
  }).join("");
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
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
  module.exports = {buildComparisonCsv, flagCode, parseComparisonUrl};
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

function comparisonFilename(extension) {
  return `eea-${timeseriesData.metric.id}-${timeseriesData.start}-${timeseriesData.end}.${extension}`;
}

async function serializedChartSvg() {
  const clone = $("timeseries-chart").cloneNode(true);
  clone.querySelectorAll(".chart-interaction").forEach(element => element.remove());
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("width", "1040");
  clone.setAttribute("height", "620");
  const style = document.createElementNS("http://www.w3.org/2000/svg", "style");
  style.textContent = `
    .chart-background{fill:#0d1626}.chart-title{fill:#edf3fb;font:750 24px system-ui,sans-serif}
    .chart-subtitle,.axis-label,.legend-label,.average-endpoint-tag{fill:#91a3ba;font:13px system-ui,sans-serif}
    .chart-grid{stroke:#2b3b52;stroke-width:1}.chart-grid.vertical{stroke-opacity:.45}
    .chart-zero{stroke:#c9d4e2;stroke-width:1.5}.chart-line{fill:none;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}
    .country-line.muted{opacity:.2}.country-line.active{stroke-width:5}.atlas-average-line{stroke:#edf3fb;stroke-width:2.5;stroke-dasharray:10 7;opacity:.85}
    .chart-guide{stroke:#dbe8f6;stroke-width:1.2;stroke-dasharray:4 5}.chart-point{stroke:#08101c;stroke-width:2}
    .endpoint-connector{fill:none;stroke-width:1.3;opacity:.8}.endpoint-tag{font:800 14px system-ui,sans-serif}
    .average-endpoint-tag{font-weight:750;fill:#edf3fb}.legend-line{stroke-width:3}.legend-line.average{stroke-dasharray:7 5}
    .x-axis-label{text-anchor:middle}.y-axis-label{text-anchor:end}
  `;
  clone.prepend(style);
  for (const image of clone.querySelectorAll("image")) {
    const response = await fetch(image.getAttribute("href"));
    const source = await response.text();
    image.setAttribute("href", `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(source)))}`);
  }
  return `<?xml version="1.0" encoding="UTF-8"?>\n${new XMLSerializer().serializeToString(clone)}`;
}

async function exportSvg() {
  downloadBlob(new Blob([await serializedChartSvg()], {type: "image/svg+xml;charset=utf-8"}), comparisonFilename("svg"));
}

async function exportPng() {
  const blob = await buildChartPngBlob();
  downloadBlob(blob, comparisonFilename("png"));
}

async function buildChartPngBlob() {
  const source = await serializedChartSvg();
  const url = URL.createObjectURL(new Blob([source], {type: "image/svg+xml;charset=utf-8"}));
  const image = new Image();
  await new Promise((resolve, reject) => {
    image.onload = resolve;
    image.onerror = reject;
    image.src = url;
  });
  const canvas = document.createElement("canvas");
  canvas.width = 2080;
  canvas.height = 1240;
  const context = canvas.getContext("2d");
  context.fillStyle = "#0a0f1c";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.drawImage(image, 0, 0, canvas.width, canvas.height);
  URL.revokeObjectURL(url);
  return new Promise(resolve => canvas.toBlob(resolve, "image/png"));
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
  renderMapControls();
  renderMap();
}

$("period-type").addEventListener("change", syncPeriodControls);
$("year").max = String(currentYear);
$("load").addEventListener("click", loadSummary);
$("compare").addEventListener("click", compare);
$("compare-load").addEventListener("click", () => loadTimeseries({updateUrl: true}));
$("compare-country-add").addEventListener("change", event => {
  if (event.target.value) toggleCountry(event.target.value, true);
  event.target.value = "";
});
$("compare-family").addEventListener("change", event => renderComparisonMetricOptions(event.target.value));
$("compare-metric").addEventListener("change", event => configureComparisonRange(metricDefinition(event.target.value)));
$("unpin-time").addEventListener("click", () => {
  chartPinnedIndex = null;
  chartHoverIndex = null;
  chartHoverCountry = null;
  renderTimeseriesChart();
});
$("export-csv").addEventListener("click", () => {
  downloadBlob(new Blob([buildComparisonCsv(timeseriesData)], {type: "text/csv;charset=utf-8"}), comparisonFilename("csv"));
});
$("export-svg").addEventListener("click", exportSvg);
$("export-png").addEventListener("click", exportPng);
$("copy-link").addEventListener("click", async () => {
  const url = writeComparisonUrl();
  await navigator.clipboard.writeText(url);
  $("comparison-status").textContent = "Direktlink wurde kopiert.";
});
$("map-family").addEventListener("change", event => {
  const variants = mapMetrics().filter(metric => familyKey(metric) === event.target.value);
  const next = variants.find(metricAvailable) || variants[0];
  if (next) setMapMetric(next.id);
});
$("map-representation").addEventListener("change", event => setMapMetric(event.target.value));
$("map-values").addEventListener("change", () => renderMapLabels(metricDefinition(mapMetricId)));

window.__atlasMapTest = {colorForValue, mapScale, NE_TO_ATLAS};
window.__atlasCompareTest = {
  buildComparisonCsv,
  flagCode,
  parseComparisonUrl,
  serializedChartSvg,
  buildChartPngBlob,
};

syncPeriodControls();
loadCoverage();
loadMetricCatalog()
  .then(() => Promise.all([loadMapAsset(), loadSummary(), loadStorage()]))
  .then(() => restoreComparisonState())
  .catch(error => {
    $("status").textContent = `Fehler: ${error.message}`;
    $("status").className = "error";
  });
