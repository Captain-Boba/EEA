from pathlib import Path
import unittest

from electricity_atlas.country_profile import build_country_profile
from electricity_atlas.db import connect, initialize
from electricity_atlas.metrics import metric_catalog


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
STYLE = (ROOT / "web" / "style.css").read_text(encoding="utf-8")
LABELING_DOC = (ROOT / "docs" / "METRIC_LABELING.md").read_text(encoding="utf-8")


class MetricLabelingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = {metric["id"]: metric for metric in metric_catalog()}

    def test_every_map_and_compare_metric_has_three_nonempty_display_levels(self):
        visible = [
            metric for metric in self.catalog.values()
            if metric["map"] or metric["compare"]
        ]
        self.assertEqual(len(visible), len(self.catalog))
        for metric in visible:
            with self.subTest(metric=metric["id"]):
                for key in ("display_topic", "display_metric", "display_basis"):
                    self.assertIsInstance(metric[key], str)
                    self.assertTrue(metric[key].strip())

    def test_required_label_examples_are_exact(self):
        expected = {
            "low_carbon_share_pct": (
                "CO₂-arme Erzeugung", "Erneuerbare und Kernenergie", "Anteil in % an der Gesamterzeugung",
            ),
            "generation_twh": ("Stromerzeugung", "Erzeugung absolut", "in TWh"),
            "carbon_intensity_gco2eq_kwh": (
                "Emissionen der Stromerzeugung", "CO₂-Intensität", "in gCO₂eq/kWh",
            ),
            "battery_energy_gwh": ("Batteriespeicher", "Installierte Speicherkapazität", "in GWh"),
            "battery_power_gw": ("Batteriespeicher", "Installierte Entladeleistung", "in GW"),
            "price_avg_eur_mwh": (
                "Großhandelsstrompreis", "Durchschnittlicher Day-Ahead-Preis", "in EUR/MWh",
            ),
        }
        for metric_id, labels in expected.items():
            metric = self.catalog[metric_id]
            self.assertEqual(
                (metric["display_topic"], metric["display_metric"], metric["display_basis"]),
                labels,
            )

    def test_basis_lines_do_not_append_a_duplicate_unit(self):
        for metric in self.catalog.values():
            with self.subTest(metric=metric["id"]):
                basis = metric["display_basis"]
                self.assertNotIn(" · in " + metric["unit"] + " · in " + metric["unit"], basis)
                self.assertNotRegex(basis, r"\bin (?:TWh|GW|GWh|EUR/MWh)\b.*\bin (?:TWh|GW|GWh|EUR/MWh)\b")

    def test_country_profile_returns_the_catalog_display_contract(self):
        connection = connect(":memory:")
        self.addCleanup(connection.close)
        initialize(connection)
        profile = build_country_profile(connection, "DE", 2025)
        profile_metrics = {
            metric["id"]
            for section in profile["sections"]
            for metric in section["metrics"]
        }
        self.assertEqual(profile_metrics, set(self.catalog))
        generation = next(
            metric for section in profile["sections"] for metric in section["metrics"]
            if metric["id"] == "generation_twh"
        )
        self.assertEqual(generation["display_topic"], "Stromerzeugung")
        self.assertEqual(generation["display_metric"], "Erzeugung absolut")
        self.assertEqual(generation["display_basis"], "in TWh")

    def test_frontend_and_exports_use_the_shared_display_helpers(self):
        self.assertIn("function metricLabels(metric)", APP)
        self.assertIn("function compactMetricLabel(metric)", APP)
        self.assertIn("function metricLabelHtml(metric", APP)
        self.assertIn('$("map-metric-title").innerHTML = metricLabelHtml(metric);', APP)
        self.assertIn('svgElement("text", {class: "chart-title", x: geometry.left, y: 30}, labels.topic)', APP)
        self.assertIn('svgElement("text", {class: "chart-period", x: geometry.left, y: 71}', APP)
        self.assertIn("const labels = metricLabels(metric);\n  root.appendChild", APP)
        self.assertIn("const labels = metricLabels(metric);\n  const source", APP)
        self.assertIn("compactMetricLabel(metric)", APP)

    def test_generation_technology_labels_do_not_repeat_the_category(self):
        expected = {
            "nuclear_twh": ("Kernenergie", "Erzeugung absolut", "in TWh"),
            "nuclear_share_pct": ("Kernenergie", "Anteil", "in % an der Gesamterzeugung"),
            "renewable_per_capita_mwh": (
                "Erneuerbare gesamt", "Erzeugung pro Kopf", "in MWh je Einwohner",
            ),
        }
        for metric_id, labels in expected.items():
            metric = self.catalog[metric_id]
            self.assertEqual(
                (metric["display_topic"], metric["display_metric"], metric["display_basis"]), labels,
            )

    def test_selectors_and_map_panel_use_the_same_three_level_labels(self):
        self.assertIn('return `${metric.group}::${metricLabels(metric).topic}`;', APP)
        self.assertIn('escapeHtml(metricLabels(variants[0]).topic)', APP)
        map_label_styles = STYLE[STYLE.index(".metric-label-topic"):STYLE.index(".map-legend")]
        self.assertNotIn("text-transform: uppercase;", map_label_styles)
        self.assertIn(".metric-label-metric,\n.metric-label-basis", STYLE)

    def test_document_matrix_covers_the_entire_catalog(self):
        documented = {}
        for line in LABELING_DOC.splitlines():
            if not line.startswith("| `"):
                continue
            columns = [column.strip() for column in line.strip("|").split("|")]
            metric_id = columns[0].strip("`")
            if metric_id in self.catalog:
                documented[metric_id] = tuple(columns[1:4])
        self.assertEqual(set(documented), set(self.catalog))
        for metric_id, metric in self.catalog.items():
            with self.subTest(metric=metric_id):
                self.assertEqual(
                    documented[metric_id],
                    (metric["display_topic"], metric["display_metric"], metric["display_basis"]),
                )

    def test_metric_ids_and_direct_link_contract_remain_stable(self):
        self.assertEqual(len(self.catalog), len(set(self.catalog)))
        self.assertIn("function mapUrlState()", APP)
        self.assertIn("function parseComparisonUrl", APP)
        self.assertIn('url.searchParams.set("map_metric", metric.id);', APP)
        self.assertIn("function comparisonQuery()", APP)
        comparison_query = APP[APP.index("function comparisonQuery()"):APP.index("function mapUrlState()")]
        self.assertIn('metric: $("compare-metric").value,', comparison_query)
