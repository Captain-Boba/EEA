# Checked-in report snapshots

The generated coverage, summary and validation files are **offline reports of
the local Atlas snapshot**, not a live mirror of the Railway database.
`REPORT_MANIFEST.generated.json` identifies their reporting year, aggregation
calendar date, logical database fingerprint and individual file checksums.
Always verify all listed checksums before treating files as one report set.

`as_of` controls calendar-dependent aggregation (closed year versus YTD); it
does not mean the sources were fetched that day. `snapshot_sha256` hashes
logical SQLite content including caches, not the physical database file.

Regeneration and verification scope: [DATA_REFRESH.md](../../docs/DATA_REFRESH.md#reproducible-offline-report-bundle).
The former Energy-Charts validation is preserved in
[the historical archive](../../docs/history/ENERGY_CHARTS_VALIDATION_2025.md).
The original August beta acceptance remains in
[BETA_DATA_VALIDATION.md](../../docs/BETA_DATA_VALIDATION.md).
