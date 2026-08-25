from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
STYLE = (ROOT / "web" / "style.css").read_text(encoding="utf-8")


class CountryProfileUiContractTests(unittest.TestCase):
    def test_full_width_profile_container_and_entry_actions_exist(self):
        self.assertIn('id="country-profile"', HTML)
        self.assertIn('id="atlas-content"', HTML)
        self.assertIn('data-country-profile="${row.country_code}"', APP)
        self.assertIn('data-country-profile="${escapeAttribute(code)}"', APP)
        self.assertIn("function openCountryProfile(code)", APP)
        self.assertIn(".country-profile", STYLE)

    def test_profile_uses_one_bundled_api_and_period_aware_direct_link(self):
        self.assertIn("/api/country-profile?country=${encodeURIComponent(code)}&${periodQuery()}", APP)
        self.assertIn('params.set("view", "country")', APP)
        self.assertIn('params.set("period", isMonthView() ? "month" : "year")', APP)
        self.assertIn('params.set("month", $("month").value)', APP)
        self.assertIn("function syncControlsFromProfileUrl()", APP)
        self.assertIn("function configureCountryProfileNavigation()", APP)

    def test_active_profile_refreshes_with_the_global_period_controls(self):
        summary = APP[APP.index("async function loadSummary()"):APP.index("function timeseriesMetrics()")]
        self.assertIn("if (activeProfileCountry) await refreshActiveCountryProfile();", summary)
        self.assertIn("async function refreshActiveCountryProfile()", APP)
        self.assertIn('params.set("year", String(selectedYear()))', APP)
        self.assertIn('params.set("period", isMonthView() ? "month" : "year")', APP)
        self.assertIn('await loadCountryProfile({scroll: false});', APP)

    def test_profile_adds_to_comparison_enforces_ten_country_limit_and_refreshes_the_plot(self):
        profile_compare = APP[APP.index("function openProfileInComparison()"):APP.index("function configureCountryProfileNavigation()")]
        self.assertNotIn("selected.clear()", profile_compare)
        self.assertIn("selected.size >= 10", profile_compare)
        self.assertIn("selected.add(code)", profile_compare)
        self.assertIn("await loadTimeseries({scroll: false, updateUrl: true});", profile_compare)

    def test_profile_shows_only_source_and_year_for_metric_provenance(self):
        self.assertIn("function profileSourceYear(metric)", APP)
        self.assertIn('[metric.source, profileSourceYear(metric)].filter(Boolean).join(" · ")', APP)
        self.assertNotIn('class="profile-meta"', APP)
        self.assertNotIn('class="profile-warning"', APP)
        self.assertIn("PROFILE_SECTION_MERGES", APP)
        self.assertIn("Stromhandel und Preise", APP)
        self.assertIn("setDocumentTitle(\"country\")", APP)

    def test_direct_profile_view_cannot_be_replaced_by_default_comparison_initialization(self):
        initialization = APP[APP.index("loadMetricCatalog()"):]
        self.assertIn("if (profileUrlState()) {", initialization)
        self.assertLess(initialization.index("if (profileUrlState()) {"), initialization.rindex("restoreComparisonState()"))
        self.assertIn("await loadCountryProfile();", initialization)
