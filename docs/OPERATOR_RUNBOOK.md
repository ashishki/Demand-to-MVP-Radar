# Operator Runbook

Date: 2026-05-20
Status: Local v1 operating guide

---

## Weekly Run Steps

1. Confirm that local configuration points at the intended data and report directories:

```bash
demand-mvp-radar health --json
```

For unattended local runs, install the user-level systemd templates from `deploy/demand-mvp-radar.service` and `deploy/demand-mvp-radar.timer`, then create `%h/.config/demand-mvp-radar/schedule.env` with local-only paths such as `DMR_WEEKLY_FIXTURE`, `DMR_DATA_DIR`, and `DMR_REPORT_DIR`.

2. Import owned sources when new Telegram Research Agent exports, operator notes, or local repository snapshots are ready:

```bash
demand-mvp-radar import-sources --fixture tests/fixtures/source_mix --run-id import-YYYY-WW
```

3. Collect approved live sources when a live-source config is available:

```bash
demand-mvp-radar collect-sources --config config/live-sources.json --run-id collect-YYYY-WW
```

The command stores normalized evidence, updates retrieval for new evidence only, records source failures in the run manifest and health output, and does not generate weekly reports.

4. Run the weekly fixture or configured weekly source bundle:

```bash
demand-mvp-radar run --fixture tests/fixtures/weekly_run --run-id weekly-YYYY-WW
```

5. Keep the generated report, dossier, experiment pack, run manifest, and SQLite database under the configured local directories. Do not move raw private inputs or generated private reports into git.

## Review Steps

1. Read the top opportunities first, then inspect dossier evidence rows for citations, captured dates, source references, and inference markers.
2. Reject or revisit any opportunity with stale evidence, weak source diversity, missing competitor proof, unclear acquisition angle, or a weak willingness-to-pay signal.
3. Record exactly one human-owned decision per reviewed opportunity:

```bash
demand-mvp-radar review \
  --opportunity-id 101 \
  --decision needs_more_evidence \
  --reason "Need fresh competitor and payment proof." \
  --dossier-path reports/dossiers/opportunity-101.md \
  --evidence-gap weak_competitor_proof
```

4. Only use `build` when the dossier has enough cited evidence, a focused one-function MVP, a plausible acquisition path, and an explicit operator reason.
5. For human `build` or `revisit` decisions, create or inspect the MVP experiment pack and confirm that success, kill, revisit, first 10 targets, and timebox are measurable.

## Source Failure Handling

Inspect import output and run metadata for source errors before trusting generated artifacts:

- `runs.source_counts` shows imported and disabled source counts.
- `runs.error_counts` shows quarantined or failed source rows.
- `runs.source_errors` shows source-scoped live collection failures without secret values.
- Evidence delta reports show new, duplicate, stale, quarantined, skipped, and changed evidence.
- Source-specific quarantine files should be reviewed locally and never committed.

Recovery steps:

1. Fix the malformed local source export or remove the bad row.
2. Re-run `import-sources` with the same run ID when the source fingerprint should remain idempotent.
3. Re-run with a new run ID when the source bundle is intentionally changed.
4. If source errors persist, disable that source in the local source catalog and continue with the remaining approved sources.

## Health Checks

Use `demand-mvp-radar health --json` before and after weekly operation. Confirm:

- `status` is `ok`.
- `database.status` is initialized or ok.
- `report_dir.status` is writable.
- `corpus_version` matches the latest intended run.
- `index_age_days` is within `max_index_age_days`.
- `configured_sources` matches the expected local source catalog.
- `credentials` reports only source credential status and environment variable names; it must never contain API keys, tokens, cookies, or secret values.
- `last_source_errors` reports the latest source-scoped collection failures without aborting unrelated sources.
- `last_scheduled_run` shows the latest scheduled run timestamp and status when a `scheduled-...` run has completed.

Treat stale index warnings as a review blocker. A stale index means the latest report may not reflect current evidence; import sources or run the weekly pipeline before recording build decisions.

Credential recovery steps:

1. Keep source configs limited to environment variable names such as `SERPAPI_API_KEY`, `YOUTUBE_API_KEY`, or `PRODUCT_HUNT_TOKEN`.
2. Put actual secret values only in the shell environment or ignored local secrets files.
3. If health reports `missing` or `invalid`, fix only that source's environment variable and leave unrelated sources enabled.
4. Inspect run manifests and logs for source-scoped credential errors, but never paste secret values into logs, issues, docs, reports, or committed fixtures.

## Cost And Budget Review

Weekly runs must respect `DMR_MAX_WEEKLY_LLM_COST_USD` or the CLI `--max-weekly-llm-cost-usd` override. If a run returns `budget_exceeded`, do not trust missing reports as a product signal.

Budget recovery steps:

1. Lower the candidate count or source scope for the next run.
2. Reuse cached local evidence and retrieval chunks where possible.
3. Keep the failed run metadata for audit, but do not manually edit score outputs.
4. Re-run only after the budget ceiling and source scope are intentional.

## Generated Artifacts

Check these local artifacts after a successful weekly loop:

- weekly Markdown report
- opportunity dossiers
- MVP experiment packs
- evidence delta report
- SQLite `runs`, `evidence`, `decisions`, and retrieval chunk rows
- audit/evaluation docs when a task changes retrieval, tools, scoring, or governance

Artifacts are advisory. The operator owns final decisions, experiment execution, outreach, publishing, and source approval.

## Privacy And Backup

Local private data stays local:

- SQLite database files under `data/`
- retrieval indexes and chunk tables
- raw snapshots and source exports
- Telegram exports
- operator notes
- generated reports, dossiers, and experiment packs
- ignored local secrets files and environment variables

Backup guidance:

1. Stop active runs before copying SQLite files.
2. Back up the configured data directory, report directory, raw snapshot directory, and private notes directory together.
3. Keep backups encrypted or on trusted local storage.
4. Never commit raw exports, database files, generated private reports, notes, credentials, cookies, or API keys.
5. After restoring, run `demand-mvp-radar health --json` and a small fixture run to verify database readability, report directory writability, corpus version, and index age.

## Recovery Steps

Use this order for failed runs:

1. Read the command output JSON and identify whether the failure is budget, source import, database, report write, stale index, or schema validation.
2. Check local logs or captured terminal output for the run ID.
3. Inspect SQLite `runs.source_counts` and `runs.error_counts`.
4. Inspect quarantine files for malformed source rows.
5. Confirm the report directory is writable.
6. Re-run the same command only when the failure is transient or the same run ID should remain idempotent.
7. Use a new run ID when inputs changed materially.
8. Record any operator decision only after the recovered artifacts are inspectable.
