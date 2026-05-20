# Implementation Journal

Status: append-only retrieval surface. This file records durable handoff context for future sessions.

---

## Entry Template

```markdown
## YYYY-MM-DD - TNN: Task Title

- Agent: codex
- Result: DONE | BLOCKED
- Files changed:
- Tests:
- Baseline before:
- Baseline after:
- Decisions/evidence updated:
- Notes for next agent:
```

---

## 2026-05-19 - Bootstrap Package

- Agent: Codex
- Result: DONE
- Files changed: Phase 1 governance package generated under `docs/`, `.github/workflows/`, and `.claude/commands/`.
- Tests: not run; implementation has not started.
- Baseline before: 0 passing tests (pre-implementation)
- Baseline after: 0 passing tests (pre-implementation)
- Decisions/evidence updated: `docs/DECISION_LOG.md`, `docs/EVIDENCE_INDEX.md`, `docs/retrieval_eval.md`, `docs/tool_eval.md`
- Notes for next agent: Start with T01. Keep the first implementation task limited to package skeleton and smoke-test imports.

## 2026-05-19 - RAG Reference Added

- Agent: Codex
- Result: DONE
- Files changed: `docs/IMPLEMENTATION_REFERENCE_MAP.md`, `docs/ARCHITECTURE.md`, `docs/tasks.md`, `docs/retrieval_eval.md`, `docs/DECISION_LOG.md`, `docs/EVIDENCE_INDEX.md`
- Tests: not run; documentation-only reference update.
- Baseline before: 0 passing tests (pre-implementation)
- Baseline after: 0 passing tests (pre-implementation)
- Decisions/evidence updated: D-009 and E-006
- Notes for next agent: For T07, T09, T10, and T18, inspect only the mapped Dream Motif Interpreter files needed for the current task. Port patterns, not domain code or PostgreSQL/pgvector requirements.

## 2026-05-19 - Codex-Only Workflow

- Agent: Codex
- Result: DONE
- Files changed: `docs/prompts/ORCHESTRATOR.md`, `prompts/ORCHESTRATOR.md`, `prompts/STRATEGIST.md`, `docs/CODEX_PROMPT.md`, `docs/DECISION_LOG.md`, `.claude/commands/orchestrate.md`, hook compatibility scripts
- Tests: documentation and workflow-script validation only; no application code exists yet.
- Baseline before: 0 passing tests (pre-implementation)
- Baseline after: 0 passing tests (pre-implementation)
- Decisions/evidence updated: D-010
- Notes for next agent: Execute orchestrator roles directly in the current Codex session. Do not use Claude Code as an outer runner and do not call `codex exec` from inside Codex.

## 2026-05-19 - Nonstop Loop Discipline

- Agent: Codex
- Result: DONE
- Files changed: `docs/prompts/ORCHESTRATOR.md`, `docs/CODEX_PROMPT.md`, `docs/DECISION_LOG.md`
- Tests: documentation validation only.
- Baseline before: 0 passing tests (pre-implementation)
- Baseline after: 0 passing tests (pre-implementation)
- Decisions/evidence updated: D-011
- Notes for next agent: Do not pause between phases. After phase review, archive, doc update, and phase report, return to Step 0 and continue to the next task unless an explicit stop condition applies.

## 2026-05-19 - T01: Project Skeleton

- Agent: Codex
- Result: DONE
- Files changed: `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `demand_mvp_radar/__init__.py`, `demand_mvp_radar/cli.py`, `demand_mvp_radar/config.py`, `demand_mvp_radar/observability.py`, package namespace `__init__.py` files, `tests/test_smoke.py`
- Tests: `.venv/bin/pytest tests/ -q` -> 3 passed; `.venv/bin/demand-mvp-radar --help` -> exit 0
- Baseline before: 0 passing tests (pre-implementation; pytest unavailable before bootstrap)
- Baseline after: 3 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: RAG remains ON. T01 intentionally created only the retrieval namespace; retrieval ingestion/query behavior starts in later RAG-tagged tasks after storage and source adapters exist.

## 2026-05-19 - T02: CI Setup

- Agent: Codex
- Result: DONE
- Files changed: `.github/workflows/ci.yml`, `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `tests/test_ci_config.py`, `tests/test_smoke.py`, `demand_mvp_radar/observability.py`
- Tests: `.venv/bin/ruff check demand_mvp_radar/ tests/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/` -> pass; `.venv/bin/pytest tests/ -q` -> 6 passed
- Baseline before: 3 passing tests
- Baseline after: 6 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: CI is configured for Python 3.12 with install, ruff check, ruff format check, and pytest steps. Remote CI has not been observed yet.

## 2026-05-19 - T03: First Smoke Tests

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/cli.py`, `demand_mvp_radar/config.py`, `tests/test_smoke.py`, `tests/test_config.py`
- Tests: `.venv/bin/ruff check demand_mvp_radar/ tests/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/` -> pass; `.venv/bin/pytest tests/ -q` -> 9 passed
- Baseline before: 6 passing tests
- Baseline after: 9 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: `demand-mvp-radar health --json` returns status, database, report_dir, configured_sources, and max_index_age_days using local defaults only.

## 2026-05-19 - T04: Configuration and Run Manifest

- Agent: Codex
- Result: DONE
- Files changed: `requirements.txt`, `demand_mvp_radar/config.py`, `demand_mvp_radar/models.py`, `tests/test_config.py`, `tests/test_run_manifest.py`
- Tests: `.venv/bin/ruff check demand_mvp_radar/ tests/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/` -> pass; `.venv/bin/pytest tests/ -q` -> 12 passed
- Baseline before: 9 passing tests
- Baseline after: 12 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: `Settings` loads DMR env overrides and rejects invalid negative budget/timeout values through Pydantic validation. `RunManifest` serializes required run audit fields to JSON.

## 2026-05-19 - T05: Domain Models and SQLite Storage

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/models.py`, `demand_mvp_radar/storage/db.py`, `demand_mvp_radar/storage/migrations.py`, `demand_mvp_radar/storage/repositories.py`, `tests/test_storage.py`
- Tests: `.venv/bin/ruff check demand_mvp_radar/ tests/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/` -> pass; `.venv/bin/pytest tests/ -q` -> 15 passed
- Baseline before: 12 passing tests
- Baseline after: 15 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: SQLite schema creates runs, evidence, opportunities, scores, briefs, decisions, tool_audit_events, and retrieval_chunks. Evidence writes are idempotent by source_fingerprint; decisions append rows.

## 2026-05-19 - T06: Tool Schema and Audit Layer

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/tools/schemas.py`, `demand_mvp_radar/tools/executor.py`, `demand_mvp_radar/tools/audit.py`, `tests/test_tools.py`, `docs/tool_eval.md`, `docs/CODEX_PROMPT.md`
- Tests: `.venv/bin/ruff check demand_mvp_radar/ tests/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/` -> pass; `.venv/bin/pytest tests/ -q` -> 19 passed; `.venv/bin/pytest tests/test_tools.py -q` -> 4 passed
- Baseline before: 15 passing tests
- Baseline after: 19 passing tests
- Decisions/evidence updated: `docs/tool_eval.md`, `docs/tasks.md`, `docs/CODEX_PROMPT.md`, `docs/audit/REVIEW_REPORT.md`
- Notes for next agent: T06 established the Tool-Use evaluation baseline and passed targeted deep review Cycle 2. T07 can implement source adapters against the existing evidence model and storage layer.

## 2026-05-19 - T07: Source Adapter Interfaces and Telegram Import

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/sources/base.py`, `demand_mvp_radar/sources/telegram_export.py`, `tests/test_sources.py`, `tests/fixtures/telegram_export.json`
- Tests: `.venv/bin/ruff check demand_mvp_radar/ tests/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/` -> pass; `.venv/bin/pytest tests/ -q` -> 22 passed
- Baseline before: 19 passing tests
- Baseline after: 22 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: Telegram adapter imports valid local fixture rows into EvidenceRecord objects, quarantines malformed rows to JSONL, and derives stable content hashes independent of run ID.

## 2026-05-19 - T08: URL and Snapshot Source Tools

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/sources/manual_urls.py`, `demand_mvp_radar/sources/serp_snapshot.py`, `demand_mvp_radar/sources/store_metadata.py`, `tests/test_source_tools.py`, `tests/fixtures/serp_snapshot.json`, `tests/fixtures/store_listing.json`, `docs/tool_eval.md`, `docs/CODEX_PROMPT.md`
- Tests: `.venv/bin/ruff check demand_mvp_radar/ tests/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/` -> pass; `.venv/bin/pytest tests/ -q` -> 27 passed; `.venv/bin/pytest tests/test_source_tools.py -q` -> 5 passed
- Baseline before: 22 passing tests
- Baseline after: 27 passing tests
- Decisions/evidence updated: `docs/tool_eval.md`, `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: URL snapshots use injectable clients, bounded timeout retry, provenance fields, shared HTTP span, and ToolExecutor audit coverage. SERP/store readers import saved fixtures only.

## 2026-05-19 - T09: Retrieval Ingestion Pipeline

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/retrieval/chunking.py`, `demand_mvp_radar/retrieval/embeddings.py`, `demand_mvp_radar/retrieval/index.py`, `demand_mvp_radar/retrieval/ingestion.py`, `scripts/eval_retrieval.py`, `tests/fixtures/retrieval_corpus.json`, `tests/test_retrieval.py`, `tests/eval/test_retrieval_eval.py`, `docs/retrieval_eval.md`, `docs/CODEX_PROMPT.md`
- Tests: `.venv/bin/python scripts/eval_retrieval.py --fixture tests/fixtures/retrieval_corpus.json` -> chunk_count 3; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/pytest tests/ -q` -> 31 passed; `.venv/bin/pytest tests/eval/test_retrieval_eval.py::test_ingestion_baseline_row_has_required_fields -q` -> 1 passed
- Baseline before: 27 passing tests
- Baseline after: 31 passing tests
- Decisions/evidence updated: `docs/retrieval_eval.md`, `docs/tasks.md`, `docs/CODEX_PROMPT.md`, `docs/audit/REVIEW_REPORT.md`
- Notes for next agent: T09 established the RAG ingestion baseline for corpus-t09-v1 with retrieval-index-v1 and local-hash-embedding-v1. T10 should implement query-time retrieval and the required insufficient_evidence path without importing ingestion code.

## 2026-05-19 - T10: Query-Time Retrieval and Insufficient Evidence

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/retrieval/query.py`, `demand_mvp_radar/retrieval/index.py`, `scripts/eval_retrieval.py`, `tests/test_retrieval_query.py`, `tests/eval/test_retrieval_eval.py`, `tests/fixtures/retrieval_queries.json`, `docs/retrieval_eval.md`, `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Tests: `.venv/bin/python scripts/eval_retrieval.py --fixture tests/fixtures/retrieval_queries.json` -> hit@3 1.0, citation_precision 1.0, no_answer_accuracy 1.0, answer_faithfulness 1.0; `.venv/bin/pytest tests/test_retrieval_query.py::test_query_returns_insufficient_evidence_when_support_is_low -q` -> 1 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/pytest tests/ -q` -> 35 passed
- Baseline before: 31 passing tests
- Baseline after: 35 passing tests
- Decisions/evidence updated: `docs/retrieval_eval.md`, `docs/tasks.md`, `docs/CODEX_PROMPT.md`, `docs/audit/REVIEW_REPORT.md`, `docs/archive/CYCLE5_T10_REVIEW.md`
- Notes for next agent: T10 established the RAG query baseline for corpus-t10-v1 and keeps query code separate from ingestion. T11 can cluster evidence using retrieval packets and stored evidence without changing retrieval schema.

## 2026-05-19 - T11: Deduplication and Opportunity Clustering

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/clustering.py`, `demand_mvp_radar/models.py`, `tests/test_clustering.py`
- Tests: `.venv/bin/pytest tests/test_clustering.py -q` -> 3 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/pytest tests/ -q` -> 38 passed
- Baseline before: 35 passing tests
- Baseline after: 38 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`, `docs/audit/REVIEW_REPORT.md`, `docs/archive/PHASE3_REVIEW.md`
- Notes for next agent: T11 closes Phase 3. Phase 4 starts at T12 scoring and can consume `OpportunityCandidate` fields: opportunity_id, normalized_pain, target_audience, workflow, acquisition_channel, source_evidence_ids, and candidate_title.

## 2026-05-19 - T12: Deterministic Scoring and Recommendations

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/scoring.py`, `demand_mvp_radar/models.py`, `tests/test_scoring.py`
- Tests: `.venv/bin/pytest tests/test_scoring.py -q` -> 3 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/pytest tests/ -q` -> 41 passed
- Baseline before: 38 passing tests
- Baseline after: 41 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: T12 scoring is deterministic and has no LLM-owned arithmetic. Low evidence returns `revisit` with a minimum-evidence threshold reason.

## 2026-05-19 - T13: LLM Extraction Adapter

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/llm/adapter.py`, `demand_mvp_radar/llm/extraction.py`, `demand_mvp_radar/models.py`, `tests/test_llm_extraction.py`, `docs/tool_eval.md`
- Tests: `.venv/bin/pytest tests/test_llm_extraction.py -q` -> 3 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/pytest tests/ -q` -> 44 passed
- Baseline before: 41 passing tests
- Baseline after: 44 passing tests
- Decisions/evidence updated: `docs/tool_eval.md`, `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: T13 uses fake providers in tests only. Extraction validates `OpportunityExtraction` before returning data and skips provider calls when retrieval status is `insufficient_evidence`.

## 2026-05-19 - T14: Brief Synthesis and Markdown Reports

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/briefs.py`, `demand_mvp_radar/reports/markdown.py`, `demand_mvp_radar/reports/html.py`, `tests/test_reports.py`
- Tests: `.venv/bin/pytest tests/test_reports.py -q` -> 3 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/pytest tests/ -q` -> 47 passed
- Baseline before: 44 passing tests
- Baseline after: 47 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`, `docs/audit/REVIEW_REPORT.md`, `docs/archive/PHASE4_REVIEW.md`
- Notes for next agent: T14 closes Phase 4. Markdown reports sort scored briefs by total score, include cited evidence/provenance, and write atomically through temp-file replace.

## 2026-05-19 - T15: Operator Decision Memory

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/decisions.py`, `demand_mvp_radar/storage/repositories.py`, `demand_mvp_radar/storage/migrations.py`, `demand_mvp_radar/models.py`, `tests/test_decisions.py`
- Tests: `.venv/bin/pytest tests/test_decisions.py tests/test_storage.py -q` -> 6 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/pytest tests/ -q` -> 50 passed
- Baseline before: 47 passing tests
- Baseline after: 50 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: Decisions remain human-owned. `record_operator_decision` appends rows, and `get_decision_history` returns the latest decision plus full chronological history.

## 2026-05-19 - T16: Rejected-Idea Suppression and Revisit Logic

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/scoring.py`, `demand_mvp_radar/models.py`, `tests/test_decision_memory.py`
- Tests: `.venv/bin/pytest tests/test_decision_memory.py tests/test_scoring.py -q` -> 6 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/pytest tests/ -q` -> 53 passed
- Baseline before: 50 passing tests
- Baseline after: 53 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: `apply_decision_memory` leaves base scoring deterministic, applies recent reject penalties, and attaches prior revisit rationale when revisit age is eligible.

## 2026-05-19 - T17: Weekly Pipeline Command

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/pipeline.py`, `demand_mvp_radar/cli.py`, `tests/test_weekly_pipeline.py`, `tests/fixtures/weekly_run/weekly_run.json`
- Tests: `.venv/bin/pytest tests/test_weekly_pipeline.py -q` -> 3 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/ scripts/` -> pass; `.venv/bin/pytest tests/ -q` -> 56 passed
- Baseline before: 53 passing tests
- Baseline after: 56 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: `demand-mvp-radar run --fixture tests/fixtures/weekly_run` is fixture-backed, budget-gated, idempotent by evidence fingerprint, and writes SQLite run metadata plus Markdown report output.

## 2026-05-19 - T18: Evaluation Baseline and Health Output

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/cli.py`, `scripts/eval_tools.py`, `tests/test_health.py`, `tests/eval/test_retrieval_eval.py`, `tests/eval/test_tool_eval.py`, `tests/fixtures/tool_eval.json`, `docs/retrieval_eval.md`, `docs/tool_eval.md`, `docs/CODEX_PROMPT.md`
- Tests: `.venv/bin/python scripts/eval_retrieval.py --fixture tests/fixtures/retrieval_queries.json` -> hit@3 1.0, citation_precision 1.0, no_answer_accuracy 1.0, answer_faithfulness 1.0; `.venv/bin/python scripts/eval_tools.py --fixture tests/fixtures/tool_eval.json` -> all tool metrics 1.0; `.venv/bin/pytest tests/ -q` -> 59 passed
- Baseline before: 56 passing tests
- Baseline after: 59 passing tests
- Decisions/evidence updated: `docs/retrieval_eval.md`, `docs/tool_eval.md`, `docs/tasks.md`, `docs/CODEX_PROMPT.md`, `docs/audit/REVIEW_REPORT.md`
- Notes for next agent: T18 finalized active RAG and Tool-Use eval baselines and expanded health output for local runtime status.

## 2026-05-20 - T19: Operator Workflow Contract

- Agent: Codex
- Result: DONE
- Files changed: `docs/OPERATOR_WORKFLOW.md`, `tests/test_docs_contracts.py`
- Tests: `.venv/bin/pytest tests/test_docs_contracts.py -q` -> 3 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/` -> pass; `.venv/bin/pytest tests/ -q` -> 62 passed
- Baseline before: 59 passing tests
- Baseline after: 62 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: T20 can use `docs/OPERATOR_WORKFLOW.md` and `docs/SOURCE_CATALOG.md` to align source catalog defaults with the personal weekly decision loop. No source adapters were implemented in T19.

## 2026-05-20 - T20: Source Catalog Config Model

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/config.py`, `demand_mvp_radar/models.py`, `tests/test_source_catalog.py`
- Tests: `.venv/bin/pytest tests/test_source_catalog.py -q` -> 3 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/` -> pass; `.venv/bin/pytest tests/ -q` -> 65 passed
- Baseline before: 62 passing tests
- Baseline after: 65 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: `Settings.source_catalog` now exposes disabled placeholders for GitHub, HN, Stack Exchange, Product Hunt, SERP, YouTube, app stores, G2, and Reddit. Enabled paid or credentialed API sources require approval.

## 2026-05-20 - T21: Telegram Research Agent Bridge

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/sources/telegram_research_agent.py`, `tests/test_telegram_research_bridge.py`, `tests/fixtures/telegram_research_agent_export.json`
- Tests: `.venv/bin/pytest tests/test_telegram_research_bridge.py -q` -> 3 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/` -> pass; `.venv/bin/pytest tests/ -q` -> 68 passed
- Baseline before: 65 passing tests
- Baseline after: 68 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: The bridge reads sanitized JSON fixture exports only; it does not read the external repository or private runtime data. Imported evidence uses source type `telegram_research_agent` and stable source fingerprints.

## 2026-05-20 - T22: Operator Notes Source

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/sources/operator_notes.py`, `demand_mvp_radar/scoring.py`, `tests/test_operator_notes.py`, `tests/fixtures/operator_notes/private_signal.md`
- Tests: `.venv/bin/pytest tests/test_operator_notes.py -q` -> 3 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/` -> pass; `.venv/bin/pytest tests/ -q` -> 71 passed
- Baseline before: 68 passing tests
- Baseline after: 71 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: Operator note evidence uses source type `operator_note` and redacted source reference `operator_note:redacted`; scoring adds a threshold reason when all candidate support comes from operator notes.

## 2026-05-20 - T23: Own GitHub Repository Source

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/sources/github_repo.py`, `demand_mvp_radar/tools/schemas.py`, `docs/ARCHITECTURE.md`, `docs/tool_eval.md`, `docs/CODEX_PROMPT.md`, `tests/test_github_source.py`, `tests/test_tools.py`, `tests/fixtures/github_repo/`
- Tests: `.venv/bin/pytest tests/test_github_source.py tests/test_tools.py -q` -> 7 passed; `.venv/bin/pytest tests/ -q` -> 74 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/` -> pass
- Baseline before: 71 passing tests
- Baseline after: 74 passing tests
- Decisions/evidence updated: `docs/tool_eval.md`, `docs/tasks.md`, `docs/CODEX_PROMPT.md`, `docs/ARCHITECTURE.md`
- Notes for next agent: `read_github_repo_snapshot` is local-snapshot only. Audit fields include run_id, repository_id_hash, source_count, and error_count; local repository paths and repository identifiers are excluded from audit fields.

## 2026-05-20 - T24: Live Evidence Import Command

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/cli.py`, `demand_mvp_radar/pipeline.py`, `tests/test_import_sources_command.py`, `tests/fixtures/source_mix/`
- Tests: `.venv/bin/pytest tests/test_import_sources_command.py -q` -> 3 passed; `.venv/bin/pytest tests/ -q` -> 77 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/` -> pass; `.venv/bin/ruff format --check demand_mvp_radar/ tests/` -> pass
- Baseline before: 74 passing tests
- Baseline after: 77 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: `import-sources` is intentionally separate from weekly report generation. It imports owned-source fixtures, builds retrieval chunks with the configured corpus version, and records skipped disabled sources in `runs.source_counts`.

## 2026-05-20 - T25: Source Trust and Freshness Scoring

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/retrieval/query.py`, `demand_mvp_radar/scoring.py`, `tests/test_source_trust.py`, `docs/retrieval_eval.md`
- Tests: `.venv/bin/pytest tests/test_source_trust.py -q` -> 3 passed; `.venv/bin/pytest tests/ -q` -> 80 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/` -> pass
- Baseline before: 77 passing tests
- Baseline after: 80 passing tests
- Decisions/evidence updated: `docs/retrieval_eval.md`, `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: Retrieval now applies default source trust downranking and accepts optional source-specific freshness windows/trust overrides. Scoring uses default trust-adjusted demand, default source-type caps, and non-build threshold reasons when support is only low-trust or stale.

## 2026-05-20 - T26: Live-Like Retrieval Evaluation Fixtures

- Agent: Codex
- Result: DONE
- Files changed: `scripts/eval_retrieval.py`, `tests/fixtures/retrieval_live_like_corpus.json`, `tests/fixtures/retrieval_live_like_queries.json`, `tests/eval/test_retrieval_eval.py`, `docs/retrieval_eval.md`
- Tests: `.venv/bin/python scripts/eval_retrieval.py --fixture tests/fixtures/retrieval_live_like_queries.json` -> all retrieval metrics 1.00; `.venv/bin/pytest tests/eval/test_retrieval_eval.py -q` -> 6 passed; `.venv/bin/pytest tests/ -q` -> 83 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass
- Baseline before: 80 passing tests
- Baseline after: 83 passing tests
- Decisions/evidence updated: `docs/retrieval_eval.md`, `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: Retrieval evaluation supports query fixtures that reference a separate corpus fixture. The T26 live-like corpus covers Telegram Research Agent, operator notes, GitHub repository snapshots, SERP, Hacker News, reviews, news, and stale forum evidence, with extended freshness and source-diversity metrics.

## 2026-05-20 - T27: Evidence Delta Report

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/reports/evidence_delta.py`, `demand_mvp_radar/pipeline.py`, `tests/test_evidence_delta.py`
- Tests: `.venv/bin/pytest tests/test_evidence_delta.py tests/test_import_sources_command.py -q` -> 6 passed; `.venv/bin/pytest tests/ -q` -> 86 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass
- Baseline before: 83 passing tests
- Baseline after: 86 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: `import-sources` now returns an `EvidenceDeltaReport`. It summarizes new, duplicate, stale, quarantined, and skipped counts by source type, groups new/changed evidence into changed clusters, and redacts private source references.

## 2026-05-20 - T28: Opportunity Dossier Schema

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/models.py`, `demand_mvp_radar/dossiers.py`, `tests/test_dossiers.py`
- Tests: `.venv/bin/pytest tests/test_dossiers.py -q` -> 3 passed; `.venv/bin/pytest tests/ -q` -> 89 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass
- Baseline before: 86 passing tests
- Baseline after: 89 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: `OpportunityDossier` requires decision-grade fields, known citation references for cited claims, explicit inference markers for uncited claims, confidence, and `why_this_may_be_wrong` countercase entries.

## 2026-05-20 - T29: Dossier Renderer

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/reports/dossier_markdown.py`, `demand_mvp_radar/reports/dossier_html.py`, `tests/test_dossier_renderer.py`
- Tests: `.venv/bin/pytest tests/test_dossier_renderer.py tests/test_dossiers.py -q` -> 6 passed; `.venv/bin/pytest tests/ -q` -> 92 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass
- Baseline before: 89 passing tests
- Baseline after: 92 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: Dossier Markdown rendering uses a stable section order, includes source provenance rows for every evidence item, marks uncited inference claims, and handles `insufficient_evidence` without presenting it as a build recommendation.

## 2026-05-20 - T30: Missing Evidence Section

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/retrieval/query.py`, `demand_mvp_radar/dossiers.py`, `tests/test_missing_evidence.py`, `tests/eval/test_retrieval_eval.py`, `docs/retrieval_eval.md`
- Tests: `.venv/bin/pytest tests/test_missing_evidence.py tests/eval/test_retrieval_eval.py -q` -> 9 passed; `.venv/bin/pytest tests/ -q` -> 95 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass
- Baseline before: 92 passing tests
- Baseline after: 95 passing tests
- Decisions/evidence updated: `docs/retrieval_eval.md`, `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: Missing-evidence analysis maps retrieval missing reasons and dossier fields into deterministic gap types with collection targets. It suggests source types and queries without claiming missing facts are true.

## 2026-05-20 - T31: Review Command

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/cli.py`, `demand_mvp_radar/decisions.py`, `demand_mvp_radar/models.py`, `demand_mvp_radar/storage/migrations.py`, `demand_mvp_radar/storage/repositories.py`, `tests/test_review_command.py`
- Tests: `.venv/bin/pytest tests/test_review_command.py tests/test_decisions.py tests/test_decision_memory.py -q` -> 9 passed; `.venv/bin/pytest tests/ -q` -> 98 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass
- Baseline before: 95 passing tests
- Baseline after: 98 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`, `docs/ARCHITECTURE.md`
- Notes for next agent: `demand-mvp-radar review` records append-only operator decisions with dossier paths. `build` requires an explicit reason, and `needs_more_evidence` stores requested evidence gaps for later experiment or source-collection workflows.

## 2026-05-20 - T32: MVP Experiment Pack Model

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/experiments.py`, `demand_mvp_radar/models.py`, `tests/test_experiments.py`
- Tests: `.venv/bin/pytest tests/test_experiments.py tests/test_dossiers.py tests/test_decisions.py -q` -> 9 passed; `.venv/bin/pytest tests/ -q` -> 101 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass
- Baseline before: 98 passing tests
- Baseline after: 101 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: Experiment packs require all validation fields, exactly ten discovery targets, a 7-14 day timebox, and a current human `build` or `revisit` decision. Generated packs inherit source dossier citations and risk flags.

## 2026-05-20 - T33: Experiment Renderer

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/reports/experiment_markdown.py`, `tests/test_experiment_renderer.py`
- Tests: `.venv/bin/pytest tests/test_experiment_renderer.py tests/test_experiments.py tests/test_reports.py -q` -> 9 passed; `.venv/bin/pytest tests/ -q` -> 104 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass
- Baseline before: 101 passing tests
- Baseline after: 104 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: Experiment Markdown includes scope, target user, validation method, first 10 targets, thresholds, timebox, source citations, and risk flags. Artifact writes are keyed by opportunity ID and run ID; a different run ID creates a separate file, and the same run ID overwrites atomically.

## 2026-05-20 - T34: Experiment Outcome Recording

- Agent: Codex
- Result: DONE
- Files changed: `demand_mvp_radar/experiments.py`, `demand_mvp_radar/decisions.py`, `demand_mvp_radar/scoring.py`, `demand_mvp_radar/models.py`, `tests/test_experiment_outcomes.py`
- Tests: `.venv/bin/pytest tests/test_experiment_outcomes.py tests/test_scoring.py tests/test_decision_memory.py -q` -> 9 passed; `.venv/bin/pytest tests/ -q` -> 107 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass
- Baseline before: 104 passing tests
- Baseline after: 107 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: Experiment outcomes map to decision-memory values deterministically. `killed` outcomes suppress matching opportunities until newer evidence is present; `validated` outcomes boost the confidence component through `ScoringConfig.experiment_validation_confidence_bonus`.

## 2026-05-20 - T35: Operator Runbook

- Agent: Codex
- Result: DONE
- Files changed: `docs/OPERATOR_RUNBOOK.md`, `tests/test_docs_contracts.py`
- Tests: `.venv/bin/pytest tests/test_docs_contracts.py -q` -> 6 passed; `.venv/bin/pytest tests/ -q` -> 110 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass
- Baseline before: 107 passing tests
- Baseline after: 110 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: The runbook documents weekly operation, review, source failure handling, health checks, budget recovery, generated artifacts, local privacy boundaries, backup targets, and failed-run recovery.

## 2026-05-20 - T36: Scheduled Run Support

- Agent: Codex
- Result: DONE
- Files changed: `deploy/demand-mvp-radar.service`, `deploy/demand-mvp-radar.timer`, `demand_mvp_radar/cli.py`, `tests/test_scheduled_run.py`, `docs/OPERATOR_RUNBOOK.md`
- Tests: `.venv/bin/pytest tests/test_scheduled_run.py tests/test_health.py tests/test_smoke.py -q` -> 9 passed; `.venv/bin/pytest tests/ -q` -> 113 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass
- Baseline before: 110 passing tests
- Baseline after: 113 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: The systemd service uses local `DMR_DATA_DIR`, `DMR_REPORT_DIR`, and `DMR_WEEKLY_FIXTURE` values, writes logs under `$DMR_DATA_DIR/logs`, and uses `scheduled-YYYY-MM-DD` run IDs. Health JSON now includes `last_scheduled_run` when a scheduled run exists.

## 2026-05-20 - T37: Backup and Recovery Guide

- Agent: Codex
- Result: DONE
- Files changed: `docs/BACKUP_RECOVERY.md`, `tests/test_docs_contracts.py`
- Tests: `.venv/bin/pytest tests/test_docs_contracts.py -q` -> 9 passed; `.venv/bin/pytest tests/ -q` -> 116 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass
- Baseline before: 113 passing tests
- Baseline after: 116 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: Backup/recovery guidance covers SQLite files and sidecars, retrieval indexes, raw snapshots, private exports, operator notes, generated reports, restore verification commands, git-ignored private artifacts, and failed-run recovery.

## 2026-05-20 - T38: Four-Run Readiness Review

- Agent: Codex
- Result: DONE
- Files changed: `docs/audit/PRODUCTION_READINESS_REVIEW.md`, `tests/test_docs_contracts.py`
- Tests: `.venv/bin/pytest tests/test_docs_contracts.py -q` -> 12 passed; `.venv/bin/pytest tests/ -q` -> 119 passed; `.venv/bin/ruff check demand_mvp_radar/ tests/ scripts/` -> pass
- Baseline before: 116 passing tests
- Baseline after: 119 passing tests
- Decisions/evidence updated: `docs/tasks.md`, `docs/CODEX_PROMPT.md`
- Notes for next agent: Production readiness is explicitly `NOT READY` until four weekly local runs prove repeated personal value. Private beta and SaaS/hosted work remain blocked by the readiness review.
