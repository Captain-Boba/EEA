# European Electricity Atlas

An open, interactive atlas for comparing European electricity systems. The web interface combines a metric-driven map of Europe with sortable rankings, country profiles, time-series comparisons, and transparent information about data status and sources.

**[Open the Atlas](https://ee-atlas.eu)** · [Latest release](https://github.com/Captain-Boba/EEA/releases/latest) · [Project and contact](https://ee-atlas.eu/contact.html) · [Privacy and cookies](https://ee-atlas.eu/privacy.html)

The public beta is desktop-first and covers 31 European countries from 2015 onwards. On smartphones, the complete 1920-pixel desktop workspace is intentionally preserved and initially scaled to fit instead of collapsing the analytical tools into an incomplete mobile layout; pinch zoom and horizontal navigation remain available. Missing, provisional, YTD, annual, monthly, and snapshot values remain visibly distinct instead of being silently filled or mixed.

## The interface

### European electricity systems ranked side by side

The main country table compares all 31 Atlas countries using consistently formatted metrics. Every metric column has explicit ascending and descending controls and can be opened directly as a map layer, while rank numbers always follow the active sorting. Countries are added to the time-series comparison through their rank control, and the sticky control bar keeps the year, period, and comparison selection within reach while scrolling.

[![Sortable country ranking in the European Electricity Atlas](docs/images/Energy%20Systems%20-%20Main%20Ranking%20V3.png)](docs/images/Energy%20Systems%20-%20Main%20Ranking%20V3.png)

### Every metric on the map of Europe

The fully local SVG map visualizes absolute, share, yearly per-capita, and cross-domain metrics with family-specific color scales and visible country values. Metric family and representation are selected independently through grouped Atlas menus. A country can be pinned without changing the comparison selection and cleared again by selecting the surrounding map background. The legend identifies the minimum and maximum countries together with the Atlas average. In fullscreen mode, the legend remains available beside the map. The current map state can be exported as SVG or PNG, including its title, period, unit, color scale, and legend.

[![Fullscreen map showing low-carbon electricity generation across Europe](docs/images/Map%20Tool%20V3.png)](docs/images/Map%20Tool%20V3.png)

### Time series for up to ten countries

The time-series comparison combines monthly or annual values with an Atlas average and a live ranking. Grouped metric-family selection, a full-baseline or visible-data-range Y-axis, and preset ranges from YTD to the complete available history complement the custom date range. Relative changes use the first year of the selected range as their baseline; monthly values are compared with the same calendar month in that baseline year. Missing values remain visible as genuine gaps in the lines. The live ranking follows the pointer at a deliberately moderated rate and can be pinned with a click. The current comparison, including its Y-axis mode, can be shared through a direct link or exported locally as CSV, SVG, and PNG.

[![Time-series comparison with country lines, Atlas average, and live ranking](docs/images/Comparison%20Tool%20V3.png)](docs/images/Comparison%20Tool%20V3.png)

### Country profiles with transparent reporting periods

Select a country name in a ranking or use the focused-country action on the map to open a full-width country profile. The direct link preserves the country and requested period. Each metric identifies its unit, source, data status, time basis, and actual reporting period. Monthly, annual, and snapshot observations are kept separate; a capacity value shown from an earlier reporting year is explicitly labelled as such and is never copied into a newer year.

### An optional visual layer for Europe

**Europa Overload** is an opt-in visual mode backed by a curated catalog of 250 attributed Wikimedia Commons images from the 31 Atlas countries. Images are requested only after the mode is enabled. Every postcard opens in a keyboard-accessible fullscreen gallery with cyclic navigation, attribution, and public server-backed voting.

## What the Atlas offers

- 31 European countries with monthly and annual values from 2015 onwards
- electricity generation, demand, generation mix, net imports, and CO₂ intensity
- yearly per-capita generation for total generation, renewables, individual renewable and fossil technologies, and nuclear power
- national monthly and annual wholesale electricity prices
- annual population and GDP metrics, installed generation capacity, household prices in ct/kWh, non-household prices in EUR/MWh, gross electricity trade, electric mobility, and inventory emissions
- annual cross-domain relations for generation and consumption per nominal GDP, electricity-and-heat emissions per GDP, the household-to-wholesale price gap, and electricity-trade throughput
- separate battery and pumped-storage power, energy capacity, and equivalent discharge duration snapshots
- a fully local map of Europe without map tiles, CDNs, or tracking
- a compact, fullscreen-capable time-series comparison for one to ten countries with an Atlas average, range-aware baseline, shareable links, and local exports
- direct-linked country profiles that group all available metrics and make monthly, annual, snapshot, source, quality, and actual reporting period explicit
- an optional **Europa Overload** mode with 250 attributed European postcards, fullscreen gallery navigation, and public score-based voting
- visible coverage gaps, provisional periods, and YTD values instead of fabricated zeroes

## Run the Atlas locally

### Prerequisites

- Windows with PowerShell
- Git
- Python 3.11 or newer

Clone the repository and create a local Python environment:

```powershell
git clone https://github.com/Captain-Boba/EEA.git
cd EEA

py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

An immutable `atlas.sqlite3` snapshot is available from the **Assets** section
of the [first public beta release](https://github.com/Captain-Boba/EEA/releases/tag/v0.4.0).
Place it at `data\atlas.sqlite3` inside the cloned repository. This historical
beta snapshot requires neither an Ember API key nor a fresh import, does not
contain the separate community vote database, and grants no access to the
hosted service. Newer releases are not required to bundle an analytical
database.

Start the server:

```powershell
.\.venv\Scripts\eea.exe serve --port 8765
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). Press `Ctrl+C` to stop the server; it is stopped once the PowerShell prompt returns.

The hosted beta runs at [ee-atlas.eu](https://ee-atlas.eu). Local operation remains useful for development, data review, and testing unreleased changes without affecting the public service.

## Data sources

| Source | Use | Time basis |
| --- | --- | --- |
| [Ember](https://ember-energy.org/) | generation, demand, generation mix, net imports, and CO₂ intensity | month and year |
| [Ember Wholesale Electricity Price Data](https://ember-energy.org/data/european-wholesale-electricity-price-data/) | national wholesale electricity prices | month and weighted annual value |
| [Eurostat](https://ec.europa.eu/eurostat/) | population, GDP, installed capacity, retail-price components, gross electricity trade, and battery-electric passenger cars | year |
| [Battery-Charts](https://battery-charts.de/) | complete German stationary battery fleet from the cleaned MaStR | monthly inventory value |
| [JRC European Energy Storage Inventory](https://ses.jrc.ec.europa.eu/storage-inventory) | operational battery projects outside Germany and pumped storage in all countries | dashboard snapshot |
| [JRC Hydro-power database](https://data.jrc.ec.europa.eu/dataset/52b00441-d3e0-44e0-8281-fda86a63546d) | reported plant, pumping, and reservoir-energy inventory | release snapshot |
| [EEA GHG inventory](https://www.eea.europa.eu/en/datahub/datahubitem-view/3b7fe76c-524a-439a-bfd2-a6e4046302a2) | CRT 1.A.1.a emissions from public electricity and heat production | year |
| [Natural Earth](https://www.naturalearthdata.com/) | local country geometries for the map of Europe | version 5.1.1 |
| [flag-icons](https://github.com/lipis/flag-icons) | local SVG country flags in the time-series comparison | version 7.4.0, MIT |

Ember, Battery-Charts, the JRC Hydro-power database, and the EEA GHG inventory are identified as `CC BY 4.0`. Natural Earth geometries are in the public domain. Eurostat data are subject to Eurostat's reuse policy and exceptions. JRC storage-inventory data may include estimates and third-party data. The project owner has accepted attributed national aggregates as a provisional risk for the non-commercial beta; this is not presented as a legal clearance, and further clarification or a later Ember replacement remains post-beta work.

## Updating the data yourself

This section is required when the historical beta snapshot is not used or a
newer analytical database needs to be built.

### Ember electricity data

The key is read first from `EMBER_API_KEY` and otherwise from the local, Git-ignored `EMBER_API_KEY.txt` file. It is neither printed nor stored in SQLite; cached request URLs contain only `api_key=REDACTED`.

```powershell
$env:EMBER_API_KEY = "<API-Key>"
.\.venv\Scripts\eea.exe import --from-year 2015
```

The historical cache is reused. `--refresh` forces a new request and atomically replaces only the explicitly requested period. Individual years, months, or countries can also be imported:

```powershell
.\.venv\Scripts\eea.exe import --year 2025
.\.venv\Scripts\eea.exe import --year 2025 --countries DE FR ES UK
.\.venv\Scripts\eea.exe import --year 2025 --months 1 7
```

### Wholesale electricity prices and Eurostat

```powershell
.\.venv\Scripts\eea.exe import-prices
.\.venv\Scripts\eea.exe import-eurostat --from-year 2015
.\.venv\Scripts\eea.exe import-eurostat-supplement --from-year 2015
```

These commands require internet access but no API key. Responses are fully validated before existing data are replaced atomically. Eurostat requests run sequentially by design and respect limited backoff and `Retry-After`. The supplement deliberately imports selected dimensions only: net installed capacity, annual household band DC and non-household band IC price components in EUR, gross imports/exports, and battery-electric passenger-car stock and new registrations.

### JRC hydropower and EEA inventory emissions

```powershell
.\.venv\Scripts\eea.exe import-hydro-inventory
.\.venv\Scripts\eea.exe import-eea-ghg
```

The JRC command imports the CC BY 4.0 release inventory without estimating missing plant storage values. The EEA command selects aggregate greenhouse gases for CRT `1.A.1.a`; this category includes public electricity **and heat** production. A reviewed local EEA CSV or ZIP can be supplied with `import-eea-ghg --file <path>` if the official Datahub download is temporarily unavailable.

### Battery and pumped-storage inventories

Battery-Charts is currently imported exclusively from two manually saved JSON responses. The Atlas does not use a Battery-Charts key and never requests its JSON endpoint:

```powershell
.\.venv\Scripts\eea.exe import-battery-storage `
  --energy-file .\battery-energy.json `
  --power-file .\battery-power.json
```

Both files are validated together and imported atomically only after validation succeeds. Raw responses and their SHA-256 hashes remain in the local source cache. If validation fails, the existing German battery inventory remains unchanged.

JRC has a separate, explicitly triggered online update command:

```powershell
.\.venv\Scripts\eea.exe update-storage
```

A fresh monthly cache prevents the JRC browser session. `--refresh` deliberately bypasses the monthly cache check. The command opens an isolated Chromium window, selects `Operational`, then exports the official dashboard's filtered Electrochemical and Pumped Hydro Storage (PHS) power and capacity XLSX files. It requires four downloads in one dashboard session, retains their raw payloads and SHA-256 values, and cannot access Battery-Charts.

The project dependency installs the Playwright library; once per machine, also
install its isolated browser runtime with `python -m playwright install
chromium`. This neither controls nor changes an installed Firefox profile.

Germany uses only the national Battery-Charts total for batteries. Other countries use the project inventory recorded by JRC, while pumped storage comes from JRC for every country. Values from different sources are never added together. The existing `import-storage` command remains available as a deprecated offline fallback for reviewed JRC CSV/XLSX files. See [JRC_STORAGE_IMPORT.md](docs/JRC_STORAGE_IMPORT.md) for details.

### Complete data refresh

Use `refresh-all` for a controlled refresh of the complete analytical database. The command builds and validates an isolated candidate below the Git-ignored `data/.refresh-work/`, publishes it only after all source imports succeed, and removes temporary candidate, rollback, and SQLite sidecar files afterwards. It never replaces or writes to the separate community vote database.

```powershell
.\.venv\Scripts\eea.exe --db data\atlas.sqlite3 refresh-all `
  --from-year 2015 `
  --to-year 2026 `
  --battery-energy-file .\battery-energy.json `
  --battery-power-file .\battery-power.json
```

The server must be stopped before publication. On Windows, an active database handle causes the command to abort before any network importer runs. See [DATA_REFRESH.md](docs/DATA_REFRESH.md) for the complete success, rollback, cleanup, and reporting contract.

## Data model and quality rules

`period_observation` is the canonical fact table. Month is the smallest unit for electricity and price data; validated annual values and separately dated storage inventories are stored independently. `api_cache` contains redacted Ember JSON responses. `source_cache` stores source responses or, for a multi-format EEA bundle, the selected gzip-compressed source CSV together with retrieval metadata and SHA-256 hashes.

- missing values remain `null` and appear as `—` in the interface
- current months and years are marked as provisional or YTD
- annual demand is derived only when exactly twelve monthly values are available
- annual prices are weighted by the actual duration of each month
- positive net imports indicate an import surplus; negative values indicate an export surplus
- Eurostat denominators are combined only with electricity values from the same calendar year
- GDP relations use nominal GDP from the same year and remain missing when either input is unavailable or zero
- per-capita generation metrics are annual-only and require a positive Eurostat population value from the same calendar year
- Eurostat installed-capacity values are net maximum electrical capacity in GW; they are not module-nameplate solar capacity in GWp
- household electricity totals and components are converted from the imported EUR/MWh observations to ct/kWh in the analytical response; non-household prices remain in EUR/MWh
- absent monthly nuclear generation is treated as zero for the approved low-carbon calculation; other missing technologies remain missing
- negative Ember residual categories (`other renewables` and `other fossil`) are exposed as missing rather than as negative generation
- estimated total generation emissions are explicitly derived from Ember intensity multiplied by Ember generation
- theoretical EV battery capacity uses the flat fleet assumption `BEV stock × 60 kWh`; it is nominal traction-battery energy, not grid-accessible V2G storage
- failed updates must not modify existing data
- visible metric names use a shared three-part contract: topic, measured value, and unit or denominator; metric IDs and calculation semantics remain unchanged

A missing analytical SQLite file is initialized automatically when the server starts. Analytical requests operate read-only afterwards. Public Europa Overload votes are the sole write API and use a separate community database; they never modify `atlas.sqlite3`.

## Local API

- `/api/` (machine-readable endpoint directory)
- `/api.html` (clickable API documentation)
- `/openapi.json` (OpenAPI 3.1 description)
- `/api/countries`
- `/api/metrics`
- `/api/summary?year=2025`
- `/api/summary?year=2025&month=7`
- `/api/map-data?metric=capacity_total_gw&year=2025`
- `/api/compare?year=2025&countries=DE,FR`
- `/api/timeseries?metric=renewable_share_pct&countries=DE,FR,UK&start=2015-01&end=2026-08`
- `/api/country-profile?country=DE&year=2025`
- `/api/country-profile?country=DE&year=2025&month=7`
- `/api/coverage?year=2025`
- `/api/storage`
- `GET /api/wallpaper-votes`
- `POST /api/wallpaper-votes`

[`/api/`](https://ee-atlas.eu/api/) provides a machine-readable directory of the live endpoints and canonical discovery documents. [`/api.html`](https://ee-atlas.eu/api.html) exposes the same entry points and common requests as real hyperlinks for browser-based tools. [`/openapi.json`](https://ee-atlas.eu/openapi.json) provides an OpenAPI 3.1 description, while [`/llms.txt`](https://ee-atlas.eu/llms.txt) adds metric semantics, interpretation constraints, and safe citation guidance for LLM sessions. Public crawlers can discover these resources through [`/robots.txt`](https://ee-atlas.eu/robots.txt) and [`/sitemap.xml`](https://ee-atlas.eu/sitemap.xml).

The web interface never performs imports. The analytical interface, map, flags, logo, and exports use local assets and no external map service. Only the optional Europa Overload mode requests attributed postcard images from Wikimedia Commons, and only after the user enables it. Its public votes are stored separately from `atlas.sqlite3` in `data/community.sqlite3` by default; set `EEA_COMMUNITY_DB` to use a persistent hosting volume.

## Development and tests

The local server and analytical API use the Python standard library. The explicitly triggered JRC dashboard refresh additionally requires the declared Playwright dependency and its isolated Chromium runtime.

```powershell
$env:PYTHONPATH = "$PWD\src"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --check web\app.js
node --check web\wallpapers.js
git diff --check
```

Tests use local fixtures exclusively and never perform live imports. Node.js is required for the JavaScript tests; set `EEA_NODE` to an explicit executable path when `node` is not available through `PATH`. The prepared GitHub Actions workflow runs the same suite with Python 3.11 and Node 22 on pushes, pull requests, and manual dispatches.

## Further documentation

- [Project roadmap](ROADMAP.md)
- [Public beta roadmap](BETA_ROADMAP.md)
- [Beta data validation](docs/BETA_DATA_VALIDATION.md)
- [Complete data refresh lifecycle](docs/DATA_REFRESH.md)
- [Metric labeling contract](docs/METRIC_LABELING.md)
- [Deployment and operations](docs/DEPLOYMENT.md)
- [Ember coverage](docs/EMBER_COVERAGE.md)
- [JRC storage import](docs/JRC_STORAGE_IMPORT.md)
- [Local map of Europe and Natural Earth provenance](docs/MAP_ASSET.md)
- [Time-series comparison behavior](docs/TIMESERIES_COMPARISON.md)
- [Country profiles](docs/COUNTRY_PROFILES.md)
- [Europa Overload behavior and privacy](docs/EUROPA_OVERLOAD.md)
- The running interface links directly to its public project/contact and privacy/cookie notices.

## Known limitations

- Individual historical country-month combinations may contain legitimate coverage gaps.
- Gross imports and exports are annual Eurostat balance values; negative-price hours and operational interval statistics remain outside the scope of the monthly Atlas.
- Technology-specific per-capita generation is annual-only because the denominator is an annual Eurostat population value.
- Eurostat installed capacity currently ends in 2024, while several price, trade, and BEV series already reach 2025. The map may display the latest earlier capacity year and labels that effective data year explicitly; the stored observations and other views are never backfilled.
- EEA CRT 1.A.1.a combines public electricity and heat production and is not a pure electricity-only inventory value.
- The JRC Hydro-power database is an incomplete reported-plant inventory with an unknown update frequency; missing reservoir energy is not estimated.
- JRC storage values represent its recorded operational project inventory, not necessarily a complete national inventory and not the energy capacity of conventional hydropower reservoirs.
- Time-series plots do not interpolate gaps. At each point, the Atlas average is the arithmetic mean of all available values across the complete country catalog.
- Missing residential or commercial batteries outside Germany are not estimated. Missing JRC energy values remain empty and are not inferred from power or project metadata.
- The visible JRC dashboard export is not formally versioned. Structural changes therefore cause a deliberate, state-preserving import failure. The previously used `/api/projects` route was an undocumented JSON endpoint, not a supported public API contract.
