const columns = [
  ["country_name", "Land", "text"],
  ["data_status", "Datenstatus", "text"],
  ["generation_twh", "Erzeugung TWh", "number"],
  ["consumption_twh", "Verbrauch TWh", "number"],
  ["renewable_twh", "EE TWh", "number"],
  ["renewable_share_pct", "EE %", "number"],
  ["wind_twh", "Wind TWh", "number"],
  ["solar_twh", "Solar TWh", "number"],
  ["nuclear_twh", "Kernkraft TWh", "number"],
  ["fossil_twh", "Fossil TWh", "number"],
  ["price_avg_eur_mwh", "Ø Preis EUR/MWh", "number"],
  ["import_twh", "Import TWh", "number"],
  ["export_twh", "Export TWh", "number"],
  ["net_import_twh", "Saldo TWh", "number"],
  ["carbon_intensity_gco2eq_kwh", "CO₂ gCO₂eq/kWh", "number"],
];

const compareMetrics = [
  ["generation_twh", "Produktion", "TWh"], ["consumption_twh", "Verbrauch", "TWh"],
  ["renewable_twh", "EE", "TWh"], ["renewable_share_pct", "EE", "%"],
  ["wind_twh", "Wind", "TWh"], ["solar_twh", "Solar", "TWh"],
  ["nuclear_twh", "Kernkraft", "TWh"], ["fossil_twh", "Fossil", "TWh"],
  ["price_avg_eur_mwh", "Ø Preis", "EUR/MWh"], ["net_import_twh", "Nettohandel", "TWh"],
  ["carbon_intensity_gco2eq_kwh", "CO₂", "gCO₂eq/kWh"],
];

let data = [];
let sortKey = "country_name";
let sortDirection = 1;
let comparisonData = [];
let compareSortKey = "country_name";
let compareSortDirection = 1;
const selected = new Set();

const $ = id => document.getElementById(id);
const periodQuery = () => {
  const params = new URLSearchParams({year: $("year").value, source: "combined"});
  if ($("period-type").value === "month") params.set("month", $("month").value);
  return params;
};

function format(value) {
  if (value === null || value === undefined) return '<span class="missing">—</span>';
  if (typeof value === "number") return new Intl.NumberFormat("de-DE", {maximumFractionDigits: 2}).format(value);
  return String(value);
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

function renderHead() {
  $("summary-head").innerHTML = '<th scope="col">Auswahl</th>' + columns.map(([key, label]) =>
    `<th scope="col" data-key="${key}"${sortKey === key ? ` aria-sort="${sortDirection > 0 ? "ascending" : "descending"}"` : ""}>${label}${sortKey === key ? (sortDirection > 0 ? " ↑" : " ↓") : ""}</th>`
  ).join("");
  document.querySelectorAll("#summary-head th[data-key]").forEach(th => th.addEventListener("click", () => {
    if (sortKey === th.dataset.key) sortDirection *= -1;
    else { sortKey = th.dataset.key; sortDirection = -1; }
    render();
  }));
}

function render() {
  renderHead();
  const sorted = sortRows(data, sortKey, sortDirection);
  $("summary-body").innerHTML = sorted.map(row => `<tr>
    <td><input type="checkbox" aria-label="${row.country_name} auswählen" data-country="${row.country_code}" ${selected.has(row.country_code) ? "checked" : ""}></td>
    ${columns.map(([key]) => `<td>${format(row[key])}</td>`).join("")}
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
  $("compare-head").innerHTML = `<th scope="col" data-key="country_name"${compareSortKey === "country_name" ? ` aria-sort="${compareSortDirection > 0 ? "ascending" : "descending"}"` : ""}>Land${compareSortKey === "country_name" ? (compareSortDirection > 0 ? " ↑" : " ↓") : ""}</th>` + compareMetrics.map(([key, label, unit]) =>
    `<th scope="col" data-key="${key}"${compareSortKey === key ? ` aria-sort="${compareSortDirection > 0 ? "ascending" : "descending"}"` : ""}>${label}${compareSortKey === key ? (compareSortDirection > 0 ? " ↑" : " ↓") : ""}<span class="unit">${unit}</span></th>`
  ).join("");
  document.querySelectorAll("#compare-head th[data-key]").forEach(th => th.addEventListener("click", () => {
    if (compareSortKey === th.dataset.key) compareSortDirection *= -1;
    else { compareSortKey = th.dataset.key; compareSortDirection = -1; }
    renderComparison();
  }));
  const sorted = sortRows(comparisonData, compareSortKey, compareSortDirection);
  $("compare-body").innerHTML = sorted.map(row =>
    `<tr><th scope="row">${row.country_name}</th>${compareMetrics.map(([key]) => `<td>${format(row[key])}</td>`).join("")}</tr>`
  ).join("");
}

function updateSelection() {
  $("selected-count").textContent = selected.size;
  $("compare").disabled = selected.size < 2 || selected.size > 4;
}

async function loadSummary() {
  $("status").textContent = "Daten werden geladen …";
  $("status").className = "";
  try {
    const response = await fetch(`/api/summary?${periodQuery()}`);
    if (!response.ok) throw new Error((await response.json()).error || response.statusText);
    data = await response.json();
    render();
    $("status").textContent = data.some(row => row.generation_twh != null)
      ? "Kombinierte Daten geladen." : "Noch keine Daten importiert.";
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

async function loadCoverage() {
  $("coverage").innerHTML = "<p>Energy-Charts und Ember bleiben in der Datenbank getrennt. Herkunft, Verarbeitung und Prioritätsregeln sind im Quellenabschnitt unter den Tabellen dokumentiert.</p>";
}

function syncPeriodControls() {
  const showMonth = $("period-type").value === "month";
  $("month-label").hidden = !showMonth;
  $("month").disabled = !showMonth;
}

$("period-type").addEventListener("change", syncPeriodControls);
$("load").addEventListener("click", loadSummary);
$("compare").addEventListener("click", compare);
syncPeriodControls();
loadCoverage();
loadSummary();
