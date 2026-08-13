import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from electricity_atlas.config import ATLAS_COUNTRIES, EMBER_ISO3
from electricity_atlas.metrics import metric_catalog


ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = ROOT / "web" / "assets" / "europe.svg"
FLAG_PATH = ROOT / "web" / "assets" / "flags"
APP_PATH = ROOT / "web" / "app.js"
INDEX_PATH = ROOT / "web" / "index.html"


def frontend_country_mapping():
    source = APP_PATH.read_text(encoding="utf-8")
    match = re.search(r"const NE_TO_ATLAS = (\{.*?\});", source, re.DOTALL)
    if not match:
        raise AssertionError("NE_TO_ATLAS mapping not found in web/app.js")
    return json.loads(match.group(1))


class MapAssetTests(unittest.TestCase):
    def test_all_atlas_countries_have_exactly_one_local_geometry(self):
        root = ET.parse(SVG_PATH).getroot()
        paths = root.findall(".//{http://www.w3.org/2000/svg}path")
        codes = [path.attrib["data-ne-code"] for path in paths]
        expected_iso3 = set(EMBER_ISO3.values())
        self.assertEqual(len(expected_iso3), 31)
        self.assertEqual({code for code in codes if code in expected_iso3}, expected_iso3)
        self.assertTrue(all(codes.count(code) == 1 for code in expected_iso3))
        self.assertEqual(len({path.attrib["data-ne-id"] for path in paths}), len(paths))

    def test_frontend_mapping_matches_catalog_including_uk_and_greece(self):
        mapping = frontend_country_mapping()
        self.assertEqual(mapping["GBR"], "UK")
        self.assertEqual(mapping["GRC"], "GR")
        self.assertEqual(mapping, {iso3: code for code, iso3 in EMBER_ISO3.items()})
        self.assertEqual(set(mapping.values()), set(ATLAS_COUNTRIES))

    def test_non_atlas_countries_remain_unmapped_background(self):
        root = ET.parse(SVG_PATH).getroot()
        codes = {path.attrib["data-ne-code"] for path in root.findall(".//{http://www.w3.org/2000/svg}path")}
        mapping = frontend_country_mapping()
        self.assertIn("ALB", codes)
        self.assertIn("RUS", codes)
        self.assertNotIn("ALB", mapping)
        self.assertNotIn("RUS", mapping)

    def test_asset_is_self_contained_and_documents_natural_earth_version(self):
        source = SVG_PATH.read_text(encoding="utf-8")
        self.assertIn("Natural Earth 1:50m Admin 0 Countries 5.1.1", source)
        self.assertNotRegex(source, r"<(?:image|script|use)\b")
        self.assertNotRegex(source, r"\b(?:href|src)=")


class MapCatalogAndUiContractTests(unittest.TestCase):
    def test_all_map_metrics_have_scale_and_temporal_metadata(self):
        metrics = metric_catalog()
        mapped = [metric for metric in metrics if metric["map"]]
        self.assertEqual(len(mapped), len(metrics))
        for metric in mapped:
            self.assertIn(metric["map_config"]["scale"], {"sequential", "diverging"})
            self.assertIn(metric["map_config"]["palette"], {"teal", "amber", "purple", "orange-purple"})
            self.assertIsInstance(metric["family"], str)
            self.assertIsInstance(metric["representation"], str)

    def test_hydro_variants_annual_limits_storage_snapshot_and_net_import_scale(self):
        metrics = {metric["id"]: metric for metric in metric_catalog()}
        hydro_twh = metrics["hydro_twh"]
        hydro_share = metrics["hydro_share_pct"]
        self.assertEqual(hydro_twh["family"], "Wasserkraft")
        self.assertEqual(hydro_share["family"], "Wasserkraft")
        self.assertNotEqual(hydro_twh["representation"], hydro_share["representation"])
        self.assertEqual(hydro_share["map_config"]["domain"], [0, 100])
        self.assertFalse(metrics["population"]["temporal_availability"]["monthly"])
        self.assertTrue(metrics["population"]["temporal_availability"]["yearly"])
        self.assertTrue(metrics["battery_power_gw"]["temporal_availability"]["snapshot"])
        self.assertTrue(metrics["pumped_storage_energy_gwh"]["temporal_availability"]["snapshot"])
        self.assertNotIn("storage_power_gw", metrics)
        self.assertEqual(metrics["net_imports_twh"]["map_config"]["scale"], "diverging")
        self.assertEqual(metrics["net_imports_twh"]["map_config"]["midpoint"], 0)

    def test_page_order_and_runtime_catalog_driven_selection(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        self.assertLess(html.index('id="atlas-map-section"'), html.index('id="summary-table"'))
        self.assertLess(html.index('id="summary-table"'), html.index('id="comparison"'))
        self.assertLess(html.index('id="comparison"'), html.index('id="storage"'))
        self.assertLess(html.index('id="storage"'), html.index('class="source-details"'))
        app = APP_PATH.read_text(encoding="utf-8")
        self.assertIn("filter(metric => metric.map)", app)
        self.assertIn('fetch("/assets/europe.svg")', app)
        external_fetches = re.findall(r"fetch\((['\"])(.*?)\1", app)
        self.assertTrue(all(url.startswith("/") for _, url in external_fetches))

    def test_timeseries_ui_replaces_placeholder_table_and_uses_local_flags(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        app = APP_PATH.read_text(encoding="utf-8")
        self.assertIn('id="timeseries-chart"', html)
        self.assertIn('id="ranking-list"', html)
        self.assertNotIn('id="compare-table"', html)
        self.assertIn("/api/timeseries?", app)
        self.assertIn("buildComparisonCsv", app)
        self.assertIn("history.replaceState", app)
        self.assertIn("prefers-reduced-motion", (ROOT / "web" / "style.css").read_text(encoding="utf-8"))
        expected = {("gb" if code == "UK" else code.lower()) + ".svg" for code in ATLAS_COUNTRIES}
        actual = {path.name for path in FLAG_PATH.glob("*.svg")}
        self.assertEqual(actual, expected)
        self.assertTrue((FLAG_PATH / "LICENSE.flag-icons.txt").is_file())


if __name__ == "__main__":
    unittest.main()
