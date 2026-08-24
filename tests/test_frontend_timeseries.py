import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "web" / "app.js"
NODE = Path(os.environ.get("EEA_NODE") or shutil.which("node") or "")


class FrontendTimeseriesTests(unittest.TestCase):
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
            encoding="utf-8",
        )
        return json.loads(result.stdout)

    def test_csv_keeps_missing_values_empty_and_includes_average(self):
        script = r'''
global.document = {getElementById: () => ({addEventListener: () => {}})};
global.window = {location: {href: "http://localhost/"}, matchMedia: () => ({matches: true})};
global.history = {replaceState: () => {}};
global.fetch = () => new Promise(() => {});
global.URLSearchParams = URLSearchParams;
const {buildComparisonCsv, flagCode} = require("./web/app.js");
const payload = {
  countries: [
    {country_code: "DE", values: [{value: 1}, {value: null}]},
    {country_code: "FR", values: [{value: 0}, {value: 2}]},
  ],
  atlas_average: {values: [{period: "2025-01", value: 0.5}, {period: "2025-02", value: 2}]},
};
process.stdout.write(JSON.stringify({csv: buildComparisonCsv(payload), uk: flagCode("UK")}));
'''
        result = self.run_node(script)
        self.assertEqual(result["uk"], "gb")
        self.assertEqual(
            result["csv"],
            "period,DE,FR,atlas_average\r\n2025-01,1,0,0.5\r\n2025-02,,2,2",
        )

    def test_png_export_includes_the_current_live_ranking_panel(self):
        app = APP_PATH.read_text(encoding="utf-8")
        self.assertIn("function liveRankingExportEntries()", app)
        self.assertIn('$("ranking-list").querySelectorAll(".ranking-item")', app)
        self.assertIn("async function serializedChartPngSvg()", app)
        self.assertIn('text(panelX + 22, 35, "Live-Ranking"', app)
        self.assertIn('$("atlas-average-value").textContent.trim()', app)
        self.assertIn('href: `/assets/flags/${flagCode(entry.code)}.svg`', app)
        self.assertIn("const source = await serializedChartPngSvg();", app)

    def test_live_ranking_units_are_centered_below_the_value(self):
        style = (ROOT / "web" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".ranking-value {\n  justify-items: center;", style)
        self.assertIn("text-align: center;", style)

    def test_comparison_family_picker_groups_metric_families(self):
        app = APP_PATH.read_text(encoding="utf-8")
        self.assertIn('const groups = new Map();', app)
        self.assertIn('<optgroup label="${escapeAttribute(group)}">', app)
        self.assertIn('${escapeHtml(variants[0].family)}</option>', app)
        self.assertNotIn('const label = `${variants[0].group} · ${variants[0].family}', app)

    def test_comparison_family_picker_renders_a_grouped_menu_grid(self):
        app = APP_PATH.read_text(encoding="utf-8")
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        style = (ROOT / "web" / "style.css").read_text(encoding="utf-8")
        self.assertIn('id="compare-family-trigger"', html)
        self.assertIn('id="compare-family-menu"', html)
        self.assertLess(html.index('id="compare-family-menu"'), html.index('id="comparison-presets"'))
        self.assertIn("function renderComparisonFamilyPicker(groups, activeFamily)", app)
        self.assertIn('class="metric-family-group"', app)
        self.assertIn('data-comparison-family=', app)
        self.assertIn("grid-template-columns: repeat(5, minmax(0, 1fr))", style)
        self.assertIn("top: calc(100% + .7rem)", style)
        self.assertIn(".metric-family-option.active", style)

    def test_native_selects_use_the_atlas_dropdown_component(self):
        app = APP_PATH.read_text(encoding="utf-8")
        style = (ROOT / "web" / "style.css").read_text(encoding="utf-8")
        self.assertIn("const ENHANCED_SELECT_IDS = Object.freeze", app)
        self.assertIn("function configureEnhancedSelectMenus()", app)
        self.assertIn("function renderEnhancedSelectMenu(select)", app)
        self.assertIn("configureEnhancedSelectMenus();", app)
        self.assertNotIn("function positionEnhancedSelectMenu(select)", app)
        self.assertIn(".enhanced-select-menu", style)
        self.assertIn(".enhanced-select-groups", style)
        self.assertIn(".enhanced-select-menu.has-groups", style)
        self.assertIn("overflow-wrap: anywhere", style)

    def test_table_formatter_keeps_two_decimal_places_by_default(self):
        script = r'''
global.document = {getElementById: () => ({addEventListener: () => {}})};
global.window = {location: {href: "http://localhost/"}, matchMedia: () => ({matches: true})};
global.history = {replaceState: () => {}};
global.fetch = () => new Promise(() => {});
global.URLSearchParams = URLSearchParams;
const {formatTableValue} = require("./web/app.js");
process.stdout.write(JSON.stringify({value: formatTableValue(1.2, "example"), zero: formatTableValue(0, "example")}));
'''
        result = self.run_node(script)
        self.assertEqual(result["value"], "1,20")
        self.assertEqual(result["zero"], "0,00")

    def test_direct_link_state_is_validated_and_restored(self):
        script = r'''
global.document = {getElementById: () => ({addEventListener: () => {}})};
global.window = {location: {href: "http://localhost/"}, matchMedia: () => ({matches: true})};
global.history = {replaceState: () => {}};
global.fetch = () => new Promise(() => {});
global.URLSearchParams = URLSearchParams;
const {parseComparisonUrl} = require("./web/app.js");
const catalog = new Map([
  ["renewable_share_pct", {id: "renewable_share_pct", unit: "%", map_config: {scale: "sequential"}, temporal_availability: {monthly: true, yearly: true}}],
]);
const countries = new Set(["DE", "FR", "UK"]);
const valid = parseComparisonUrl(
  "?view=compare&metric=renewable_share_pct&countries=DE,FR,UK&start=2015-01&end=2026-08&axis=data-range",
  countries,
  catalog,
  new Date("2026-08-13T12:00:00Z"),
);
const duplicate = parseComparisonUrl(
  "?view=compare&metric=renewable_share_pct&countries=DE,DE&start=2015-01&end=2026-08",
  countries,
  catalog,
  new Date("2026-08-13T12:00:00Z"),
);
const future = parseComparisonUrl(
  "?view=compare&metric=renewable_share_pct&countries=DE&start=2015-01&end=2026-09",
  countries,
  catalog,
  new Date("2026-08-13T12:00:00Z"),
);
process.stdout.write(JSON.stringify({
  valid: {ok: valid.valid, codes: valid.codes, metric: valid.metric.id, start: valid.start, end: valid.end, axisMode: valid.axisMode},
  duplicate: duplicate.valid,
  future: future.valid,
}));
'''
        result = self.run_node(script)
        self.assertEqual(
            result["valid"],
            {
                "ok": True,
                "codes": ["DE", "FR", "UK"],
                "metric": "renewable_share_pct",
                "start": "2015-01",
                "end": "2026-08",
                "axisMode": "data-range",
            },
        )
        self.assertFalse(result["duplicate"])
        self.assertFalse(result["future"])

    def test_all_plots_can_use_their_visible_data_range_without_clipping_self_sufficiency(self):
        script = r'''
const axisMode = {value: "data-range", addEventListener: () => {}};
global.document = {getElementById: id => id === "compare-axis-mode" ? axisMode : {addEventListener: () => {}}};
global.window = {location: {href: "http://localhost/"}, matchMedia: () => ({matches: true})};
global.history = {replaceState: () => {}};
global.fetch = () => new Promise(() => {});
global.URLSearchParams = URLSearchParams;
const {chartScale} = require("./web/app.js");
const payload = {
  metric: {unit: "%", map_config: {scale: "sequential"}},
  countries: [{values: [{value: 34.2}, {value: 65.1}]}],
  atlas_average: {values: [{value: 48.6}, {value: 54.3}]},
};
const geometry = {left: 0, right: 100, top: 0, bottom: 100};
const cropped = chartScale(payload, geometry);
axisMode.value = "full";
const full = chartScale(payload, geometry);
axisMode.value = "data-range";
const absolute = chartScale({
  metric: {unit: "TWh", map_config: {scale: "sequential"}},
  countries: [{values: [{value: 12.4}, {value: 48.7}]}],
  atlas_average: {values: [{value: 19.6}, {value: 31.2}]},
}, geometry);
axisMode.value = "full";
const selfSufficiency = chartScale({
  metric: {id: "self_sufficiency_pct", unit: "%", map_config: {scale: "sequential"}},
  countries: [{values: [{value: 84.8}, {value: 125.3}]}],
  atlas_average: {values: [{value: 91.5}, {value: 100.2}]},
}, geometry);
process.stdout.write(JSON.stringify({cropped: [cropped.minimum, cropped.maximum], full: [full.minimum, full.maximum], absolute: [absolute.minimum, absolute.maximum], selfSufficiency: [selfSufficiency.minimum, selfSufficiency.maximum]}));
'''
        result = self.run_node(script)
        self.assertEqual(result["cropped"], [34.2, 100])
        self.assertEqual(result["full"], [0, 100])
        self.assertEqual(result["absolute"], [12.4, 48.7])
        self.assertEqual(result["selfSufficiency"][0], 0)
        self.assertAlmostEqual(result["selfSufficiency"][1], 132.818, places=9)

    def test_metric_variants_use_absolute_share_then_per_capita_order(self):
        script = r'''
global.document = {getElementById: () => ({addEventListener: () => {}})};
global.window = {location: {href: "http://localhost/"}, matchMedia: () => ({matches: true})};
global.history = {replaceState: () => {}};
global.fetch = () => new Promise(() => {});
global.URLSearchParams = URLSearchParams;
const {orderedMetricVariants} = require("./web/app.js");
const variants = orderedMetricVariants([
  {id: "renewable_per_capita_mwh", unit: "MWh/Einwohner", representation: "Erzeugung in MWh je Einwohner"},
  {id: "renewable_share_pct", unit: "%", representation: "Anteil an der Gesamterzeugung"},
  {id: "renewable_twh", unit: "TWh", representation: "Erzeugung in TWh"},
]);
process.stdout.write(JSON.stringify(variants.map(metric => metric.id)));
'''
        self.assertEqual(
            self.run_node(script),
            ["renewable_twh", "renewable_share_pct", "renewable_per_capita_mwh"],
        )

    def test_stock_chart_presets_cover_monthly_and_yearly_ranges_without_filling_gaps(self):
        script = r'''
global.document = {getElementById: () => ({addEventListener: () => {}})};
global.window = {location: {href: "http://localhost/"}, matchMedia: () => ({matches: true})};
global.history = {replaceState: () => {}};
global.fetch = () => new Promise(() => {});
global.URLSearchParams = URLSearchParams;
const {availableComparisonRange, comparisonPresetRange, latestCompleteComparisonIndex, latestCompleteComparisonPeriod} = require("./web/app.js");
const monthly = {temporal_availability: {monthly: true, yearly: true}};
const yearly = {temporal_availability: {monthly: false, yearly: true}};
const available = availableComparisonRange({
  countries: [{values: [
    {period: "2015-01", value: null},
    {period: "2015-02", value: 2},
    {period: "2026-06", value: 4},
    {period: "2026-07", value: null},
  ]}],
  atlas_average: {values: []},
});
process.stdout.write(JSON.stringify({
  ytd: comparisonPresetRange("ytd", monthly, "2026-08"),
  oneYear: comparisonPresetRange("1y", monthly, "2026-08"),
  tenYears: comparisonPresetRange("10y", monthly, "2026-08"),
  threeCalendarYears: comparisonPresetRange("3y", yearly, "2026"),
  yearlyYtd: comparisonPresetRange("ytd", yearly, "2026"),
  maximum: comparisonPresetRange("max", monthly, "2026-08", available),
  completeEnd: latestCompleteComparisonPeriod({countries: [
    {values: [{period: "2026-06", value: 4}, {period: "2026-07", value: 5}]},
    {values: [{period: "2026-06", value: 3}, {period: "2026-07", value: null}]},
  ]}),
  completeIndex: latestCompleteComparisonIndex({countries: [
    {values: [{period: "2026-06", value: 4}, {period: "2026-07", value: 5}]},
    {values: [{period: "2026-06", value: 3}, {period: "2026-07", value: null}]},
  ]}),
  available,
}));
'''
        result = self.run_node(script)
        self.assertEqual(result["ytd"], {"start": "2026-01", "end": "2026-08"})
        self.assertEqual(result["oneYear"], {"start": "2025-08", "end": "2026-08"})
        self.assertEqual(result["tenYears"], {"start": "2016-08", "end": "2026-08"})
        self.assertEqual(result["threeCalendarYears"], {"start": "2024", "end": "2026"})
        self.assertIsNone(result["yearlyYtd"])
        self.assertEqual(result["available"], {"start": "2015-02", "end": "2026-06"})
        self.assertEqual(result["maximum"], {"start": "2015-02", "end": "2026-06"})
        self.assertEqual(result["completeEnd"], "2026-06")
        self.assertEqual(result["completeIndex"], 0)

    def test_flag_colors_are_preferred_without_conflicts_and_monthly_change_uses_range_start_year(self):
        script = r'''
global.document = {getElementById: () => ({addEventListener: () => {}})};
global.window = {location: {href: "http://localhost/"}, matchMedia: () => ({matches: true})};
global.history = {replaceState: () => {}};
global.fetch = () => new Promise(() => {});
global.URLSearchParams = URLSearchParams;
const {assignCountryColors, chartIndexFromClientX, colorDistance, extractFlagColors, comparisonBaselinePoint, rankingFallbackDetails, relativeBaselineChange} = require("./web/app.js");
const candidates = new Map([
  ["DE", extractFlagColors('<path fill="#fc0"/><path fill="#000001"/><path fill="red"/>')],
  ["ES", extractFlagColors('<path fill="#aa151b"/><path fill="#f1bf00"/>')],
  ["FR", extractFlagColors('<path fill="#fff"/><path fill="#000091"/><path fill="#e1000f"/>')],
  ["UK", extractFlagColors('<path fill="#012169"/><path fill="#fff"/><path fill="#c8102e"/>')],
]);
const colors = assignCountryColors(["DE", "ES", "FR", "UK"], candidates);
const tenCodes = Array.from({length: 10}, (_, index) => `C${index}`);
const conflicting = new Map(tenCodes.map(code => [code, ["#ff0000", "#f90008"]]));
const tenColors = [...assignCountryColors(tenCodes, conflicting).values()];
const minimumDistance = Math.min(...tenColors.flatMap((color, index) => tenColors.slice(index + 1).map(other => colorDistance(color, other))));
const monthly = {
  country_code: "DE",
  values: [{period: "2026-07", value: 15}],
  baseline_values: [{period: "2015-07", value: 5}],
};
const threeYears = {
  country_code: "DE",
  values: [{period: "2026-07", value: 15}],
  baseline_values: [{period: "2023-07", value: 6}],
};
const zeroBaseline = {
  country_code: "DE",
  values: [{period: "2026", value: 15}],
  baseline_values: [{period: "2015", value: 0}],
};
const missingBaseline = {
  country_code: "DE",
  values: [{period: "2026-07", value: 15}],
  baseline_values: [{period: "2015-07", value: null}],
};
process.stdout.write(JSON.stringify({
  colors: Object.fromEntries(colors),
  unique: new Set(colors.values()).size,
  tenUnique: new Set(tenColors).size,
  minimumDistance,
  hitIndices: [
    chartIndexFromClientX(100, {left: 100, width: 900}, 10),
    chartIndexFromClientX(550, {left: 100, width: 900}, 10),
    chartIndexFromClientX(1000, {left: 100, width: 900}, 10),
  ],
  monthlyBaseline: comparisonBaselinePoint(monthly, "2026-07", "monthly"),
  monthlyChange: relativeBaselineChange(monthly, 0, "monthly"),
  threeYearBaseline: comparisonBaselinePoint(threeYears, "2026-07", "monthly", 2023),
  threeYearChange: relativeBaselineChange(threeYears, 0, "monthly", 2023),
  zeroChange: relativeBaselineChange(zeroBaseline, 0, "yearly"),
  missingChange: relativeBaselineChange(missingBaseline, 0, "monthly"),
  missingFallback: rankingFallbackDetails({...missingBaseline, country_name: "Deutschland"}, 0),
}));
'''
        result = self.run_node(script)
        self.assertEqual(result["colors"]["DE"], "#ffcc00")
        self.assertEqual(result["colors"]["FR"], "#4090ff")
        self.assertEqual(result["unique"], 4)
        self.assertEqual(result["tenUnique"], 10)
        self.assertGreaterEqual(result["minimumDistance"], 96)
        self.assertEqual(result["hitIndices"], [0, 5, 9])
        self.assertEqual(result["monthlyBaseline"], {"period": "2015-07", "value": 5})
        self.assertEqual(result["monthlyChange"], 200)
        self.assertEqual(result["threeYearBaseline"], {"period": "2023-07", "value": 6})
        self.assertEqual(result["threeYearChange"], 150)
        self.assertIsNone(result["zeroChange"])
        self.assertIsNone(result["missingChange"])
        self.assertTrue(result["missingFallback"]["active"])
        self.assertIn("Vergleichswert 2015 fehlt", result["missingFallback"]["text"])

    def test_hover_uses_a_120ms_leading_plus_trailing_throttle_and_cleans_up(self):
        script = r'''
global.document = {getElementById: () => ({addEventListener: () => {}})};
global.window = {location: {href: "http://localhost/"}, matchMedia: () => ({matches: true})};
global.history = {replaceState: () => {}};
global.fetch = () => new Promise(() => {});
global.URLSearchParams = URLSearchParams;
const {createLeadingTrailingThrottle} = require("./web/app.js");
let now = 0;
const queue = [];
const timers = {
  setTimeout(callback, delay) { const timer = {callback, due: now + delay, cancelled: false}; queue.push(timer); return timer; },
  clearTimeout(timer) { timer.cancelled = true; },
};
const values = [];
const throttle = createLeadingTrailingThrottle(value => values.push({value, now}), 120, () => now, timers);
const flushDue = () => queue.filter(timer => !timer.cancelled && timer.due <= now).forEach(timer => { timer.cancelled = true; timer.callback(); });
throttle.push("first");
now = 20; throttle.push("middle");
now = 80; throttle.push("last");
now = 120; flushDue();
now = 130; throttle.push("cancelled");
throttle.cancel();
now = 250; flushDue();
process.stdout.write(JSON.stringify(values));
'''
        result = self.run_node(script)
        self.assertEqual(result, [{"value": "first", "now": 0}, {"value": "last", "now": 120}])
        app = APP_PATH.read_text(encoding="utf-8")
        self.assertIn("const CHART_HOVER_THROTTLE_MS = 120", app)
        self.assertIn("scheduleChartHoverIndex(index)", app)
        self.assertIn("clearChartHoverThrottle();\n    if (chartPinnedIndex", app)
        self.assertIn("clearChartHoverThrottle();\n    const count", app)


if __name__ == "__main__":
    unittest.main()
