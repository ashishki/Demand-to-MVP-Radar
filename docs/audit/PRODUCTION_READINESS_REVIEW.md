# Production Readiness Review

Updated: 2026-07-13
Scope: Four evidence cycles plus longitudinal operating proof before private beta
Verdict: NOT READY

---

## Readiness Verdict

Demand-to-MVP Radar is not ready for private beta or SaaS work until the operator completes four weekly local runs and records enough evidence that the system creates repeated personal value.

Current status:

- Counting evidence cycles: `2/4`
- Human-recorded decisions: `0`
- Four distinct weekly windows: not demonstrated
- Private beta: blocked
- SaaS or hosted product work: blocked
- Allowed next work: local reliability, source quality, backup/recovery, and personal weekly operation

## Four-Run Evidence Checklist

Each weekly run must be reviewed as an operating record, not just a passing command.

| Run | Run success | Source failures | Retrieval metrics | Decision count | Cost | Backup status | Privacy checks | Verdict |
|-----|-------------|-----------------|-------------------|----------------|------|---------------|----------------|---------|
| Run 1 / T62 | report present; not full pipeline | historical report notes | n/a manual report | 0 human | USD 0 | not run | public-source report | no-count |
| Run 2 / R2 | public backfill present | historical report notes | n/a manual report | 0 human | USD 0 | not run | public URLs only | counts, incomplete operating proof |
| Run 3 / DSM | public backfill present | historical report notes | n/a manual report | 0 human | USD 0 | not run | public URLs only | counts, incomplete operating proof |
| Run 4 / W14 | referenced output absent from clean clone | Telegram-only source gap reported | unavailable for clean-clone verification | 0 human | reported USD 0 | not run | cannot verify absent artifact | no-count |

This table is reconciled by
`reports/evidence/portfolio-audit-2026-07-13/four_slot_decision_log.json`.
It does not transform same-week backfills into longitudinal weekly evidence.

Required evidence for each row:

- run success: run ID, timestamp, status, report path, and `last_scheduled_run` when scheduled
- source failures: `runs.source_counts`, `runs.error_counts`, quarantine review, and disabled source notes
- retrieval metrics: corpus version, index age, retrieval eval status, insufficient-evidence count, and source diversity where available
- decision count: number of operator decisions recorded from dossiers
- cost: estimated LLM cost, configured budget ceiling, and any `budget_exceeded` result
- backup status: latest backup timestamp, SQLite integrity check result, and restore-smoke status
- privacy checks: no raw exports, private notes, SQLite files, credentials, or generated private reports in git

## Minimum Readiness Criteria

Private beta remains blocked until all of these are true:

- four weekly local runs complete without manual code changes
- failed sources are isolated and do not block all other approved sources
- at least 10-20 dossiers exist from real evidence
- at least one MVP experiment is launched, killed, or revisited because of the system
- every material dossier claim has citations or explicit inference markers
- `needs_more_evidence` and `insufficient_evidence` appear when evidence is weak
- backup and recovery verification commands pass
- the operator can review top opportunities in under 15 minutes
- no private data appears in git

## Private Beta Gate

Private beta is blocked until the four-run checklist is complete and the readiness verdict changes to READY.

The beta package must not be prepared from promises, screenshots, or isolated successful runs. It requires evidence that the operator repeatedly imports sources, reviews dossiers, records decisions, and acts on at least one experiment outcome.

## SaaS Work Gate

SaaS or hosted product work is blocked after private beta as well. Hosted work requires proof that users need convenience more than local control and that authentication, tenancy, privacy, source compliance, and operational support are worth the added complexity.

Until then, the project remains a local-first personal decision system.

## Review Procedure

1. Run or inspect the latest four weekly run records.
2. Fill one checklist row per run.
3. Attach the report path, corpus version, decision count, cost result, backup verification, and privacy check notes.
4. Mark any failed source as isolated or blocking.
5. Update the readiness verdict only when every minimum readiness criterion is satisfied.
