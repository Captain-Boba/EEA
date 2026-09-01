import json
import re
import unittest
from pathlib import Path

from electricity_atlas.config import ATLAS_COUNTRIES
from electricity_atlas.wallpaper_catalog import wallpaper_catalog


ROOT = Path(__file__).resolve().parents[1]


class WallpaperTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.javascript = (ROOT / "web" / "wallpapers.js").read_text(encoding="utf-8")
        cls.html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "web" / "style.css").read_text(encoding="utf-8")
        cls.manifest = json.loads((ROOT / "web" / "wallpapers.json").read_text(encoding="utf-8"))

    def test_canonical_catalog_has_stable_attributed_unique_entries(self):
        self.assertEqual(len(self.manifest), 250)
        self.assertEqual(len({entry["id"] for entry in self.manifest}), 250)
        self.assertEqual(len({entry["title"] for entry in self.manifest}), 250)
        self.assertEqual(len({entry["subject"] for entry in self.manifest}), 250)
        self.assertEqual(len({entry["file"] for entry in self.manifest}), 250)
        self.assertTrue(all(entry["id"].startswith("commons-") for entry in self.manifest))
        self.assertTrue(all(entry["author"] and entry["license"] for entry in self.manifest))
        self.assertTrue(all(entry["width"] / entry["height"] < 2 for entry in self.manifest))

    def test_catalog_uses_only_atlas_countries_and_is_shared_with_server(self):
        allowed = {country.name for country in ATLAS_COUNTRIES.values()}
        for entry in self.manifest:
            self.assertTrue(all(country in allowed for country in entry["country"].split(" / ")))
        self.assertEqual(len(wallpaper_catalog()), 250)
        self.assertIn('const CATALOG_URL = "/wallpapers.json"', self.javascript)
        self.assertNotIn("const WALLPAPERS", self.javascript)

    def test_gallery_navigation_is_cyclic_keyboard_accessible_and_limits_high_resolution_preload(self):
        for token in ("wallpaper-gallery-previous", "wallpaper-gallery-next", "ArrowLeft", "ArrowRight", "activeIndex + 1", "activeIndex - 1"):
            self.assertIn(token, self.javascript)
        self.assertIn("(index + sequence.length) % sequence.length", self.javascript)
        self.assertIn("${activeIndex + 1} / ${sequence.length}", self.javascript)
        self.assertIn("for (const offset of [-1, 0, 1])", self.javascript)
        self.assertIn("imageUrl(wallpaper.file, 3840)", self.javascript)
        self.assertIn("imageUrl(wallpaper.file, 960)", self.javascript)
        self.assertIn("object-fit: contain", self.css)

    def test_public_vote_controls_are_symbolic_accessible_and_not_localstorage_reactions(self):
        self.assertIn('const VOTES_URL = "/api/wallpaper-votes"', self.javascript)
        self.assertIn('button("wallpaper-vote-up", "Daumen hoch vergeben"', self.javascript)
        self.assertIn('button("wallpaper-vote-down", "Daumen runter vergeben"', self.javascript)
        self.assertIn("aria-pressed", self.javascript)
        self.assertIn("votePending", self.javascript)
        self.assertIn("own_vote", self.javascript)
        self.assertIn("if (!own)", self.javascript)
        self.assertIn("voteSummary.hidden = !voteError", self.javascript)
        self.assertIn("reactions.append(voteSummary, upButton, downButton, voteHelp)", self.javascript)
        self.assertNotIn("eea-europa-overload-reactions", self.javascript)
        self.assertIn("wallpaper-vote-summary", self.javascript)
        self.assertIn("wallpaper-reactions button:disabled", self.css)

    def test_vote_controls_explain_gallery_keyboard_shortcuts_on_hover_and_focus(self):
        self.assertIn('voteHelp.className = "wallpaper-vote-help"', self.javascript)
        self.assertIn('voteHelp.tabIndex = 0', self.javascript)
        self.assertIn('voteHelpTooltip.setAttribute("role", "tooltip")', self.javascript)
        self.assertIn('←/→ Bildwechsel\\n↑ Like\\n↓ Dislike', self.javascript)
        self.assertIn(".wallpaper-vote-help:hover .wallpaper-vote-help-tooltip", self.css)
        self.assertIn(".wallpaper-vote-help:focus .wallpaper-vote-help-tooltip", self.css)
        self.assertIn("white-space: pre-line", self.css)

    def test_gallery_arrow_keys_use_existing_vote_actions_only_while_open(self):
        self.assertIn('if (activeIndex === null) return;', self.javascript)
        self.assertIn('event.key === "ArrowUp"', self.javascript)
        self.assertIn('void submitVote("up")', self.javascript)
        self.assertIn('event.key === "ArrowDown"', self.javascript)
        self.assertIn('void submitVote("down")', self.javascript)
        self.assertIn('upButton.setAttribute("aria-keyshortcuts", "ArrowUp")', self.javascript)
        self.assertIn('downButton.setAttribute("aria-keyshortcuts", "ArrowDown")', self.javascript)

    def test_lightbox_preserves_close_focus_and_scroll_contract(self):
        for token in ("wallpaper-lightbox", "aria-modal", "europe-star.svg", "event.key === \"Escape\"", "event.target === lightbox", "lockScroll", "unlockScroll", "focusBeforeLightbox.focus"):
            self.assertIn(token, self.javascript)
        self.assertIn("prefers-reduced-motion", self.css)

    def test_opt_in_loads_catalog_and_votes_only_after_enablement(self):
        self.assertIn("if (readOptIn()) void start()", self.javascript)
        self.assertIn("await loadCatalog(); if (!readOptIn()) return; active = true", self.javascript)
        self.assertLess(self.javascript.index("await loadCatalog()"), self.javascript.index("sequence = shuffled(catalog)"))
        self.assertIn('src="/wallpapers.js?v=europa-overload-gallery-v4"', self.html)
        self.assertIn('id="wallpaper-stream"', self.html)
        self.assertIn('aria-pressed="false"', self.html)
