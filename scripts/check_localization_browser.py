"""Opt-in local DE/EN browser regression check; never refreshes/publishes data.

Run with PYTHONPATH=src. Requires the project Playwright browser installation.
The Atlas database is opened read-only; votes use a disposable community store.
All remote image requests are fulfilled locally, not sent to Wikimedia.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

from electricity_atlas.server import create_server


def check(db: Path, artifacts: Path) -> None:
    artifacts.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="eea-language-browser-") as directory:
        server = create_server(db.resolve(), "127.0.0.1", 0,
                               community_path=Path(directory) / "community.sqlite3", require_existing_db=True)
        server.RequestHandlerClass.log_message = lambda *args: None
        original_handle_error = server.handle_error
        def handle_error(request, address):
            # Navigating deliberately cancels outstanding asset/API requests.
            # Do not hide any other server-side exception from this check.
            if not isinstance(sys.exception(), (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
                original_handle_error(request, address)
        server.handle_error = handle_error
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, env={**os.environ,
                    "CHROME_LOG_FILE": str((artifacts / "chromium.log").resolve())})
                context = browser.new_context(viewport={"width": 1536, "height": 1000}, reduced_motion="reduce")
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                # Exercise image loading and gallery state without using third-party bandwidth.
                context.route("https://**/*", lambda route: route.fulfill(status=200, content_type="image/svg+xml",
                    body='<svg xmlns="http://www.w3.org/2000/svg" width="160" height="90"><rect width="160" height="90" fill="#164563"/></svg>'))

                def ready():
                    page.wait_for_function("typeof timeseriesData !== 'undefined' && timeseriesData?.countries?.length > 0")
                    page.wait_for_function("document.querySelectorAll('#summary-table tbody tr').length > 0")

                page.goto(base + "/")
                ready()
                assert page.url == base + "/", "Initial visit changed the URL"
                assert page.title() == "European Electricity Atlas", page.title()
                assert page.locator("html").get_attribute("lang") == "de"
                for lang in ("en", "de"):
                    page.locator(f'[data-language="{lang}"]').click()
                    ready()
                    assert page.locator("html").get_attribute("lang") == lang
                    page.wait_for_timeout(200)
                    assert page.evaluate("selected.size") == 5
                    text = page.locator("#summary-table").inner_text()
                    assert ("Germany" if lang == "en" else "Deutschland") in text
                    # The map toolbar must not cover either dropdown or checkbox.
                    actions = page.locator(".map-actions").bounding_box()
                    controls = page.locator(".map-controls").bounding_box()
                    assert actions["y"] >= controls["y"] + controls["height"]
                    page.screenshot(path=str(artifacts / f"home-{lang}.png"))
                    for name, expression in (("map", "serializedMapSvg()"), ("comparison", "serializedComparisonExportSvg()")):
                        svg = page.evaluate(expression)
                        assert "{{" not in svg and "<svg" in svg
                        assert ("Atlas average" if lang == "en" else "Atlas-Durchschnitt") in svg
                        if lang == "en":
                            assert "Atlas-Durchschnitt" not in svg
                        # Parse in the browser to detect invalid SVG markup.
                        assert page.evaluate("svg => !new DOMParser().parseFromString(svg, 'image/svg+xml').querySelector('parsererror')", svg)
                    png = page.evaluate("async () => {const blob=await buildMapPngBlob(); const bytes=new Uint8Array(await blob.arrayBuffer()); return {size:blob.size, magic:[...bytes.slice(0,8)]};}")
                    assert png["size"] > 10000 and png["magic"] == [137,80,78,71,13,10,26,10]
                    chart_png = page.evaluate("async () => (await buildChartPngBlob()).size")
                    assert chart_png > 10000
                    csv = page.evaluate("buildComparisonCsv(timeseriesData)")
                    assert csv.startswith("period,") and "DE" in csv and "atlas_average" in csv
                    page.locator("#map-fullscreen").click()
                    page.wait_for_function("document.fullscreenElement?.id === 'map-stage'")
                    assert page.locator("#map-fullscreen").inner_text() == ("Exit fullscreen" if lang == "en" else "Vollbild verlassen")
                    page.locator("#map-fullscreen").click()
                    page.wait_for_function("!document.fullscreenElement")
                    print(f"PASS {lang}: rendering, root state, map/plot SVG and PNG, CSV", flush=True)

                # Change state through the actual controls/functions, then switch language.
                page.evaluate("""async () => {
                    selected.clear(); selected.add('DE'); selected.add('FR');
                    renderComparisonControls('generation_twh');
                    document.getElementById('compare-start').value='2024-01';
                    document.getElementById('compare-end').value='2025-12';
                    document.getElementById('compare-axis-mode').value='full';
                    await loadTimeseries({updateUrl:true, scroll:false});
                    mapMetricId='renewable_share_pct'; renderMapControls(); renderMap();
                    summaryExpanded=true; sortKey='generation_twh'; sortDirection=1; render();
                }""")
                before = page.evaluate("window.AtlasI18n.captureState()")
                page.locator('[data-language="en"]').click()
                ready()
                page.wait_for_function("summaryExpanded && sortDirection === 1 && selected.size === 2")
                after = page.evaluate("window.AtlasI18n.captureState()")
                for key in ("controls", "countries", "comparisonMetric", "mapMetric", "sortKey", "sortDirection", "summaryExpanded"):
                    assert before[key] == after[key], (key, before[key], after[key])
                assert "lang=en" in page.url and "countries=DE%2CFR" in page.url
                print("PASS language switch preserves metric, date range, countries, axes and table state", flush=True)

                page.evaluate("openCountryProfile('DE')")
                page.wait_for_function("document.querySelector('#country-profile').innerText.includes('Germany')")
                page.locator('[data-language="de"]').click()
                page.wait_for_function("document.querySelector('#country-profile').innerText.includes('Deutschland')")
                assert "view=country" in page.url
                assert page.locator("#country-profile").is_visible()
                print("PASS country profile and direct link survive language switch", flush=True)

                # Exercise each map layer with real local data, including annual
                # fallbacks and snapshots; no translated label may become an ID.
                page.goto(base + "/?lang=en")
                ready()
                mapped = page.evaluate("""async () => {
                    const ids=[...metricCatalog.values()].filter(metric=>metric.map).map(metric=>metric.id);
                    for (const id of ids) {
                        await selectMapMetricForPeriod(id);
                        if (mapMetricId!==id || !mapPaletteName(metricCatalog.get(id))) throw new Error('Layer failed: '+id);
                    }
                    return ids.length;
                }""")
                assert mapped == 87
                page.goto(base + "/?view=country&country=DE&year=2025&period=month&month=7&lang=en")
                page.wait_for_function("document.querySelector('#country-profile').innerText.includes('Germany')")
                page.screenshot(path=str(artifacts / "profile-en.png"), full_page=True)
                assert page.locator("#period-type").input_value() == "month"
                assert page.locator("#month").input_value() == "7"
                page.locator('[data-language="de"]').click()
                page.wait_for_function("document.querySelector('#country-profile').innerText.includes('Deutschland')")
                assert page.locator("#month").input_value() == "7"
                print("PASS all 87 map layers and monthly profile state", flush=True)

                page.goto(base + "/?lang=en")
                ready()
                page.locator("#europe-overload").click()
                page.wait_for_function("window.__atlasWallpaper?.isEnabled()")
                page.locator(".wallpaper-panel").first.evaluate("panel => panel.click()")
                page.wait_for_function("!document.querySelector('#wallpaper-lightbox').hidden")
                gallery_before = page.evaluate("window.__atlasWallpaper.captureState()")
                page.keyboard.press("ArrowRight")
                assert page.evaluate("window.__atlasWallpaper.captureState().index") == 1
                page.keyboard.press("ArrowLeft")
                page.keyboard.press("ArrowUp")
                page.wait_for_function("document.querySelector('.wallpaper-vote-up').getAttribute('aria-pressed') === 'true'")
                page.keyboard.press("ArrowDown")
                page.wait_for_function("document.querySelector('.wallpaper-vote-down').getAttribute('aria-pressed') === 'true'")
                page.evaluate("document.querySelector('[data-language=de]').click()")
                ready()
                page.wait_for_function("window.__atlasWallpaper?.captureState().index === 0")
                assert page.evaluate("window.__atlasWallpaper.captureState()") == gallery_before
                assert "Bildwechsel" in page.locator("#wallpaper-vote-help-tooltip").text_content()
                assert page.locator(".wallpaper-vote-down").get_attribute("aria-pressed") == "true"
                page.keyboard.press("Escape")
                print("PASS gallery order, all four arrow keys, local voting and translation", flush=True)

                # Static pages and their metadata work without JS, including crawlers.
                nojs = browser.new_context(java_script_enabled=False)
                static = nojs.new_page()
                for lang in ("de", "en"):
                    for path in ("/", "/contact.html", "/privacy.html", "/api.html"):
                        static.goto(base + path + "?lang=" + lang)
                        assert static.locator("html").get_attribute("lang") == lang
                        assert "{{" not in static.content()
                        assert static.locator('[data-language="en"]').count() == 1
                nojs.close()
                # Mobile still uses the intentional zoomable desktop workspace.
                mobile = browser.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True,
                    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148")
                mobile_page = mobile.new_page()
                mobile_page.goto(base + "/?lang=en")
                mobile_page.wait_for_selector("#mobile-desktop-notice", state="visible")
                assert "Desktop view enabled" in mobile_page.locator("#mobile-desktop-notice").inner_text()
                assert "width=1920" in mobile_page.locator('meta[name="viewport"]').get_attribute("content")
                mobile.close()
                context.route("**/api/metrics?*", lambda route: route.fulfill(
                    status=503, content_type="application/json", body='{"error":"Failed to fetch"}'))
                for lang, expected in (("de", "Fehler: Der Abruf ist fehlgeschlagen"), ("en", "Error: Failed to fetch")):
                    page.goto(base + "/?lang=" + lang)
                    page.wait_for_function("expected => document.querySelector('#status').textContent === expected", arg=expected)
                assert not errors, errors
                print("PASS no-JS pages, metadata, mobile notice, localized errors; no browser errors", flush=True)
                browser.close()
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/atlas.sqlite3"))
    parser.add_argument("--artifacts", type=Path, required=True, help="Directory for local QA screenshots")
    args = parser.parse_args()
    check(args.db, args.artifacts)
