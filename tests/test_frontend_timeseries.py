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


if __name__ == "__main__":
    unittest.main()
