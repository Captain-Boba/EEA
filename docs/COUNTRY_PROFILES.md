# Country profiles

Country profiles are a full-width detail view inside the local Atlas. They provide a transparent single-country reading of the existing metric catalog without creating, importing, or estimating any data.

## Navigation and direct links

Open a profile from a country name in a country ranking or from the action in the map's focused-country detail. The profile does not change the existing time-series comparison selection.

The view state is encoded locally in the URL:

```text
?view=country&country=DE&year=2025&period=year
?view=country&country=DE&year=2025&period=month&month=7
```

Browser back and forward preserve the Atlas state. The profile's plot action adds its country to the existing selection when fewer than ten countries are selected; it never removes an existing selection and it does not calculate a new time series automatically.

## API contract

`GET /api/country-profile?country=DE&year=2025[&month=7]` returns one bundled response. It is generated from the runtime metric catalog and contains:

- requested country and period;
- coverage of the requested electricity period;
- metric groups and representations;
- value, unit, source, data status, quality status, warnings, and time basis for every metric;
- the actual reporting period separate from the requested period.

The browser fetches this single endpoint when opening a profile. It does not fetch one endpoint per metric.

## Time bases and missing data

Monthly-capable metrics use the requested month in a monthly profile. Annual-only metrics still identify themselves as annual. Storage inventory values remain snapshots and expose their snapshot date and provenance. Missing values are `null` in the API and `—` in the interface; they are never converted to zero or estimated.

Installed-capacity metrics use the newest available reporting year at or before the selected year. The response keeps `requested_period` and `actual_period` distinct, so a value from 2024 shown while 2025 is selected is visibly a 2024 reporting value. No observation is copied into a later year.

## Scope

Profiles only present existing aggregated Atlas, Eurostat, EEA, JRC, and Battery-Charts data. They do not alter importers, the SQLite schema, source definitions, map geometry, or data coverage.
