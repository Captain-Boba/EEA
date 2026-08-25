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

Existing files in `data/reports/` are preserved. Coverage and summary reports remain separate products of `eea report`.

## Failure and rollback

An importer or candidate-validation failure occurs before publication and leaves `atlas.sqlite3` byte-identical. The run directory is cleaned and the compact report records the failed phase, error type, relevant hashes and cleanup result.

Once exchange preparation has started, any detected target change or loss of a committed WAL/journal causes restoration from the consistent rollback database. The restored database is validated before cleanup. A work directory is retained only if restoration or exact cleanup itself fails; the report then names that one concrete directory and error instead of creating additional large diagnostic copies.

Deletion is limited to resolved paths inside the current per-run directory. The lifecycle does not use recursive wildcard cleanup and refuses to remove unexpected files.

## Community database protection

`community.sqlite3` is independent from the analytical snapshot. The refresh never opens it for writing, copies it into the candidate, replaces it, clears it or deletes its sidecars. Its before/after SHA-256 is included in the compact lifecycle report as an additional non-interference check. Public votes therefore remain outside every Atlas candidate and rollback.

Do not point `--db` at `community.sqlite3`; the lifecycle rejects a collision between the Atlas and community paths.
