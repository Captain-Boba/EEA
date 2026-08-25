# Storage source update

Storage sources use separate import paths. Neither path runs on server startup,
page load, or API access.

Battery-Charts is imported exclusively from manually saved JSON responses:

```powershell
eea import-battery-storage --energy-file battery-energy.json --power-file battery-power.json
```

The Atlas does not call the Battery-Charts JSON endpoint. Its online client is
explicitly disabled in code and aborts before opening a network connection.
The normal storage update command only targets JRC:

```powershell
eea update-storage
```

## Source resolution

The Atlas keeps battery and pumped-storage metrics separate:

- Germany batteries: Battery-Charts only, coverage
  `national_registry_total`.
- Other Atlas-country batteries: JRC, coverage
  `tracked_project_inventory`.
- Pumped storage in every Atlas country, including Germany: JRC, coverage
  `tracked_project_inventory`.
- German JRC battery projects are excluded and are never added to the
  Battery-Charts national total.

For each technology the Atlas stores discharge power, storage energy, and the
derived equivalent discharge duration. A duration is created only when both
positive dimensions are available from the same source and scope.

In tables and country summaries, storage energy is always presented before
discharge power and equivalent discharge duration. This display order does not
change the source fields or imply that missing energy can be derived from
power.

## Battery-Charts

The user manually saves the responses corresponding to `bess_monthly_energy`
and `bess_monthly_power`. The offline importer retains the
segments `home`, `industrial`, and `grossspeicher`; the national value is their
exact sum. Values are normalized from kW/kWh to GW/GWh. Both responses must
contain the same strictly increasing dates. A latest partial month is retained
as provisional, while an incomplete non-final month is rejected.

Battery-Charts describes these data as the cleaned German MaStR stock. The
Atlas labels them `Battery-Charts – bereinigter MaStR-Gesamtbestand, CC BY 4.0`.
Vehicle batteries are outside this scope.

## JRC dashboard export

`eea update-storage` opens the official public dashboard at
`https://ses.jrc.ec.europa.eu/storage-inventory` in an isolated Chromium
window. It uses only visible dashboard controls and no session-bound endpoint:

The one-time machine setup is `python -m playwright install chromium` after
installing the project dependencies. The isolated runtime does not access or
modify a user's Firefox profile.

1. clear selections, select `Project status → Operational`,
2. select `Technology → Electrochemical`, export `Power (GW)` and
   `Capacity (GWh)`,
3. clear selections, select `Project status → Operational`,
   `Technology → Mechanical`, and exact `Subtechnology → Pumped Hydro Storage
   (PHS)`, then export both dimensions.

This is one dashboard session with four XLSX downloads. Mechanical storage as a
whole is never accepted: flywheels, CAES, thermal, and chemical storage are not
reclassified as pumped storage. Germany's JRC battery export is parsed but not
stored; the German national Battery-Charts total remains exclusive. Missing
power or energy remains missing, never zero.

The dashboard's visible `Last update` date is stored as the inventory date. An
unexpected XLSX schema, status, country, or value aborts the complete JRC
transaction and preserves the previous snapshot. Raw XLSX files, stable
dashboard URL, retrieval time, content type, and SHA-256 are retained in
`source_cache`; temporary Qlik download URLs, cookies, and session identifiers
are never stored.

The JRC inventory states that it uses mainly public and Wood Mackenzie data and
that some MWh capacities are estimated. Confirm redistribution rights before a
public or commercial release of the JRC payload. When in doubt, contact
`JRC-Smart-Electricity@ec.europa.eu`.

Both files are validated before either replaces existing Battery-Charts rows.
Their unchanged payloads, filenames, retrieval/import time, and SHA-256 are
stored in `source_cache`. No API key or request URL is stored or required.

## JRC request and transaction limits

- A regular JRC update is skipped when all four filtered exports were fetched
  in the current calendar month.
- `--refresh` bypasses that freshness check but keeps all request limits.
- Maximum per update: one dashboard session and four XLSX downloads.
  Battery-Charts is not contacted.
- The dashboard automation makes no retry loop. A failed browser session or
  download aborts before any SQLite data are replaced.
- Raw payload, retrieval time, HTTP metadata, and SHA-256 are stored in
  `source_cache` only after validation.
- JRC is replaced in a SQLite savepoint only after full validation.

## Deprecated offline fallback

The previous reviewed JRC CSV and paired-dashboard-XLSX routes remain available
for recovery only:

```powershell
eea import-storage --power-file jrc-power.xlsx --capacity-file jrc-capacity.xlsx --snapshot-date YYYY-MM-DD
```

The fallback preserves the legacy combined `storage_*` representation and is
not used by the primary `/api/storage` response. New JRC data should use
`eea update-storage`; new German battery data should use
`eea import-battery-storage`.
