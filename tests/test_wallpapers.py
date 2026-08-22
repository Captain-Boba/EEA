import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WallpaperTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.javascript = (ROOT / "web" / "wallpapers.js").read_text(encoding="utf-8")
        cls.html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "web" / "style.css").read_text(encoding="utf-8")
        cls.manifest = cls.javascript.split("const WALLPAPERS", 1)[1].split("]);", 1)[0]

    def test_manifest_contains_unique_commons_wallpapers(self):
        titles = re.findall(r'\{title: "([^"]+)"', self.manifest)
        files = re.findall(r'file: "([^"]+)"', self.manifest)
        self.assertEqual(len(titles), 186)
        self.assertEqual(len(set(titles)), 186)
        self.assertEqual(len(set(files)), 186)

    def test_manifest_carries_visible_attribution_fields(self):
        self.assertEqual(len(re.findall(r'author: "[^"]+"', self.manifest)), 186)
        self.assertEqual(len(re.findall(r'license: "[^"]+"', self.manifest)), 186)
        self.assertIn("https://commons.wikimedia.org/wiki/File:", self.javascript)
        self.assertIn("Wikimedia Commons", self.javascript)

    def test_random_sequence_uses_side_postcard_panels(self):
        self.assertNotIn("WALLPAPERS_ENABLED", self.javascript)
        self.assertIn('const OVERLOAD_STORAGE_KEY = "eea-europa-overload"', self.javascript)
        self.assertIn("function highResolutionImage(file)", self.javascript)
        self.assertIn("?width=3840", self.javascript)
        self.assertIn("function shuffled(items)", self.javascript)
        self.assertIn("sequence = shuffled(WALLPAPERS)", self.javascript)
        self.assertIn("function centeredWallpaperIndex()", self.javascript)
        self.assertIn("window.scrollY + viewportHeight / 2", self.javascript)
        self.assertIn('window.addEventListener("scroll", scheduleWallpaperUpdate, {passive: true})', self.javascript)
        self.assertIn('window.removeEventListener("scroll", scheduleWallpaperUpdate)', self.javascript)
        self.assertIn("function createPanel(index)", self.javascript)
        self.assertIn('panel.className = "wallpaper-panel"', self.javascript)
        self.assertIn("function postcardStep()", self.javascript)
        self.assertIn('panel.style.top = `${index * postcardStep() + Math.max(24, viewportHeight * .06)}px`', self.javascript)
        self.assertIn("[index - 1, index, index + 1]", self.javascript)
        self.assertIn("Math.ceil(contentHeight / postcardStep())", self.javascript)
        self.assertEqual(self.javascript.count("new Image()"), 1)

    def test_overload_is_opt_in_persistent_and_fully_cleaned_up(self):
        self.assertIn("function readOptIn()", self.javascript)
        self.assertIn("function persistOptIn(enabled)", self.javascript)
        self.assertIn("function start()", self.javascript)
        self.assertIn("function stop()", self.javascript)
        self.assertIn("if (readOptIn()) setEnabled(true)", self.javascript)
        self.assertIn("stream.replaceChildren()", self.javascript)
        self.assertIn("cancelAnimationFrame(scrollFrame)", self.javascript)
        self.assertIn("resizeObserver?.disconnect()", self.javascript)
        self.assertIn("window.__atlasWallpaper = controller", self.javascript)

    def test_page_has_stream_and_script(self):
        self.assertIn('id="wallpaper-stream"', self.html)
        self.assertIn('id="europe-overload"', self.html)
        self.assertIn('aria-pressed="false"', self.html)
        self.assertNotIn('id="wallpaper-credit"', self.html)
        self.assertIn('src="/wallpapers.js?v=europa-overload-v1"', self.html)

    def test_panels_scroll_naturally_and_keep_content_above_them(self):
        self.assertRegex(self.css, r"body\s*\{[^}]*isolation:\s*isolate;[^}]*background-attachment:\s*scroll;")
        self.assertRegex(self.css, r"\.wallpaper-stream\s*\{[^}]*position:\s*absolute;[^}]*overflow:\s*hidden;")
        self.assertRegex(self.css, r"\.wallpaper-panel\s*\{[^}]*position:\s*absolute;")
        self.assertIn(".wallpaper-panel:nth-child(odd)", self.css)
        self.assertIn(".wallpaper-panel:nth-child(even)", self.css)
        self.assertIn("width: min(24rem, 24vw)", self.css)
        self.assertIn(".wallpaper-panel:nth-child(odd) { left: .75rem; }", self.css)
        self.assertIn(".wallpaper-panel:nth-child(even) { right: .75rem;", self.css)
        self.assertIn(".wallpaper-panel::after", self.css)
        self.assertIn(".wallpaper-caption", self.css)
        self.assertIn("bottom: calc(100% + .55rem)", self.css)
        self.assertIn('caption.className = "wallpaper-caption"', self.javascript)
        self.assertNotIn("wallpaper-credit", self.css)
        self.assertIn("background-size: cover", self.css)
        self.assertRegex(self.css, r"main\s*\{\s*position:\s*relative;\s*z-index:\s*1;")


if __name__ == "__main__":
    unittest.main()
