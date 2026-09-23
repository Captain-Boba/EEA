# English/German localization

English is the internal/source language. German is a complete translation, not
a second set of application logic. Existing first visits and public API calls
without a language parameter retain their German presentation for compatibility.

## Visitors and URLs

- `/?lang=en` and `/?lang=de` are explicit, shareable language choices.
- The DE/EN header switch uses the current URL, preserving analytical parameters.
- A switch saves `eea_language=de|en` for up to 180 days (`SameSite=Lax`, `Secure`
  on HTTPS). It is a functional preference, not a visitor identifier.
- Explicit `lang` wins over the cookie. Without either, pages use German.
- The current in-memory selection, map, ranges, axes, table sort/expansion,
  pinned chart period, open sections, scroll position and gallery sequence are
  carried across a switch using short-lived session storage. The state is used
  once, only for the exact destination URL, and expires after 60 seconds.
- If browser storage is disabled, explicit language links still work; unsaved
  in-memory view state may be lost. Initial page loading does not rewrite `/`.
- Direct links explicitly include the active language. HTML pages render their
  language, title, description, Open Graph tags, canonical and alternate links
  on the server; crawlers do not need JavaScript to discover these.
- The intentional mobile desktop viewport, zoom and one-time notice remain.

## Resources and rendering

- `web/locales/en.json`: English source messages; `de.json`: German equivalents.
  Sentence keys are used for UI messages; gallery titles use stable image IDs.
- `web/locales/resources.js`: generated local browser bundle. Rebuild with
  `python scripts/build_locales.py`; `--check` detects a stale bundle, missing
  keys, empty translations and mismatched interpolation parameters.
- `web/i18n.js`: pinned i18next, locale formatting and language switching.
  English uses `en-GB`, German uses `de-DE` for displayed dates and numbers.
- `src/electricity_atlas/locales/metrics.*.json` and `countries.*.json`:
  presentation resources for 87 metrics and 31 countries. Metric configuration,
  formulas, stored observations, source IDs and country codes remain separate.
  `metric-identities.json` freezes the grouping identifiers separately from wording.
- `src/electricity_atlas/pages.py`: Jinja2 templates for the Atlas, contact,
  privacy and API help pages. Autoescaping is enabled; templates are trusted
  repository files, never user-supplied. Includes cannot be fetched as raw HTML.
- `web/wallpapers.json`: English canonical captions. Both languages cover all
  250 image IDs; file names, authors, licences and voting identity are unchanged.

Jinja2 (BSD-3-Clause) is a Python runtime dependency in both `pyproject.toml` and
`requirements.txt`. i18next (MIT) is vendored at a fixed version with provenance
and a hash under `web/vendor/i18next/`. Neither sends translation data externally.
Updates require the usual dependency/security review; no custom translation
parser, CDN or paid translation service is part of the runtime.

## API and data compatibility

Analytical GET endpoints accept `lang=en|de`. The default is always German,
independent of the browser preference cookie. Invalid languages return HTTP 400.
`/api/`, health and voting remain machine-oriented, language-neutral interfaces.

- `label` and human-readable metadata follow the requested language.
- `label_de` always stays German; `label_en` always stays English.
- `group_id`, `family_id` and `category_id` are language-independent keys.
- Legacy country-profile section `id` values remain German for compatibility;
  new clients use `group_id`, not the translated `label`.
- Numbers, nulls, temporal bases, dates, source/quality codes, retention metadata
  and formulas are unchanged. Human-readable unit spellings can be translated
  without rescaling the underlying measurement.
- Stored provenance is not migrated. Known source display labels are translated
  at the response boundary, not rewritten in the database.
- SVG and PNG use the selected language. CSV intentionally remains a machine
  format: stable country-code headers, ISO periods, comma separators, decimal
  points and empty missing values in both languages.

## Maintaining translations

1. Use an English key with `t(...)` in JavaScript or `{{ t(...) }}` in templates.
2. Add the key to both JSON catalogs. Prefer whole sentences with named
   `{{placeholders}}` over concatenated fragments when word order differs.
3. Never use translated text as an identifier or a calculation input. Keep
   country codes, metric IDs, statuses, database fields and source keys stable.
4. Put text into `textContent`, escaped attributes or Jinja autoescaped output.
   i18next interpolation is not itself HTML sanitization.
5. Rebuild the resource bundle and run the suite. Review both languages visually.
   Restart the local server after editing JSON catalogs, which are cached in memory.

## Checks

```powershell
$env:PYTHONPATH = "$PWD\src"
python scripts/build_locales.py --check
python -m unittest discover -s tests -v
node --check web/app.js
node --check web/wallpapers.js
node --check web/i18n.js
```

The regular suite covers catalog completeness, template rendering/escaping,
language precedence, legacy API responses and DE/EN numerical equivalence using
local fixtures. The optional browser check needs Playwright Chromium and an
existing local Atlas database:

```powershell
python scripts/check_localization_browser.py --db data/atlas.sqlite3 --artifacts "$env:TEMP\eea-localization-qa"
```

It reads the Atlas database without imports, stores test votes in a disposable
community database, replaces external gallery image requests with a local fixture,
and exercises language/state switching, country profiles, gallery arrow keys,
voting, SVG/PNG/CSV exports, no-JavaScript pages and the mobile notice.
Screenshots are local QA artifacts, not release assets. Nothing is deployed.
