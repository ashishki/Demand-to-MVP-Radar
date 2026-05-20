# Production Readiness Review

Date: 2026-05-20
Scope: Four weekly local runs before private beta
Verdict: NOT READY

---

## Readiness Verdict

Demand-to-MVP Radar is not ready for private beta or SaaS work until the operator completes four weekly local runs and records enough evidence that the system creates repeated personal value.

Current status:

- Four-run evidence checklist: not complete
- Private beta: blocked
- SaaS or hosted product work: blocked
- Allowed next work: local reliability, source quality, backup/recovery, and personal weekly operation

## Four-Run Evidence Checklist

Each weekly run must be reviewed as an operating record, not just a passing command.

| Run | Run success | Source failures | Retrieval metrics | Decision count | Cost | Backup status | Privacy checks | Verdict |
|-----|-------------|-----------------|-------------------|----------------|------|---------------|----------------|---------|
| Run 1 | pending | pending | pending | pending | pending | pending | pending | pending |
| Run 2 | pending | pending | pending | pending | pending | pending | pending | pending |
| Run 3 | pending | pending | pending | pending | pending | pending | pending | pending |
| Run 4 | pending | pending | pending | pending | pending | pending | pending | pending |

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
