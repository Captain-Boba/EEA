"""Bilingual presentation must not alter the underlying data/API contract."""
import copy
import importlib.util
import json
import re
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from electricity_atlas.config import COUNTRIES, EMBER_SOURCE_NAME
from electricity_atlas.db import connect
from electricity_atlas.localization import RETAINED_DETAILS_PREFIX, localize_payload, resource
from electricity_atlas.metrics import METRICS, metric_catalog
from electricity_atlas.pages import PUBLIC_PAGES, render_page
from electricity_atlas.server import create_server

ROOT = Path(__file__).resolve().parents[1]


class LocalizationResourcesTests(unittest.TestCase):
    def test_bundle_is_current_and_placeholders_match(self):
        spec = importlib.util.spec_from_file_location("build_locales", ROOT / "scripts/build_locales.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.build(), (ROOT / "web/locales/resources.js").read_text(encoding="utf-8"))

    def test_all_literal_translation_calls_have_both_languages(self):
        catalogs = {lang: json.loads((ROOT / f"web/locales/{lang}.json").read_text(encoding="utf-8")) for lang in ("en", "de")}
        for path in list((ROOT / "web").glob("*.html")) + [ROOT / "web/app.js", ROOT / "web/wallpapers.js"]:
            for match in re.finditer(r'\bt\(("(?:[^"\\]|\\.)*")', path.read_text(encoding="utf-8")):
                key = json.loads(match[1])
                for lang in catalogs:
                    with self.subTest(path=path.name, key=key, lang=lang):
                        self.assertIn(key, catalogs[lang])

    def test_all_metrics_have_english_internals_and_legacy_german_labels(self):
        en, de = metric_catalog("en"), metric_catalog()
        self.assertEqual(len(en), 87)
        self.assertEqual(set(resource("metrics", "en")), {m["id"] for m in METRICS})
        self.assertEqual(set(resource("metrics", "en")), set(resource("metrics", "de")))
        for internal, english, german in zip(METRICS, en, de):
            self.assertEqual(internal["label"], english["label"])
            self.assertEqual(english["label_de"], german["label_de"])
            self.assertEqual(german["label"], german["label_de"])
            for key in ("id", "group_id", "family_id", "category_id", "temporal_availability", "map_config", "views"):
                self.assertEqual(english[key], german[key])
        self.assertEqual(COUNTRIES["DE"].name, "Germany")
        self.assertEqual(resource("countries", "de")["DE"], "Deutschland")

    def test_gallery_has_two_titles_for_each_stable_image_id(self):
        gallery = json.loads((ROOT / "web/wallpapers.json").read_text(encoding="utf-8"))
        en = json.loads((ROOT / "web/locales/en.json").read_text(encoding="utf-8"))
        de = json.loads((ROOT / "web/locales/de.json").read_text(encoding="utf-8"))
        self.assertEqual(len(gallery), 250)
        for item in gallery:
            key = f'gallery.{item["id"]}.title'
            self.assertEqual(en[key], item["title"])
            self.assertTrue(de[key])
            subject_key = f'gallery.{item["id"]}.subject'
            self.assertEqual(en.get(subject_key, en[key]), item["subject"])
            if item["subject"] != item["title"]:
                self.assertIn(subject_key, de)

    def test_templates_are_server_rendered_and_escape_url_input(self):
        for name in PUBLIC_PAGES:
            for lang in ("en", "de"):
                html = render_page(name, lang, '/?metric=x%22%3E%3Cscript%3E').decode()
                self.assertIn(f'<html lang="{lang}">', html)
                self.assertNotIn("{{", html)
                self.assertNotIn("{%", html)
                self.assertIn('hreflang="en"', html)
                self.assertIn('hreflang="de"', html)
                self.assertNotIn('x"><script>', html)
        html = render_page("index.html", "en", "https://untrusted.example/?year=2025").decode()
        self.assertNotIn("untrusted.example", html)
        self.assertIn("Europe’s electricity systems at a glance.", html)

    def test_localization_is_a_copy_and_preserves_machine_fields(self):
        original = {"country_code": "DE", "country_name": "Germany", "generation_twh": 123.45,
                    "missing": None, "quality_status": "observed", "period": "2025-01",
                    "metric": dict(METRICS[0]), "warnings": ["source_withdrawn"]}
        before = copy.deepcopy(original)
        german = localize_payload(original, "de")
        self.assertEqual(original, before)
        self.assertEqual(german["country_name"], "Deutschland")
        for key in ("generation_twh", "missing", "quality_status", "period", "warnings"):
            self.assertEqual(original[key], german[key])

    def test_retention_warning_is_english_internally_and_keeps_legacy_german_text(self):
        warning = {"issue_type": "retained_source_gap", "severity": "warning",
                   "details": RETAINED_DETAILS_PREFIX["en"] + "2024-01, 2024-02."}
        german = localize_payload(warning, "de")
        self.assertEqual(german["details"], RETAINED_DETAILS_PREFIX["de"] + "2024-01, 2024-02.")
        self.assertEqual(localize_payload(german, "en"), warning)


class LocalizationHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="eea-localization-test-")
        cls.db = Path(cls.temp.name) / "atlas.sqlite3"
        cls.server = create_server(cls.db, "127.0.0.1", 0, community_path=Path(cls.temp.name) / "community.sqlite3")
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        with connect(cls.db) as connection:
            for code, value in (("DE", 400), ("FR", 500)):
                connection.execute("""INSERT INTO period_observation
                    (country_code,period_start,period_end,granularity,source,source_endpoint,
                     source_series,metric,value,unit,quality_status)
                    VALUES (?, '2025-01-01', '2025-12-31', 'yearly', ?, 'fixture', '',
                            'generation_total', ?, 'TWh', 'observed')""", (code, EMBER_SOURCE_NAME, value))
            connection.commit()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        cls.server.server_close()
        cls.temp.cleanup()

    def fetch(self, path, cookie=""):
        with urlopen(Request(self.base + path, headers={"Cookie": cookie}), timeout=10) as response:
            return response.read(), response.headers

    def test_language_preference_and_explicit_link_precedence(self):
        for path, cookie, lang in (("/", "", "de"), ("/", "eea_language=en", "en"),
                                   ("/?lang=de", "eea_language=en", "de"),
                                   ("/?lang=en", "eea_language=de", "en"),
                                   ("/?lang=invalid", "", "de")):
            body, headers = self.fetch(path, cookie)
            self.assertIn(f'<html lang="{lang}">'.encode(), body)
            self.assertEqual(headers["Content-Language"], lang)
            self.assertEqual(headers["Vary"], "Cookie")
            self.assertIn("private", headers["Cache-Control"])
            self.assertNotIn("Set-Cookie", headers)

    def test_templates_cannot_be_downloaded_unrendered(self):
        with self.assertRaises(HTTPError) as error:
            self.fetch("/language-switch.html")
        self.assertEqual(error.exception.code, 404)
        html, _ = self.fetch("/./index.html?lang=en")
        self.assertNotIn(b"{{", html)

    def test_api_default_ignores_browser_cookie_and_rejects_invalid_language(self):
        body, _ = self.fetch("/api/countries", "eea_language=en")
        self.assertEqual(next(c["name"] for c in json.loads(body) if c["code"] == "DE"), "Deutschland")
        with self.assertRaises(HTTPError) as error:
            self.fetch("/api/metrics?lang=fr")
        self.assertEqual(error.exception.code, 400)

    def test_analytical_endpoints_keep_all_numbers_dates_ids_and_statuses(self):
        # Exclude only the documented presentation fields, not every string.
        translated = {"country_name", "name", "label", "group", "family", "unit", "source",
                      "source_label", "price_source_label", "representation", "display_topic", "display_metric", "display_basis"}
        def machine(value):
            if isinstance(value, list):
                return [machine(item) for item in value]
            if isinstance(value, dict):
                return {k: machine(v) for k, v in value.items() if k not in translated}
            return value
        paths = ["/api/countries", "/api/metrics", "/api/summary?year=2025",
                 "/api/compare?year=2025&countries=DE,FR", "/api/country-profile?year=2025&country=DE",
                 "/api/map-data?year=2025&metric=capacity_total_gw", "/api/storage", "/api/coverage?year=2025",
                 "/api/timeseries?metric=generation_per_capita_mwh&countries=DE,FR&start=2024&end=2025"]
        for path in paths:
            with self.subTest(path=path):
                default = json.loads(self.fetch(path)[0])
                separator = "&" if "?" in path else "?"
                de = json.loads(self.fetch(path + separator + "lang=de")[0])
                en = json.loads(self.fetch(path + separator + "lang=en")[0])
                self.assertEqual(default, de)
                self.assertEqual(machine(de), machine(en))
        en = json.loads(self.fetch("/api/compare?year=2025&countries=DE,FR&lang=en")[0])
        self.assertEqual([row["generation_twh"] for row in en], [400, 500])
        self.assertEqual([row["country_name"] for row in en], ["Germany", "France"])
