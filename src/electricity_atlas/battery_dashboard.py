"""Public Battery-Charts CSV exports; no API keys or private endpoints."""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from .config import BATTERY_CHARTS_ENERGY_ENDPOINT, BATTERY_CHARTS_POWER_ENDPOINT
from .storage_errors import StorageOnlineError
from .storage_online import SourceDownload


BATTERY_DASHBOARD_URL = "https://battery-charts.de/battery-charts/"


class BatteryDashboardClient:
    """Use the same two download buttons as a visitor, in a temporary browser.

    CSV numbers are in GWh/GW, unlike the old local JSON's kWh/kW. The
    importer handles that explicit format distinction and retains raw CSV.
    No cookies, page scripts, API credentials or temporary URLs are persisted.
    """

    def fetch_pair(self) -> tuple[SourceDownload, SourceDownload]:
        from playwright.sync_api import Error as PlaywrightError, sync_playwright

        downloads = []
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                try:
                    page = browser.new_page(locale="en-GB", viewport={"width": 1600, "height": 1000})
                    page.set_default_timeout(30_000)
                    response = page.goto(BATTERY_DASHBOARD_URL, wait_until="domcontentloaded", timeout=90_000)
                    if response is None or response.status != 200:
                        raise StorageOnlineError("Battery-Charts landing page was not successful")
                    for chart_id, endpoint, unit in (
                        ("bessCumulativeEnergyChart", BATTERY_CHARTS_ENERGY_ENDPOINT, "GWh"),
                        ("bessCumulativePowerChart", BATTERY_CHARTS_POWER_ENDPOINT, "GW"),
                    ):
                        # Wait for actual chart data, not an arbitrary network-idle
                        # delay. Also fail closed if the dashboard changes units.
                        page.wait_for_function("""({id, unit}) => {
                            const chart = globalThis.Chart?.getChart(id);
                            return chart?.data?.labels?.length > 0 &&
                                chart.data.datasets?.length === 3 &&
                                chart.data.datasets.every(d => d.data.length === chart.data.labels.length) &&
                                Array.from(chart.options.scales.y.title.text).includes('in ' + unit);
                        }""", arg={"id": chart_id, "unit": unit})
                        button = page.locator(f"canvas#{chart_id}").locator("..").get_by_title(
                            "Download Recent Data", exact=True
                        )
                        with page.expect_download(timeout=30_000) as pending:
                            button.click()
                        download = pending.value
                        if download.suggested_filename != f"{chart_id}.csv":
                            raise StorageOnlineError("Battery-Charts download format changed")
                        path = download.path()
                        if path is None or Path(path).stat().st_size > 5_000_000:
                            raise StorageOnlineError("Battery-Charts CSV missing or unexpectedly large")
                        raw = Path(path).read_bytes()
                        downloads.append(SourceDownload(
                            source="battery_charts", endpoint=endpoint,
                            request_url=BATTERY_DASHBOARD_URL,
                            fetched_at=datetime.now(UTC).isoformat(), status_code=200,
                            content_type="text/csv", etag=None, last_modified=None,
                            sha256=hashlib.sha256(raw).hexdigest(), payload_text=raw.decode("utf-8-sig"),
                        ))
                finally:
                    browser.close()  # also removes all browser-managed downloads
        except (PlaywrightError, OSError, UnicodeError) as exc:
            # Browser error text can contain third-party request URLs. Do not
            # retain those URLs or embedded query parameters in refresh reports.
            raise StorageOnlineError(f"Battery-Charts browser export failed ({type(exc).__name__})") from exc
        return downloads[0], downloads[1]
