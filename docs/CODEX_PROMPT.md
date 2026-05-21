# CODEX_PROMPT.md

Version: 2.35
Date: 2026-05-21
Phase: 11

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

- Phase: 11
- Baseline: 145 passing tests
- Ruff: configured; `ruff check demand_mvp_radar/ tests/ scripts/` passes locally. `ruff format --check demand_mvp_radar/ tests/ scripts/` currently reports pre-existing formatting drift in untouched code/test files and needs a separate formatting-only commit.
- Last CI: workflow configured; remote run not yet observed
- Last updated: 2026-05-21
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
- Personal-to-production roadmap: `docs/PERSONAL_TO_PRODUCTION_PLAN.md`
- Live source production roadmap: `docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md`
- Source strategy: `docs/SOURCE_CATALOG.md`
- AI development pack: `docs/AI_DEVELOPMENT_PACK.md`

---

## Next Task

T45: GitHub Public Search Connector

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

- T17: Weekly Pipeline Command — DONE on 2026-05-19. Baseline moved from 53 to 56 passing tests. `run --fixture` orchestrates fixture evidence through storage, retrieval ingestion, clustering, scoring, Markdown report generation, run metadata, budget checks, and idempotent re-runs. Light review passed.
- T18: Evaluation Baseline and Health Output — DONE on 2026-05-19. Baseline moved from 56 to 59 passing tests. Health JSON exposes database, report directory, corpus version, index age, max index age, and configured source count; final RAG and Tool-Use baselines are recorded. Deep review Cycle 8 passed with Stop-Ship: No.
- T19: Operator Workflow Contract — DONE on 2026-05-20. Baseline moved from 59 to 62 passing tests. Operator workflow contract defines weekly inputs, weekly outputs, the under-15-minute review target, decision taxonomy, adoption failure conditions, and privacy boundaries for Telegram exports, operator notes, and credentials. Light review passed.
- T20: Source Catalog Config Model — DONE on 2026-05-20. Baseline moved from 62 to 65 passing tests. Source catalog entries validate source type, priority, trust level, freshness window, access method, enabled state, and approval requirements; default settings include disabled placeholders for planned public, paid, and credentialed sources. Light review passed.
- T21: Telegram Research Agent Bridge — DONE on 2026-05-20. Baseline moved from 65 to 68 passing tests. Sanitized `telegram-research-agent` exports import as first-class evidence, repeated imports are idempotent by source fingerprint, and malformed/private rows are quarantined without blocking valid rows. Light review passed.
- T22: Operator Notes Source — DONE on 2026-05-20. Baseline moved from 68 to 71 passing tests. Markdown operator notes import as redacted local evidence, operator-note-only candidates cannot receive `build`, and private note paths are excluded from serialized evidence. Light review passed.
- T23: Own GitHub Repository Source — DONE on 2026-05-20. Baseline moved from 71 to 74 passing tests. Local repository snapshots import selected README, issue, TODO, and recent-change evidence, exclude private/generated paths, and audit `read_github_repo_snapshot` with repository_id_hash without leaking local paths. Tool-Use evaluation recorded. Light review passed.
- T24: Live Evidence Import Command — DONE on 2026-05-20. Baseline moved from 74 to 77 passing tests. `import-sources` imports Telegram bridge, operator notes, and GitHub source fixtures into storage, updates retrieval chunks and corpus version, records disabled sources in the run manifest, and does not generate reports. Light review passed.
- T25: Source Trust and Freshness Scoring — DONE on 2026-05-20. Baseline moved from 77 to 80 passing tests. Retrieval applies default source trust downranking plus optional source-specific freshness windows, scoring uses default trust-adjusted demand plus source-type caps, and low-trust or stale-only support cannot trigger `build`. RAG evaluation recorded. Deep review Cycle 11 passed with Stop-Ship: No.
- T26: Live-Like Retrieval Evaluation Fixtures — DONE on 2026-05-20. Baseline moved from 80 to 83 passing tests. Retrieval evaluation now supports separate live-like corpus/query fixtures, covers at least ten queries across seven source types, and reports freshness_compliance plus source_diversity alongside existing RAG metrics. Deep review Cycle 12 passed with Stop-Ship: No.
- T27: Evidence Delta Report — DONE on 2026-05-20. Baseline moved from 83 to 86 passing tests. Import runs now include an evidence delta report that summarizes new, duplicate, stale, quarantined, and skipped counts, lists changed clusters, and redacts private source references. Phase 7 deep review Cycle 13 passed with Stop-Ship: No.
- T28: Opportunity Dossier Schema — DONE on 2026-05-20. Baseline moved from 86 to 89 passing tests. Added decision-grade dossier models and a validation helper; claims must cite known evidence or be explicitly marked as inference, and dossiers include confidence plus countercase fields. Light review passed.
- T29: Dossier Renderer — DONE on 2026-05-20. Baseline moved from 89 to 92 passing tests. Added Markdown and HTML dossier renderers with stable decision sections, provenance-rich citation rows, inference markers, and explicit `insufficient_evidence` handling. Light review passed.
- T30: Missing Evidence Section — DONE on 2026-05-20. Baseline moved from 92 to 95 passing tests. Added deterministic missing-evidence analysis for absent independent sources, stale evidence, weak competitor proof, missing acquisition proof, and missing willingness-to-pay signal, plus retrieval eval no-answer history. Deep review Cycle 14 passed with Stop-Ship: No.
- T31: Review Command — DONE on 2026-05-20. Baseline moved from 95 to 98 passing tests. Added `review` CLI decision recording for generated dossiers, explicit build-reason rejection, `needs_more_evidence` support, and requested evidence gap persistence. Phase 8 deep review Cycle 15 passed with Stop-Ship: No.
- T32: MVP Experiment Pack Model — DONE on 2026-05-20. Baseline moved from 98 to 101 passing tests. Added experiment pack validation, human `build`/`revisit` decision gating, and dossier citation/risk inheritance. Light review passed.
- T33: Experiment Renderer — DONE on 2026-05-20. Baseline moved from 101 to 104 passing tests. Added actionable Markdown experiment rendering with citations, risk flags, threshold sections, and run-id keyed atomic artifact writes. Light review passed.
- T34: Experiment Outcome Recording — DONE on 2026-05-20. Baseline moved from 104 to 107 passing tests. Added typed experiment outcome records, outcome-to-decision mapping, killed-experiment suppression until newer evidence appears, and deterministic validated-experiment confidence boosts. Phase 9 deep review Cycle 16 passed with Stop-Ship: No.
- T35: Operator Runbook — DONE on 2026-05-20. Baseline moved from 107 to 110 passing tests. Added `docs/OPERATOR_RUNBOOK.md` with weekly run, review, source failure, health, budget, artifact, privacy, backup, and recovery guidance. Light review passed.
- T36: Scheduled Run Support — DONE on 2026-05-20. Baseline moved from 110 to 113 passing tests. Added user-level systemd service/timer templates, local scheduled-run logging paths, and `health --json` reporting for the latest `scheduled-...` run. Light review passed.
- T37: Backup and Recovery Guide — DONE on 2026-05-20. Baseline moved from 113 to 116 passing tests. Added `docs/BACKUP_RECOVERY.md` with backup targets, restore steps, verification commands, git-ignored private artifacts, and failed-run recovery checklist. Light review passed.
- T38: Four-Run Readiness Review — DONE on 2026-05-20. Baseline moved from 116 to 119 passing tests. Added `docs/audit/PRODUCTION_READINESS_REVIEW.md` with four-run evidence checklist, readiness verdict, operational metrics, and explicit private beta/SaaS gates. Phase 10 deep review Cycle 17 passed with Stop-Ship: No.
- Roadmap/task graph extension — DONE on 2026-05-20. Baseline moved from 122 to 125 passing tests. Added the live-source production roadmap into the authoritative task graph as T39-T57 and updated AI loop handoff docs so Phase 11 resumes with live source connector protocol work.
- T39: Live Source Connector Protocol — DONE on 2026-05-21. Baseline moved from 125 to 128 passing tests. Added shared live connector config/result/rate-limit contracts, optional live provenance fields on evidence records, and validation that live evidence carries source name, URL/locator, captured timestamp, content hash, source fingerprint, connector version, and run ID. Deep review passed with Stop-Ship: No.
- T40: Credential Resolver and Secret Redaction — DONE on 2026-05-21. Baseline moved from 128 to 131 passing tests. Added environment-name-only credential requirements, typed available/missing/invalid/not-required resolution, source-scoped credential disablement, secret-safe manifest/error/health serialization, and operator runbook guidance. Deep review passed with Stop-Ship: No.
- T41: collect-sources Command — DONE on 2026-05-21. Baseline moved from 131 to 134 passing tests. Added fixture-first live source collection command, retrieval ingestion without report generation, source-scoped failure isolation into run manifests and health output, and idempotent evidence/retrieval writes by source fingerprint. Deep review passed with Stop-Ship: No.
- T42: Hacker News Live Connector — DONE on 2026-05-21. Baseline moved from 134 to 138 passing tests. Added a fixture-first Hacker News connector for story/comment evidence, author hashing, source locators, cursor state, malformed-row quarantine, and `collect-sources` support for `source_type=hacker_news`. Deep review passed with Stop-Ship: No.
- T43: Stack Exchange Live Connector — DONE on 2026-05-21. Baseline moved from 138 to 141 passing tests. Added a fixture-first Stack Exchange connector for question/answer evidence, site/tag/score/accepted-answer metadata, configured site/tag validation, rate-limit backoff handling, and `collect-sources` support for `source_type=stack_exchange`. Deep review passed with Stop-Ship: No.
- T44: RSS Feed Connector — DONE on 2026-05-21. Baseline moved from 141 to 145 passing tests. Added a stdlib RSS/Atom fixture connector with feed and entry provenance, published/captured timestamps, cursor dedupe by source fingerprint, malformed-feed quarantine, and `collect-sources` support for `source_type=rss`. Deep review passed with Stop-Ship: No.

## Completed Tasks Archive

- T01-T04: Phase 1 Foundation — DONE on 2026-05-19. Baseline moved from 0 to 12 passing tests. Built package skeleton, CI, smoke tests, health output, typed configuration, and run manifest. Phase 1 deep review passed with Stop-Ship: No.
- T05-T08: Phase 2 Evidence Ingestion and Storage — DONE on 2026-05-19. Baseline moved from 12 to 27 passing tests. Built SQLite storage, evidence/source models, Tool-Use schema/audit layer, Telegram import, URL/SERP/store source tools, and Tool-Use evaluation rows. Phase 2 deep review passed with Stop-Ship: No.
- T09-T11: Phase 3 Retrieval and Candidate Formation — DONE on 2026-05-19. Baseline moved from 27 to 38 passing tests. Built text-only retrieval ingestion, query-time evidence packets, insufficient-evidence gating, RAG evaluation baselines, and deterministic opportunity clustering. Phase 3 deep review passed with Stop-Ship: No.
- T12-T14: Phase 4 Scoring and Brief Generation — DONE on 2026-05-19. Baseline moved from 38 to 47 passing tests. Built deterministic scoring, fake-provider LLM extraction validation, Markdown report rendering, and atomic report writes. Phase 4 deep review passed with Stop-Ship: No.
- T15-T16: Phase 5 Decision Memory — DONE on 2026-05-19. Baseline moved from 47 to 53 passing tests. Built append-only operator decision recording, history lookup, rejected-idea suppression, and revisit rationale propagation. Later Phase 5 work continues in active Completed Tasks above.

---

## Phase History

- Phase 5 Decision Memory and Weekly Run — completed 2026-05-19. Built operator decision memory, rejected-idea suppression, weekly run command, final health output, and final RAG/Tool-Use baselines. Deep review Cycle 9 passed with Stop-Ship: No, P0: 0, P1: 0, P2: 0.
- Phase 6 Personal Source Foundation — completed 2026-05-20. Built operator workflow contract, source catalog config, sanitized Telegram Research Agent bridge, redacted operator notes importer, local GitHub repository source, and `read_github_repo_snapshot` Tool-Use evaluation. Deep review Cycle 10 passed with Stop-Ship: No, P0: 0, P1: 0, P2: 0.
- Phase 7 Live Evidence Trust — completed 2026-05-20. Built `import-sources`, source trust/freshness retrieval and scoring controls, live-like retrieval evaluation fixtures, and evidence delta reporting. Deep review Cycle 13 passed with Stop-Ship: No, P0: 0, P1: 0, P2: 0.
- Phase 8 Decision-Grade Artifacts — completed 2026-05-20. Built dossier schemas, dossier renderers, missing-evidence analysis, and review-command decision recording. Deep review Cycle 15 passed with Stop-Ship: No, P0: 0, P1: 0, P2: 0.
- Phase 9 MVP Experiment Conversion — completed 2026-05-20. Built experiment pack validation, experiment rendering, and deterministic outcome feedback. Deep review Cycle 16 passed with Stop-Ship: No, P0: 0, P1: 0, P2: 0.
- Phase 10 Operator Production Readiness — completed 2026-05-20. Built operator runbook, scheduled local run support, backup/recovery guide, and four-run readiness gate. Deep review Cycle 17 passed with Stop-Ship: No, P0: 0, P1: 0, P2: 0.

## Phase History Archive

- Phase 1 Foundation — completed 2026-05-19. Built package skeleton, CI, smoke tests, health output, typed configuration, and run manifest. Deep review Cycle 1 passed with Stop-Ship: No, P0: 0, P1: 0, P2: 0.
- Phase 2 Evidence Ingestion and Storage — completed 2026-05-19. Built SQLite storage, evidence/source models, Tool-Use schema/audit layer, Telegram import, URL/SERP/store source tools, and Tool-Use evaluation rows. Deep review Cycle 3 passed with Stop-Ship: No, P0: 0, P1: 0, P2: 0.
- Phase 3 Retrieval and Candidate Formation — completed 2026-05-19. Built text-only retrieval ingestion, query-time evidence packets, insufficient-evidence gating, RAG evaluation baselines, and deterministic opportunity clustering. Deep review Cycle 6 passed with Stop-Ship: No, P0: 0, P1: 0, P2: 0.
- Phase 4 Scoring and Brief Generation — completed 2026-05-19. Built deterministic scoring, fake-provider LLM extraction validation, Tool-Use extraction evaluation, Markdown report rendering, and atomic report writes. Deep review Cycle 7 passed with Stop-Ship: No, P0: 0, P1: 0, P2: 0.

---

## Summary State

Bootstrap package generated on 2026-05-19. T01 created the minimal Python package skeleton, editable install metadata, CLI help entrypoint, shared config/observability stubs, package directories including retrieval and tools namespaces, and smoke tests. T02 configured GitHub Actions, dev dependencies, and ruff checks. T03 added health JSON and default configuration smoke coverage. T04 added Pydantic settings and run manifest models. T05 added domain records plus SQLite schema/repositories for evidence and decisions. T06 added the v1 Tool-Use schema catalog, executor validation/permission boundary, audit persistence, and Tool-Use baseline evaluation. T07 added source adapter contracts and Telegram export normalization with quarantine handling. T08 added bounded source tools for mocked URL snapshots, SERP snapshots, and store metadata fixtures. T09 added text-only retrieval ingestion, chunk metadata preservation, deterministic local embeddings, SQLite index writes, and RAG ingestion evaluation. T10 added query-time retrieval, cited evidence packet assembly, metadata/freshness/source-link filtering, minimum independent source gating, and the required `insufficient_evidence` path. T11 added deterministic opportunity clustering with stable candidate IDs, normalized pain/audience/workflow/channel fields, and source evidence IDs. T12 added deterministic score components, recommendations, confidence bands, and threshold reasons. T13 added fake-provider LLM extraction with schema validation and skip-on-insufficient-evidence behavior. T14 added Markdown report rendering and atomic report writes. T15 added append-only operator decision recording and history lookup. T16 added rejected-idea suppression and revisit rationale propagation. T17 added the fixture-based weekly run command and budget guard. T19 added the personal operator workflow contract for weekly inputs/outputs, decision taxonomy, adoption failure conditions, and privacy boundaries. T20 added typed source catalog entries and disabled default source placeholders with approval requirements for paid and credentialed sources. T21 added a sanitized `telegram-research-agent` bridge that writes evidence idempotently and quarantines malformed/private rows. T22 added a redacted operator notes importer and deterministic scoring guard so notes alone cannot justify `build`. T23 added a local GitHub repository source and `read_github_repo_snapshot` tool schema/audit path with Tool-Use evaluation. T24 added the `import-sources` command that stores owned-source evidence, updates retrieval chunks, records disabled sources, and skips report generation. T25 added default query-time source trust downranking, optional source-specific freshness controls, and default trust-adjusted scoring caps so stale or low-trust-only support cannot produce `build`. T26 added sanitized live-like retrieval fixtures and extended retrieval evaluation metrics for freshness compliance and source diversity. T27 added evidence delta reporting for source imports, including redacted changed-cluster summaries. T28 added decision-grade dossier models with citation/inference validation. T29 added stable Markdown/HTML dossier renderers. T30 added deterministic missing-evidence analysis and RAG no-answer eval history. T31 added local review-command decision recording from generated dossiers, including `needs_more_evidence` gaps. T32 added human-gated MVP experiment pack validation with dossier citation and risk inheritance. T33 added run-id keyed Markdown experiment rendering and atomic artifact writes. T34 added experiment outcome recording and deterministic scoring feedback for killed and validated experiments. T35 added the operator runbook for weekly operation, failures, health checks, privacy, and backup. T36 added user-level systemd scheduling templates and scheduled-run health reporting. T37 added the backup and recovery guide. T38 added the four-run production readiness review gate. Dream Motif Interpreter is available as a RAG implementation pattern reference through `docs/IMPLEMENTATION_REFERENCE_MAP.md`. The active workflow is Codex-only and nonstop across phases: no Claude Code layer, no nested `codex exec` calls, and no pause between phases unless an explicit stop condition applies.

After T38, `docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md` was promoted into the authoritative implementation queue as T39-T57 across Phase 11 through Phase 16. T39 added the shared live connector protocol. T40 added credential-safe resolution and redaction. T41 added `collect-sources`. T42 added the Hacker News live connector. T43 added the Stack Exchange live connector. T44 added RSS/Atom. The next loop starts at T45 with GitHub public search.

---

## Profile State: RAG

- RAG Status: ON
- Active corpora: local single-operator text evidence corpus
- Retrieval baseline: T09 ingestion baseline established for corpus-t09-v1 (chunk_count=3, index_schema_version=retrieval-index-v1); T10 query baseline established for corpus-t10-v1 (hit@3=1.00, citation_precision=1.00, no_answer_accuracy=1.00, answer_faithfulness=1.00); T25 trust/freshness slice established for corpus-t25-source-trust-v1 (hit@3=1.00, citation_precision=1.00, no_answer_accuracy=1.00, answer_faithfulness=1.00); T26 live-like slice established for corpus-t26-live-like-v1 (hit@3=1.00, citation_precision=1.00, no_answer_accuracy=1.00, answer_faithfulness=1.00, freshness_compliance=1.00, source_diversity=1.00)
- Open retrieval findings: none
- Index schema version: retrieval-index-v1
- Pending reindex actions: none
- Retrieval-related next tasks: T45-T47 GitHub public search, source health, and public-live retrieval evaluation
- Retrieval-driven tasks: Phase 11 live source connector foundation and Phase 12 source health/evaluation

---

## Tool-Use State

- Tool-Use Profile: ON
- Registered tool schemas: v1 catalog implemented in T06 for read_telegram_evidence, fetch_url_snapshot, read_serp_snapshot, read_store_metadata, retrieve_evidence, write_report, and record_operator_decision; T23 added read_github_repo_snapshot
- LLM provider boundary: fake-provider extraction adapter implemented in T13 with required-field validation and malformed-output rejection.
- Unsafe-action guardrails: v1 has no destructive external tools; credentialed sources, public publishing, outreach, repository creation, scoring-weight changes, deletion, live bot/channel collection, and hosted/SaaS work require human approval.
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

- Profile: RAG
- Task: T26
- Date: 2026-05-20
- Eval Source: `.venv/bin/python scripts/eval_retrieval.py --fixture tests/fixtures/retrieval_live_like_queries.json, run 2026-05-20`
- Metric(s): hit@3, citation_precision, no_answer_accuracy, answer_faithfulness, freshness_compliance, source_diversity
- Score: 1.00, 1.00, 1.00, 1.00, 1.00, 1.00
- Baseline: compared against T18 RAG query baseline
- Delta: 0.00
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
- 2026-05-20 — T23 Tool-Use GitHub repository source: schema_validation_pass_rate 1.00, permission_check_pass_rate 1.00, audit_field_completeness 1.00, retry policy n/a. Eval Source: `.venv/bin/pytest tests/test_github_source.py -q, run 2026-05-20`.
- 2026-05-20 — T25 RAG source trust and freshness slice: corpus_version corpus-t25-source-trust-v1, hit@3 1.00, citation_precision 1.00, no_answer_accuracy 1.00, answer_faithfulness 1.00. Eval Source: `.venv/bin/pytest tests/test_source_trust.py -q, run 2026-05-20`.
- 2026-05-20 — T26 RAG live-like retrieval slice: corpus_version corpus-t26-live-like-v1, hit@3 1.00, citation_precision 1.00, no_answer_accuracy 1.00, answer_faithfulness 1.00, freshness_compliance 1.00, source_diversity 1.00. Eval Source: `.venv/bin/python scripts/eval_retrieval.py --fixture tests/fixtures/retrieval_live_like_queries.json, run 2026-05-20`.

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
