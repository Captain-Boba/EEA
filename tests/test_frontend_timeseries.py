import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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

    def test_flag_colors_are_preferred_without_conflicts_and_2015_is_the_baseline(self):
        script = r'''
global.document = {getElementById: () => ({addEventListener: () => {}})};
global.window = {location: {href: "http://localhost/"}, matchMedia: () => ({matches: true})};
global.history = {replaceState: () => {}};
global.fetch = () => new Promise(() => {});
global.URLSearchParams = URLSearchParams;
const {assignCountryColors, extractFlagColors, relativeBaselineChange} = require("./web/app.js");
const candidates = new Map([
  ["DE", extractFlagColors('<path fill="#fc0"/><path fill="#000001"/><path fill="red"/>')],
  ["ES", extractFlagColors('<path fill="#aa151b"/><path fill="#f1bf00"/>')],
  ["FR", extractFlagColors('<path fill="#fff"/><path fill="#000091"/><path fill="#e1000f"/>')],
  ["UK", extractFlagColors('<path fill="#012169"/><path fill="#fff"/><path fill="#c8102e"/>')],
]);
const colors = assignCountryColors(["DE", "ES", "FR", "UK"], candidates);
const monthly = {
  values: [{period: "2026-07", value: 15}],
  baseline_values: [{period: "2015-07", value: 5}],
};
const zeroBaseline = {
  values: [{period: "2026", value: 15}],
  baseline_values: [{period: "2015", value: 0}],
};
process.stdout.write(JSON.stringify({
  colors: Object.fromEntries(colors),
  unique: new Set(colors.values()).size,
  monthlyChange: relativeBaselineChange(monthly, 0, "monthly"),
  zeroChange: relativeBaselineChange(zeroBaseline, 0, "yearly"),
}));
'''
        result = self.run_node(script)
        self.assertEqual(result["colors"]["DE"], "#ffcc00")
        self.assertEqual(result["colors"]["FR"], "#4da3ff")
        self.assertEqual(result["unique"], 4)
        self.assertEqual(result["monthlyChange"], 200)
        self.assertIsNone(result["zeroChange"])


if __name__ == "__main__":
    unittest.main()
