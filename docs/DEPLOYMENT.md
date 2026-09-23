# Deployment and operations

The European Electricity Atlas has no runtime dependency beyond Python 3.11 or newer and the Python standard library. It serves the Atlas snapshot as a read-only SQLite dataset and keeps public Europa-Overload votes in a separate SQLite database.

## Runtime configuration

The bilingual public pages require Jinja2, declared in both `pyproject.toml` and
`requirements.txt`; deploy through the normal dependency-installing build.
The pinned i18next runtime and generated translation bundle are served locally.
No translation API, language secret, database migration or additional Railway
service is needed. See [localization](LOCALIZATION.md).

The command-line value wins over an environment variable; an environment variable wins over the local default.

| Setting | Default | Purpose |
| --- | --- | --- |
| `EEA_ATLAS_DB` | `data/atlas.sqlite3` | Read-only Atlas dataset for the UI API. |
| `EEA_COMMUNITY_DB` | `data/community.sqlite3` | Separate persistent database for anonymous wallpaper votes. |
| `EEA_HOST` | `127.0.0.1` | Interface to bind. |
| `EEA_PORT` | `8000` | TCP port, from 1 through 65535. |
| `EEA_PUBLIC_ORIGIN` | unset | Exact public `http://` or `https://` origin allowed to submit votes. |
| `EEA_REQUIRE_EXISTING_DB` | unset / false | Require an existing, readable Atlas database with the expected schema. |
| `EEA_MONTHLY_REFRESH` | `0` | Opt-in internal monthly candidate refresh; use exactly `1` to enable. |
| `EEA_MONTHLY_REFRESH_DAY_UTC` | `2` | UTC calendar day of the normal monthly run (1–28). |
| `EEA_MONTHLY_REFRESH_HOUR_UTC` | `3` | UTC hour of the normal monthly run (0–23). |
| `EEA_MONTHLY_REFRESH_POLL_SECONDS` | `86400` | Scheduler fallback check interval. |
| `EEA_MONTHLY_REFRESH_RETRY_SECONDS` | `21600` | Delay after a failed run before another attempt. |
| `EEA_MONTHLY_REFRESH_LOCK_STALE_SECONDS` | `43200` | Legacy setting; OS locks now release automatically on process exit. |
| `EEA_MONTHLY_REFRESH_FROM_YEAR` | `2015` | History start for planned Ember and Eurostat imports. |
| `EEA_BATTERY_ENERGY_FILE` | unset | Optional local energy JSON override; otherwise public dashboard export. |
| `EEA_BATTERY_POWER_FILE` | unset | Matching local power JSON override; configure both or neither. |
| `RAILPACK_PYTHON_PLAYWRIGHT_INSTALL` | `1` | Build-time installation of Playwright browsers and their system dependencies for public storage exports. |

Example local development start:

```powershell
$env:EEA_ATLAS_DB = '.\data\atlas.sqlite3'
$env:EEA_COMMUNITY_DB = '.\data\community.sqlite3'
eea serve --port 8765
```

For a production-like start, use a persistent Atlas snapshot and reject a missing or invalid one before the HTTP port is opened:

```powershell
$env:EEA_HOST = '127.0.0.1'
$env:EEA_PORT = '8000'
$env:EEA_PUBLIC_ORIGIN = 'https://atlas.example'
eea --db 'D:\eea-data\atlas.sqlite3' serve --community-db 'D:\eea-community\community.sqlite3' --require-existing-db
```

`EEA_PUBLIC_ORIGIN` is an origin, not a URL: it may not contain a path, query, fragment, or credentials. When it is configured, every vote `POST` must carry exactly that `Origin` header. A public HTTPS origin also makes the anonymous vote cookie `Secure`, in addition to `HttpOnly`, `SameSite=Lax`, and `Path=/`.

Do not let a reverse proxy’s client-supplied `Host` or `X-Forwarded-*` headers define the public origin. The application uses only the configured `EEA_PUBLIC_ORIGIN`; the proxy should preserve the browser `Origin` header and restrict access to same-origin traffic. Terminate HTTPS at the proxy and forward ordinary requests to the local Atlas process.

## Railway beta deployment

The repository contains `railpack.json` as the reproducible Railway/Railpack
entry point. It pins Python 3.11 and starts the source-layout application on
Railway's injected `PORT`. Browser binaries are deliberately not installed:
HTTP requests read a prepared Atlas snapshot. Only the explicitly enabled
monthly scheduler may launch a separate importer child process.

Use one service instance and attach one persistent volume at `/data`. Before
the first healthy deployment, upload the reviewed release snapshot as
`/data/atlas.sqlite3`. The service creates `/data/community.sqlite3` on first
start and keeps public vote state separate from the analytical snapshot.

The minimum Railway service setup is:

1. Connect the GitHub repository to the service.
2. Attach a persistent volume with mount path `/data`.
3. Register a local SSH public key with Railway; volume file commands require
   an active deployment and a registered key.
4. Upload `data/atlas.sqlite3` to `/atlas.sqlite3` on that volume, for example
   with `railway volume files upload ./data/atlas.sqlite3 /atlas.sqlite3`.
5. Configure `/api/health` as the deployment healthcheck path.
6. Generate the temporary Railway domain and set `EEA_PUBLIC_ORIGIN` to its
   exact `https://...up.railway.app` origin.
7. Keep one replica while the writable community store remains SQLite.

The beta service uses `https://ee-atlas.eu` as its public origin. The generated
`https://eea-production.up.railway.app` address remains a technical Railway
fallback and is not the address advertised to users. The service uses the
Railway healthcheck path `/api/health` and this effective start command:

```text
PYTHONPATH=src python -m electricity_atlas.cli --db /data/atlas.sqlite3 serve --community-db /data/community.sqlite3 --host 0.0.0.0 --port $PORT --require-existing-db
```

The start command uses `--require-existing-db`; a missing, empty, or invalid
Atlas snapshot therefore fails closed instead of publishing an empty Atlas.
The production domain is attached in the service's **Settings → Networking →
Public Networking** section. Railway supplies a routing target and a separate
TXT ownership challenge. The root domain uses the DNS provider's dynamic
ALIAS/CNAME-flattening record, while the TXT challenge is copied exactly from
Railway. Any conflicting parking A record for the root domain must be removed;
nameserver and SOA records remain untouched.

Wait until Railway has accepted both DNS records and completed certificate
authority validation before advertising the domain. Then set
`EEA_PUBLIC_ORIGIN=https://ee-atlas.eu`, deploy the resulting configuration,
and verify `/api/health`, `/api/`, `/api.html`, `/openapi.json`, core navigation,
and a vote submission through the custom HTTPS domain. Follow at least one
linked analytical example from `/api.html` to confirm that the public discovery
chain reaches a JSON response. Do not add a trailing slash or path to the origin
value.

## Data volumes and replacement

Treat `atlas.sqlite3` as a versioned, read-only release snapshot. Mount or copy it from persistent storage, start the server with `--require-existing-db`, and replace it only in a controlled maintenance step.

For a complete source refresh, use the isolated [`refresh-all` lifecycle](DATA_REFRESH.md). It builds the candidate and rollback database under the Git-ignored `data/.refresh-work/<run-id>/`, checks Windows replacement locks before network access, publishes the validated candidate atomically where possible, and removes its temporary databases and sidecars after success. Persistent fallback copies do not remain in `data/` by default. The community vote database is never part of this lifecycle.

Treat `community.sqlite3` as a separate persistent database on the same `/data` volume. It contains public vote state and must never be replaced by an Atlas dataset or included in a data release. Keep Ember keys and all other secrets outside both SQLite files and outside release assets.

### Monthly refresh on Railway

Use the existing web service and its attached `/data` volume. Do **not** create
a second Railway Cron service for this workflow unless shared-volume ownership,
single-writer behaviour, and same-volume atomic replacement have separately
been proved. Railway Cron services are designed to run their start command and
exit after the task, whereas the selected design keeps the permanently running
web server, its candidate database, lock, reports, and published Atlas snapshot
on the one known writable volume.

After committing/pushing the hardening patch and confirming Linux CI and the
new deployment are green, keep `EEA_MONTHLY_REFRESH=0` for the supervised first
run. In Railway open **European Electricity Atlas → EEA → Variables** and add
`EMBER_API_KEY` securely (never paste it into commands, Git or logs).

On your Windows PC, open PowerShell in `E:\EEA`. If the CLI says Unauthorized,
log in, then open a shell **inside the deployed service**:

```powershell
C:\Tools\Railway\railway.exe login
C:\Tools\Railway\railway.exe ssh --service EEA
```

In that remote shell, run:

```sh
PYTHONPATH=src python -m electricity_atlas.cli --db /data/atlas.sqlite3 monthly-refresh-run --community-db /data/community.sqlite3
PYTHONPATH=src python -m electricity_atlas.cli --db /data/atlas.sqlite3 monthly-refresh-status
```

The first command performs real source requests and publishes only a checked
candidate. Confirm `status=success`, `publication=published`, cleanup success
and expected source statuses; check the public `/api/health` and a data page.
Do not use `railway run` for this: it runs locally with Railway environment
variables, not inside the service container.

Then set these **EEA service Variables** and deploy the pending changes:

```text
EEA_MONTHLY_REFRESH=1
EEA_MONTHLY_REFRESH_DAY_UTC=2
EEA_MONTHLY_REFRESH_HOUR_UTC=3
EEA_MONTHLY_REFRESH_FROM_YEAR=2015
```

Only set the optional `EEA_BATTERY_ENERGY_FILE` and `EEA_BATTERY_POWER_FILE` when
both approved JSON files actually exist on the volume. No placeholder paths
are required. Keep **one replica**, the persistent `/data` volume, and the web
service continuously running (do not enable service sleeping for this scheduler).

Keep Ember credentials exclusively as Railway secrets. The scheduler checks on
startup and wakes at schedule/retry deadlines (at most 24 hours between checks).
A missed due time is caught up after a restart; a completed month is not run
again. Enabling after day 2 can start the current month's run immediately if
it has not yet succeeded. It runs the child without stopping HTTP handling. Read
`/data/reports/MONTHLY_REFRESH.generated.json` for the last result, candidate
and publication hashes, source policy, and next retry time.

### Browser exports for JRC storage and Battery-Charts

In **Railway → EEA → Variables**, add:

```text
RAILPACK_PYTHON_PLAYWRIGHT_INSTALL=1
```

Deploy the code and variable together. This is the official
[Railpack Python Playwright integration](https://railpack.com/languages/python/#playwright):
it installs browser binaries matching the project's Playwright package plus
Linux runtime libraries during the build. A restart of an older image is not
enough. If the selected Railpack version does not recognize this setting,
update the builder before enabling browser exports; do not install packages
in the running service or add a separate cron service with a different volume.

The repository includes `requirements.txt` as Railpack's pip installation
entry point. Railpack 0.39 detects a plain `pyproject.toml` as Python, but does
not install its dependencies without requirements or a supported lockfile.
Keep `requirements.txt` synchronized with `[project].dependencies`; an offline
test enforces this. The build must show `pip install -r requirements.txt`
before `playwright install --only-shell`. The resulting `/app/.venv` and browser
cache must be carried into the runtime image by Railpack.

Verified on Railway Linux on 2026-09-23 (deployment
`ba7b4848-45e3-4343-a00a-23f45f30c556`): Playwright 1.63.0 / Chromium 153
started successfully. Against an in-memory copy of the production Atlas,
Battery-Charts imported 1,692 observations through 2026-09-22 and JRC imported
150 observations from four exports dated 2026-09-23. Both passed the published
coverage checks; production Atlas/community file hashes were unchanged and
the public health check stayed healthy. This was an acquisition smoke test,
not another monthly publication. The CLI-deployed requirements fix must also
be committed/pushed so subsequent GitHub deployments retain it.

Playwright is already a production dependency (established Microsoft project,
Apache-2.0); this adds its browser runtime, not another Python library.
Browser binaries enlarge the image and increase peak RAM during the two
sequential monthly acquisitions. Keep Playwright/browser security updates
current. No privileged container, custom sandbox bypass, persistent browser
profile or extracted website API key is required. Do not suppress TLS checks.

JRC storage downloads its four official filtered XLSX exports; Battery-Charts
downloads the energy/power CSV pair through the public buttons. Leave both
`EEA_BATTERY_*_FILE` variables unset for automatic CSV acquisition. Explicit
local JSON overrides remain available. The old direct Battery-Charts API
client remains disabled.

These sources, JRC hydro and EEA GHG are optional: failures preserve their
existing observations and source caches and appear as `failed_optional` in
the monthly report. Core sources (Ember, prices and both Eurostat imports)
remain critical. A completed monthly run does not rerun just because this
browser setting was added; the next due month uses it automatically.

After deployment, verify the build installed browsers and perform a read-only,
in-memory acquisition/import check on Linux before claiming production browser
acceptance. Local Windows headless success is not Linux deployment acceptance.
Do not force another whole monthly refresh just to test the browser runtime.

The worker creates only its exact candidate/rollback files below
`/data/.refresh-work/<run-id>/` plus two small persistent lock files
`/data/.monthly-refresh.lock` and `/data/.atlas-refresh.lock`, and two overwritten
monthly/lifecycle reports under `/data/reports`. Cleanup never scans `*.sqlite3`, `*-wal`, or
`*-shm`. `community.sqlite3` and its sidecars are outside the lifecycle and are
hash-checked for non-interference. For operational rollback, leave the failed
report in place, keep the old published Atlas file, correct the source or
secret, and let the reported retry time or a manual `monthly-refresh-run`
attempt create a new candidate.

Empty/partial responses are checked against previously published coverage.
Critical-source loss blocks publication; optional-source loss rolls that source
back. See [DATA_REFRESH.md](DATA_REFRESH.md) for cache retention and crash recovery.
To disable future launches set `EEA_MONTHLY_REFRESH=0` and deploy the change;
this is not a cancellation command for an already running worker.

To update the Atlas snapshot safely:

1. Stop the server or route traffic away from it.
2. Preserve the current Atlas file for rollback.
3. Validate the replacement snapshot with the project checks.
4. Publish the replacement as the configured Atlas file.
5. Start with `--require-existing-db` and call `/api/health`.

To roll back, stop the server, restore the previous Atlas snapshot, and start it again. This does not alter the community database.

## Health check

`GET /api/health` reports component states and a strictly limited refresh summary:

```json
{"status":"ok","atlas_database":"ok","community_database":"ok","monthly_refresh":{"last_run_status":"not_run"}}
```

It returns a non-success status when either database cannot be reached. A failed
refresh alone does not make the serving database unhealthy. The refresh summary
may add `target_month`, `completed_at`, `next_attempt_at`, `publication`, `sources`
and `source_warnings`. These describe the last recorded attempt, not proof that
a worker is alive or all upstream data is recent. It never exposes file paths,
detailed errors, source payloads, request URLs or secrets.

For example, `last_run_status=success`, `publication=published` and
`sources.jrc_storage=failed_optional` means the core candidate was published
while JRC kept its previous data. `refreshed_with_retention` identifies Ember
updates containing explicitly retained historical months. Inspect the local
monthly report for the details. A successful month does not retry optional
sources automatically. If `publication=not_published`, even `refreshed` source
steps belong only to the rejected attempt, not the serving database.

`source_warnings` contains known source IDs with a status other than `refreshed`
after a completed attempt, including `unknown` for incomplete legacy reports.
The health contract is documented in `/openapi.json`. Do not turn these source
warnings into service restart/HTTP-503 conditions; database availability and
data freshness are different signals.

## Community backups and restore

Create a consistent copy with SQLite’s backup API:

```powershell
eea backup-community --output 'D:\eea-backups\community-2026-08-25.sqlite3'
```

The command uses `EEA_COMMUNITY_DB` unless `--community-db` is supplied. It creates the output parent directory, refuses to overwrite an existing target unless `--force` is specified, writes through a temporary file, and publishes the completed backup atomically. Vote contents are never printed.

On the Railway Hobby beta service, create the consistent copy inside the
running container and then download it from the volume:

```sh
cd /app
PYTHONPATH=src python -m electricity_atlas.cli backup-community --community-db /data/community.sqlite3 --output /data/backups/community-2026-08-25.sqlite3
```

```powershell
railway volume files --volume eea-volume download /backups/community-2026-08-25.sqlite3 E:\EEA-Backups\community-2026-08-25.sqlite3
```

Railway-managed volume backups and point-in-time recovery require the Pro
plan. They are not part of the Hobby beta operating model. A consistent manual
backup has been downloaded outside the repository; the full restore rehearsal
is post-beta because the community score belongs only to the optional Europa
Overload feature and is not an analytical Atlas dataset.

For a manual restore, stop the server first, retain the current community database as a rollback copy, then replace only the community database with the selected backup. Start the server and check `/api/health`. Never restore a community backup over `atlas.sqlite3`, and never replace `community.sqlite3` with an Atlas release snapshot.

The anonymous browser cookie and basic rate limit reduce accidental repeat votes and simple click spam. They are not a manipulation-proof election system.
