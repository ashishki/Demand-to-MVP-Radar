# CODEX_PROMPT.md

Version: 2.4
Date: 2026-05-19
Phase: 5

This file is the session handoff and state authority for Codex implementation roles.

---

## Execution Model

- Active executor: current Codex session only.
- Claude Code layer: not used.
- Nested Codex subprocesses: forbidden. Do not call `codex exec` from inside Codex.
- Orchestration, implementation, review, consolidation, and doc updates are performed sequentially in the same Codex session using local tools.
- Loop mode: nonstop across phase boundaries. Finish phase-boundary review, archive, doc update, and report, then immediately continue to the next task unless an explicit blocker, P0, provider/rate-limit failure, project completion, or human approval boundary requires a stop.

---

## Current State

- Phase: 5
- Baseline: 59 passing tests
- Ruff: configured; `ruff check demand_mvp_radar/ tests/` and `ruff format --check demand_mvp_radar/ tests/` pass locally
- Last CI: workflow configured; remote run not yet observed
- Last updated: 2026-05-19
- Session tokens (approx): not yet tracked
- Cumulative phase tokens (approx): not yet tracked

---

## Continuity Pointers

- Decision log: `docs/DECISION_LOG.md`
- Implementation journal: `docs/IMPLEMENTATION_JOURNAL.md`
- Evidence index: `docs/EVIDENCE_INDEX.md`
- Implementation reference map: `docs/IMPLEMENTATION_REFERENCE_MAP.md`
- Retrieval evaluation: `docs/retrieval_eval.md`
- Tool-use evaluation: `docs/tool_eval.md`
- Task-scoped context: read `Context-Refs` in `docs/tasks.md` before broad searching.

---

## Next Task

none — T01 through T18 complete

Before implementation, the orchestrator should hand Codex a narrow task digest inline:

- assignment and acceptance criteria
- file scope
- applicable contract rules only
- dependency facts from prior tasks
- immediate pipeline or flow if one matters

Only send Codex to full documents when the task is architecture-shaping, security-sensitive, ambiguous, changes retrieval/tool semantics, or is marked `Execution-Mode: heavy`.

---

## Fix Queue

empty

---

## Open Findings

none

---

## Completed Tasks

- T01: Project Skeleton — DONE on 2026-05-19. Baseline moved from 0 passing tests (pre-implementation; pytest unavailable before bootstrap) to 3 passing tests. Light review passed.
- T02: CI Setup — DONE on 2026-05-19. Baseline moved from 3 to 6 passing tests. Ruff check and ruff format check pass locally. Light review passed.
- T03: First Smoke Tests — DONE on 2026-05-19. Baseline moved from 6 to 9 passing tests. Health JSON and default config smoke tests pass. Light review passed.
- T04: Configuration and Run Manifest — DONE on 2026-05-19. Baseline moved from 9 to 12 passing tests. Pydantic settings, env overrides, validation errors, and run manifest serialization pass. Light review passed.
- T05: Domain Models and SQLite Storage — DONE on 2026-05-19. Baseline moved from 12 to 15 passing tests. SQLite schema, idempotent evidence writes, and append-only decisions pass. Light review passed.
- T06: Tool Schema and Audit Layer — DONE on 2026-05-19. Baseline moved from 15 to 19 passing tests. Tool schema catalog, pre-execution validation, human approval boundary, audit persistence, and Tool-Use evaluation pass. Deep review Cycle 2 passed with Stop-Ship: No.
- T07: Source Adapter Interfaces and Telegram Import — DONE on 2026-05-19. Baseline moved from 19 to 22 passing tests. Telegram fixture import, quarantine behavior, and stable content hash pass. Light review passed.
- T08: URL and Snapshot Source Tools — DONE on 2026-05-19. Baseline moved from 22 to 27 passing tests. Mocked URL snapshot provenance, ToolExecutor audit fields, timeout retry, SERP fixture import, store metadata import, and Tool-Use evaluation pass. Light review passed.
- T09: Retrieval Ingestion Pipeline — DONE on 2026-05-19. Baseline moved from 27 to 31 passing tests. Retrieval chunks, deterministic local embeddings, SQLite index writes, corpus/schema manifest metadata, ingestion/query separation, and RAG ingestion evaluation pass. Deep review Cycle 4 passed with Stop-Ship: No.
- T10: Query-Time Retrieval and Insufficient Evidence — DONE on 2026-05-19. Baseline moved from 31 to 35 passing tests. Query-time retrieval returns cited evidence packets, enforces minimum independent source support, returns `insufficient_evidence` with reasons on weak support, and records RAG query metrics. Deep review Cycle 5 passed with Stop-Ship: No.
- T11: Deduplication and Opportunity Clustering — DONE on 2026-05-19. Baseline moved from 35 to 38 passing tests. Deterministic clustering groups near-duplicate evidence, splits broad topics by target audience, and returns stable opportunity candidates with source evidence IDs. Phase 3 deep review Cycle 6 passed with Stop-Ship: No.
- T12: Deterministic Scoring and Recommendations — DONE on 2026-05-19. Baseline moved from 38 to 41 passing tests. Deterministic scoring returns required score components, stable totals/recommendations, confidence bands, and threshold reasons for low evidence. Light review passed.
- T13: LLM Extraction Adapter — DONE on 2026-05-19. Baseline moved from 41 to 44 passing tests. Fake-provider extraction validates required structured fields, rejects malformed provider output without returning extraction data, and skips provider calls on `insufficient_evidence`. Tool-Use evaluation row recorded. Light review passed.
- T14: Brief Synthesis and Markdown Reports — DONE on 2026-05-19. Baseline moved from 44 to 47 passing tests. Markdown reports include the configured top five scored opportunities, required recommendation/evidence/score/risk/rationale fields, and atomic report writes. Phase 4 deep review Cycle 7 passed with Stop-Ship: No.
- T15: Operator Decision Memory — DONE on 2026-05-19. Baseline moved from 47 to 50 passing tests. Operator decisions record reason, actor, created_at, source report path, append without overwrite, and support full/current history lookup. Light review passed.
- T16: Rejected-Idea Suppression and Revisit Logic — DONE on 2026-05-19. Baseline moved from 50 to 53 passing tests. Recent rejects lower score/rank with suppression reasons; eligible revisit decisions preserve prior rationale without lowering score; suppression is deterministic. Light review passed.
- T17: Weekly Pipeline Command — DONE on 2026-05-19. Baseline moved from 53 to 56 passing tests. `run --fixture` orchestrates fixture evidence through storage, retrieval ingestion, clustering, scoring, Markdown report generation, run metadata, budget checks, and idempotent re-runs. Light review passed.
- T18: Evaluation Baseline and Health Output — DONE on 2026-05-19. Baseline moved from 56 to 59 passing tests. Health JSON exposes database, report directory, corpus version, index age, max index age, and configured source count; final RAG and Tool-Use baselines are recorded. Deep review Cycle 8 passed with Stop-Ship: No.

---

## Phase History

- Phase 1 Foundation — completed 2026-05-19. Built package skeleton, CI, smoke tests, health output, typed configuration, and run manifest. Deep review Cycle 1 passed with Stop-Ship: No, P0: 0, P1: 0, P2: 0.
- Phase 2 Evidence Ingestion and Storage — completed 2026-05-19. Built SQLite storage, evidence/source models, Tool-Use schema/audit layer, Telegram import, URL/SERP/store source tools, and Tool-Use evaluation rows. Deep review Cycle 3 passed with Stop-Ship: No, P0: 0, P1: 0, P2: 0.
- Phase 3 Retrieval and Candidate Formation — completed 2026-05-19. Built text-only retrieval ingestion, query-time evidence packets, insufficient-evidence gating, RAG evaluation baselines, and deterministic opportunity clustering. Deep review Cycle 6 passed with Stop-Ship: No, P0: 0, P1: 0, P2: 0.
- Phase 4 Scoring and Brief Generation — completed 2026-05-19. Built deterministic scoring, fake-provider LLM extraction validation, Tool-Use extraction evaluation, Markdown report rendering, and atomic report writes. Deep review Cycle 7 passed with Stop-Ship: No, P0: 0, P1: 0, P2: 0.
- Phase 5 Decision Memory and Weekly Run — completed 2026-05-19. Built operator decision memory, rejected-idea suppression, weekly run command, final health output, and final RAG/Tool-Use baselines. Deep review Cycle 9 passed with Stop-Ship: No, P0: 0, P1: 0, P2: 0.

---

## Summary State

Bootstrap package generated on 2026-05-19. T01 created the minimal Python package skeleton, editable install metadata, CLI help entrypoint, shared config/observability stubs, package directories including retrieval and tools namespaces, and smoke tests. T02 configured GitHub Actions, dev dependencies, and ruff checks. T03 added health JSON and default configuration smoke coverage. T04 added Pydantic settings and run manifest models. T05 added domain records plus SQLite schema/repositories for evidence and decisions. T06 added the v1 Tool-Use schema catalog, executor validation/permission boundary, audit persistence, and Tool-Use baseline evaluation. T07 added source adapter contracts and Telegram export normalization with quarantine handling. T08 added bounded source tools for mocked URL snapshots, SERP snapshots, and store metadata fixtures. T09 added text-only retrieval ingestion, chunk metadata preservation, deterministic local embeddings, SQLite index writes, and RAG ingestion evaluation. T10 added query-time retrieval, cited evidence packet assembly, metadata/freshness/source-link filtering, minimum independent source gating, and the required `insufficient_evidence` path. T11 added deterministic opportunity clustering with stable candidate IDs, normalized pain/audience/workflow/channel fields, and source evidence IDs. T12 added deterministic score components, recommendations, confidence bands, and threshold reasons. T13 added fake-provider LLM extraction with schema validation and skip-on-insufficient-evidence behavior. T14 added Markdown report rendering and atomic report writes. T15 added append-only operator decision recording and history lookup. T16 added rejected-idea suppression and revisit rationale propagation. T17 added the fixture-based weekly run command and budget guard. Dream Motif Interpreter is available as a RAG implementation pattern reference through `docs/IMPLEMENTATION_REFERENCE_MAP.md`. The active workflow is Codex-only and nonstop across phases: no Claude Code layer, no nested `codex exec` calls, and no pause between phases unless an explicit stop condition applies.

---

## Profile State: RAG

- RAG Status: ON
- Active corpora: local single-operator text evidence corpus
- Retrieval baseline: T09 ingestion baseline established for corpus-t09-v1 (chunk_count=3, index_schema_version=retrieval-index-v1); T10 query baseline established for corpus-t10-v1 (hit@3=1.00, citation_precision=1.00, no_answer_accuracy=1.00, answer_faithfulness=1.00)
- Open retrieval findings: none
- Index schema version: retrieval-index-v1
- Pending reindex actions: none
- Retrieval-related next tasks: T18
- Retrieval-driven tasks: none

---

## Tool-Use State

- Tool-Use Profile: ON
- Registered tool schemas: v1 catalog implemented in T06 for read_telegram_evidence, fetch_url_snapshot, read_serp_snapshot, read_store_metadata, retrieve_evidence, write_report, and record_operator_decision
- LLM provider boundary: fake-provider extraction adapter implemented in T13 with required-field validation and malformed-output rejection.
- Unsafe-action guardrails: v1 has no destructive external tools; credentialed sources, public publishing, outreach, repository creation, scoring-weight changes, and deletion require human approval.
- Open tool findings: none

---

## Agentic State

- Agentic Profile: OFF
- Active agent roles: n/a
- Loop termination contract version: n/a
- Cross-iteration state mechanism: n/a
- Open agent findings: none

---

## Planning State

- Planning Profile: OFF
- Plan schema version: n/a
- Plan validation method: n/a
- Open plan findings: none

---

## Compliance State

- Compliance Status: OFF
- Active frameworks: n/a
- Controls implemented: n/a
- Controls partial: n/a
- Controls not started: n/a
- Evidence artifact: n/a
- Open compliance findings: none

---

## NFR Baseline

- API p99 latency: not yet measured
- Error rate: not yet measured
- Throughput: not yet measured
- Last measured: n/a
- NFR regression open: No

---

## Evaluation State

### Last Evaluation

- Profile: Tool-Use
- Task: T18
- Date: 2026-05-19
- Eval Source: `python scripts/eval_tools.py --fixture tests/fixtures/tool_eval.json, run 2026-05-19`
- Metric(s): schema_validation_pass_rate, permission_check_pass_rate, audit_field_completeness, retry_policy_pass_rate
- Score: 1.00, 1.00, 1.00, 1.00
- Baseline: finalized by T18 for tool-eval-v1
- Delta: n/a
- Regression: No

### Regression Thresholds

- Retrieval hit@3 drop greater than 15 percent vs baseline: P0
- Retrieval hit@3 drop greater than 5 percent vs baseline: P1
- Citation precision drop greater than 10 percent vs baseline: P1
- No-answer accuracy below 0.90 after baseline: P1
- Tool schema validation pass rate below 1.00 after baseline: P1
- Tool audit field completeness below 1.00 after baseline: P1

### Open Evaluation Issues

none

### Evaluation History

- 2026-05-19 — T06 Tool-Use baseline: schema validation 1.00, permission checks 1.00, audit field completeness 1.00, retry policy n/a. Eval Source: `.venv/bin/pytest tests/test_tools.py -q, run 2026-05-19`.
- 2026-05-19 — T08 Tool-Use source-tool evaluation: schema validation 1.00, permission checks n/a, audit field completeness 1.00, retry policy 1.00. Eval Source: `.venv/bin/pytest tests/test_source_tools.py -q, run 2026-05-19`.
- 2026-05-19 — T09 RAG ingestion baseline: corpus_version corpus-t09-v1, chunk_count 3, index_schema_version retrieval-index-v1, embedding_model local-hash-embedding-v1. Eval Source: `python scripts/eval_retrieval.py --fixture tests/fixtures/retrieval_corpus.json, run 2026-05-19`.
- 2026-05-19 — T10 RAG query baseline: corpus_version corpus-t10-v1, hit@3 1.00, citation_precision 1.00, no_answer_accuracy 1.00, answer_faithfulness 1.00. Eval Source: `python scripts/eval_retrieval.py --fixture tests/fixtures/retrieval_queries.json, run 2026-05-19`.
- 2026-05-19 — T13 Tool-Use LLM extraction boundary: schema_validation_pass_rate 1.00, permission checks n/a, audit field completeness n/a, retry policy n/a. Eval Source: `.venv/bin/pytest tests/test_llm_extraction.py -q, run 2026-05-19`.
- 2026-05-19 — T18 final RAG and Tool-Use baselines: RAG hit@3 1.00, citation_precision 1.00, no_answer_accuracy 1.00, answer_faithfulness 1.00; Tool-Use schema_validation_pass_rate 1.00, permission_check_pass_rate 1.00, audit_field_completeness 1.00, retry_policy_pass_rate 1.00. Eval Sources: `python scripts/eval_retrieval.py --fixture tests/fixtures/retrieval_queries.json, run 2026-05-19`; `python scripts/eval_tools.py --fixture tests/fixtures/tool_eval.json, run 2026-05-19`.

---

## Instructions for Codex

1. Read `docs/IMPLEMENTATION_CONTRACT.md` before starting any task.
2. Read the full task definition in `docs/tasks.md` before writing code.
3. Read all Depends-On tasks to understand interface contracts.
4. Read task `Context-Refs` and relevant continuity artifacts when the task depends on prior decisions, proof, retrieval semantics, tool semantics, or findings.
5. Execute work directly in the current Codex session; do not call `codex exec` or spawn a nested Codex process.
6. Run `pytest -q` to capture the current baseline before making changes.
7. Run `ruff check` before implementation once ruff is configured. If ruff is not configured yet, implement T01/T02 first and record that state.
8. Write tests before or alongside implementation. Every acceptance criterion has a passing test.
9. Do not stop merely because a phase ended. Run the required phase-boundary gates and continue to the next task.
10. Update this file at every phase boundary and after capability evaluation tasks.
11. Commit with format `type(scope): description`; one logical change per commit.
12. When done, return `IMPLEMENTATION_RESULT: DONE` with baseline before and after, files changed, tests added, and AC status.
13. When blocked, return `IMPLEMENTATION_RESULT: BLOCKED` with the exact blocker and the smallest next action needed.

---

## Compaction Protocol

- Trigger compaction when Completed Tasks exceeds 20 entries or Phase History exceeds 5 phase summaries.
- Keep Summary State current before archiving older detail.
- Do not delete audit reports, ADRs, evaluation artifacts, or task definitions.
