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

let metricCatalog = new Map();
let data = [];
let sortKey = "country_name";
let sortDirection = 1;
let comparisonData = [];
let compareSortKey = "country_name";
let compareSortDirection = 1;
let storageData = [];
let storageSortKey = "storage_power_gw";
let storageSortDirection = -1;
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

function periodQuery() {
  const params = new URLSearchParams({year: selectedYear()});
  if ($("period-type").value === "month") params.set("month", $("month").value);
  return params;
}

function format(value) {
  if (value === null || value === undefined) return '<span class="missing">—</span>';
  if (typeof value === "number") {
    return new Intl.NumberFormat("de-DE", {maximumFractionDigits: 2}).format(value);
  }
  return String(value);
}

function metricDefinition(id) {
  return metricCatalog.get(id) || {id, label_de: id, unit: ""};
}

function metricHeader(id, activeKey, direction) {
  const metric = metricDefinition(id);
  const active = activeKey === id;
  const arrow = active ? (direction > 0 ? " ↑" : " ↓") : "";
  const ariaSort = active ? ` aria-sort="${direction > 0 ? "ascending" : "descending"}"` : "";
  const unit = metric.unit ? `<span class="unit">${metric.unit}</span>` : "";
  return `<th scope="col" data-key="${id}"${ariaSort}>${metric.label_de}${arrow}${unit}</th>`;
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

function escapeAttribute(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
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
  document.querySelectorAll(selector).forEach(th => th.addEventListener("click", () => callback(th.dataset.key)));
}

function renderHead() {
  const countryArrow = sortKey === "country_name" ? (sortDirection > 0 ? " ↑" : " ↓") : "";
  const countrySort = sortKey === "country_name" ? ` aria-sort="${sortDirection > 0 ? "ascending" : "descending"}"` : "";
  $("summary-head").innerHTML = '<th scope="col">Auswahl</th>'
    + `<th scope="col" data-key="country_name"${countrySort}>Land${countryArrow}</th>`
    + TABLE_METRIC_IDS.map(id => metricHeader(id, sortKey, sortDirection)).join("");
  bindSort("#summary-head th[data-key]", key => {
    if (sortKey === key) sortDirection *= -1;
    else { sortKey = key; sortDirection = -1; }
    render();
  });
}

function render() {
  renderHead();
  const sorted = sortRows(data, sortKey, sortDirection);
  $("summary-body").innerHTML = sorted.map(row => `<tr>
    <td><input type="checkbox" aria-label="${escapeAttribute(row.country_name)} auswählen" data-country="${row.country_code}" ${selected.has(row.country_code) ? "checked" : ""}></td>
    <th scope="row"><span class="country-name">${row.country_name}</span>${statusBadge(row)}</th>
    ${TABLE_METRIC_IDS.map(id => `<td>${format(row[id])}</td>`).join("")}
  </tr>`).join("");
  document.querySelectorAll("input[data-country]").forEach(input => input.addEventListener("change", event => {
    const code = event.target.dataset.country;
    if (event.target.checked && selected.size >= 4) { event.target.checked = false; return; }
    event.target.checked ? selected.add(code) : selected.delete(code);
    updateSelection();
  }));
  updateSelection();
}

function renderComparison() {
  const countryArrow = compareSortKey === "country_name" ? (compareSortDirection > 0 ? " ↑" : " ↓") : "";
  const countrySort = compareSortKey === "country_name" ? ` aria-sort="${compareSortDirection > 0 ? "ascending" : "descending"}"` : "";
  $("compare-head").innerHTML = `<th scope="col" data-key="country_name"${countrySort}>Land${countryArrow}</th>`
    + TABLE_METRIC_IDS.map(id => metricHeader(id, compareSortKey, compareSortDirection)).join("");
  bindSort("#compare-head th[data-key]", key => {
    if (compareSortKey === key) compareSortDirection *= -1;
    else { compareSortKey = key; compareSortDirection = -1; }
    renderComparison();
  });
  const sorted = sortRows(comparisonData, compareSortKey, compareSortDirection);
  $("compare-body").innerHTML = sorted.map(row =>
    `<tr><th scope="row"><span class="country-name">${row.country_name}</span>${statusBadge(row)}</th>${TABLE_METRIC_IDS.map(id => `<td>${format(row[id])}</td>`).join("")}</tr>`
  ).join("");
}

function renderStorage() {
  const countryArrow = storageSortKey === "country_name" ? (storageSortDirection > 0 ? " ↑" : " ↓") : "";
  const countrySort = storageSortKey === "country_name" ? ` aria-sort="${storageSortDirection > 0 ? "ascending" : "descending"}"` : "";
  $("storage-head").innerHTML = `<th scope="col" data-key="country_name"${countrySort}>Land${countryArrow}</th>`
    + STORAGE_METRIC_IDS.map(id => metricHeader(id, storageSortKey, storageSortDirection)).join("");
  bindSort("#storage-head th[data-key]", key => {
    if (storageSortKey === key) storageSortDirection *= -1;
    else { storageSortKey = key; storageSortDirection = -1; }
    renderStorage();
  });
  const sorted = sortRows(storageData, storageSortKey, storageSortDirection);
  $("storage-body").innerHTML = sorted.map(row => `<tr>
    <th scope="row">${row.country_name}${row.quality_status === "missing" ? '<span class="status-badge missing">fehlend</span>' : ""}</th>
    ${STORAGE_METRIC_IDS.map(id => `<td>${format(row[id])}</td>`).join("")}
  </tr>`).join("");
}

function updateSelection() {
  $("selected-count").textContent = selected.size;
  $("compare").disabled = selected.size < 2 || selected.size > 4;
}

async function loadMetricCatalog() {
  const response = await fetch("/api/metrics");
  if (!response.ok) throw new Error((await response.json()).error || response.statusText);
  metricCatalog = new Map((await response.json()).map(metric => [metric.id, metric]));
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
    if (!storage.snapshot_date) return;
    storageData = storage.countries;
    const missingNote = storage.countries_missing?.length
      ? ` Ohne Exportwert: ${storage.countries_missing.join(", ")}.`
      : "";
    $("storage-note").textContent = `Snapshot ${storage.snapshot_date} · ${storage.countries_with_values}/${storage.countries.length} Länder · ${storage.source_label}.${missingNote}`;
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
  const showMonth = $("period-type").value === "month";
  $("month-label").hidden = !showMonth;
  $("month").disabled = !showMonth;
}

$("period-type").addEventListener("change", syncPeriodControls);
$("year").max = String(currentYear);
$("load").addEventListener("click", loadSummary);
$("compare").addEventListener("click", compare);
syncPeriodControls();
loadCoverage();
loadSummary();
loadStorage();
