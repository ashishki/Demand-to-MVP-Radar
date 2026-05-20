# Backup and Recovery Guide

Date: 2026-05-20
Status: Local v1 backup and restore guide

---

## Backup Targets

Back up these local artifacts together so evidence, retrieval state, generated outputs, and decisions stay consistent:

- SQLite database: `data/radar.sqlite3`
- SQLite sidecar files: `data/radar.sqlite3-wal` and `data/radar.sqlite3-shm` when present
- retrieval indexes and retrieval chunk metadata under the configured data directory
- raw snapshots and source exports
- Telegram Research Agent exports
- operator notes
- generated reports, dossiers, experiment packs, and evidence delta reports
- ignored local source catalog overrides and schedule environment files

Backups should be encrypted or stored on trusted local media. Do not upload private source exports, operator notes, SQLite files, or generated private reports to public storage.

## Restore Steps

1. Stop scheduled runs and confirm no `demand-mvp-radar run` or `import-sources` process is active.
2. Move the current data and report directories aside instead of deleting them.
3. Restore the SQLite database file and any `-wal` or `-shm` sidecars from the same backup snapshot.
4. Restore retrieval indexes, raw snapshots, Telegram exports, operator notes, reports, dossiers, and experiment packs from the matching backup.
5. Restore ignored local configuration such as `schedule.env` only on the same trusted machine or after reviewing paths and secrets.
6. Run the verification commands below before recording new operator decisions.

## Verification Commands

Run these commands after restore:

```bash
demand-mvp-radar health --json
```

```bash
python - <<'PY'
import sqlite3

connection = sqlite3.connect("data/radar.sqlite3")
print(connection.execute("PRAGMA integrity_check").fetchone()[0])
print(connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0])
PY
```

```bash
demand-mvp-radar run --fixture tests/fixtures/weekly_run --run-id restore-smoke
```

The restore is usable only when health reports a readable database and writable report directory, SQLite returns `ok`, the latest corpus version is expected, index age is acceptable, and the smoke run can write local artifacts.

## Git-Ignored Private Artifacts

These files must remain ignored by git unless intentionally sanitized and reviewed:

- SQLite database files: `data/*.sqlite3`, `*.sqlite3-wal`, `*.sqlite3-shm`
- retrieval indexes and vector/index cache files
- raw snapshots
- private source exports
- Telegram exports
- operator notes and unsanitized notes
- generated reports, dossiers, experiment packs, and evidence delta reports
- local systemd schedule environment files such as `schedule.env`
- `.env`, secrets files, API keys, cookies, tokens, and credentials
- quarantine files that may contain malformed private source rows

If any private artifact appears in `git status`, stop and move it back under the configured local data or report directory before committing.

## Failed-Run Recovery Checklist

Use this checklist before retrying a failed scheduled or manual run:

1. Capture the run ID, command, exit code, and timestamp.
2. Read the command JSON output and local scheduled log under `$DMR_DATA_DIR/logs`.
3. Check `demand-mvp-radar health --json` for database status, report directory writability, corpus version, index age, and last scheduled run status.
4. Inspect SQLite `runs.status`, `runs.source_counts`, and `runs.error_counts`.
5. Inspect quarantine files for malformed source rows.
6. Check whether the failure was caused by budget ceiling, source import, stale index, database write, report write, schema validation, or missing local configuration.
7. Fix source files, permissions, paths, or budget settings without editing generated scores by hand.
8. Retry with the same run ID only when the inputs are unchanged and idempotency is desired.
9. Use a new run ID when inputs or source exports changed materially.
10. After recovery, verify generated reports, dossiers, experiment packs, and decision history before recording new `build`, `reject`, or `revisit` decisions.
