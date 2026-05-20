# Phase 8 Report — Decision-Grade Artifacts

Date: 2026-05-20

## What Was Built

Phase 8 is in progress. T28-T30 turn trusted evidence into decision-grade dossier artifacts that expose citations, uncertainty, and next evidence collection targets.

T28 added decision-grade dossier models and a validation helper. Claims must cite known evidence or be explicitly marked as inference, and dossiers include confidence plus countercase fields.

T29 added Markdown and HTML dossier renderers with stable decision sections, provenance-rich citation rows, inference markers, and explicit `insufficient_evidence` handling.

T30 added deterministic missing-evidence analysis for absent independent sources, stale evidence, weak competitor proof, missing acquisition proof, and missing willingness-to-pay signals. It also recorded missing-evidence no-answer coverage in the retrieval evaluation history.

T31 added a local `review` command for recording human operator decisions from generated dossiers. It records dossier paths, rejects `build` decisions without explicit operator rationale, and stores requested evidence gaps for `needs_more_evidence`.

T32 added MVP experiment pack validation and generation. Experiment packs require validation scope, target user, method, first 10 targets, success/kill/revisit thresholds, and a 7-14 day timebox, and can only be generated from a current human `build` or `revisit` decision.

T33 added actionable Markdown rendering for experiment packs. Artifacts include validation sections, citations, risk flags, thresholds, and run-id keyed atomic writes.

T34 added experiment outcome recording and deterministic scoring feedback. Killed experiments suppress matching opportunities until newer evidence appears, and validated experiments raise confidence through configured scoring rules.

T35 added the operator runbook for weekly operation, review, source failure handling, health checks, budget recovery, generated artifacts, privacy, backups, and failed-run recovery.

T36 added local scheduled-run support through user-level systemd service/timer templates and health reporting for the latest `scheduled-...` run.

T37 added the backup and recovery guide for SQLite files, retrieval indexes, reports, raw snapshots, private exports, restore verification, git-ignored artifacts, and failed-run recovery.

T38 added the four-run production readiness review. The current verdict is `NOT READY`; private beta and SaaS or hosted work remain blocked until repeated personal value is proven across four weekly local runs.

## Test Delta

Baseline moved from 86 passing tests after Phase 7 to 119 passing tests after T38.

Current local checks:

- `.venv/bin/pytest tests/ -q` -> 119 passed
- `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass

## Review Result

Phase 8 deep review Cycle 15 completed with Stop-Ship: No.
Phase 9 deep review Cycle 16 completed with Stop-Ship: No.
Phase 10 deep review Cycle 17 completed with Stop-Ship: No.

Findings:

- P0: 0
- P1: 0
- P2: 0

## Health Verdict

OK.

The system remains local-first and deterministic where required. Decision artifacts now expose cited claims, inference markers, and missing-evidence collection gaps without retrieval schema drift.

## Next Task

All planned tasks are complete.

The next goal is to run the system weekly and fill the four-run readiness checklist with real local evidence.

## Notification Summary

Ph8 Decision-Grade Artifacts IN PROGRESS
Built: dossier schema, dossier renderer, missing-evidence analysis, review command, experiment pack model, experiment renderer, experiment outcome feedback, operator runbook, scheduled-run support, backup/recovery guide, production readiness review
Tests: 86->119 pass
Issues: P1:0 P2:0
Health: OK
Next: Run four weekly local readiness cycles
