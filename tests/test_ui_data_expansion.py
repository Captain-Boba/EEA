import json
import os
import shutil
import re
import subprocess
import unittest
from pathlib import Path

from electricity_atlas.metrics import metric_catalog


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "web" / "app.js"
INDEX_PATH = ROOT / "web" / "index.html"
STYLE_PATH = ROOT / "web" / "style.css"
NODE = Path(os.environ.get("EEA_NODE") or shutil.which("node") or "")


class DataExpansionUiTests(unittest.TestCase):
    def run_node(self, script):
        if not NODE.is_file():
            self.skipTest("Bundled Node runtime is unavailable")
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
            "decarbonization_rate_pct",
            "eea_public_electricity_heat_emissions_mtco2eq",
            "capacity_total_gw",
            "household_electricity_price_eur_mwh",
            "gross_imports_twh",
            "bev_stock",
            "bev_new_registrations",
            "ev_battery_nominal_capacity_est_gwh",
        }
        for metric_id in yearly_metrics:
            metric = metrics[metric_id]
            self.assertTrue(metric["map"])
            self.assertTrue(metric["compare"])
            self.assertTrue(metric["temporal_availability"]["yearly"])
        for metric_id in (
            "hydro_plant_capacity_gw",
            "hydro_pumping_power_gw",
            "hydro_reservoir_energy_gwh",
        ):
            metric = metrics[metric_id]
            self.assertTrue(metric["map"])
            self.assertFalse(metric["compare"])
            self.assertTrue(metric["temporal_availability"]["snapshot"])

    def test_estimate_eea_hydro_and_derivation_definitions_are_visible(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        self.assertIn("Theoretische nominale Batteriekapazität = BEV-Bestand × 60 kWh", html)
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


if __name__ == "__main__":
    unittest.main()
