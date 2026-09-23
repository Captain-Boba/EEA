"""English presentation resources with an explicit German compatibility layer.

Only human-readable fields are localized. Metric IDs, dates, source identifiers,
status codes, numerical values and database records are never translated.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

LOCALES = Path(__file__).with_name("locales")
LANGUAGES = ("de", "en")
SOURCE_LABELS = {
    "Eurostat – installed net capacity": "Eurostat – installierte Nettoleistung",
    "Eurostat – electricity prices and price components": "Eurostat – Strompreise und Preisbestandteile",
    "Eurostat – electricity balance": "Eurostat – Strombilanz",
    "Eurostat – road vehicle stock and new registrations": "Eurostat – Straßenverkehrsbestand und Neuzulassungen",
    "Battery-Charts – cleaned MaStR total, CC BY 4.0": "Battery-Charts – bereinigter MaStR-Gesamtbestand, CC BY 4.0",
}
RETAINED_DETAILS_PREFIX = {
    "en": "Older data: Ember no longer provides previously available monthly values. "
          "Related monthly data was retained (not replaced with null): ",
    "de": "Älterer Datenstand: Ember liefert zuvor vorhandene Monatswerte nicht mehr. "
          "Zusammengehörige Monatsdaten wurden beibehalten (keine Null-Ersetzung): ",
}


@lru_cache(maxsize=8)
def resource(name: str, language: str) -> dict:
    if language not in LANGUAGES:
        raise ValueError("lang must be 'de' or 'en'")
    return json.loads((LOCALES / f"{name}.{language}.json").read_text(encoding="utf-8"))


def metric_labels(metric_id: str, language: str = "en") -> dict[str, str]:
    return dict(resource("metrics", language)[metric_id])


@lru_cache(maxsize=1)
def metric_identities() -> dict[str, dict[str, str]]:
    """Frozen technical keys: editing a translation must not change identity."""
    return json.loads((LOCALES / "metric-identities.json").read_text(encoding="utf-8"))


def country_name(code: str, language: str = "en") -> str:
    return resource("countries", language).get(code, code)


def source_label(text: str, language: str = "en") -> str:
    for english, german in SOURCE_LABELS.items():
        text = text.replace(german, english) if language == "en" else text.replace(english, german)
    return text


def localize_payload(value: Any, language: str = "de") -> Any:
    """Return localized copies; the no-lang HTTP contract remains German."""
    labels = resource("metrics", language)
    if isinstance(value, list):
        return [localize_payload(item, language) for item in value]
    if not isinstance(value, dict):
        return value
    result = {key: localize_payload(item, language) for key, item in value.items()}
    if value.get("issue_type") == "retained_source_gap" and isinstance(value.get("details"), str):
        for prefix in RETAINED_DETAILS_PREFIX.values():
            if value["details"].startswith(prefix):
                result["details"] = RETAINED_DETAILS_PREFIX[language] + value["details"][len(prefix):]
                break
    for key in ("source", "source_label", "price_source_label"):
        if isinstance(result.get(key), str):
            result[key] = source_label(result[key], language)
    metric_id = value.get("id")
    if metric_id in labels:
        for key, text in labels[metric_id].items():
            if key in result:
                result[key] = text
    code = value.get("country_code", value.get("code"))
    if code in resource("countries", language):
        for key in ("country_name", "name"):
            if key in result:
                result[key] = country_name(code, language)
    if "metrics" in value and "group_id" in value:
        key = next((key for key, identity in metric_identities().items()
                    if identity["group_id"] == value["group_id"]), None)
        if key:
            # Section id was historically a German display label. Retain it
            # for old clients and expose group_id for language-neutral logic.
            result["id"] = resource("metrics", "de")[key]["group"]
            result["label"] = labels[key]["group"]
    if result.get("label") == "Atlas average":
        result["label"] = "Atlas-Durchschnitt" if language == "de" else "Atlas average"
    return result
