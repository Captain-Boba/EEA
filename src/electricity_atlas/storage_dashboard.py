from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from .config import JRC_SOURCE_NAME, JRC_STORAGE_DASHBOARD_URL
from .storage_importer import JRC_DASHBOARD_EXPORTS, StorageCachePayload
from .storage_errors import StorageOnlineError


@dataclass(frozen=True)
class JrcDashboardDownloads:
    snapshot_date: str
    exports: dict[tuple[str, str], StorageCachePayload]


class JrcDashboardClient:
    """Download the four explicitly filtered JRC dashboard XLSX exports.

    The dashboard is a public Qlik application, not a stable file endpoint.
    This client only uses its visible controls and deliberately stores the
    stable official landing page as provenance, never an ephemeral download
    location, browser cookie, or Qlik object identifier.
    """

    DASHBOARD_WAIT_MS = 20_000
    CONTROL_WAIT_MS = 650

    def __init__(
        self,
        *,
        dashboard_url: str = JRC_STORAGE_DASHBOARD_URL,
        now: Any | None = None,
        headed: bool = True,
    ):
        self.dashboard_url = dashboard_url
        self.now = now or (lambda: datetime.now(UTC))
        self.headed = headed

    def fetch_exports(self) -> JrcDashboardDownloads:
        try:
            from playwright.sync_api import Error as PlaywrightError
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise StorageOnlineError(
                "JRC dashboard automation requires Playwright; install the project dependencies first"
            ) from exc

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=not self.headed)
                try:
                    page = browser.new_page(viewport={"width": 1600, "height": 1000})
                    page.goto(self.dashboard_url, wait_until="domcontentloaded", timeout=90_000)
                    frame = self._dashboard_frame(page)
                    exports: dict[tuple[str, str], StorageCachePayload] = {}
                    for kind, technology, subtechnology in (
                        ("battery", "Electrochemical", None),
                        ("pumped_storage", "Mechanical", "Pumped Hydro Storage (PHS)"),
                    ):
                        self._clear_selections(frame)
                        self._select_filter(frame, "Project status", "Operational")
                        self._select_filter(frame, "Technology", technology)
                        if subtechnology is not None:
                            self._select_filter(frame, "Subtechnology", subtechnology)
                        for dimension in ("power", "capacity"):
                            payload = self._download_dimension(page, frame, dimension)
                            endpoint = JRC_DASHBOARD_EXPORTS[(kind, dimension)]
                            exports[(kind, dimension)] = StorageCachePayload(
                                endpoint=endpoint,
                                path=Path(f"jrc-{kind}-{dimension}.xlsx"),
                                payload_bytes=payload,
                                request_url=self.dashboard_url,
                                fetched_at=self.now().isoformat(),
                                status_code=200,
                                content_type=(
                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                ),
                            )
                    snapshot = self._snapshot_date(frame)
                finally:
                    browser.close()
        except (PlaywrightError, PlaywrightTimeoutError, OSError) as exc:
            raise StorageOnlineError(
                f"JRC dashboard export failed ({type(exc).__name__}: {exc}); no local storage data were changed"
            ) from exc
        return JrcDashboardDownloads(snapshot_date=snapshot, exports=exports)

    def _dashboard_frame(self, page: Any) -> Any:
        deadline = self.DASHBOARD_WAIT_MS // 250
        for _ in range(deadline):
            for frame in page.frames:
                if "dashboard/embed" in frame.url:
                    try:
                        frame.get_by_role("button", name="Clear all selections").first.wait_for(
                            state="visible", timeout=250
                        )
                        return frame
                    except Exception:
                        pass
            page.wait_for_timeout(250)
        raise StorageOnlineError("JRC dashboard did not become ready")

    def _clear_selections(self, frame: Any) -> None:
        frame.get_by_role("button", name="Clear all selections").first.click(force=True)
        frame.page.wait_for_timeout(self.CONTROL_WAIT_MS)

    def _select_filter(self, frame: Any, name: str, option: str) -> None:
        field = frame.locator(f'[data-testid="collapsed-title-{name}"]').first
        field.scroll_into_view_if_needed()
        field.click(force=True)
        box = frame.locator('[data-testid="filterpane-listbox-container"]')
        box.wait_for(state="visible", timeout=10_000)
        choice = box.get_by_text(option, exact=True)
        choice.wait_for(state="visible", timeout=10_000)
        choice.click(force=True)
        box.get_by_label("Confirm selection").click(force=True)
        frame.page.wait_for_timeout(self.CONTROL_WAIT_MS)

    def _download_dimension(self, page: Any, frame: Any, dimension: str) -> bytes:
        if dimension == "power":
            button_name = "Power (GW)"
            chart_name = "Storage power (GW) by country and status"
        elif dimension == "capacity":
            button_name = "Capacity (GWh)"
            chart_name = "Capacity (GWh) by country and status"
        else:  # pragma: no cover - guarded by the fixed caller
            raise StorageOnlineError(f"Unsupported JRC dashboard dimension {dimension}")
        frame.get_by_role("button", name=button_name).first.click(force=True)
        frame.page.wait_for_timeout(self.CONTROL_WAIT_MS)
        chart = frame.get_by_role("tabpanel", name=chart_name)
        chart.scroll_into_view_if_needed()
        box = chart.bounding_box()
        if not box:
            raise StorageOnlineError(f"JRC dashboard {dimension} chart is not visible")
        chart.hover(position={"x": max(box["width"] * 0.8, 10), "y": max(box["height"] * 0.55, 10)})
        frame.page.wait_for_timeout(250)
        download_button = self._visible(frame.locator('[title="Download data"]'))
        with page.expect_download(timeout=30_000) as download_info:
            download_button.click(force=True)
        download = download_info.value
        path = download.path()
        if not path:
            raise StorageOnlineError("JRC dashboard download did not provide a file")
        payload = Path(path).read_bytes()
        if not payload:
            raise StorageOnlineError("JRC dashboard download is empty")
        return payload

    @staticmethod
    def _visible(locator: Any) -> Any:
        for candidate in locator.all():
            if candidate.is_visible():
                return candidate
        raise StorageOnlineError("JRC dashboard did not expose its Download data control")

    @staticmethod
    def _snapshot_date(frame: Any) -> str:
        text = frame.locator("body").inner_text()
        match = re.search(r"Last update:\s*(\d{2}/\d{2}/\d{4})", text)
        if not match:
            raise StorageOnlineError("JRC dashboard did not expose a data-stamp")
        try:
            return datetime.strptime(match.group(1), "%d/%m/%Y").date().isoformat()
        except ValueError as exc:  # pragma: no cover - protected by the expression above
            raise StorageOnlineError("JRC dashboard has an invalid data-stamp") from exc
