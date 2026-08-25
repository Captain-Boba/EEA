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
    def test_map_asset_has_no_native_hover_title(self):
        source = SVG_PATH.read_text(encoding="utf-8")
        self.assertNotIn("<title", source)
        self.assertNotIn("Europäische Länderkarte", source)
        self.assertIn('aria-label="Karte der europäischen Länder"', source)

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
        self.assertIn("--glass-menu: rgba(255, 255, 255, .035)", style)
        self.assertIn("--glass-border: rgba(220, 232, 242, .24)", style)
        self.assertIn("backdrop-filter: blur(24px) saturate(145%)", style)
        self.assertIn('fill="#b89a5a"', icon)
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

    def test_successful_summary_status_keeps_its_layout_space_without_copy(self):
        app = APP_PATH.read_text(encoding="utf-8")
        style = STYLE_PATH.read_text(encoding="utf-8")
        self.assertIn('const hasSummaryValues = data.some(', app)
        self.assertIn('$("status").textContent = hasSummaryValues ? "" : `Noch keine Daten importiert.${periodNote}`;', app)
        self.assertNotIn('`Atlas-Daten geladen.${periodNote}`', app)
        self.assertIn("#status:empty { min-height: 1lh; }", style)

    def test_header_adds_the_opt_in_overload_toggle_and_short_dynamic_title(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        app = APP_PATH.read_text(encoding="utf-8")
        self.assertIn("<title>EEA</title>", html)
        self.assertIn('id="europe-overload"', html)
        self.assertIn('aria-pressed="false"', html)
        self.assertIn("const TITLE_BY_SECTION", app)
        for title in ("EEA · Karte", "EEA · Zeitvergleich", "EEA · Stromsysteme", "EEA · E-Mobilität", "EEA · Speicher", "EEA · Quellen"):
            self.assertIn(title, app)
        self.assertIn("new IntersectionObserver", app)
        self.assertIn('window.addEventListener("scroll", scheduleDynamicDocumentTitle, {passive: true});', app)
        self.assertIn("requestAnimationFrame", app)
        self.assertIn('setDocumentTitle("map")', app)
        self.assertIn('setDocumentTitle("comparison")', app)
        self.assertIn("await loadTimeseries({scroll: false, updateUrl: false});\n  setDocumentTitle(\"comparison\");", app)
        self.assertIn("updateDynamicDocumentTitle();", app)

    def test_sticky_controls_and_accessible_hidden_selection_heading(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        app = APP_PATH.read_text(encoding="utf-8")
        style = STYLE_PATH.read_text(encoding="utf-8")
        self.assertRegex(style, r"\.controls\s*\{[^}]*position:\s*sticky")
        self.assertRegex(style, r"\.controls\s*\{[^}]*z-index:\s*60")
        self.assertNotIn('<th scope="col">Auswahl</th>', app)
        self.assertIn('class="sr-only"', app)
        self.assertIn('aria-label="Zeitraum"', html)

    def test_expanded_table_headers_follow_controls_header(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        app = APP_PATH.read_text(encoding="utf-8")
        style = STYLE_PATH.read_text(encoding="utf-8")
        self.assertIn("table-card.table-card-expanded thead th", style)
        self.assertIn("top: var(--atlas-controls-height)", style)
        self.assertIn(".table-card:not(.table-card-expanded) thead th", style)
        self.assertIn("position: static;", style)
        self.assertIn(".table-card.table-card-expanded .table-wrap", style)
        self.assertIn("overflow: visible", style)
        self.assertIn("syncStickyHeaderOffset", app)
        self.assertIn("function tableHeaderText(value)", app)
        self.assertNotIn('<th scope="col">Auswahl</th>', app)
        self.assertIn("Länder für den Zeitvergleich auswählen", app)
        self.assertIn('class="sr-only"', app)
        self.assertIn('aria-label="Zeitraum"', html)

    def test_map_fullscreen_exports_are_wired_without_a_map_help_popover(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        app = APP_PATH.read_text(encoding="utf-8")
        style = STYLE_PATH.read_text(encoding="utf-8")
        for element_id in ("map-stage", "map-fullscreen", "map-export-svg", "map-export-png", "map-copy-link"):
            self.assertIn(f'id="{element_id}"', html)
        self.assertLess(html.index('id="map-stage"'), html.index('id="map-family"'))
        self.assertLess(html.index('id="map-family"'), html.index('class="map-layout"'))
        self.assertIn('id="map-values" type="checkbox" checked', html)
        self.assertIn('<header class="tool-card-header">', html)
        self.assertLess(html.index('class="tool-card-header"'), html.index('id="map-stage"'))
        self.assertLess(html.index('id="comparison-title"'), html.index('id="comparison-stage"'))
        self.assertIn('Länder vergleichen (<span id="selected-count">0</span>)', html)
        self.assertIn('<h2 id="comparison-title">Zeitvergleich</h2>', html)
        self.assertIn('aria-label="Zeitvergleich steuern"', html)
        self.assertIn("Im Zeitvergleich öffnen", app)
        self.assertIn("Maximal zehn Länder können gleichzeitig im Zeitvergleich ausgewählt werden.", app)
        self.assertIn('border-radius: .9rem;', style)
        self.assertIn("#map-fullscreen", style)
        self.assertIn("#comparison-fullscreen", style)
        self.assertIn("--signal: #ffffff", style)
        self.assertIn("requestFullscreen", app)
        self.assertIn("serializedMapSvg", app)
        self.assertIn("buildMapPngBlob", app)
        self.assertIn("appendExportBranding(root, metric", app)
        self.assertIn("return rasterizeExportSvg(await serializedMapSvg());", app)
        self.assertIn("await inlineSvgImages(root);", app)
        self.assertIn("function appendMapExportSummary", app)
        self.assertIn('appendMapExportSummary(root, summaryX, summaryY, summaryWidth, "Minimum"', app)
        self.assertIn('appendMapExportSummary(root, summaryX, summaryY + 52, summaryWidth, "Maximum"', app)
        self.assertIn('appendMapExportSummary(root, summaryX, summaryY + 104, summaryWidth, "Atlas-Durchschnitt"', app)

        self.assertIn('"Legende"', app)
        self.assertNotIn('querySelector("#map-tooltip")', app)
        self.assertNotIn('data-info-target="map-info"', html)
        self.assertNotIn('id="map-info"', html)
        self.assertNotIn('data-info-target="comparison-info"', html)
        self.assertNotIn('id="comparison-info"', html)
        self.assertIn(".comparison-presets button.active:hover:not(:disabled)", style)
        self.assertIn("closeInfoPanel", app)

    def test_map_direct_link_captures_and_restores_current_map_state(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        app = APP_PATH.read_text(encoding="utf-8")
        self.assertIn('id="map-copy-link"', html)
        self.assertIn("function mapUrlState()", app)
        self.assertIn("function writeMapUrl()", app)
        self.assertIn("async function restoreMapState()", app)
        for parameter in ("view", "year", "period", "map_metric", "map_values"):
            self.assertIn(f'url.searchParams.set("{parameter}"', app)
        self.assertIn('url.searchParams.set("country", focusedMapCountry);', app)
        self.assertIn('await navigator.clipboard.writeText(url);', app)
        self.assertIn('if (await restoreMapState()) return;', app)
        self.assertIn("focusMapCountry(path, false);", app)

    def test_comparison_fullscreen_uses_one_chart_surface(self):
        style = STYLE_PATH.read_text(encoding="utf-8")
        self.assertIn(".comparison-stage:fullscreen .chart-panel,", style)
        self.assertIn(".comparison-stage:fullscreen .chart-background { fill: #081a2c; }", style)
        self.assertIn("background: #081a2c;", style)

    def test_clicking_map_water_clears_the_country_focus(self):
        app = APP_PATH.read_text(encoding="utf-8")
        self.assertIn("function clearMapCountryFocus(syncUrl = true)", app)
        self.assertIn('mapSvg.addEventListener("click", event => {', app)
        self.assertIn('event.target.closest?.(".map-country")', app)
        self.assertIn('$("map-detail").textContent = "Ein Land fokussieren, um Details anzuzeigen.";', app)

    def test_compact_map_labels_keep_two_decimal_places_for_millions(self):
        app = APP_PATH.read_text(encoding="utf-8")
        self.assertIn("compact && Math.abs(value) >= 1_000_000", app)
        self.assertIn("value / 1_000_000", app)
        self.assertIn("minimumFractionDigits: 2", app)
        self.assertIn("maximumFractionDigits: 2", app)
        self.assertIn("Mio.", app)

    def test_map_legend_includes_country_extremes_and_atlas_average(self):
        app = APP_PATH.read_text(encoding="utf-8")
        style = STYLE_PATH.read_text(encoding="utf-8")
        self.assertIn("function mapLegendSummaries(metric)", app)
        self.assertIn('mapLegendCountrySummary("Minimum", summaries.minimum, metric)', app)
        self.assertIn('mapLegendCountrySummary("Maximum", summaries.maximum, metric)', app)
        self.assertIn("Atlas-Durchschnitt", app)
        self.assertIn("map-legend-summary", style)

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
        self.assertIn('id="ranking-footnotes"', html)
        self.assertIn('id="comparison-fullscreen"', html)
        self.assertIn("relativeBaselineChange", app)
        self.assertIn("comparisonBaselinePoint", app)
        self.assertIn("comparisonBaselineYear", app)
        self.assertIn("chartIndexFromClientX", app)
        self.assertIn("rankingFallbackDetails", app)
        self.assertIn("latestCompleteComparisonIndex", app)
        self.assertIn("latestCompleteComparisonPeriod", app)
        self.assertIn("Veränderung gegenüber demselben Kalendermonat ${baselineYear}", app)
        self.assertNotIn("RANGE_BASELINE_FALLBACK_COUNTRIES", app)
        self.assertNotIn("getScreenCTM", app)
        self.assertIn("const SHOW_RANKING_DATA_QUALITY_NOTICES = false", app)
        self.assertIn('country.values.some(point => !Number.isFinite(point.value))', app)
        self.assertIn('class="ranking-fallback-marker"', app)
        self.assertIn('class="ranking-footnote-star"', app)
        self.assertIn(".ranking-footnotes", style)
        self.assertIn(".ranking-footnote-star { color: var(--europe-gold)", style)

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
        self.assertEqual(len(family_palettes), 31)
        self.assertTrue({
            "CO₂-arme Erzeugung", "Eigenversorgung", "Erzeugungsemissionen",
            "Inventaremissionen", "Installierte Leistung", "Haushaltsstrompreis",
            "Nicht-Haushaltsstrompreis", "Stromhandel", "Batterieelektrische Pkw",
            "Wasserkraftinventar",
        }.issubset(family_palettes))
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
        self.assertIn('generation: ["#cadbf0"', app)
        self.assertIn('renewables: ["#c6e0c8"', app)
        self.assertIn('trade: ["#2a6fbb", "#80b1d3", "#d8e3ed"', app)
        self.assertIn('class="table-header-copy"', app)
        self.assertIn("function fitTableHeaderText(headId)", app)
        self.assertIn("fitTableHeaderText(\"summary-head\")", app)
        self.assertIn("transform: scaleX(var(--header-text-scale))", STYLE_PATH.read_text(encoding="utf-8"))

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

    def test_renewables_are_a_single_family_with_three_catalog_variants(self):
        metrics = metric_catalog()
        renewable_total = [metric for metric in metrics if metric["family"] == "Erneuerbare gesamt"]
        self.assertEqual(
            {(metric["id"], metric["group"], metric["representation"]) for metric in renewable_total},
            {
                ("renewable_twh", "Erneuerbare", "Erzeugung in TWh"),
                ("renewable_share_pct", "Erneuerbare", "Anteil an der Gesamterzeugung"),
                ("renewable_per_capita_mwh", "Erneuerbare", "Erzeugung in MWh je Einwohner"),
            },
        )
        per_capita = next(metric for metric in renewable_total if metric["id"] == "renewable_per_capita_mwh")
        self.assertFalse(per_capita["temporal_availability"]["monthly"])
        self.assertTrue(per_capita["temporal_availability"]["yearly"])
        app = APP_PATH.read_text(encoding="utf-8")
        self.assertIn('return `${metric.group}::${metricLabels(metric).topic}`;', app)
        self.assertIn("renderComparisonMetricOptions", app)

    def test_each_generation_source_family_has_per_capita_as_third_variant(self):
        expected = {
            ("Erneuerbare", "Erneuerbare gesamt"): "renewable",
            ("Erneuerbare", "Wind"): "wind",
            ("Erneuerbare", "Solar"): "solar",
            ("Erneuerbare", "Wasserkraft"): "hydro",
            ("Erneuerbare", "Bioenergie"): "bioenergy",
            ("Erneuerbare", "Sonstige Erneuerbare"): "other_renewables",
            ("Fossile", "Fossile gesamt"): "fossil",
            ("Fossile", "Kohle"): "coal",
            ("Fossile", "Gas"): "gas",
            ("Fossile", "Sonstige Fossile"): "other_fossil",
            ("Kernenergie", "Kernenergie"): "nuclear",
        }
        catalog = metric_catalog()
        for (group, family), prefix in expected.items():
            variants = [
                metric for metric in catalog
                if metric["group"] == group and metric["family"] == family
            ]
            self.assertEqual(
                [metric["id"] for metric in variants],
                [f"{prefix}_twh", f"{prefix}_share_pct", f"{prefix}_per_capita_mwh"],
            )
            self.assertEqual(
                [metric["representation"] for metric in variants],
                ["Erzeugung in TWh", "Anteil an der Gesamterzeugung", "Erzeugung in MWh je Einwohner"],
            )
            self.assertFalse(variants[2]["temporal_availability"]["monthly"])
            self.assertTrue(variants[2]["temporal_availability"]["yearly"])

    def test_page_order_and_runtime_catalog_driven_selection(self):
        html = INDEX_PATH.read_text(encoding="utf-8")
        self.assertLess(html.index('id="atlas-map-section"'), html.index('id="comparison"'))
        self.assertLess(html.index('id="comparison"'), html.index('id="summary-table"'))
        self.assertLess(html.index('id="summary-table"'), html.index('id="storage"'))
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
            self.assertNotIn(f'id="{table}-count"', html)
            self.assertNotIn(f'id="{table}-table-state"', html)
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
        self.assertIn('id="comparison-presets"', html)
        self.assertIn('<section id="comparison" aria-labelledby="comparison-title">', html)
        self.assertNotIn('id="compare-load"', html)
        for preset in ("ytd", "1y", "3y", "5y", "10y", "max"):
            self.assertIn(f'data-range-preset="{preset}"', html)
        self.assertLess(html.index('id="comparison-stage"'), html.index('id="comparison-controls"'))
        self.assertLess(html.index('id="comparison-controls"'), html.index('id="comparison-layout"'))
        self.assertNotIn('id="compare-table"', html)
        self.assertIn("/api/timeseries?", app)
        self.assertIn("buildComparisonCsv", app)
        self.assertIn("history.replaceState", app)
        self.assertIn('const DEFAULT_COMPARISON_METRIC = "low_carbon_share_pct"', app)
        self.assertIn('const DEFAULT_COMPARISON_COUNTRIES = ["FR", "DE", "ES", "UK", "IT"]', app)
        self.assertIn("async function initializeDefaultComparison()", app)
        self.assertIn('$(id).addEventListener("change", () => loadTimeseries', app)
        self.assertIn("requestFullscreen", app)
        self.assertNotIn("chartHoverCountry", app)
        self.assertNotIn(')} pp`', app)
        self.assertIn("prefers-reduced-motion", (ROOT / "web" / "style.css").read_text(encoding="utf-8"))
        expected = {("gb" if code == "UK" else code.lower()) + ".svg" for code in ATLAS_COUNTRIES}
        actual = {path.name for path in FLAG_PATH.glob("*.svg")}
        self.assertEqual(actual, expected)
        self.assertTrue((FLAG_PATH / "LICENSE.flag-icons.txt").is_file())

    def test_desktop_presets_storage_order_and_annual_map_fallback_are_wired(self):
        app = APP_PATH.read_text(encoding="utf-8")
        style = STYLE_PATH.read_text(encoding="utf-8")
        storage = re.search(r"const STORAGE_METRIC_IDS = \[(.*?)\];", app, re.DOTALL)
        self.assertIsNotNone(storage)
        ordered = storage.group(1)
        self.assertLess(ordered.index('"battery_energy_gwh"'), ordered.index('"battery_power_gw"'))
        self.assertLess(ordered.index('"battery_power_gw"'), ordered.index('"battery_duration_hours"'))
        self.assertLess(ordered.index('"pumped_storage_energy_gwh"'), ordered.index('"pumped_storage_power_gw"'))
        self.assertLess(ordered.index('"pumped_storage_power_gw"'), ordered.index('"pumped_storage_duration_hours"'))
        self.assertIn("async function selectMapMetricForPeriod(metricId)", app)
        self.assertIn('$("period-type").value = "year"', app)
        self.assertIn("metric.temporal_availability.yearly", app)
        self.assertIn("async function applyComparisonPreset(preset)", app)
        self.assertIn("availabilityPreset", app)
        self.assertIn(".comparison-presets::before", style)
        self.assertIn(".selection-energy-pulse", style)
        self.assertIn(".export-success-pulse", style)
        self.assertIn("legend-morph", style)
        self.assertIn("function orderedMetricVariants(metrics)", app)
        self.assertIn("STORAGE_VARIANT_ORDER", app)
        self.assertIn("function animateTableDisclosure(kind, renderTable, collapsing)", app)
        self.assertIn("function scrollTableCardHeading(kind)", app)
        self.assertIn("function lockTableDisclosureScrollAnchoring()", app)
        self.assertIn("const unlockScrollAnchoring = lockTableDisclosureScrollAnchoring();", app)
        self.assertIn('heading?.scrollIntoView?.({behavior: motionAllowed() ? "smooth" : "auto", block: "start"})', app)
        self.assertNotIn("window.scrollBy?.({top: endHeight - startHeight", app)
        self.assertIn("overflow-anchor: none", style)
        self.assertIn("html.table-disclosure-updating", style)
        self.assertIn("scroll-margin-top: calc(var(--atlas-controls-height) + 1rem)", style)
        self.assertIn("transition: height 760ms", style)
        self.assertIn(".tool-actions", style)


if __name__ == "__main__":
    unittest.main()
