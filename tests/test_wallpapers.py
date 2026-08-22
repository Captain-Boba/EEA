import re
import unittest
from pathlib import Path

from electricity_atlas.config import ATLAS_COUNTRIES


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
        self.assertEqual(len(titles), 250)
        self.assertEqual(len(set(titles)), 250)
        self.assertEqual(len(set(files)), 250)

    def test_manifest_carries_visible_attribution_fields(self):
        self.assertEqual(len(re.findall(r'author: "[^"]+"', self.manifest)), 250)
        self.assertEqual(len(re.findall(r'license: "[^"]+"', self.manifest)), 250)
        self.assertIn("https://commons.wikimedia.org/wiki/File:", self.javascript)

    def test_manifest_sources_fit_square_preview(self):
        dimensions = [
            (int(width), int(height))
            for width, height in re.findall(r'width: (\d+), height: (\d+)', self.manifest)
        ]
        self.assertEqual(len(dimensions), 250)
        for width, height in dimensions:
            self.assertGreaterEqual(width, 3000)
            self.assertGreaterEqual(height, 2500)
            self.assertGreaterEqual(width / height, 0.8)
            self.assertLessEqual(width / height, 1.6)

    def test_manifest_only_uses_atlas_countries(self):
        atlas_country_names = {country.name for country in ATLAS_COUNTRIES.values()}
        countries = re.findall(r'country: "([^"]+)"', self.manifest)
        self.assertEqual(len(countries), 250)
        for label in countries:
            self.assertTrue(
                all(country in atlas_country_names for country in label.split(" / ")),
                f"Wallpaper country is outside the Atlas catalog: {label}",
            )

    def test_rejected_wallpapers_do_not_return(self):
        rejected_files = {
            "Ivo Pevalek.jpg",
            "Seat of the European Central Bank and Frankfurt Skyline at dawn 20150422 1.jpg",
            "Megyeri híd.jpg",
            "Panorama of Tallinn, Estonia (8067727177).jpg",
            "Lysekil Panorama.jpg",
            "Znojmo Old Town Panorama from Castle 20190217.jpg",
            "Korfu (GR), Korfu, Alte Festung -- 2018 -- 1137.jpg",
            "The Duomo and Tower of Pisa at sunrise.jpg",
            "Seine wide.jpg",
            "Rouen France Panoramic-View-02.jpg",
            "Real Monasterio de San Juan de la Peña, Huesca, España, 2023-01-05, DD 48-50 HDR.jpg",
            "London 360 from St Paul's Cathedral - Sept 2007.jpg",
            "Panorámica Madrid, con Sierra de Guadarrama al fondo.jpg",
            "Firth of Forth bridges panorama by Greg Barbier 13750x1915.jpg",
            "Warsaw 07-13 img29 View from Palace of Culture and Science.jpg",
            "Livorno Panorama.jpg",
            "Brandenburg Pano 02 (MK).jpg",
        }
        manifest_files = set(re.findall(r'file: "([^"]+)"', self.manifest))
        self.assertTrue(rejected_files.isdisjoint(manifest_files))

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

    def test_postcards_have_an_accessible_lightbox_with_local_reactions(self):
        self.assertIn('const REACTION_STORAGE_KEY = "eea-europa-overload-reactions"', self.javascript)
        self.assertIn('lightbox.id = "wallpaper-lightbox"', self.javascript)
        self.assertIn('lightbox.setAttribute("aria-modal", "true")', self.javascript)
        self.assertIn('closeStar.src = "/assets/europe-star.svg"', self.javascript)
        self.assertIn("function openLightbox(index, panel)", self.javascript)
        self.assertIn("function closeLightbox", self.javascript)
        self.assertIn('event.key === "Escape"', self.javascript)
        self.assertIn('if (event.target === lightbox) closeLightbox()', self.javascript)
        self.assertIn("function handleLightboxKeydown(event)", self.javascript)
        self.assertIn("function setReaction(reaction)", self.javascript)
        self.assertIn("window.scrollTo({top: lockedScrollY", self.javascript)
        self.assertIn("panel.setAttribute(\"role\", \"button\")", self.javascript)

    def test_lightbox_styles_preserve_image_and_respect_reduced_motion(self):
        self.assertIn(".wallpaper-lightbox {", self.css)
        self.assertIn("object-fit: contain", self.css)
        self.assertIn(".wallpaper-lightbox-close", self.css)
        self.assertIn(".wallpaper-reactions", self.css)
        self.assertIn(".wallpaper-lightbox-card { transition: none; }", self.css)

    def test_page_has_stream_and_script(self):
        self.assertIn('id="wallpaper-stream"', self.html)
        self.assertIn('id="europe-overload"', self.html)
        self.assertIn('aria-pressed="false"', self.html)
        self.assertNotIn('id="wallpaper-credit"', self.html)
        self.assertIn('src="/wallpapers.js?v=europa-overload-v2"', self.html)

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
