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

## Data volumes and replacement

Treat `atlas.sqlite3` as a versioned, read-only release snapshot. Mount or copy it from persistent storage, start the server with `--require-existing-db`, and replace it only in a controlled maintenance step.

Treat `community.sqlite3` as a separate persistent volume. It contains public vote state and must never be replaced by an Atlas dataset or included in a data release. Keep Ember keys and all other secrets outside both SQLite files and outside release assets.

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

For a manual restore, stop the server first, retain the current community database as a rollback copy, then replace only the community database with the selected backup. Start the server and check `/api/health`. Never restore a community backup over `atlas.sqlite3`, and never replace `community.sqlite3` with an Atlas release snapshot.

The anonymous browser cookie and basic rate limit reduce accidental repeat votes and simple click spam. They are not a manipulation-proof election system.
