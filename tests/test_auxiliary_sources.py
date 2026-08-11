import hashlib
import io
import json
import sqlite3
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path

from electricity_atlas.aggregation import aggregate_country
from electricity_atlas.config import EUROSTAT_GEO, EUROSTAT_GEO_TO_ATLAS
from electricity_atlas.db import initialize
from electricity_atlas.eurostat_importer import (
    DATASETS,
    EurostatDownload,
    EurostatImportError,
    EurostatImporter,
)
from electricity_atlas.metrics import metric_catalog
from electricity_atlas.storage_importer import JrcStorageImporter, StorageImportError, latest_storage


def json_stat(values):
    return json.dumps({
        "id": ["geo", "time"],
        "size": [2, 1],
        "dimension": {
            "geo": {"category": {"index": {"DE": 0, "FR": 1}}},
            "time": {"category": {"index": {"2025": 0}}},
        },
        "value": {"0": values[0], "1": values[1]},
    })


def xlsx_bytes(rows):
    def cell(reference, value):
        if isinstance(value, (int, float)):
            return f'<c r="{reference}"><v>{value}</v></c>'
        escaped = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f'<c r="{reference}" t="inlineStr"><is><t>{escaped}</t></is></c>'

    xml_rows = []
    for row_number, row in enumerate(rows, start=1):
        xml_rows.append(
            f'<row r="{row_number}">'
            + "".join(cell(f"{chr(65 + index)}{row_number}", value) for index, value in enumerate(row))
            + "</row>"
        )
    worksheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData>' + "".join(xml_rows) + '</sheetData></worksheet>'
    )
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)
    return output.getvalue()


class FixtureEurostatClient:
    VALUES = {
        "population": (83_000_000, 68_000_000),
        "gdp_current_billion_eur": (4_000_000, 3_000_000),
        "gdp_per_capita_pps": (46_000, 42_000),
    }

    def __init__(self, broken_metric=None):
        self.broken_metric = broken_metric
        self.calls = []

    def fetch(self, dataset, start_year, end_year):
        self.calls.append((dataset.code, start_year, end_year))
        payload = "{}" if dataset.metric == self.broken_metric else json_stat(self.VALUES[dataset.metric])
        return EurostatDownload(
            dataset=dataset,
            request_url=f"https://example.test/{dataset.code}",
            fetched_at="2026-08-11T12:00:00+00:00",
            status_code=200,
            content_type="application/json",
            etag=None,
            last_modified=None,
            sha256=hashlib.sha256(payload.encode()).hexdigest(),
            payload_text=payload,
        )


class EurostatImportTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        initialize(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_three_datasets_are_imported_sequentially_and_derived_values_use_same_year(self):
        self.assertEqual(EUROSTAT_GEO["GR"], "EL")
        self.assertEqual(EUROSTAT_GEO_TO_ATLAS["EL"], "GR")
        client = FixtureEurostatClient()
        result = EurostatImporter(self.connection, client).import_years(2025, 2025)

        self.assertEqual(client.calls, [(dataset.code, 2025, 2025) for dataset in DATASETS])
        self.assertEqual(result["rows"], 6)
        self.assertEqual(result["countries_with_values"], 2)
        germany_gdp = self.connection.execute(
            "SELECT value FROM period_observation WHERE source='eurostat' AND country_code='DE' AND metric='gdp_current_billion_eur'"
        ).fetchone()[0]
        self.assertEqual(germany_gdp, 4000.0)

        self.connection.execute(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                source_series,metric,value,unit,quality_status)
               VALUES ('DE','2025-01-01','2025-12-31','yearly','ember','electricity-demand/yearly','Demand','demand_total',415,'TWh','observed')"""
        )
        summary = aggregate_country(self.connection, "DE", 2025)
        self.assertEqual(summary["population"], 83_000_000)
        self.assertEqual(summary["consumption_per_capita_mwh"], 5.0)
        self.assertIsNone(aggregate_country(self.connection, "DE", 2025, 1)["consumption_per_capita_mwh"])

    def test_invalid_refresh_preserves_existing_eurostat_rows_and_cache(self):
        EurostatImporter(self.connection, FixtureEurostatClient()).import_years(2025, 2025)
        before_rows = self.connection.execute(
            "SELECT COUNT(*),SUM(value) FROM period_observation WHERE source='eurostat'"
        ).fetchone()
        before_cache = self.connection.execute(
            "SELECT endpoint,sha256 FROM source_cache WHERE source='eurostat' ORDER BY endpoint"
        ).fetchall()

        with self.assertRaises(EurostatImportError):
            EurostatImporter(self.connection, FixtureEurostatClient("gdp_per_capita_pps")).import_years(2025, 2025)

        after_rows = self.connection.execute(
            "SELECT COUNT(*),SUM(value) FROM period_observation WHERE source='eurostat'"
        ).fetchone()
        after_cache = self.connection.execute(
            "SELECT endpoint,sha256 FROM source_cache WHERE source='eurostat' ORDER BY endpoint"
        ).fetchall()
        self.assertEqual(tuple(after_rows), tuple(before_rows))
        self.assertEqual([tuple(row) for row in after_cache], [tuple(row) for row in before_cache])


class JrcStorageImportTests(unittest.TestCase):
    HEADER = "Country Code,Snapshot Date,Project Status,Technology,Subtechnology,Power (MW),Capacity (MWh)\n"
    VALID = HEADER + (
        "DE,2026-06-30,Operational,Electrochemical,Lithium-ion,1000,2000\n"
        "DE,2026-06-30,Operational,Mechanical,Pumped hydro,2000,12000\n"
        "FR,2026-06-30,Planned,Electrochemical,Lithium-ion,900,1800\n"
    )

    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        initialize(self.connection)

    def tearDown(self):
        self.connection.close()

    def import_text(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "jrc-storage.csv"
            path.write_text(text, encoding="utf-8")
            return JrcStorageImporter(self.connection).import_file(path)

    def test_manual_snapshot_aggregates_only_operational_electricity_storage(self):
        result = self.import_text(self.VALID)
        self.assertEqual(result["snapshot_date"], "2026-06-30")
        self.assertEqual(result["countries_with_values"], 1)
        storage = latest_storage(self.connection)
        self.assertEqual(storage["snapshot_date"], "2026-06-30")
        self.assertEqual(storage["countries_with_values"], 1)
        germany = next(country for country in storage["countries"] if country["country_code"] == "DE")
        self.assertEqual(germany["storage_power_gw"], 3.0)
        self.assertEqual(germany["storage_energy_gwh"], 14.0)
        self.assertAlmostEqual(germany["storage_duration_hours"], 14 / 3)

    def test_invalid_refresh_is_atomic(self):
        self.import_text(self.VALID)
        before = [tuple(row) for row in self.connection.execute(
            "SELECT metric,value FROM period_observation WHERE source='jrc' ORDER BY metric"
        )]
        with self.assertRaises(StorageImportError):
            self.import_text(self.VALID.replace("Country Code", "Country"))
        after = [tuple(row) for row in self.connection.execute(
            "SELECT metric,value FROM period_observation WHERE source='jrc' ORDER BY metric"
        )]
        self.assertEqual(after, before)

    def test_paired_dashboard_exports_are_imported_with_raw_binary_provenance(self):
        power = xlsx_bytes([
            ["Country", "Project status", "Power (GW)"],
            ["Germany", "Operational", 9.5],
            ["France", "Operational", 6.0],
            ["Albania", "Operational", 0.1],
        ])
        capacity = xlsx_bytes([
            ["Country", "Project status", "Capacity (GWh)"],
            ["Germany", "Operational", 50.0],
            ["France", "Operational", 42.0],
            ["Turkey", "Operational", 0.1],
        ])
        with tempfile.TemporaryDirectory() as directory:
            power_path = Path(directory) / "power.xlsx"
            capacity_path = Path(directory) / "capacity.xlsx"
            power_path.write_bytes(power)
            capacity_path.write_bytes(capacity)
            result = JrcStorageImporter(self.connection).import_exports(
                power_path, capacity_path, "2026-08-11"
            )

        self.assertEqual(result["countries_with_values"], 2)
        self.assertEqual(result["rows"], 6)
        self.assertIn("ME", result["countries_missing"])
        germany = next(
            country for country in latest_storage(self.connection)["countries"]
            if country["country_code"] == "DE"
        )
        self.assertEqual(germany["storage_power_gw"], 9.5)
        self.assertEqual(germany["storage_energy_gwh"], 50.0)
        self.assertAlmostEqual(germany["storage_duration_hours"], 50 / 9.5)
        cache = list(self.connection.execute(
            "SELECT endpoint,content_type,payload_text FROM source_cache WHERE source='jrc' ORDER BY endpoint"
        ))
        self.assertEqual(len(cache), 2)
        self.assertTrue(all(row["payload_text"].startswith("base64:") for row in cache))
        self.assertTrue(all("spreadsheetml" in row["content_type"] for row in cache))

    def test_invalid_dashboard_pair_preserves_previous_snapshot(self):
        power = xlsx_bytes([
            ["Country", "Project status", "Power (GW)"],
            ["Germany", "Operational", 9.5],
        ])
        capacity = xlsx_bytes([
            ["Country", "Project status", "Capacity (GWh)"],
            ["Germany", "Operational", 50.0],
        ])
        damaged = xlsx_bytes([
            ["Country", "Project status", "Broken"],
            ["Germany", "Operational", 99.0],
        ])
        with tempfile.TemporaryDirectory() as directory:
            power_path = Path(directory) / "power.xlsx"
            capacity_path = Path(directory) / "capacity.xlsx"
            power_path.write_bytes(power)
            capacity_path.write_bytes(capacity)
            importer = JrcStorageImporter(self.connection)
            importer.import_exports(power_path, capacity_path, "2026-08-11")
            before = [tuple(row) for row in self.connection.execute(
                "SELECT metric,value FROM period_observation WHERE source='jrc' ORDER BY metric"
            )]
            power_path.write_bytes(damaged)
            with self.assertRaises(StorageImportError):
                importer.import_exports(power_path, capacity_path, "2026-08-12")
        after = [tuple(row) for row in self.connection.execute(
            "SELECT metric,value FROM period_observation WHERE source='jrc' ORDER BY metric"
        )]
        self.assertEqual(after, before)


class MetricCatalogTests(unittest.TestCase):
    def test_catalog_is_unique_and_marks_exactly_the_requested_main_table_metrics(self):
        catalog = metric_catalog()
        ids = [metric["id"] for metric in catalog]
        self.assertEqual(len(ids), len(set(ids)))
        table_ids = {metric["id"] for metric in catalog if metric["table"]}
        self.assertEqual(table_ids, {
            "generation_twh", "consumption_twh", "consumption_per_capita_mwh",
            "renewable_share_pct", "fossil_share_pct", "nuclear_share_pct",
            "net_import_share_pct", "carbon_intensity_gco2eq_kwh", "price_avg_eur_mwh",
        })
        per_capita = next(metric for metric in catalog if metric["id"] == "consumption_per_capita_mwh")
        self.assertFalse(per_capita["temporal_availability"]["monthly"])
        self.assertTrue(per_capita["temporal_availability"]["yearly"])


if __name__ == "__main__":
    unittest.main()
