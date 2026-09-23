# Atlas validation 2025

Status: **passed**; errors: 0; warnings: 0.
As-of date: 2026-09-23 (aggregation calendar, not a historical database reconstruction).

Logical snapshot SHA-256: `a6836eb87e543564768bd49a02aa1b2422260bb3bb962bc16fae710888465173`

Offline stored Ember observation/cache consistency for DE, FR, UK, ES, NO; shared importer normalization. Not an independent source audit or live freshness check. Cache-only records not imported are not audited.

Missing values remain null. Retained source-gap values are NOT freshly verified.
Period end dates in the inventory are reporting periods, NOT fetch/freshness timestamps.

| Country | Stored observations | Matched | Retained | No cache | Errors |
|---|---:|---:|---:|---:|---:|
| DE | 363 | 363 | 0 | 0 | 0 |
| FR | 339 | 339 | 0 | 0 | 0 |
| UK | 339 | 339 | 0 | 0 | 0 |
| ES | 363 | 363 | 0 | 0 | 0 |
| NO | 315 | 315 | 0 | 0 | 0 |

Countries missing one or more core summary values: none.

See VALIDATION.generated.json for per-observation issues, cache evidence and source inventory.
REPORT_MANIFEST.generated.json identifies the complete report set and each file's checksum.
