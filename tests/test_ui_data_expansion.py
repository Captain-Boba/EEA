import json
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from electricity_atlas.metrics import metric_catalog


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "web" / "app.js"
INDEX_PATH = ROOT / "web" / "index.html"
STYLE_PATH = ROOT / "web" / "style.css"


def resolve_node() -> Path | None:
    explicit = os.environ.get("EEA_NODE")
    if explicit:
        candidate = Path(explicit)
        if candidate.is_file():
            return candidate
        raise RuntimeError(f"EEA_NODE does not point to a file: {candidate}")
    from_path = shutil.which("node")
    if from_path:
        return Path(from_path)
    return None


NODE = resolve_node()


class DataExpansionUiTests(unittest.TestCase):
    def run_node(self, script):
        if NODE is None:
            self.fail("Node.js is required for JavaScript tests; set EEA_NODE or add node to PATH.")
        encoded = script.encode("utf-8").hex()
        bootstrap = f'eval(Buffer.from("{encoded}", "hex").toString("utf8"))'
        result = subprocess.run(
            [str(NODE), "-e", bootstrap],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def test_ev_ranking_contains_exactly_three_metrics_and_accessible_controls(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        app = APP_PATH.read_text(encoding="utf-8")
        metric_block = re.search(r"const EV_METRIC_IDS = \[(.*?)\];", app, re.DOTALL)
        self.assertIsNotNone(metric_block)
        self.assertEqual(
            re.findall(r'"([a-z0-9_]+)"', metric_block.group(1)),
            ["bev_stock", "bev_new_registrations", "ev_battery_nominal_capacity_est_gwh"],
        )
        self.assertLess(html.index('id="comparison"'), html.index('id="summary-table"'))
        self.assertLess(html.index('id="summary-table"'), html.index('id="electromobility"'))
        self.assertIn('id="ev-note" class="hint" role="status"', html)
        self.assertIn('id="ev-toggle"', html)
        self.assertIn('aria-controls="ev-table-region"', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn('updateTableDisclosure("ev"', app)
        self.assertIn("evSortDirection = -1", app)
        self.assertIn("${index + 1}", app)
        self.assertIn(".table-card #ev-table", STYLE_PATH.read_text(encoding="utf-8"))

    def test_ev_sorting_top_ten_month_suppression_and_missing_values(self):
        script = r'''
global.document = {getElementById: () => ({addEventListener: () => {}})};
global.window = {location: {href: "http://localhost/"}, matchMedia: () => ({matches: true})};
global.history = {replaceState: () => {}};
global.fetch = () => new Promise(() => {});
global.URLSearchParams = URLSearchParams;
const {electromobilityRowsForView, formatTableValue} = require("./web/app.js");
const rows = Array.from({length: 12}, (_, index) => ({
  country_code: index === 11 ? "UK" : `C${index}`,
  bev_stock: index === 11 ? null : index * 100,
  bev_new_registrations: index === 11 ? null : index * 10,
  ev_battery_nominal_capacity_est_gwh: index === 11 ? null : index * 0.006,
}));
const top = electromobilityRowsForView(rows, false, "bev_stock", -1, false);
const ascending = electromobilityRowsForView(rows, false, "bev_stock", 1, true);
process.stdout.write(JSON.stringify({
  topCodes: top.map(row => row.country_code),
  topLength: top.length,
  ascendingFirst: ascending[0].country_code,
  ascendingLast: ascending.at(-1).country_code,
  monthlyLength: electromobilityRowsForView(rows, true, "bev_stock", -1, true).length,
  ukValue: rows.at(-1).bev_stock,
  ukFormatted: formatTableValue(rows.at(-1).bev_stock, "bev_stock"),
}));
'''
        result = self.run_node(script)
        self.assertEqual(result["topLength"], 10)
        self.assertEqual(result["topCodes"][0], "C10")
        self.assertNotIn("UK", result["topCodes"])
        self.assertEqual(result["ascendingFirst"], "C0")
        self.assertEqual(result["ascendingLast"], "UK")
        self.assertEqual(result["monthlyLength"], 0)
        self.assertIsNone(result["ukValue"])
        self.assertIn("missing", result["ukFormatted"])

    def test_catalog_exposes_new_yearly_metrics_and_keeps_hydro_snapshot_only(self):
        metrics = {metric["id"]: metric for metric in metric_catalog()}
        yearly_metrics = {
            "renewable_per_capita_mwh",
            "wind_per_capita_mwh",
            "solar_per_capita_mwh",
            "hydro_per_capita_mwh",
            "bioenergy_per_capita_mwh",
            "other_renewables_per_capita_mwh",
            "fossil_per_capita_mwh",
            "coal_per_capita_mwh",
            "gas_per_capita_mwh",
            "other_fossil_per_capita_mwh",
            "nuclear_per_capita_mwh",
            "decarbonization_rate_pct",
            "eea_public_electricity_heat_emissions_mtco2eq",
            "capacity_total_gw",
            "household_electricity_price_eur_mwh",
            "gross_imports_twh",
            "bev_stock",
            "bev_new_registrations",
            "ev_battery_nominal_capacity_est_gwh",
            "generation_gdp_intensity_kwh_eur",
            "consumption_gdp_intensity_kwh_eur",
            "electricity_heat_emissions_gdp_t_million_eur",
            "household_wholesale_price_gap_ct_kwh",
            "electricity_trade_throughput_pct",
        }
        for metric_id in yearly_metrics:
            metric = metrics[metric_id]
            self.assertTrue(metric["map"])
            self.assertTrue(metric["compare"])
            self.assertTrue(metric["temporal_availability"]["yearly"])

        expected_placement = {
            "generation_gdp_intensity_kwh_eur": ("Stromsystem", "Erzeugung"),
            "consumption_gdp_intensity_kwh_eur": ("Stromsystem", "Verbrauch"),
            "electricity_heat_emissions_gdp_t_million_eur": ("Klima", "Inventaremissionen"),
            "household_wholesale_price_gap_ct_kwh": ("Endkundenpreise", "Haushaltsstrompreis"),
            "electricity_trade_throughput_pct": ("Handel", "Stromhandel"),
        }
        self.assertEqual(
            {
                metric_id: (metrics[metric_id]["group"], metrics[metric_id]["family"])
                for metric_id in expected_placement
            },
            expected_placement,
        )
        self.assertIn('metric.id.includes("_gdp_")', APP_PATH.read_text(encoding="utf-8"))
        for metric_id in (
            "hydro_plant_capacity_gw",
            "hydro_pumping_power_gw",
            "hydro_reservoir_energy_gwh",
        ):
            metric = metrics[metric_id]
            self.assertTrue(metric["map"])
            self.assertFalse(metric["compare"])
            self.assertTrue(metric["temporal_availability"]["snapshot"])

    def test_household_price_defaults_to_total_and_uses_cents_per_kwh(self):
        family = [
            metric
            for metric in metric_catalog()
            if metric["family"] == "Haushaltsstrompreis"
        ]
        self.assertEqual(family[0]["id"], "household_electricity_price_eur_mwh")
        self.assertEqual(family[0]["representation"], "Gesamtpreis (2.500–4.999 kWh/Jahr)")
        self.assertEqual({metric["unit"] for metric in family}, {"ct/kWh"})
        self.assertEqual(
            [metric["representation"] for metric in family[1:]],
            [
                "Energie und Vertrieb (Preisbestandteil)",
                "Netzentgelte (Preisbestandteil)",
                "Steuern, Abgaben und Umlagen (Preisbestandteil)",
                "Haushaltspreis minus Großhandelspreis",
            ],
        )

    def test_estimate_eea_hydro_and_derivation_definitions_are_visible(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        self.assertIn("Pauschale Flottenannahme:</strong> Theoretische nominale Batteriekapazität = BEV-Bestand × 60 kWh", html)
        self.assertIn("weder nutzbare Energie noch eine V2G- oder netzverfügbare Speicherkapazität", html)
        self.assertIn("Die Kategorie umfasst die öffentliche Strom- <strong>und Wärmeerzeugung</strong>", html)
        self.assertIn("JRC Hydro-power database", html)
        self.assertIn("Fehlende Speicherenergie wird weder aus Leistung noch aus anderen Anlagendaten geschätzt", html)
        self.assertIn("Positive Werte bedeuten sinkende, negative Werte steigende CO₂-Intensität", html)
        self.assertIn("Das Ergebnis ist eine rechnerische Schätzung und kein Treibhausgasinventar", html)

    def test_snapshot_context_uses_metric_specific_provenance_date(self):
        app = APP_PATH.read_text(encoding="utf-8")
        self.assertIn("row?.metric_provenance?.[metric.id]?.date || storageSnapshot", app)
        self.assertIn("const source = provenance?.source_label || metric.source", app)
        self.assertIn("const value = metricAvailable(metric) && row ? row[metric.id] : null", app)
        self.assertIn('filter(metric => metric.compare)', app)

    def test_capacity_map_uses_an_api_reported_year_without_renaming_net_capacity(self):
        app = APP_PATH.read_text(encoding="utf-8")
        metrics = {metric["id"]: metric for metric in metric_catalog()}
        self.assertIn("async function loadMapData", app)
        self.assertIn("/api/map-data?metric=", app)
        self.assertIn("function usesLatestAvailableMapYear(metric)", app)
        self.assertIn("metric?.map_config?.latest_available_year", app)
        self.assertIn("data_year", app)
        self.assertIn("kein Leistungsdatenstand verfügbar", app)
        self.assertIn("Keine Werte für den ausgewählten Datenstand verfügbar", app)
        self.assertNotIn("2024", app[app.index("function usesLatestAvailableMapYear"):app.index("function countryName")])
        for metric_id in (
            "capacity_total_gw", "capacity_wind_gw", "capacity_solar_gw", "capacity_hydro_gw",
            "capacity_fossil_gw", "capacity_nuclear_gw",
        ):
            self.assertEqual(metrics[metric_id]["unit"], "GW")
            self.assertNotIn("GWp", metrics[metric_id]["unit"])

    def test_storage_table_keeps_source_details_out_of_visible_value_cells(self):
        app = APP_PATH.read_text(encoding="utf-8")
        style = STYLE_PATH.read_text(encoding="utf-8")
        self.assertIn('return `<td title="${escapeAttribute(title)}">${formatTableValue(row[metricId], metricId)}</td>`;', app)
        self.assertNotIn("cell-provenance", app)
        self.assertNotIn(".cell-provenance", style)

    def test_table_headers_start_with_metrics_not_rank_or_country(self):
        app = APP_PATH.read_text(encoding="utf-8")
        self.assertIn("function leadingTableHeader", app)
        self.assertIn('colspan="2" class="table-leading-spacer"', app)
        self.assertNotIn("function countryHeader", app)
        self.assertNotIn("function rankHeader", app)


if __name__ == "__main__":
    unittest.main()
