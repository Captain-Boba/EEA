import unittest

from electricity_atlas.normalization import (
    energy_to_mwh,
    iso_to_utc,
    mwh_to_twh,
    mw_interval_to_mwh,
    normalize_public_power_record,
    power_to_mw,
    split_physical_flows,
)


class UnitConversionTests(unittest.TestCase):
    def test_power_units(self):
        self.assertEqual(power_to_mw(1, "GW"), 1000)
        self.assertEqual(power_to_mw(1000, "kW"), 1)

    def test_energy_units(self):
        self.assertEqual(energy_to_mwh(1, "TWh"), 1_000_000)
        self.assertEqual(mwh_to_twh(1_000_000), 1)
        self.assertEqual(mw_interval_to_mwh(100, 15), 25)

    def test_invalid_unit_is_not_guessed(self):
        with self.assertRaises(ValueError):
            power_to_mw(1, "MWh")


class PublicPowerNormalizationTests(unittest.TestCase):
    def test_categories_total_and_load(self):
        series = [
            {"id": "solar"}, {"id": "wind_onshore"}, {"id": "hydro_run_of_river"},
            {"id": "nuclear"}, {"id": "fossil_gas"}, {"id": "geothermal"},
            {"id": "load"}, {"id": "cross_border_electricity_trading"},
        ]
        metrics, unmapped = normalize_public_power_record(
            {"solar": 10, "wind_onshore": 20, "hydro_run_of_river": 5, "nuclear": 30,
             "fossil_gas": 15, "geothermal": 2, "load": 90, "cross_border_electricity_trading": 8},
            series,
        )
        self.assertEqual(metrics["generation_total"], 82)
        self.assertEqual(metrics["generation_other"], 2)
        self.assertEqual(metrics["consumption"], 90)
        self.assertEqual(unmapped, ["geothermal"])
        self.assertNotIn("generation_coal", metrics)


class FlowAndTimezoneTests(unittest.TestCase):
    def test_physical_flow_signs_and_balance(self):
        imports, exports, net, bilateral = split_physical_flows(
            {"france": 1.5, "poland": -2.0, "sum": -0.5}, "GW"
        )
        self.assertEqual(imports, 1500)
        self.assertEqual(exports, 2000)
        self.assertEqual(net, -500)
        self.assertEqual(bilateral["france"], 1500)

    def test_dst_fallback_offsets_remain_distinct(self):
        summer_time = iso_to_utc("2025-10-26T02:00:00+02:00")
        winter_time = iso_to_utc("2025-10-26T02:00:00+01:00")
        self.assertNotEqual(summer_time, winter_time)
        self.assertEqual(summer_time, "2025-10-26T00:00:00+00:00")
        self.assertEqual(winter_time, "2025-10-26T01:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
