# Deployment and operations

The European Electricity Atlas has no runtime dependency beyond Python 3.11 or newer and the Python standard library. It serves the Atlas snapshot as a read-only SQLite dataset and keeps public Europa-Overload votes in a separate SQLite database.

## Runtime configuration

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
| `EEA_MONTHLY_REFRESH_LOCK_STALE_SECONDS` | `43200` | Expiry for a crashed monthly-worker lease. |
| `EEA_MONTHLY_REFRESH_FROM_YEAR` | `2015` | History start for planned Ember and Eurostat imports. |
| `EEA_BATTERY_ENERGY_FILE` | unset | Approved local Battery-Charts energy JSON on the service volume. |
| `EEA_BATTERY_POWER_FILE` | unset | Approved local Battery-Charts power JSON on the service volume. |

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
the public service reads a prepared Atlas snapshot and never runs importers.

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

Treat `community.sqlite3` as a separate persistent volume. It contains public vote state and must never be replaced by an Atlas dataset or included in a data release. Keep Ember keys and all other secrets outside both SQLite files and outside release assets.

### Monthly refresh on Railway

Use the existing web service and its attached `/data` volume. Do **not** create
a second Railway Cron service for this workflow unless shared-volume ownership,
single-writer behaviour, and same-volume atomic replacement have separately
been proved. Railway Cron services are designed to run their start command and
exit after the task, whereas the selected design keeps the permanently running
web server, its candidate database, lock, reports, and published Atlas snapshot
on the one known writable volume.

To activate it, set Railway service variables such as:

```text
EEA_MONTHLY_REFRESH=1
EEA_MONTHLY_REFRESH_DAY_UTC=2
EEA_MONTHLY_REFRESH_HOUR_UTC=3
EEA_MONTHLY_REFRESH_FROM_YEAR=2015
EEA_BATTERY_ENERGY_FILE=/data/inputs/battery-energy.json
EEA_BATTERY_POWER_FILE=/data/inputs/battery-power.json
```

Keep Ember credentials exclusively as Railway secrets. The scheduler checks on
startup and then daily, so a missed UTC time is caught up after a Railway
restart. It runs the child refresh process without stopping HTTP handling. Read
`/data/reports/MONTHLY_REFRESH.generated.json` for the last result, candidate
and publication hashes, source policy, and next retry time.

The production Docker/Railpack image deliberately has no Playwright/Chromium
runtime. Planned runs therefore preserve the existing JRC storage snapshot;
they do not delete it or create zeros. JRC hydro and EEA GHG are optional and
preserved on failure. Ember, prices, and both Eurostat imports are critical:
their failure prevents publication entirely. Battery values are refreshed only
from both approved local JSON files; absent files preserve the current values
without any Battery-Charts network access.

The worker creates only its exact candidate/rollback files below
`/data/.refresh-work/<run-id>/` plus the short-lived
`/data/.monthly-refresh.lock`. Cleanup never scans `*.sqlite3`, `*-wal`, or
`*-shm`. `community.sqlite3` and its sidecars are outside the lifecycle and are
hash-checked for non-interference. For operational rollback, leave the failed
report in place, keep the old published Atlas file, correct the source or
secret, and let the reported retry time or a manual `monthly-refresh-run`
attempt create a new candidate.

To update the Atlas snapshot safely:

1. Stop the server or route traffic away from it.
2. Preserve the current Atlas file for rollback.
3. Validate the replacement snapshot with the project checks.
4. Publish the replacement as the configured Atlas file.
5. Start with `--require-existing-db` and call `/api/health`.

To roll back, stop the server, restore the previous Atlas snapshot, and start it again. This does not alter the community database.

## Health check

`GET /api/health` reports only component states:

```json
{"status":"ok","atlas_database":"ok","community_database":"ok"}
```

It returns a non-success status when either database cannot be reached. It deliberately does not expose file paths, import state, request URLs, or secrets.

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
