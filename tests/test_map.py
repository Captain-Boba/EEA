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
STYLE_PATH = ROOT / "web" / "style.css"
LOGO_PATH = ROOT / "web" / "assets" / "eea-mark.svg"
EUROPE_STAR_PATH = ROOT / "web" / "assets" / "europe-star.svg"


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
    def test_midnight_grid_logo_is_local_and_self_contained(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        logo = LOGO_PATH.read_text(encoding="utf-8")
        ET.fromstring(logo)
        self.assertIn('href="/assets/eea-mark.svg"', html)
        self.assertIn('src="/assets/eea-mark.svg"', html)
        self.assertNotRegex(logo, r"(?:href|src)=\"https?://")
        self.assertNotRegex(logo, r"<(?:image|script)\b")

    def test_europe_night_clear_action_is_local_and_wired(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        app = APP_PATH.read_text(encoding="utf-8")
        style = STYLE_PATH.read_text(encoding="utf-8")
        icon = EUROPE_STAR_PATH.read_text(encoding="utf-8")
        ET.fromstring(icon)
        self.assertIn('id="clear-selection"', html)
        self.assertIn('/assets/europe-star.svg', html)
        self.assertNotIn('/assets/europe-star-x.svg', html)
        self.assertNotRegex(icon, r"(?:href|src)=\"https?://")
        self.assertIn("function clearSelection", app)
        self.assertIn("selected.clear()", app)
        self.assertIn('$("clear-selection").addEventListener("click", clearSelection)', app)
        self.assertIn("--europe-night: #070d18", style)
        self.assertIn("--europe-gold: #b89a5a", style)
        self.assertIn("--signal: #ffffff", style)
        self.assertIn('--font-display: Calibri, "Segoe UI", sans-serif', style)
        self.assertIn('--font-ui: Calibri, "Segoe UI", sans-serif', style)
        self.assertNotIn("Palatino Linotype", style)
        self.assertNotIn('"Aptos"', style)
        self.assertIn('font-family:Calibri,"Segoe UI",sans-serif', app)
        self.assertIn("--glass-menu: rgba(20, 31, 48, .68)", style)
        self.assertIn("--glass-border: rgba(82, 101, 122, .74)", style)
        self.assertIn("backdrop-filter: blur(26px) saturate(150%)", style)
        self.assertIn('fill="#ffffff"', icon)
        self.assertEqual(icon.count("<path"), 1)

    def test_header_keeps_only_logo_and_atlas_name(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        header = re.search(r'<header class="site-header">(.*?)</header>', html, re.DOTALL)
        self.assertIsNotNone(header)
        markup = header.group(1)
        self.assertIn('<h1>European Electricity Atlas</h1>', markup)
        self.assertIn('/assets/eea-mark.svg', markup)
        self.assertNotIn("European data infrastructure", markup)
        self.assertNotIn("Vergleichbare Stromdaten", markup)
        self.assertNotIn("Data core online", markup)

    def test_sticky_controls_and_accessible_hidden_selection_heading(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        app = APP_PATH.read_text(encoding="utf-8")
        style = STYLE_PATH.read_text(encoding="utf-8")
        self.assertRegex(style, r"\.controls\s*\{[^}]*position:\s*sticky")
        self.assertRegex(style, r"\.controls\s*\{[^}]*z-index:\s*60")
        self.assertNotIn('<th scope="col">Auswahl</th>', app)
        self.assertIn("Länder für den Zeitreihenvergleich auswählen", app)
        self.assertIn('class="sr-only"', app)
        self.assertIn('aria-label="Zeitraum"', html)

    def test_map_fullscreen_exports_and_info_panels_are_wired(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        app = APP_PATH.read_text(encoding="utf-8")
        style = STYLE_PATH.read_text(encoding="utf-8")
        for element_id in ("map-stage", "map-fullscreen", "map-export-svg", "map-export-png"):
            self.assertIn(f'id="{element_id}"', html)
        self.assertLess(html.index('id="map-stage"'), html.index('id="map-family"'))
        self.assertLess(html.index('id="map-family"'), html.index('class="map-layout"'))
        self.assertIn('id="map-values" type="checkbox" checked', html)
        self.assertIn("#map-fullscreen", style)
        self.assertIn("#comparison-fullscreen", style)
        self.assertIn("--signal: #ffffff", style)
        self.assertIn("requestFullscreen", app)
        self.assertIn("serializedMapSvg", app)
        self.assertIn("buildMapPngBlob", app)
        self.assertIn('"Legende"', app)
        self.assertNotIn('querySelector("#map-tooltip")', app)
        self.assertIn('data-info-target="map-info"', html)
        self.assertIn('aria-expanded="false"', html)
        self.assertIn("closeInfoPanel", app)

    def test_motion_contract_preserves_reduced_motion_and_v2_structure(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        app = APP_PATH.read_text(encoding="utf-8")
        style = STYLE_PATH.read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion", style)
        self.assertIn("motionAllowed", app)
        self.assertIn("animateRowReorder", app)
        self.assertIn("animateChartNextRender", app)
        self.assertIn('id="timeseries-chart"', html)
        self.assertIn('id="ranking-list"', html)
        self.assertIn('id="comparison-fullscreen"', html)
        self.assertIn("relativeBaselineChange", app)

    def test_all_map_metrics_have_scale_and_temporal_metadata(self):
        metrics = metric_catalog()
        mapped = [metric for metric in metrics if metric["map"]]
        palettes = {
            "generation", "consumption", "renewables", "wind", "solar", "hydro",
            "bioenergy", "other-renewables", "fossil", "coal", "gas", "other-fossil",
            "nuclear", "trade", "price", "carbon", "population", "gdp",
            "gdp-per-capita", "battery", "pumped-storage",
        }
        self.assertEqual(len(mapped), len(metrics))
        for metric in mapped:
            self.assertIn(metric["map_config"]["scale"], {"sequential", "diverging"})
            self.assertIn(metric["map_config"]["palette"], palettes)
            self.assertIsInstance(metric["family"], str)
            self.assertIsInstance(metric["representation"], str)
        family_palettes = {}
        for metric in mapped:
            family_palettes.setdefault(metric["family"], set()).add(metric["map_config"]["palette"])
        self.assertTrue(all(len(value) == 1 for value in family_palettes.values()))
        self.assertEqual(len(family_palettes), 21)
        self.assertEqual({metric["map_config"]["palette"] for metric in mapped}, palettes)
        app = APP_PATH.read_text(encoding="utf-8")
        palette_block = re.search(r"const MAP_PALETTES = \{(.*?)\n\};", app, re.DOTALL)
        self.assertIsNotNone(palette_block)
        for palette in palettes:
            self.assertRegex(palette_block.group(1), rf'(?:^|\n)\s*(?:"{re.escape(palette)}"|{re.escape(palette)}):\s*\[')
        self.assertIn("const MAP_PALETTE_BY_FAMILY", app)
        self.assertIn("function mapPaletteName(metric)", app)
        self.assertIn("MAP_PALETTE_BY_FAMILY[metric?.family]", app)
        self.assertIn("paletteColor(mapPaletteName(metric), position)", app)

    def test_hydro_variants_annual_limits_storage_snapshot_and_net_import_scale(self):
        metrics = {metric["id"]: metric for metric in metric_catalog()}
        hydro_twh = metrics["hydro_twh"]
        hydro_share = metrics["hydro_share_pct"]
        self.assertEqual(hydro_twh["family"], "Wasserkraft")
        self.assertEqual(hydro_share["family"], "Wasserkraft")
        self.assertNotEqual(hydro_twh["representation"], hydro_share["representation"])
        self.assertIsNone(hydro_share["map_config"]["domain"])
        self.assertFalse(metrics["population"]["temporal_availability"]["monthly"])
        self.assertTrue(metrics["population"]["temporal_availability"]["yearly"])
        self.assertTrue(metrics["battery_power_gw"]["temporal_availability"]["snapshot"])
        self.assertTrue(metrics["pumped_storage_energy_gwh"]["temporal_availability"]["snapshot"])
        self.assertNotIn("storage_power_gw", metrics)
        self.assertEqual(metrics["net_imports_twh"]["map_config"]["scale"], "diverging")
        self.assertEqual(metrics["net_imports_twh"]["map_config"]["midpoint"], 0)
        app = APP_PATH.read_text(encoding="utf-8")
        self.assertIn("function mapScalePosition(value, metric, scale)", app)
        self.assertIn("const min = Math.min(...finite), max = Math.max(...finite)", app)
        self.assertNotIn("Math.max(Math.abs(min - midpoint)", app)
        self.assertNotIn("Array.isArray(config.domain)", app)

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

    def test_both_data_tables_use_collapsible_top_ten_rankings(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        app = APP_PATH.read_text(encoding="utf-8")
        style = STYLE_PATH.read_text(encoding="utf-8")
        for table in ("summary", "storage"):
            self.assertIn(f'id="{table}-toggle"', html)
            self.assertIn(f'aria-controls="{table}-table-region"', html)
            self.assertIn(f'id="{table}-count"', html)
            self.assertIn(f'id="{table}-table-state"', html)
            self.assertLess(html.index(f'id="{table}-table-region"'), html.index(f'id="{table}-toggle"'))
        self.assertIn("const TABLE_PREVIEW_LIMIT = 10", app)
        self.assertIn("sorted.slice(0, TABLE_PREVIEW_LIMIT)", app)
        self.assertIn('updateTableDisclosure("summary"', app)
        self.assertIn('updateTableDisclosure("storage"', app)
        self.assertIn("summaryExpanded = !summaryExpanded", app)
        self.assertIn("storageExpanded = !storageExpanded", app)
        self.assertIn(".table-card", style)
        self.assertIn(".table-rank", style)
        self.assertIn(".table-edge-toggle", style)
        self.assertIn(".table-card tbody td { color: #f7f5f0; font-size: .98rem", style)

    def test_timeseries_ui_replaces_placeholder_table_and_uses_local_flags(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        app = APP_PATH.read_text(encoding="utf-8")
        self.assertIn('id="timeseries-chart"', html)
        self.assertIn('id="ranking-list"', html)
        self.assertIn('id="comparison-fullscreen"', html)
        self.assertLess(html.index('id="comparison-stage"'), html.index('id="comparison-controls"'))
        self.assertLess(html.index('id="comparison-controls"'), html.index('id="comparison-layout"'))
        self.assertNotIn('id="compare-table"', html)
        self.assertIn("/api/timeseries?", app)
        self.assertIn("buildComparisonCsv", app)
        self.assertIn("history.replaceState", app)
        self.assertIn("requestFullscreen", app)
        self.assertNotIn("chartHoverCountry", app)
        self.assertNotIn(')} pp`', app)
        self.assertIn("prefers-reduced-motion", (ROOT / "web" / "style.css").read_text(encoding="utf-8"))
        expected = {("gb" if code == "UK" else code.lower()) + ".svg" for code in ATLAS_COUNTRIES}
        actual = {path.name for path in FLAG_PATH.glob("*.svg")}
        self.assertEqual(actual, expected)
        self.assertTrue((FLAG_PATH / "LICENSE.flag-icons.txt").is_file())


if __name__ == "__main__":
    unittest.main()
