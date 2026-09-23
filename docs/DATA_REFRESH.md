# Atlas data refresh lifecycle

Use the lifecycle command for a complete production refresh:

```powershell
eea --db data/atlas.sqlite3 refresh-all `
  --from-year 2015 `
  --to-year 2026 `
  --battery-energy-file battery-energy.json `
  --battery-power-file battery-power.json
```

The Battery-Charts files remain controlled local inputs. `refresh-all` does not enable automatic Battery-Charts network access. An optional reviewed EEA file can be supplied with `--eea-file`; otherwise the official EEA URL is used.

## Isolated candidate build

Every run receives a unique directory below `data/.refresh-work/<run-id>/`. The directory is on the same volume as `atlas.sqlite3` and is ignored by Git. It contains only explicitly named lifecycle files:

- `rollback.sqlite3`: consistent SQLite backup of the current production database
- `candidate.sqlite3`: separate database on which all importers operate
- `restore.sqlite3`: created only when a begun exchange must be rolled back
- the corresponding SQLite `-wal`, `-shm`, or `-journal` sidecars while connections are active

Persistent `pre-refresh`, `refresh-candidate`, `attempt2`, or similar files in `data/` are not part of the supported workflow.

## Successful publication

Before any network importer runs, the lifecycle verifies that the Atlas directory is writable and that `atlas.sqlite3` and existing sidecars can be opened for exclusive replacement. On Windows this detects an active SQLite/server handle. The check is repeated immediately before publication. A running foreign server is never stopped automatically; the refresh exits early with a concrete lock error.

The success sequence is:

1. create a consistent SQLite rollback backup;
2. copy it to the isolated candidate;
3. run all source importers sequentially on the candidate;
4. close importer connections and fully checkpoint the candidate WAL;
5. validate integrity, country set, key uniqueness and required values;
6. remove only verified inactive production sidecars and atomically replace `atlas.sqlite3`;
7. validate the published database and require its SHA-256 to equal the candidate SHA-256;
8. remove the explicitly named candidate, rollback, restore and sidecar files;
9. remove the empty per-run directory and empty `.refresh-work` root;
10. write the compact `data/reports/REFRESH.generated.json` lifecycle report.

Existing files in `data/reports/` are preserved. Coverage, summary and offline validation reports remain separate products of `eea report`; a refresh does not silently regenerate checked-in reports.

## Reproducible offline report bundle

Run locally against the exact database you want to inspect (no API key, browser
or network access is used):

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m electricity_atlas.cli --db .\data\atlas.sqlite3 report --year 2025 --as-of 2026-09-23 --output .\data\reports
```

Omit `--as-of` for today's aggregation calendar. An explicit date makes the
closed-year/YTD and price classification reproducible; it does **not** recreate
an older database or filter out observations acquired after that date. Use a
matching archived database if you need an actual historical snapshot.

The command produces:

- `COVERAGE.generated.md`: country coverage using the same aggregation rules as the API.
- `SUMMARY.generated.json`: the existing array-shaped annual summary; missing values stay `null`, genuine zero remains zero.
- `VALIDATION.generated.md` and `.json`: SQLite integrity, source/quality inventory, summary status counts and stored Ember observation/cache comparisons for DE, FR, UK, ES and NO in the requested year (monthly and yearly).
- `REPORT_MANIFEST.generated.json`: year, calendar date, logical snapshot fingerprint and SHA-256 of each of the four report files.

All reads share one read-only SQLite transaction, including committed WAL
content. The fingerprint hashes logical database content, **not** just the
main `.sqlite3` file, and is not interchangeable with lifecycle file hashes.
The cache check reuses importer normalization; it detects stored-value/cache
disagreements, not shared parser errors or incorrect source data. It does not
audit cache-only records absent from SQLite, other countries' raw records,
auxiliary-source transformations or independent official national statistics.
No raw payloads, request URLs or API keys are copied into the reports.

The newest covering successful cached response is used; an older response
cannot hide a withdrawn or revised value. Retained source-gap observations and
missing caches are explicitly warnings/unverifiable, never newly verified
values. Period end dates in the inventory are not fetch/freshness timestamps.
Incomplete coverage is visible, not filled with zeros. A clean cache comparison
does not certify that the database is current or ready for production.

Exit code `1` signals detected consistency errors or report-generation failure;
`0` allows documented coverage/retention warnings. All files are prepared before
replacement; each replacement is atomic and the manifest is written last. The
directory is not a multi-file atomic transaction: if interrupted during
replacement, compare **all four hashes** with the manifest and rerun the command
if any differ. Do not accept a mixed report set. Temporary staging files are
removed on controlled failure. Run only one report writer per output directory.

The former Energy-Charts validation is archived under
`docs/history/ENERGY_CHARTS_VALIDATION_2025.md`. The August beta acceptance in
`docs/BETA_DATA_VALIDATION.md` remains historical evidence; newly generated local
reports must not be presented as checks of the newer Railway database.

## Failure and rollback

An importer or candidate-validation failure occurs before publication and leaves `atlas.sqlite3` byte-identical. The run directory is cleaned and the compact report records the failed phase, error type, relevant hashes and cleanup result.

Once exchange preparation has started, any detected target change or loss of a committed WAL/journal causes restoration from the consistent rollback database. The restored database is validated before cleanup. A work directory is retained only if restoration or exact cleanup itself fails; the report then names that one concrete directory and error instead of creating additional large diagnostic copies.

Deletion is limited to resolved paths inside the current per-run directory. The lifecycle does not use recursive wildcard cleanup and refuses to remove unexpected files.

## Community database protection

`community.sqlite3` is independent from the analytical snapshot. The refresh never opens it for writing, copies it into the candidate, replaces it, clears it or deletes its sidecars. Its before/after SHA-256 is included in the compact lifecycle report as an additional non-interference check. Public votes therefore remain outside every Atlas candidate and rollback.

Do not point `--db` at `community.sqlite3`; the lifecycle rejects a collision between the Atlas and community paths.

## Opt-in monthly production refresh

The persistent web service can start one planned production refresh per UTC
calendar month. It is disabled by default (`EEA_MONTHLY_REFRESH=0`) and is
enabled only with `EEA_MONTHLY_REFRESH=1`. The service itself remains available:
the scheduler starts a separate Python child process for the actual refresh.
The child uses this same lifecycle, builds its candidate below the same `/data`
volume, then exits after success or failure.

The standard schedule is the second day of each month at 03:00 UTC. It may be
changed without a cron parser:

| Setting | Default | Purpose |
| --- | --- | --- |
| `EEA_MONTHLY_REFRESH` | `0` | Opt in with exactly `1`; any other value is rejected. |
| `EEA_MONTHLY_REFRESH_DAY_UTC` | `2` | Calendar day, 1 through 28. |
| `EEA_MONTHLY_REFRESH_HOUR_UTC` | `3` | UTC hour, 0 through 23. |
| `EEA_MONTHLY_REFRESH_POLL_SECONDS` | `86400` | Fallback check interval. |
| `EEA_MONTHLY_REFRESH_RETRY_SECONDS` | `21600` | Delay before retrying a failed current-month run. |
| `EEA_MONTHLY_REFRESH_LOCK_STALE_SECONDS` | `43200` | Legacy setting, accepted but no longer used; the OS releases crashed-worker locks. |
| `EEA_MONTHLY_REFRESH_FROM_YEAR` | `2015` | First Ember/Eurostat year for the planned run. |
| `EEA_BATTERY_ENERGY_FILE` | unset | Optional local energy JSON override; otherwise public dashboard CSV. |
| `EEA_BATTERY_POWER_FILE` | unset | Matching local power JSON override; configure both or neither. |

At startup and at each check, a successful report for the current month
suppresses another run. If the service was down at the scheduled time, the
first later check starts the current due month. A successful previous month does
not trigger a run before this month's configured day/hour. The scheduler wakes
at the next scheduled/retry deadline, with the daily interval as an upper bound.
Failed runs record a UTC retry time;
they may be retried, but a successful month is never published twice.

`data/.monthly-refresh.lock` is a small persistent file with an OS-owned lock
(`flock` on Linux, `msvcrt.locking` on Windows). Closing/crashing releases the
lock automatically; no process is killed and no PID/age heuristic is used.
The file stays in place to avoid inode-replacement races. A second shared
`data/.atlas-refresh.lock` serializes both `refresh-all` and monthly lifecycle
workers. Direct individual import commands are still maintenance-only: do not
run them against production while the service/scheduler is active. Use one
writable service replica. The worker rechecks monthly success under its lock.

The compact report is written atomically to
`data/reports/MONTHLY_REFRESH.generated.json`. It records the target month,
timestamps, old/candidate/published hashes, source statuses, publication and
cleanup status, retry time, and a sanitised error when applicable. It never
contains API keys or request URLs with credentials. The separate fixed-size-in-count
`MONTHLY_LIFECYCLE.generated.json` stores lifecycle results. A shared run ID
allows recovery if the worker exits after publication but before recording
monthly success. Logs identify source/country progress and publication phases.

Read the status without opening or changing either database:

```powershell
eea --db data/atlas.sqlite3 monthly-refresh-status
```

The status command reports `not_run` or `unreadable_report` explicitly. The
public `/api/health` includes last-run state, target month, valid completion/retry
timestamps, publication status and allowlisted statuses for all eight sources.
`source_warnings` lists retained, failed, unattempted or unknown source results
after a completed attempt; it is absent while running. It is not a refresh
control endpoint and exposes no errors, paths or source payloads. These source
statuses describe the **latest attempt**, not necessarily the serving database:
`not_published` means even successful source steps did not reach production.
`unknown` is used for missing/invalid fields in older reports. `refreshed` means
the importer succeeded, not that the upstream dataset has recent observations.
A `running` report after an abrupt exit is the last recorded
state, not proof that a process is still alive; kernel locks remain authoritative.

### Planned source policy

The planned mode is intentionally separate from strict `refresh-all`; it does
not weaken that manual command.

- Ember, Ember wholesale prices, Eurostat core, and Eurostat supplement are
  critical. Any error aborts the candidate and leaves the published
  `atlas.sqlite3` byte-identical.
- Automatic publication must preserve every previously published observation
  key (country, source, series, metric, unit and period). Empty/partial source
  responses that remove keys are rejected even if HTTP/JSON parsing succeeded,
  except for the narrowly defined Ember monthly component policy below.
  Numerical revisions are allowed. Snapshots may advance their date but cannot
  lose series or move backwards. Eurostat core and supplement are checked as
  one group because core temporarily replaces supplement rows. Actual deletion
  of published series still requires a reviewed manual decision.
- When a previously published **monthly Ember generation component or its
  percentage share** disappears, keep the entire previous country/month across
  generation (including all totals and shares), demand and carbon intensity.
  Other months, countries and yearly data can update normally. Do not fill gaps
  with zero or splice old components into revised totals. This policy applies
  only after every Ember import succeeds, only while fresh generation components
  remain for that month, and never to missing aggregate, demand, carbon or yearly
  keys. Those losses, empty periods and request/normalization failures still abort.
  The final global coverage guard remains mandatory after restoration.
- Retained observations carry `quality_status=retained_source_gap` in SQLite.
  The Ember result is `refreshed_with_retention`; its `retention` object lists
  missing series, missing/retained observation counts and each country/month.
  Summary/compare rows expose `retained_source_periods`, `retained_source_metrics`
  and a warning in `quality_issues`. YTD and yearly monthly-demand fallbacks
  propagate retention only to dependent metrics; independent yearly generation
  is not marked merely because historical months were retained. Time-series
  points (including the Atlas average) and profiles expose quality status.
  Map details and comparison/ranking notices explain the older data; affected
  comparison CSVs include quality columns. A complete later source response
  replaces the retained month and clears its flag automatically. A cache fetch
  timestamp is not a fresh observation timestamp for these retained values.
  No extra persistent database copies or external dependencies are introduced.
- Battery-Charts uses the two public CSV download buttons at
  <https://battery-charts.de/battery-charts/> in headless Chromium. CSV values
  are GWh/GW, not the kWh/kW used by local JSON. Units are checked against the
  loaded charts; column names, finite/non-negative values, matching dates and
  historical coverage are validated before replacement. The raw CSVs replace
  the same two source-cache entries, with landing-page provenance and hashes.
  Data attribution remains Battery-Charts / RWTH ISEA, CC BY 4.0. No API key
  is extracted, configured or retained; the legacy direct API remains disabled.
  Two configured local JSONs take precedence. If only one file is configured,
  or a configured file is missing, retain `preserved_controlled_input` without
  silently falling back to network access.
- Battery month identity includes its month start; its published end date
  may advance (including closing a provisional month), never move backwards.
  Every prior month/segment/metric must remain present. This exception is
  restricted to Battery-Charts monthly records, not other time series.
- JRC storage uses the existing four filtered XLSX dashboard downloads in
  headless Chromium (Operational; Electrochemical and Mechanical/PHS).
  Snapshots cannot move backwards or lose published series.
- Both browser sources are optional and run sequentially in the existing
  monthly child process. Missing browser/runtime, timeout, malformed/partial
  exports or coverage loss produces `failed_optional` and restores that source's
  rows and cache. A successful core refresh may still publish; a successful
  month does not retry its optional failures until the next monthly run.
  Downloads and browser profiles are temporary and removed on browser close;
  no new persistent JSON/CSV/database copies are created in `/data`.
  Install the browser during the build, never from the running monthly worker;
  see [DEPLOYMENT.md](DEPLOYMENT.md#browser-exports-for-jrc-storage-and-battery-charts).
- JRC hydro and EEA GHG are attempted as optional sources. A temporary failure
  rolls only that source back inside the candidate and is reported as
  `failed_optional`; existing rows remain part of the published candidate.

Optional-source coverage checks run inside the source savepoint, so a partial
response restores both observations and cache changes. After successful core
checks, cache cleanup removes only older Ember responses fully covered by a
newer response fetched this run for the exact same endpoint and target/options.
Partial overlaps and unrelated caches remain. SQLite reuses freed pages; no
live `VACUUM` is run and immediate physical file shrinkage is not guaranteed.
Existing source-cache keys are overwritten by their importers. Crash-retained
work directories are not blindly swept: inspect them before manual recovery.

For a supervised one-off run with the same source policy, use:

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m electricity_atlas.cli --db .\data\atlas.sqlite3 monthly-refresh-run --community-db .\data\community.sqlite3
```

This command does not need `EEA_MONTHLY_REFRESH=1`; that switch controls only
the background scheduler. Disable the scheduler again with
`EEA_MONTHLY_REFRESH=0` and restart the web service. A successful current month
is a no-op even for the one-off command. Disabling prevents future launches;
it does not cancel an already running worker.
