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
  ["renewable_share_pct", {id: "renewable_share_pct", temporal_availability: {monthly: true, yearly: true}}],
]);
const countries = new Set(["DE", "FR", "UK"]);
const valid = parseComparisonUrl(
  "?view=compare&metric=renewable_share_pct&countries=DE,FR,UK&start=2015-01&end=2026-08",
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
  valid: {ok: valid.valid, codes: valid.codes, metric: valid.metric.id, start: valid.start, end: valid.end},
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
            },
        )
        self.assertFalse(result["duplicate"])
        self.assertFalse(result["future"])

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

    def test_flag_colors_are_preferred_without_conflicts_and_monthly_change_uses_2015_month(self):
        script = r'''
global.document = {getElementById: () => ({addEventListener: () => {}})};
global.window = {location: {href: "http://localhost/"}, matchMedia: () => ({matches: true})};
global.history = {replaceState: () => {}};
global.fetch = () => new Promise(() => {});
global.URLSearchParams = URLSearchParams;
const {assignCountryColors, colorDistance, extractFlagColors, comparisonBaselinePoint, rankingFallbackDetails, relativeBaselineChange} = require("./web/app.js");
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
  monthlyBaseline: comparisonBaselinePoint(monthly, "2026-07", "monthly"),
  monthlyChange: relativeBaselineChange(monthly, 0, "monthly"),
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
        self.assertEqual(result["monthlyBaseline"], {"period": "2015-07", "value": 5})
        self.assertEqual(result["monthlyChange"], 200)
        self.assertIsNone(result["zeroChange"])
        self.assertIsNone(result["missingChange"])
        self.assertTrue(result["missingFallback"]["active"])
        self.assertIn("Vergleichswert 2015 fehlt", result["missingFallback"]["text"])


if __name__ == "__main__":
    unittest.main()
