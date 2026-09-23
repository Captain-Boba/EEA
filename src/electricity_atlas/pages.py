"""Server-rendered public pages; English keys, German legacy landing page."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

WEB_ROOT = Path(__file__).resolve().parents[2] / "web"
PUBLIC_PAGES = frozenset({"index.html", "contact.html", "privacy.html", "api.html"})
TEMPLATES = Environment(
    loader=FileSystemLoader(WEB_ROOT), autoescape=select_autoescape(["html"]),
    undefined=StrictUndefined, auto_reload=True,
)


@lru_cache(maxsize=2)
def messages(language: str) -> dict[str, str]:
    return json.loads((WEB_ROOT / "locales" / f"{language}.json").read_text(encoding="utf-8"))


def localized_url(url: str, language: str) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["lang"] = language
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def render_page(name: str, language: str, request_url: str) -> bytes:
    if name not in PUBLIC_PAGES or language not in {"de", "en"}:
        raise ValueError("unsupported page or language")
    catalog = messages(language)
    canonical_path = "/" if name == "index.html" else f"/{name}"
    canonical = "https://ee-atlas.eu" + canonical_path
    return TEMPLATES.get_template(name).render(
        t=lambda key: catalog.get(key, key), language=language,
        og_locale="de_DE" if language == "de" else "en_GB",
        page_url=lambda url: localized_url(url, language),
        language_url=lambda lang: localized_url(
            urlunsplit(("", "", canonical_path, urlsplit(request_url).query, "")), lang
        ),
        canonical_url=canonical if language == "de" else localized_url(canonical, "en"),
        alternate_de=canonical, alternate_en=localized_url(canonical, "en"),
    ).encode("utf-8")
