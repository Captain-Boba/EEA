import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
SCRIPT = (ROOT / "web" / "mobile-viewport.js").read_text(encoding="utf-8")
STYLE = (ROOT / "web" / "style.css").read_text(encoding="utf-8")


class MobileDesktopViewportTests(unittest.TestCase):
    def test_mobile_viewport_script_runs_before_stylesheet(self):
        self.assertIn('id="viewport-meta"', INDEX)
        self.assertIn('src="/mobile-viewport.js?v=desktop-workspace-v1"', INDEX)
        self.assertLess(INDEX.index("/mobile-viewport.js"), INDEX.index("/style.css"))

    def test_mobile_devices_receive_full_hd_workspace_without_disabling_zoom(self):
        self.assertIn("const FORCED_DESKTOP_WIDTH = 1920", SCRIPT)
        self.assertIn("navigator.userAgentData?.mobile", SCRIPT)
        self.assertIn("Android|webOS|iPhone|iPad|iPod|IEMobile|Opera Mini", SCRIPT)
        self.assertIn('navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1', SCRIPT)
        self.assertIn('window.matchMedia("(pointer: coarse)").matches', SCRIPT)
        self.assertIn("Math.min(window.screen.width, window.screen.height) <= 600", SCRIPT)
        self.assertIn("user-scalable=yes", SCRIPT)
        self.assertNotIn("user-scalable=no", SCRIPT)
        self.assertIn('classList.add(LAYOUT_CLASS)', SCRIPT)

    def test_mobile_notice_explains_orientation_zoom_and_horizontal_navigation(self):
        self.assertIn('id="mobile-desktop-notice"', INDEX)
        self.assertIn("Desktopansicht aktiviert", INDEX)
        self.assertIn("quer halten", INDEX)
        self.assertIn("zwei Fingern zoomen", INDEX)
        self.assertIn("horizontal verschieben", INDEX)
        self.assertIn("eea-mobile-desktop-notice-dismissed", SCRIPT)
        self.assertIn(".mobile-desktop-notice", STYLE)


if __name__ == "__main__":
    unittest.main()
