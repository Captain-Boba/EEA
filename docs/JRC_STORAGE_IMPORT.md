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

## JRC project API

The importer requests at most once per update:

`https://ses.jrc.ec.europa.eu/storage-inventory-tool/api/projects`

Only projects with `status.name == Operational` are considered. Batteries
require `technology.parentName == Electrochemical` (case-insensitive). Pumped
storage requires the exact technology name `Pumped Hydro Storage (PHS)`;
flywheels, CAES, thermal, and chemical storage are not reclassified as pumped
storage. Missing energy remains missing, never zero. `estimated_capacity` is
preserved in metric quality and provenance.

The public project API is not formally versioned. An unexpected schema aborts
the JRC source transaction and preserves the previous snapshot. JRC values are
an inventory of tracked projects, not a guaranteed complete national stock and
not the total energy content of conventional hydropower reservoirs.

The JRC inventory states that it uses mainly public and Wood Mackenzie data and
that some MWh capacities are estimated. Confirm redistribution rights before a
public or commercial release of the JRC payload. When in doubt, contact
`JRC-Smart-Electricity@ec.europa.eu`.

Both files are validated before either replaces existing Battery-Charts rows.
Their unchanged payloads, filenames, retrieval/import time, and SHA-256 are
stored in `source_cache`. No API key or request URL is stored or required.

## JRC request and transaction limits

- A regular JRC update is skipped when its response was already fetched in the
  current calendar month.
- `--refresh` bypasses that freshness check but keeps all request limits.
- Maximum per update: one JRC request. Battery-Charts is not contacted.
- HTTP 403 and 429 abort without a retry. `Retry-After` is reported/respected.
- Timeout and HTTP 5xx receive at most one retry after at least ten seconds.
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
