import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from electricity_atlas.aggregation import aggregate_country
from electricity_atlas.db import initialize
from electricity_atlas.eea_ghg_importer import EeaGhgImporter
from electricity_atlas.eurostat_importer import EurostatDownload
from electricity_atlas.eurostat_supplement import SUPPLEMENT_DATASETS, EurostatSupplementImporter
from electricity_atlas.hydro_importer import JrcHydroImporter


def json_stat(de_value=1, fr_value=2):
    return json.dumps({
        "id": ["geo", "time"],
        "size": [2, 1],
        "dimension": {
            "geo": {"category": {"index": {"DE": 0, "FR": 1}}},
            "time": {"category": {"index": {"2025": 0}}},
        },
        "value": {"0": de_value, "1": fr_value},
    })


class FixtureSupplementClient:
    def __init__(self):
        self.calls = []

    def fetch(self, dataset, start_year, end_year):
        self.calls.append((dataset.metric, start_year, end_year))
        payload = json_stat()
        return EurostatDownload(
            dataset=dataset,
            request_url=f"https://example.test/{dataset.code}/{dataset.metric}",
            fetched_at="2026-08-14T12:00:00+00:00",
            status_code=200,
            content_type="application/json",
            etag=None,
            last_modified=None,
            sha256=hashlib.sha256(payload.encode()).hexdigest(),
            payload_text=payload,
        )


class DataExpansionTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        initialize(self.connection)

    def tearDown(self):
        self.connection.close()

    def insert(self, code, year, metric, value, unit, source="ember", granularity="yearly"):
        start = f"{year}-01-01" if granularity == "yearly" else f"{year}-07-01"
        end = f"{year}-12-31" if granularity == "yearly" else f"{year}-07-31"
        self.connection.execute(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                source_series,metric,value,unit,quality_status)
               VALUES (?,?,?,?,?,'fixture','',?,?,?,'observed')""",
            (code, start, end, granularity, source, metric, value, unit),
        )

    def test_five_derived_metrics_and_ev_capacity_are_exposed(self):
        for metric, value in (
            ("generation_total", 100),
            ("generation_renewables", 50),
            ("generation_nuclear", 20),
            ("generation_wind", 20),
            ("demand_total", 90),
        ):
            self.insert("DE", 2024, metric, value, "TWh")
        self.insert("DE", 2024, "carbon_intensity", 300, "gCO2/kWh")
        self.insert("DE", 2023, "carbon_intensity", 350, "gCO2/kWh")
        self.insert("DE", 2024, "population", 10_000_000, "people", source="eurostat")
        self.insert("DE", 2024, "capacity_wind_gw", 10, "GW", source="eurostat")
        self.insert("DE", 2024, "bev_stock", 100_000, "vehicles", source="eurostat")
        summary = aggregate_country(self.connection, "DE", 2024)
        self.assertEqual(summary["renewable_per_capita_mwh"], 5)
        self.assertEqual(summary["low_carbon_share_pct"], 70)
        self.assertAlmostEqual(summary["self_sufficiency_pct"], 100 / 90 * 100)
        self.assertEqual(summary["estimated_generation_emissions_mtco2eq"], 30)
        self.assertAlmostEqual(summary["decarbonization_rate_pct"], (350 - 300) / 350 * 100)
        self.assertEqual(summary["ev_battery_nominal_capacity_est_gwh"], 6)
        self.assertAlmostEqual(summary["capacity_factor_wind_pct"], 20 * 1000 / (10 * 8784) * 100)

    def test_monthly_missing_nuclear_is_zero_only_for_approved_low_carbon_rule(self):
        self.insert("DE", 2025, "generation_total", 10, "TWh", granularity="monthly")
        self.insert("DE", 2025, "generation_renewables", 5, "TWh", granularity="monthly")
        summary = aggregate_country(self.connection, "DE", 2025, 7)
        self.assertEqual(summary["nuclear_twh"], 0)
        self.assertEqual(summary["low_carbon_share_pct"], 50)

    def test_negative_ember_residual_categories_are_exposed_as_missing(self):
        self.insert("DE", 2025, "generation_total", 10, "TWh", granularity="monthly")
        self.insert("DE", 2025, "generation_other_renewables", -0.1, "TWh", granularity="monthly")
        summary = aggregate_country(self.connection, "DE", 2025, 7)
        self.assertIsNone(summary["other_renewables_twh"])
        self.assertIsNone(summary["other_renewables_share_pct"])
        self.assertIn(
            "negative_source_residual_treated_as_missing",
            {issue["issue_type"] for issue in summary["quality_issues"]},
        )

    def test_eurostat_supplement_import_is_filtered_and_keeps_base_eurostat_rows(self):
        self.insert("DE", 2025, "population", 83_000_000, "people", source="eurostat")
        client = FixtureSupplementClient()
        result = EurostatSupplementImporter(self.connection, client).import_years(2025, 2025)
        self.assertEqual(len(client.calls), len(SUPPLEMENT_DATASETS))
        self.assertEqual(result["rows"], len(SUPPLEMENT_DATASETS) * 2)
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM source_cache WHERE source='eurostat'").fetchone()[0],
            len(SUPPLEMENT_DATASETS),
        )
        self.assertEqual(
            self.connection.execute("SELECT value FROM period_observation WHERE metric='population'").fetchone()[0],
            83_000_000,
        )

    def test_jrc_hydro_normalization_preserves_missing_storage_as_missing(self):
        payload = (
            '"id","name","installed_capacity_MW","pumping_MW","type","country_code","lat","lon","dam_height_m","volume_Mm3","storage_capacity_MWh","avg_annual_generation_GWh","pypsa_id","GEO","WRI"\n'
            '"H1","One",1000,,"HDAM","DE",,,,,5000,,,,\n'
            '"H2","Two",500,200,"HPHS","DE",,,,,,,,,\n'
            '"H3","Three",300,,"HDAM","FR",,,,,,,,,\n'
        ).encode()
        rows = JrcHydroImporter(self.connection)._normalize(payload)
        values = {(row[0], row[6]): row[7] for row in rows}
        self.assertEqual(values[("DE", "hydro_plant_capacity_gw")], 1.5)
        self.assertEqual(values[("DE", "hydro_pumping_power_gw")], 0.2)
        self.assertEqual(values[("DE", "hydro_reservoir_energy_gwh")], 5)
        self.assertNotIn(("FR", "hydro_reservoir_energy_gwh"), values)

    def test_eea_csv_import_filters_aggregate_1a1a_and_maps_gb_to_uk(self):
        csv_text = (
            "Country_code,Year,Sector_code,Pollutant_name,Unit,Emissions\n"
            "DE,2024,1.A.1.a,Aggregate greenhouse gases,Gg CO2 equivalent,250000\n"
            "GB,2024,1.A.1.a,Aggregate greenhouse gases,Gg CO2 equivalent,100000\n"
            "FR,2024,1.A.2,Aggregate greenhouse gases,Gg CO2 equivalent,999999\n"
            "DE,2024,1.A.1.a,CO2,Gg,123\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "eea.csv"
            path.write_text(csv_text, encoding="utf-8")
            result = EeaGhgImporter(self.connection).import_file(path)
        self.assertEqual(result["rows"], 2)
        values = dict(self.connection.execute(
            "SELECT country_code,value FROM period_observation WHERE source='eea'"
        ))
        self.assertEqual(values, {"DE": 250, "UK": 100})
        cached = self.connection.execute(
            "SELECT payload_text FROM source_cache WHERE source='eea'"
        ).fetchone()[0]
        self.assertTrue(cached.startswith("gzip+base64:"))


if __name__ == "__main__":
    unittest.main()
