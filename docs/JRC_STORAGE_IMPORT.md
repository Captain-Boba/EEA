# JRC storage snapshot import

The Atlas does not scrape or automate the interactive JRC dashboard. In the
dashboard select `Project status = Operational` and the technologies
`Mechanical` and `Electrochemical`. Download the country/status chart once from
the `Power (GW)` tab and once from the `Capacity (GWh)` tab. Record the dashboard
`Last update` date shown below the real-time dashboard.

Import the paired files with:

```powershell
eea import-storage --power-file jrc-power.xlsx --capacity-file jrc-capacity.xlsx --snapshot-date YYYY-MM-DD
```

The workbook headers must be exactly `Country`, `Project status`, and either
`Power (GW)` or `Capacity (GWh)`. Both workbooks are validated before the old
snapshot is replaced. Known non-Atlas export countries are ignored; unknown
country names are rejected. Missing Atlas countries remain null.

The older reviewed CSV exchange route remains available through
`JRC_STORAGE_IMPORT_TEMPLATE.csv`.

Required normalization:

- `Country Code`: one of the 31 Atlas ISO2 codes; use `UK` and `GR`.
- `Snapshot Date`: one common ISO date (`YYYY-MM-DD`) for the complete file.
- `Project Status`: `Operational` for commissioned capacity. Other statuses are
  retained in the reviewed exchange file but excluded from Atlas totals.
- `Technology`: `Electrochemical` or `Mechanical` for electricity storage.
  Thermal storage is not included in the electricity-storage total.
- `Subtechnology`: descriptive source classification, for example `Lithium-ion`
  or `Pumped hydro`.
- `Power (MW)` and `Capacity (MWh)`: non-negative finite numbers or empty when
  the source does not provide that dimension. Do not convert a missing value to
  zero.

The importer requires one snapshot date, rejects unknown countries, malformed
numbers and duplicate rows, and replaces the previous JRC snapshot only after
the complete file pair has passed validation. The exact reviewed CSV or
Base64-encoded XLSX exports and their SHA-256 hashes are stored in `source_cache`.

Source: https://ses.jrc.ec.europa.eu/storage-inventory

The JRC page states that the inventory is based mainly on public data and Wood
Mackenzie data and that some MWh capacities are estimated. Confirm redistribution
rights for the selected export before public or commercial publication. When in
doubt, contact `JRC-Smart-Electricity@ec.europa.eu`.
