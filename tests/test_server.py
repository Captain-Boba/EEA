import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import urlopen

from electricity_atlas.server import create_server


class ServerSmokeTests(unittest.TestCase):
    def test_missing_database_is_initialized_before_read_only_summary_api(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "test.sqlite3"
            self.assertFalse(db_path.exists())
            server = create_server(db_path, "127.0.0.1", 0)
            self.assertTrue(db_path.is_file())
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                with urlopen(base + "/", timeout=5) as response:
                    html = response.read().decode("utf-8")
                with urlopen(base + "/contact.html", timeout=5) as response:
                    contact_html = response.read().decode("utf-8")
                with urlopen(base + "/privacy.html", timeout=5) as response:
                    privacy_html = response.read().decode("utf-8")
                with urlopen(base + "/llms.txt", timeout=5) as response:
                    llms_text = response.read().decode("utf-8")
                    llms_content_type = response.headers.get_content_type()
                with urlopen(base + "/api.html", timeout=5) as response:
                    api_html = response.read().decode("utf-8")
                    api_html_content_type = response.headers.get_content_type()
                with urlopen(base + "/openapi.json", timeout=5) as response:
                    openapi = json.load(response)
                    openapi_content_type = response.headers.get_content_type()
                with urlopen(base + "/api/", timeout=5) as response:
                    api_discovery = json.load(response)
                with urlopen(base + "/api", timeout=5) as response:
                    api_discovery_alias = json.load(response)
                with urlopen(base + "/robots.txt", timeout=5) as response:
                    robots_text = response.read().decode("utf-8")
                    robots_content_type = response.headers.get_content_type()
                with urlopen(base + "/sitemap.xml", timeout=5) as response:
                    sitemap_xml = response.read().decode("utf-8")
                    sitemap_content_type = response.headers.get_content_type()
                with urlopen(base + "/assets/europe.svg", timeout=5) as response:
                    map_svg = response.read().decode("utf-8")
                with urlopen(base + "/api/countries", timeout=5) as response:
                    countries = json.load(response)
                with urlopen(base + "/api/summary?year=2025&month=7", timeout=5) as response:
                    summary = json.load(response)
                with urlopen(base + "/api/summary?year=2025&month=7&source=ember", timeout=5) as response:
                    ember_summary = json.load(response)
                with urlopen(base + "/api/map-data?metric=capacity_total_gw&year=2025", timeout=5) as response:
                    capacity_map = json.load(response)
                with urlopen(base + "/api/metrics", timeout=5) as response:
                    metrics = json.load(response)
                with urlopen(base + "/api/storage", timeout=5) as response:
                    storage = json.load(response)
                with urlopen(base + "/api/country-profile?country=DE&year=2025&month=7", timeout=5) as response:
                    profile = json.load(response)
                with urlopen(
                    base + "/api/timeseries?metric=generation_twh&countries=DE&start=2025-01&end=2025-02",
                    timeout=5,
                ) as response:
                    timeseries = json.load(response)
                self.assertIn("European Electricity Atlas", html)
                self.assertIn("Datenquellen und Herkunft", html)
                self.assertIn('href="/contact.html"', html)
                self.assertIn('href="/privacy.html"', html)
                self.assertIn('rel="help" href="/llms.txt"', html)
                self.assertIn('rel="service-desc" href="/openapi.json"', html)
                self.assertIn('href="/api.html">API &amp; Datenzugriff</a>', html)
                self.assertIn('href="/llms.txt" type="text/plain">Datenzugriff für LLMs</a>', html)
                self.assertIn('<link rel="canonical" href="https://ee-atlas.eu/">', html)
                self.assertIn('property="og:site_name" content="European Electricity Atlas"', html)
                self.assertIn('property="og:title" content="Europas Stromsysteme auf einen Blick."', html)
                self.assertIn('property="og:description" content="Vergleiche 31 europäische Länder', html)
                self.assertIn('name="twitter:card" content="summary"', html)
                self.assertEqual(llms_content_type, "text/plain")
                self.assertIn("Machine-readable guidance for language models", llms_text)
                self.assertIn("Clickable API documentation: https://ee-atlas.eu/api.html", llms_text)
                self.assertIn("OpenAPI description: https://ee-atlas.eu/openapi.json", llms_text)
                self.assertEqual(api_html_content_type, "text/html")
                self.assertIn("API &amp; Datenzugriff", api_html)
                self.assertIn('href="/api/compare?year=2025&amp;countries=DE,FR"', api_html)
                self.assertEqual(openapi_content_type, "application/json")
                self.assertEqual(openapi["openapi"], "3.1.0")
                self.assertEqual(openapi["servers"][0]["url"], "https://ee-atlas.eu")
                self.assertIn("/api/compare", openapi["paths"])
                self.assertEqual(api_discovery_alias, api_discovery)
                self.assertEqual(api_discovery["canonical_url"], "https://ee-atlas.eu/api/")
                self.assertEqual(api_discovery["documentation_url"], "https://ee-atlas.eu/api.html")
                self.assertEqual(api_discovery["llms_url"], "https://ee-atlas.eu/llms.txt")
                self.assertEqual(api_discovery["openapi_url"], "https://ee-atlas.eu/openapi.json")
                for endpoint in api_discovery["analytical_endpoints"]:
                    self.assertIn(endpoint["path"], openapi["paths"])
                    example = urlsplit(endpoint["example_url"])
                    local_example = base + example.path
                    if example.query:
                        local_example += "?" + example.query
                    with urlopen(local_example, timeout=5) as response:
                        self.assertEqual(response.status, 200, endpoint["example_url"])
                        self.assertEqual(response.headers.get_content_type(), "application/json")
                self.assertEqual(robots_content_type, "text/plain")
                self.assertIn("User-agent: *", robots_text)
                self.assertIn("Sitemap: https://ee-atlas.eu/sitemap.xml", robots_text)
                self.assertIn(sitemap_content_type, {"application/xml", "text/xml"})
                self.assertIn("https://ee-atlas.eu/llms.txt", sitemap_xml)
                self.assertIn("https://ee-atlas.eu/api.html", sitemap_xml)
                self.assertIn("https://ee-atlas.eu/api/", sitemap_xml)
                self.assertIn("https://ee-atlas.eu/openapi.json", sitemap_xml)
                self.assertIn("Projekt &amp; Kontakt", contact_html)
                self.assertIn("GitHub Issues", contact_html)
                self.assertIn("Datenschutz &amp; Cookies", privacy_html)
                self.assertIn("eea_community", privacy_html)
                self.assertIn("eea-europa-overload", privacy_html)
                self.assertIn('id="atlas-map-section"', html)
                self.assertNotIn("Energy-Charts", html)
                self.assertIn('id="year" type="number" min="2015"', html)
                self.assertIn("Natural Earth 1:50m Admin 0 Countries 5.1.1", map_svg)
                self.assertEqual(len(countries), 31)
                self.assertEqual({country["code"] for country in countries}, {row["country_code"] for row in summary})
                self.assertEqual(len(summary), 31)
                self.assertEqual(
                    {row["country_code"] for row in summary},
                    {"AT", "BE", "BG", "CH", "CZ", "DE", "DK", "ES", "EE", "FI", "FR", "UK", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "ME", "MK", "NL", "NO", "PL", "PT", "RO", "RS", "SK", "SI", "SE"},
                )
                self.assertEqual(summary[0]["period"], "2025-07")
                self.assertTrue(all(row["source"] == "ember" for row in summary))
                self.assertTrue(all(row["data_status"] == "missing" for row in summary))
                self.assertEqual(len(ember_summary), 31)
                self.assertTrue(all(row["source"] == "ember" for row in ember_summary))
                self.assertTrue(all(row["data_status"] == "missing" for row in ember_summary))
                self.assertEqual(capacity_map["requested_year"], 2025)
                self.assertIsNone(capacity_map["data_year"])
                self.assertEqual(capacity_map["rows"], [])
                self.assertIn("net_import_share_pct", {metric["id"] for metric in metrics})
                self.assertIn("battery_power_gw", {metric["id"] for metric in metrics})
                self.assertIn("pumped_storage_energy_gwh", {metric["id"] for metric in metrics})
                self.assertEqual(storage["snapshot_date"], None)
                self.assertEqual(storage["source"], "resolved_storage_sources")
                self.assertIn("JRC", storage["source_label"])
                self.assertIn("Battery-Charts", storage["source_label"])
                self.assertEqual(storage["countries"], [])
                self.assertEqual(profile["country"]["code"], "DE")
                self.assertEqual(profile["requested"]["period"], "2025-07")
                self.assertTrue(profile["sections"])
                self.assertEqual(timeseries["granularity"], "monthly")
                self.assertEqual(len(timeseries["countries"]), 1)
                self.assertEqual(len(timeseries["countries"][0]["values"]), 2)
                self.assertEqual(timeseries["countries"][0]["values"][0]["value"], None)
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + "/api/summary?year=2025&source=combined", timeout=5)
                self.assertEqual(error.exception.code, 400)
                error.exception.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
