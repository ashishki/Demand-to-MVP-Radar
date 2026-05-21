# Tasks - Demand-to-MVP Radar

Version: 1.0
Date: 2026-05-19

This file is the authoritative implementation task graph. Every acceptance criterion has one test reference.

---

## Phase 1 - Foundation

Business goal: create a runnable Python project with CI, smoke tests, configuration loading, and health output before implementing the research pipeline.

## T01: Project Skeleton

Owner:      codex
Phase:      1
Status:     [x]
Type:       none
Depends-On: none

Objective: |
  Create the Python package skeleton, packaging metadata, CLI entrypoint, configuration module, observability module, and empty package directories needed by later tasks.

Acceptance-Criteria:
  - id: AC-1
    description: "The package installs in editable mode and exposes a `demand-mvp-radar` console script that exits with code 0 for `--help`."
    test: "tests/test_smoke.py::test_cli_help_exits_zero"
  - id: AC-2
    description: "`demand_mvp_radar.__version__` is importable and equals the package version declared in `pyproject.toml`."
    test: "tests/test_smoke.py::test_package_version_matches_pyproject"
  - id: AC-3
    description: "The repository contains package directories for storage, sources, tools, retrieval, llm, reports, and tests import them without ImportError."
    test: "tests/test_smoke.py::test_core_packages_import"

Files:
  - pyproject.toml
  - requirements.txt
  - requirements-dev.txt
  - demand_mvp_radar/__init__.py
  - demand_mvp_radar/cli.py
  - demand_mvp_radar/config.py
  - demand_mvp_radar/observability.py
  - demand_mvp_radar/storage/__init__.py
  - demand_mvp_radar/sources/__init__.py
  - demand_mvp_radar/tools/__init__.py
  - demand_mvp_radar/retrieval/__init__.py
  - demand_mvp_radar/llm/__init__.py
  - demand_mvp_radar/reports/__init__.py
  - tests/test_smoke.py

Context-Refs:
  - docs/ARCHITECTURE.md#file-layout
  - docs/IMPLEMENTATION_CONTRACT.md#mandatory-pre-task-protocol

Notes: |
  Keep the skeleton minimal. Do not implement ingestion, retrieval, scoring, or LLM behavior in this task.

## T02: CI Setup

Owner:      codex
Phase:      1
Status:     [x]
Type:       none
Depends-On: T01

Objective: |
  Configure GitHub Actions and local development dependencies so every push and pull request to main runs ruff check, ruff format --check, and pytest.

Acceptance-Criteria:
  - id: AC-1
    description: ".github/workflows/ci.yml specifies Python 3.12 and contains separate steps for dependency install, ruff check, ruff format --check, and pytest."
    test: "tests/test_ci_config.py::test_ci_workflow_has_required_steps"
  - id: AC-2
    description: "`requirements-dev.txt` includes pytest and ruff, and `requirements.txt` is included by reference."
    test: "tests/test_ci_config.py::test_dev_requirements_include_test_and_lint_tools"
  - id: AC-3
    description: "The ruff configuration in `pyproject.toml` targets the `demand_mvp_radar` package and `tests` directory."
    test: "tests/test_ci_config.py::test_ruff_config_targets_project_paths"

Files:
  - .github/workflows/ci.yml
  - pyproject.toml
  - requirements-dev.txt
  - tests/test_ci_config.py

Context-Refs:
  - docs/ARCHITECTURE.md#tech-stack
  - docs/IMPLEMENTATION_CONTRACT.md#ci-gate

Notes: |
  CI must not contain unresolved template placeholders. Keep service containers disabled until a task introduces an external test dependency.

## T03: First Smoke Tests

Owner:      codex
Phase:      1
Status:     [x]
Type:       none
Depends-On: T01, T02

Objective: |
  Add the first runnable smoke tests for CLI help, health output, and configuration defaults, establishing the initial passing baseline.

Acceptance-Criteria:
  - id: AC-1
    description: "`pytest tests/ -q` runs the smoke test module and reports at least three passing tests."
    test: "tests/test_smoke.py::test_pytest_discovers_smoke_suite"
  - id: AC-2
    description: "`demand-mvp-radar health --json` prints JSON containing `status`, `database`, `report_dir`, and `configured_sources` keys."
    test: "tests/test_smoke.py::test_health_json_contains_required_keys"
  - id: AC-3
    description: "Default configuration uses a local data directory, a local report directory, and a max index age of 7 days when no env vars are set."
    test: "tests/test_config.py::test_default_configuration_values"

Files:
  - demand_mvp_radar/cli.py
  - demand_mvp_radar/config.py
  - tests/test_smoke.py
  - tests/test_config.py

Context-Refs:
  - docs/ARCHITECTURE.md#runtime-contract
  - docs/CODEX_PROMPT.md#next-task

Notes: |
  Use temporary directories in tests. Do not require network, database files outside tmp, or real provider credentials.

## T04: Configuration and Run Manifest

Owner:      codex
Phase:      1
Status:     [x]
Type:       none
Depends-On: T03

Objective: |
  Implement typed configuration loading and a run manifest model that records source status, corpus version, budget ceiling, start/end timestamps, and run outcome.

Acceptance-Criteria:
  - id: AC-1
    description: "Configuration values load from environment variables with `DMR_` prefix and override defaults for data dir, report dir, max weekly cost, timeout, and max index age."
    test: "tests/test_config.py::test_environment_overrides_defaults"
  - id: AC-2
    description: "A run manifest serializes to JSON with run_id, started_at, ended_at, status, source_counts, error_counts, duplicate_count, corpus_version, and max_weekly_llm_cost_usd."
    test: "tests/test_run_manifest.py::test_run_manifest_serializes_required_fields"
  - id: AC-3
    description: "Invalid negative budget or timeout values raise a validation error before any source adapter runs."
    test: "tests/test_config.py::test_invalid_runtime_values_raise_validation_error"

Files:
  - demand_mvp_radar/config.py
  - demand_mvp_radar/models.py
  - tests/test_config.py
  - tests/test_run_manifest.py

Context-Refs:
  - docs/ARCHITECTURE.md#runtime-contract

Notes: |
  Use Pydantic for structured config and manifests. Do not call external services.

---

## Phase 2 - Evidence Ingestion and Storage

Business goal: ingest source evidence into durable, idempotent local storage with provenance and audit fields.

## T05: Domain Models and SQLite Storage

Owner:      codex
Phase:      2
Status:     [x]
Type:       none
Depends-On: T04

Objective: |
  Implement evidence, opportunity, score, brief, decision, and audit event models plus a SQLite storage layer with idempotent writes.

Acceptance-Criteria:
  - id: AC-1
    description: "The SQLite schema creates tables for runs, evidence, opportunities, scores, briefs, decisions, tool_audit_events, and retrieval_chunks."
    test: "tests/test_storage.py::test_schema_contains_required_tables"
  - id: AC-2
    description: "Writing the same evidence source fingerprint twice stores one evidence row and returns the existing evidence ID on the second write."
    test: "tests/test_storage.py::test_evidence_write_is_idempotent_by_fingerprint"
  - id: AC-3
    description: "Decision rows are append-only: inserting two decisions for one opportunity stores two timestamped records."
    test: "tests/test_storage.py::test_decisions_are_append_only"

Files:
  - demand_mvp_radar/models.py
  - demand_mvp_radar/storage/db.py
  - demand_mvp_radar/storage/migrations.py
  - demand_mvp_radar/storage/repositories.py
  - tests/test_storage.py

Context-Refs:
  - docs/IMPLEMENTATION_CONTRACT.md#sql-safety
  - docs/ARCHITECTURE.md#security-boundaries

Notes: |
  All SQL must use named parameters. Use temporary SQLite databases in tests.

## T06: Tool Schema and Audit Layer

Owner:      codex
Phase:      2
Status:     [x]
Type:       tool:schema
Depends-On: T05

Objective: |
  Define versioned tool schemas, permission checks, side-effect metadata, retry metadata, and audit event recording for all v1 tools in the Tool Catalog.

Acceptance-Criteria:
  - id: AC-1
    description: "Every v1 tool listed in ARCHITECTURE.md Tool Catalog has a schema entry with name, version, input model, output model, side_effect_class, idempotency_key_fields, permission_level, retry_policy, and audit_fields."
    test: "tests/test_tools.py::test_tool_catalog_schema_entries_are_complete"
  - id: AC-2
    description: "Invalid tool input fails schema validation before the executor calls a tool implementation."
    test: "tests/test_tools.py::test_invalid_tool_input_is_rejected_before_execution"
  - id: AC-3
    description: "Every tool call writes a tool audit event containing run_id, tool_name, version, success, latency_ms, and audit fields declared by the schema."
    test: "tests/test_tools.py::test_tool_executor_records_audit_event"

Files:
  - demand_mvp_radar/tools/schemas.py
  - demand_mvp_radar/tools/executor.py
  - demand_mvp_radar/tools/audit.py
  - tests/test_tools.py
  - docs/tool_eval.md

Context-Refs:
  - docs/ARCHITECTURE.md#profile-tool-use
  - docs/IMPLEMENTATION_CONTRACT.md#tool-use-rules-profile-rules-tool-use

Notes: |
  This task defines schemas and executor contracts only. Source-specific tool implementations come later.

## T07: Source Adapter Interfaces and Telegram Import

Owner:      codex
Phase:      2
Status:     [x]
Type:       none
Depends-On: T05, T06

Objective: |
  Implement the source adapter interface and a Telegram export adapter that turns local Telegram-derived records into normalized evidence.

Acceptance-Criteria:
  - id: AC-1
    description: "The Telegram adapter imports a fixture with two messages into two normalized evidence records containing source_type, source_id, captured_at, title, snippet, normalized_text, and content_hash."
    test: "tests/test_sources.py::test_telegram_export_imports_two_evidence_records"
  - id: AC-2
    description: "A malformed Telegram row is written to quarantine with source reference and error reason while valid rows in the same file are imported."
    test: "tests/test_sources.py::test_malformed_telegram_row_is_quarantined"
  - id: AC-3
    description: "The adapter returns deterministic content hashes for the same message text and metadata across two runs."
    test: "tests/test_sources.py::test_telegram_content_hash_is_stable"

Files:
  - demand_mvp_radar/sources/base.py
  - demand_mvp_radar/sources/telegram_export.py
  - demand_mvp_radar/models.py
  - tests/test_sources.py
  - tests/fixtures/telegram_export.json

Context-Refs:
  - docs/spec.md#feature-area-1-source-ingestion
  - docs/IMPLEMENTATION_REFERENCE_MAP.md#file-to-target-map

Notes: |
  Use local fixture files only. Do not require Telegram network credentials.

## T08: URL and Snapshot Source Tools

Owner:      codex
Phase:      2
Status:     [x]
Type:       tool:call
Depends-On: T06, T07

Objective: |
  Implement bounded read tools for manual URL snapshots, saved SERP snapshots, and store metadata fixtures with timeout, retry, and provenance recording.

Acceptance-Criteria:
  - id: AC-1
    description: "`fetch_url_snapshot` records url, status_code, fetched_at, content_hash, and normalized text when given a mocked HTTP 200 response."
    test: "tests/test_source_tools.py::test_fetch_url_snapshot_records_provenance"
  - id: AC-2
    description: "`read_serp_snapshot` imports saved query results with query, provider, rank, title, url, snippet, and captured_at fields."
    test: "tests/test_source_tools.py::test_read_serp_snapshot_imports_fixture_results"
  - id: AC-3
    description: "`read_store_metadata` imports store listing fixtures with listing_id, store, title, description, rating, review_count, and captured_at fields."
    test: "tests/test_source_tools.py::test_read_store_metadata_imports_listing_fixture"

Files:
  - demand_mvp_radar/sources/manual_urls.py
  - demand_mvp_radar/sources/serp_snapshot.py
  - demand_mvp_radar/sources/store_metadata.py
  - demand_mvp_radar/tools/executor.py
  - tests/test_source_tools.py
  - tests/fixtures/serp_snapshot.json
  - tests/fixtures/store_listing.json
  - docs/tool_eval.md

Context-Refs:
  - docs/ARCHITECTURE.md#tool-catalog
  - docs/spec.md#feature-area-1-source-ingestion

Notes: |
  Network calls must use injectable clients and mocked tests. Credentialed live providers are out of scope.

---

## Phase 3 - Retrieval and Candidate Formation

Business goal: build a text-only evidence corpus, evaluate retrieval, and produce clustered opportunity candidates.

## T09: Retrieval Ingestion Pipeline

Owner:      codex
Phase:      3
Status:     [x]
Type:       rag:ingestion
Depends-On: T05, T07, T08

Objective: |
  Implement text normalization, source-aware chunking, embedding adapter interface, local index writes, and corpus version metadata for evidence records.

Acceptance-Criteria:
  - id: AC-1
    description: "Chunking preserves evidence_id, source_type, source_url, captured_at, content_hash, corpus_version, and index_schema_version on every retrieval chunk."
    test: "tests/test_retrieval.py::test_chunks_preserve_source_metadata"
  - id: AC-2
    description: "Building a corpus from three evidence records writes retrieval chunks and records corpus_version plus `retrieval-index-v1` in the run manifest."
    test: "tests/test_retrieval.py::test_corpus_build_records_version_and_schema"
  - id: AC-3
    description: "The retrieval evaluation artifact records an initial ingestion baseline row with eval source, date, corpus version, chunk count, and schema version."
    test: "tests/eval/test_retrieval_eval.py::test_ingestion_baseline_row_has_required_fields"

Files:
  - demand_mvp_radar/retrieval/chunking.py
  - demand_mvp_radar/retrieval/embeddings.py
  - demand_mvp_radar/retrieval/index.py
  - demand_mvp_radar/retrieval/ingestion.py
  - scripts/eval_retrieval.py
  - tests/test_retrieval.py
  - tests/eval/test_retrieval_eval.py
  - docs/retrieval_eval.md

Context-Refs:
  - docs/ARCHITECTURE.md#profile-rag
  - docs/IMPLEMENTATION_CONTRACT.md#rag-rules-profile-rules-rag
  - docs/retrieval_eval.md#evaluation-dataset
  - docs/IMPLEMENTATION_REFERENCE_MAP.md#reference-decisions-to-port

Execution-Mode: heavy
Evidence:
  - `python scripts/eval_retrieval.py --fixture tests/fixtures/retrieval_corpus.json`
  - `pytest tests/eval/test_retrieval_eval.py::test_ingestion_baseline_row_has_required_fields`
Verifier-Focus: |
  Verify that schema version, corpus version, source metadata, and eval source are all recorded. Verify that ingestion code does not import query code. A passing unit test alone is not enough for this task.

## T10: Query-Time Retrieval and Insufficient Evidence

Owner:      codex
Phase:      3
Type:       rag:query
Depends-On: T09
Status:     [x]

Objective: |
  Implement query-time retrieval, metadata filtering, evidence packet assembly, and the required `insufficient_evidence` response.

Acceptance-Criteria:
  - id: AC-1
    description: "A query with at least the configured minimum independent sources returns evidence packets containing evidence_id, source_url, captured_at, snippet, relevance_score, and citation_number."
    test: "tests/test_retrieval_query.py::test_query_returns_cited_evidence_packets"
  - id: AC-2
    description: "A query with fewer than the configured minimum independent sources returns status `insufficient_evidence` and lists missing evidence reasons."
    test: "tests/test_retrieval_query.py::test_query_returns_insufficient_evidence_when_support_is_low"
  - id: AC-3
    description: "Retrieval evaluation records hit@3, citation_precision, no_answer_accuracy, answer_faithfulness, eval source, date, and corpus version for the query fixture set."
    test: "tests/eval/test_retrieval_eval.py::test_query_eval_row_has_required_metrics"

Files:
  - demand_mvp_radar/retrieval/query.py
  - demand_mvp_radar/retrieval/index.py
  - scripts/eval_retrieval.py
  - tests/test_retrieval_query.py
  - tests/eval/test_retrieval_eval.py
  - docs/retrieval_eval.md

Context-Refs:
  - docs/ARCHITECTURE.md#rag-architecture
  - docs/spec.md#insufficient-evidence-behavior
  - docs/IMPLEMENTATION_REFERENCE_MAP.md#reference-decisions-to-port

Execution-Mode: heavy
Evidence:
  - `python scripts/eval_retrieval.py --fixture tests/fixtures/retrieval_queries.json`
  - `pytest tests/test_retrieval_query.py::test_query_returns_insufficient_evidence_when_support_is_low`
Verifier-Focus: |
  Verify that the system skips synthesis when support is low, query code does not import ingestion code, and eval rows include both metrics and provenance.

## T11: Deduplication and Opportunity Clustering

Owner:      codex
Phase:      3
Type:       none
Depends-On: T05, T10
Status:     [x]

Objective: |
  Group related evidence into stable opportunity candidates by normalized pain, workflow, audience, and acquisition channel.

Acceptance-Criteria:
  - id: AC-1
    description: "Two evidence records with the same normalized pain and overlapping source URLs map to one opportunity fingerprint."
    test: "tests/test_clustering.py::test_near_duplicate_evidence_maps_to_one_opportunity"
  - id: AC-2
    description: "Two evidence records with different target audiences produce different opportunity fingerprints even when the broad topic matches."
    test: "tests/test_clustering.py::test_audience_difference_splits_opportunities"
  - id: AC-3
    description: "Cluster output includes opportunity_id, normalized_pain, target_audience, source_evidence_ids, and candidate_title."
    test: "tests/test_clustering.py::test_cluster_output_contains_required_fields"

Files:
  - demand_mvp_radar/clustering.py
  - demand_mvp_radar/models.py
  - tests/test_clustering.py

Context-Refs:
  - docs/spec.md#feature-area-4-clustering-and-scoring

Notes: |
  Prefer deterministic heuristics and fixture tests for v1. Do not introduce an agent loop.

---

## Phase 4 - Scoring and Brief Generation

Business goal: rank candidates with deterministic scores and generate source-grounded MVP briefs for the top opportunities.

## T12: Deterministic Scoring and Recommendations

Owner:      codex
Phase:      4
Type:       none
Depends-On: T11
Status:     [x]

Objective: |
  Implement deterministic opportunity scoring, confidence bands, threshold-based recommendations, and score explanations.

Acceptance-Criteria:
  - id: AC-1
    description: "For a fixed opportunity fixture, scoring returns demand, evidence_diversity, freshness, competition, acquisition_fit, risk, confidence, and total score components."
    test: "tests/test_scoring.py::test_score_output_contains_components"
  - id: AC-2
    description: "The same input fixture and scoring config produce identical total score and recommendation across two runs."
    test: "tests/test_scoring.py::test_scoring_is_deterministic_for_same_input"
  - id: AC-3
    description: "Candidates below minimum evidence threshold receive recommendation `reject` or `revisit` with threshold reason."
    test: "tests/test_scoring.py::test_low_evidence_candidate_gets_threshold_reason"

Files:
  - demand_mvp_radar/scoring.py
  - demand_mvp_radar/models.py
  - tests/test_scoring.py

Context-Refs:
  - docs/ARCHITECTURE.md#deterministic-vs-llm-owned-subproblems

Notes: |
  LLMs must not own scoring arithmetic or threshold decisions.

## T13: LLM Extraction Adapter

Owner:      codex
Phase:      4
Type:       tool:call
Depends-On: T06, T10, T12
Status:     [x]

Objective: |
  Implement a provider-abstracted LLM extraction path that accepts evidence packets, validates structured output, and stores extracted opportunity fields.

Acceptance-Criteria:
  - id: AC-1
    description: "The extraction adapter validates user_pain, target_audience, current_workaround, competitor_shape, mvp_function, acquisition_angle, risk_flags, and confidence_note before returning a result."
    test: "tests/test_llm_extraction.py::test_extraction_output_requires_expected_fields"
  - id: AC-2
    description: "When the fake provider returns malformed JSON or missing required fields, the adapter returns a validation error and does not write extraction output."
    test: "tests/test_llm_extraction.py::test_malformed_provider_output_is_rejected"
  - id: AC-3
    description: "Extraction is skipped when the retrieval result status is `insufficient_evidence`."
    test: "tests/test_llm_extraction.py::test_extraction_skips_insufficient_evidence"

Files:
  - demand_mvp_radar/llm/adapter.py
  - demand_mvp_radar/llm/extraction.py
  - demand_mvp_radar/models.py
  - tests/test_llm_extraction.py
  - docs/tool_eval.md

Context-Refs:
  - docs/ARCHITECTURE.md#inference-model-strategy
  - docs/spec.md#feature-area-5-llm-extraction-and-brief-synthesis

Notes: |
  Use fake providers in tests. Do not require real LLM credentials.

## T14: Brief Synthesis and Markdown Reports

Owner:      codex
Phase:      4
Type:       none
Depends-On: T12, T13
Status:     [x]

Objective: |
  Generate ranked Markdown reports with the configured top opportunities, cited evidence, score components, risks, and build / reject / revisit recommendations.

Acceptance-Criteria:
  - id: AC-1
    description: "A report generated from a fixture with six scored opportunities includes exactly the configured top five opportunities by total score."
    test: "tests/test_reports.py::test_markdown_report_includes_configured_top_n"
  - id: AC-2
    description: "Every opportunity section includes recommendation, score table, one-function MVP scope, acquisition channel, risk flags, cited evidence links, and rationale."
    test: "tests/test_reports.py::test_opportunity_sections_include_required_fields"
  - id: AC-3
    description: "Report writes are atomic: an interrupted write leaves either the previous report or the complete new report, not a partial target file."
    test: "tests/test_reports.py::test_report_write_is_atomic"

Files:
  - demand_mvp_radar/briefs.py
  - demand_mvp_radar/reports/markdown.py
  - demand_mvp_radar/reports/html.py
  - tests/test_reports.py

Context-Refs:
  - docs/spec.md#feature-area-6-reports-and-operator-decisions

Notes: |
  HTML output is optional in implementation, but Markdown output is required.

---

## Phase 5 - Decision Memory and Weekly Run

Business goal: close the loop by recording operator decisions, suppressing repeated weak ideas, and running the complete weekly pipeline.

## T15: Operator Decision Memory

Owner:      codex
Phase:      5
Type:       none
Depends-On: T05, T14
Status:     [x]

Objective: |
  Implement append-only operator decision recording and decision-history lookup for build, reject, and revisit outcomes.

Acceptance-Criteria:
  - id: AC-1
    description: "Recording a decision stores opportunity_id, decision, reason, actor, created_at, and source_report_path."
    test: "tests/test_decisions.py::test_decision_record_contains_required_fields"
  - id: AC-2
    description: "Recording a second decision for the same opportunity appends a new row and preserves the first decision row."
    test: "tests/test_decisions.py::test_second_decision_appends_without_overwrite"
  - id: AC-3
    description: "Decision history lookup returns the most recent decision and the full prior decision list for an opportunity."
    test: "tests/test_decisions.py::test_decision_history_returns_current_and_full_history"

Files:
  - demand_mvp_radar/decisions.py
  - demand_mvp_radar/storage/repositories.py
  - tests/test_decisions.py

Context-Refs:
  - docs/ARCHITECTURE.md#human-approval-boundaries

Notes: |
  Decisions are human-owned. The system may record a recommendation, but it may not record a "build now" decision without operator input.

## T16: Rejected-Idea Suppression and Revisit Logic

Owner:      codex
Phase:      5
Type:       none
Depends-On: T12, T15
Status:     [x]

Objective: |
  Apply decision history to suppress recently rejected opportunities, revisit deferred opportunities after the configured window, and preserve rationale in score explanations.

Acceptance-Criteria:
  - id: AC-1
    description: "A candidate matching a rejected opportunity inside the suppression window receives a lower rank and a suppression reason."
    test: "tests/test_decision_memory.py::test_recent_reject_suppresses_matching_candidate"
  - id: AC-2
    description: "A candidate matching a revisit decision after the revisit date remains eligible and includes prior rationale in the explanation."
    test: "tests/test_decision_memory.py::test_revisit_candidate_includes_prior_rationale"
  - id: AC-3
    description: "Suppression logic is deterministic for the same candidate, decision history, and scoring config."
    test: "tests/test_decision_memory.py::test_suppression_is_deterministic"

Files:
  - demand_mvp_radar/decisions.py
  - demand_mvp_radar/scoring.py
  - tests/test_decision_memory.py

Context-Refs:
  - docs/spec.md#feature-area-6-reports-and-operator-decisions

Notes: |
  Changing default suppression windows after this task requires a documented scoring decision.

## T17: Weekly Pipeline Command

Owner:      codex
Phase:      5
Type:       none
Depends-On: T08, T10, T11, T12, T13, T14, T16
Status:     [x]

Objective: |
  Implement the end-to-end weekly run command that ingests sources, updates retrieval, clusters candidates, scores opportunities, generates the report, and writes run metadata.

Acceptance-Criteria:
  - id: AC-1
    description: "`demand-mvp-radar run --fixture tests/fixtures/weekly_run` writes a run manifest, SQLite records, retrieval corpus metadata, and a Markdown report."
    test: "tests/test_weekly_pipeline.py::test_weekly_run_writes_expected_artifacts"
  - id: AC-2
    description: "The weekly run output includes estimated LLM cost and fails before synthesis when the configured budget ceiling is exceeded."
    test: "tests/test_weekly_pipeline.py::test_weekly_run_enforces_llm_budget_ceiling"
  - id: AC-3
    description: "The command is idempotent by run ID and source fingerprints: re-running the same fixture does not duplicate evidence or decisions."
    test: "tests/test_weekly_pipeline.py::test_weekly_run_is_idempotent_for_same_fixture"

Files:
  - demand_mvp_radar/cli.py
  - demand_mvp_radar/pipeline.py
  - demand_mvp_radar/models.py
  - tests/test_weekly_pipeline.py
  - tests/fixtures/weekly_run/

Context-Refs:
  - docs/ARCHITECTURE.md#data-flow
  - docs/spec.md#overview

Notes: |
  Keep this as orchestration of existing modules. Do not move scoring, retrieval, or source-specific logic into the CLI.

## T18: Evaluation Baseline and Health Output

Owner:      codex
Phase:      5
Type:       rag:query tool:call
Depends-On: T10, T17
Status:     [x]

Objective: |
  Finalize retrieval and tool-use evaluation baselines and expose local health output with database, report directory, corpus version, index age, and configured-source status.

Acceptance-Criteria:
  - id: AC-1
    description: "`demand-mvp-radar health --json` reports database status, report_dir status, corpus_version, index_age_days, max_index_age_days, and configured_sources count."
    test: "tests/test_health.py::test_health_json_reports_runtime_status"
  - id: AC-2
    description: "Retrieval eval history contains a baseline row with hit@3, citation_precision, no_answer_accuracy, answer_faithfulness, corpus version, eval source, and date."
    test: "tests/eval/test_retrieval_eval.py::test_final_retrieval_baseline_contains_required_metrics"
  - id: AC-3
    description: "Tool eval history contains a baseline row with schema_validation_pass_rate, permission_check_pass_rate, audit_field_completeness, eval source, and date."
    test: "tests/eval/test_tool_eval.py::test_tool_eval_baseline_contains_required_metrics"

Files:
  - demand_mvp_radar/cli.py
  - demand_mvp_radar/observability.py
  - scripts/eval_retrieval.py
  - scripts/eval_tools.py
  - tests/test_health.py
  - tests/eval/test_retrieval_eval.py
  - tests/eval/test_tool_eval.py
  - docs/retrieval_eval.md
  - docs/tool_eval.md

Context-Refs:
  - docs/ARCHITECTURE.md#observability
  - docs/IMPLEMENTATION_REFERENCE_MAP.md#file-to-target-map
  - docs/retrieval_eval.md#evaluation-history
  - docs/tool_eval.md#evaluation-history

Execution-Mode: heavy
Evidence:
  - `python scripts/eval_retrieval.py --fixture tests/fixtures/retrieval_queries.json`
  - `python scripts/eval_tools.py --fixture tests/fixtures/tool_eval.json`
Verifier-Focus: |
  Confirm that both active profile eval artifacts include current baseline metrics, eval source, date, and regression thresholds before Phase 5 closes.

---

## Phase 6 - Personal Source Foundation

Business goal: turn the fixture-backed MVP into a personal workflow by ingesting operator-owned sources and documenting the weekly decision loop.

## T19: Operator Workflow Contract

Owner:      codex
Phase:      6
Type:       docs
Depends-On: T18
Status:     [x]

Objective: |
  Create the operator workflow contract that defines the personal pain, decision taxonomy, weekly review constraints, and adoption failure conditions.

Acceptance-Criteria:
  - id: AC-1
    description: "`docs/OPERATOR_WORKFLOW.md` defines weekly inputs, weekly outputs, review time target, and decision taxonomy."
    test: "tests/test_docs_contracts.py::test_operator_workflow_contains_required_sections"
  - id: AC-2
    description: "The workflow contract lists failure conditions that make a weekly report not worth reading."
    test: "tests/test_docs_contracts.py::test_operator_workflow_lists_failure_conditions"
  - id: AC-3
    description: "The workflow contract defines privacy boundaries for Telegram exports, operator notes, and credentials."
    test: "tests/test_docs_contracts.py::test_operator_workflow_defines_privacy_boundaries"

Files:
  - docs/OPERATOR_WORKFLOW.md
  - tests/test_docs_contracts.py

Context-Refs:
  - docs/PERSONAL_TO_PRODUCTION_PLAN.md#phase-0---personal-operating-contract
  - docs/IMPLEMENTATION_CONTRACT.md#credentials-and-secrets

Notes: |
  This is a docs-and-tests task. Do not implement new source adapters here.

## T20: Source Catalog Config Model

Owner:      codex
Phase:      6
Type:       none
Depends-On: T19
Status:     [x]

Objective: |
  Add a typed source catalog configuration model that can represent source priority, trust level, freshness window, access method, and approval requirements.

Acceptance-Criteria:
  - id: AC-1
    description: "A source catalog entry validates source_type, priority, trust_level, freshness_window_days, access_method, enabled, and approval_required."
    test: "tests/test_source_catalog.py::test_source_catalog_entry_validates_required_fields"
  - id: AC-2
    description: "Invalid trust levels, negative freshness windows, or enabled credentialed sources without approval raise validation errors."
    test: "tests/test_source_catalog.py::test_invalid_source_catalog_entries_are_rejected"
  - id: AC-3
    description: "Default configuration includes disabled placeholders for GitHub, HN, Stack Exchange, Product Hunt, SERP, YouTube, app stores, G2, and Reddit."
    test: "tests/test_source_catalog.py::test_default_catalog_contains_planned_source_placeholders"

Files:
  - demand_mvp_radar/config.py
  - demand_mvp_radar/models.py
  - tests/test_source_catalog.py

Context-Refs:
  - docs/SOURCE_CATALOG.md#recommended-initial-sources-beyond-telegram
  - docs/ARCHITECTURE.md#human-approval-boundaries

Notes: |
  Do not call live source APIs. This task only adds typed config and validation.

## T21: Telegram Research Agent Bridge

Owner:      codex
Phase:      6
Type:       none
Depends-On: T20
Status:     [x]

Objective: |
  Import sanitized outputs from `telegram-research-agent` as first-class Demand-to-MVP evidence without coupling to that repository's internal runtime.

Acceptance-Criteria:
  - id: AC-1
    description: "Given a sanitized telegram-research-agent export fixture, the bridge stores evidence records with source type, upstream ID, captured_at, normalized text, content hash, and source fingerprint."
    test: "tests/test_telegram_research_bridge.py::test_bridge_imports_sanitized_export_as_evidence"
  - id: AC-2
    description: "Repeated bridge imports are idempotent by upstream source fingerprint."
    test: "tests/test_telegram_research_bridge.py::test_bridge_import_is_idempotent"
  - id: AC-3
    description: "Malformed or private rows are quarantined with a reason and do not block valid rows."
    test: "tests/test_telegram_research_bridge.py::test_bridge_quarantines_invalid_rows"

Files:
  - demand_mvp_radar/sources/telegram_research_agent.py
  - tests/test_telegram_research_bridge.py
  - tests/fixtures/telegram_research_agent_export.json

Context-Refs:
  - docs/PERSONAL_TO_PRODUCTION_PLAN.md#phase-2---telegram-research-agent-bridge
  - docs/SOURCE_CATALOG.md#wave-1---owned-and-low-risk

Notes: |
  Use a sanitized fixture. Do not read the external repository or private runtime data during tests.

## T22: Operator Notes Source

Owner:      codex
Phase:      6
Type:       none
Depends-On: T20
Status:     [x]

Objective: |
  Add a local operator notes importer for Markdown or JSON notes that can seed hypotheses without alone justifying a build recommendation.

Acceptance-Criteria:
  - id: AC-1
    description: "Markdown notes with frontmatter import as evidence with source_type `operator_note`, captured_at, title, normalized text, and content hash."
    test: "tests/test_operator_notes.py::test_markdown_operator_notes_import_as_evidence"
  - id: AC-2
    description: "Operator-note-only candidates cannot receive a `build` recommendation without at least one corroborating non-note source."
    test: "tests/test_operator_notes.py::test_operator_notes_alone_do_not_justify_build"
  - id: AC-3
    description: "Private note paths are not written to reports or logs; reports use a redacted source reference."
    test: "tests/test_operator_notes.py::test_private_note_paths_are_redacted"

Files:
  - demand_mvp_radar/sources/operator_notes.py
  - demand_mvp_radar/scoring.py
  - tests/test_operator_notes.py
  - tests/fixtures/operator_notes/

Context-Refs:
  - docs/SOURCE_CATALOG.md#evidence-weighting-guidance
  - docs/IMPLEMENTATION_CONTRACT.md#pii-policy

Notes: |
  Notes are high founder-fit signal but weak market proof. Preserve that distinction.

## T23: Own GitHub Repository Source

Owner:      codex
Phase:      6
Type:       tool:call
Depends-On: T20
Status:     [x]

Objective: |
  Import selected evidence from operator-owned GitHub repositories, starting with local repository scans and optional GitHub REST snapshots.

Acceptance-Criteria:
  - id: AC-1
    description: "A local repository fixture imports selected README, issue snapshot, TODO, and recent-change records as evidence with repository provenance."
    test: "tests/test_github_source.py::test_local_repo_snapshot_imports_project_evidence"
  - id: AC-2
    description: "The importer excludes secrets, ignored files, local databases, virtual environments, and generated reports."
    test: "tests/test_github_source.py::test_local_repo_import_excludes_private_and_generated_paths"
  - id: AC-3
    description: "GitHub source tool audit events record repository identifier hash, source count, error count, and run ID without leaking private local paths."
    test: "tests/test_github_source.py::test_github_source_audit_redacts_private_paths"

Files:
  - demand_mvp_radar/sources/github_repo.py
  - demand_mvp_radar/tools/schemas.py
  - tests/test_github_source.py
  - docs/tool_eval.md

Context-Refs:
  - docs/SOURCE_CATALOG.md#recommended-initial-sources-beyond-telegram
  - docs/IMPLEMENTATION_CONTRACT.md#pii-policy

Notes: |
  Prefer local snapshots first. Live GitHub API access should remain optional and fixture-backed in CI.

---

## Phase 7 - Live Evidence Trust

Business goal: make real-source evidence measurable, retrievable, and auditable before relying on generated briefs.

## T24: Live Evidence Import Command

Owner:      codex
Phase:      7
Type:       none
Depends-On: T21, T22, T23
Status:     [x]

Objective: |
  Add an import command that ingests configured owned sources, writes a run manifest, and updates retrieval without generating a weekly opportunity report.

Acceptance-Criteria:
  - id: AC-1
    description: "`demand-mvp-radar import-sources --fixture tests/fixtures/source_mix` stores evidence from Telegram bridge, operator notes, and GitHub source fixtures."
    test: "tests/test_import_sources_command.py::test_import_sources_fixture_writes_evidence_and_manifest"
  - id: AC-2
    description: "The command updates retrieval chunks and records corpus version without synthesizing reports."
    test: "tests/test_import_sources_command.py::test_import_sources_updates_retrieval_without_report_generation"
  - id: AC-3
    description: "Disabled sources are skipped and recorded in the manifest."
    test: "tests/test_import_sources_command.py::test_import_sources_records_disabled_sources"

Files:
  - demand_mvp_radar/cli.py
  - demand_mvp_radar/pipeline.py
  - tests/test_import_sources_command.py
  - tests/fixtures/source_mix/

Context-Refs:
  - docs/spec.md#feature-area-1-source-ingestion
  - docs/PERSONAL_TO_PRODUCTION_PLAN.md#phase-3---evidence-vault-and-rag-trust-layer

Notes: |
  Keep import separate from weekly report generation so evidence quality can be inspected before synthesis.

## T25: Source Trust and Freshness Scoring

Owner:      codex
Phase:      7
Type:       rag:query
Depends-On: T20, T24
Status:     [x]

Objective: |
  Apply source trust, freshness windows, and source-type caps in retrieval and scoring so high-volume weak sources cannot dominate recommendations.

Acceptance-Criteria:
  - id: AC-1
    description: "Retrieval filters or downranks stale evidence based on source-specific freshness windows."
    test: "tests/test_source_trust.py::test_retrieval_applies_source_specific_freshness"
  - id: AC-2
    description: "Scoring applies source trust and caps repeated evidence from the same source type."
    test: "tests/test_source_trust.py::test_scoring_applies_source_trust_and_type_caps"
  - id: AC-3
    description: "Candidates supported only by low-trust or stale sources return `insufficient_evidence` or a non-build recommendation."
    test: "tests/test_source_trust.py::test_low_trust_stale_support_cannot_trigger_build"

Files:
  - demand_mvp_radar/retrieval/query.py
  - demand_mvp_radar/scoring.py
  - tests/test_source_trust.py
  - docs/retrieval_eval.md

Context-Refs:
  - docs/SOURCE_CATALOG.md#evidence-weighting-guidance
  - docs/IMPLEMENTATION_CONTRACT.md#retrieval-evaluation-gate

Notes: |
  Update retrieval evaluation because this changes query-time evidence selection.

## T26: Live-Like Retrieval Evaluation Fixtures

Owner:      codex
Phase:      7
Type:       rag:query
Depends-On: T25
Status:     [x]

Objective: |
  Extend retrieval evaluation with sanitized live-like fixtures representing Telegram bridge, notes, GitHub, competitor URLs, and public developer demand.

Acceptance-Criteria:
  - id: AC-1
    description: "Retrieval eval fixtures include at least five source types and at least ten query cases."
    test: "tests/eval/test_retrieval_eval.py::test_live_like_eval_fixture_has_required_source_coverage"
  - id: AC-2
    description: "Evaluation reports hit@3, citation_precision, no_answer_accuracy, answer_faithfulness, freshness_compliance, and source_diversity."
    test: "tests/eval/test_retrieval_eval.py::test_live_like_eval_reports_extended_metrics"
  - id: AC-3
    description: "Regression notes distinguish code-induced regressions from corpus/source-fixture changes."
    test: "tests/eval/test_retrieval_eval.py::test_retrieval_eval_records_regression_cause"

Files:
  - scripts/eval_retrieval.py
  - tests/fixtures/retrieval_live_like_corpus.json
  - tests/fixtures/retrieval_live_like_queries.json
  - tests/eval/test_retrieval_eval.py
  - docs/retrieval_eval.md

Context-Refs:
  - docs/IMPLEMENTATION_CONTRACT.md#retrieval-evaluation-gate
  - docs/PERSONAL_TO_PRODUCTION_PLAN.md#phase-3---evidence-vault-and-rag-trust-layer

Execution-Mode: heavy

## T27: Evidence Delta Report

Owner:      codex
Phase:      7
Type:       none
Depends-On: T24, T26
Status:     [x]

Objective: |
  Generate an evidence delta report that shows new, changed, duplicated, stale, quarantined, and source-skipped evidence since the previous import.

Acceptance-Criteria:
  - id: AC-1
    description: "The delta report summarizes new, duplicate, stale, quarantined, and skipped counts by source type."
    test: "tests/test_evidence_delta.py::test_delta_report_summarizes_source_counts"
  - id: AC-2
    description: "The delta report lists evidence clusters with meaningful changes since the prior run."
    test: "tests/test_evidence_delta.py::test_delta_report_lists_changed_clusters"
  - id: AC-3
    description: "The delta report redacts private note paths and credentialed source identifiers."
    test: "tests/test_evidence_delta.py::test_delta_report_redacts_private_source_details"

Files:
  - demand_mvp_radar/reports/evidence_delta.py
  - demand_mvp_radar/pipeline.py
  - tests/test_evidence_delta.py

Context-Refs:
  - docs/IMPLEMENTATION_CONTRACT.md#pii-policy
  - docs/PERSONAL_TO_PRODUCTION_PLAN.md#phase-3---evidence-vault-and-rag-trust-layer

---

## Phase 8 - Decision-Grade Artifacts

Business goal: turn real evidence into opportunity dossiers that are strong enough for the operator to make decisions without reopening every source.

## T28: Opportunity Dossier Schema

Owner:      codex
Phase:      8
Type:       none
Depends-On: T25, T27
Status:     [x]

Objective: |
  Define a structured dossier model for decision-grade opportunity review.

Acceptance-Criteria:
  - id: AC-1
    description: "The dossier model validates pain, audience, workaround, evidence, competitor_shape, one_function_mvp, acquisition_angle, risks, missing_evidence, score_components, recommendation, and prior_decisions."
    test: "tests/test_dossiers.py::test_dossier_schema_requires_decision_grade_fields"
  - id: AC-2
    description: "Dossier creation fails when claims lack citations or explicit inference markers."
    test: "tests/test_dossiers.py::test_dossier_rejects_uncited_claims"
  - id: AC-3
    description: "Dossiers include confidence and why-this-may-be-wrong fields."
    test: "tests/test_dossiers.py::test_dossier_includes_confidence_and_countercase"

Files:
  - demand_mvp_radar/models.py
  - demand_mvp_radar/dossiers.py
  - tests/test_dossiers.py

Context-Refs:
  - docs/PERSONAL_TO_PRODUCTION_PLAN.md#phase-4---opportunity-dossier
  - docs/AI_DEVELOPMENT_PACK.md#artifact-quality-bar

## T29: Dossier Renderer

Owner:      codex
Phase:      8
Type:       none
Depends-On: T28
Status:     [x]

Objective: |
  Render opportunity dossiers as Markdown and optional HTML with evidence, score, risk, missing-evidence, and decision sections.

Acceptance-Criteria:
  - id: AC-1
    description: "Markdown dossier output contains all required decision sections in a stable order."
    test: "tests/test_dossier_renderer.py::test_markdown_dossier_contains_required_sections"
  - id: AC-2
    description: "Every cited evidence item includes source type, source title or ID, captured date, and redacted link/reference."
    test: "tests/test_dossier_renderer.py::test_dossier_citations_include_required_provenance"
  - id: AC-3
    description: "The renderer supports `insufficient_evidence` dossiers without synthesizing unsupported build recommendations."
    test: "tests/test_dossier_renderer.py::test_renderer_handles_insufficient_evidence_dossier"

Files:
  - demand_mvp_radar/reports/dossier_markdown.py
  - demand_mvp_radar/reports/dossier_html.py
  - tests/test_dossier_renderer.py

Context-Refs:
  - docs/AI_DEVELOPMENT_PACK.md#artifact-quality-bar
  - docs/spec.md#feature-area-5-llm-extraction-and-brief-synthesis

## T30: Missing Evidence Section

Owner:      codex
Phase:      8
Type:       rag:query
Depends-On: T28, T29
Status:     [x]

Objective: |
  Add explicit missing-evidence analysis to dossiers so weak opportunities explain what proof is absent.

Acceptance-Criteria:
  - id: AC-1
    description: "Missing-evidence output can identify absent independent sources, stale evidence, weak competitor proof, missing acquisition proof, and missing willingness-to-pay signal."
    test: "tests/test_missing_evidence.py::test_missing_evidence_identifies_required_gap_types"
  - id: AC-2
    description: "The missing-evidence section proposes source queries or source types to collect next without inventing facts."
    test: "tests/test_missing_evidence.py::test_missing_evidence_suggests_next_collection_targets"
  - id: AC-3
    description: "Retrieval eval records no-answer accuracy for missing-evidence cases."
    test: "tests/eval/test_retrieval_eval.py::test_missing_evidence_cases_are_in_eval_history"

Files:
  - demand_mvp_radar/retrieval/query.py
  - demand_mvp_radar/dossiers.py
  - tests/test_missing_evidence.py
  - docs/retrieval_eval.md

Context-Refs:
  - docs/IMPLEMENTATION_CONTRACT.md#insufficient-evidence-path
  - docs/PERSONAL_TO_PRODUCTION_PLAN.md#phase-4---opportunity-dossier

## T31: Review Command

Owner:      codex
Phase:      8
Type:       none
Depends-On: T15, T29
Status:     [x]

Objective: |
  Add a local review command for recording operator decisions from generated dossiers.

Acceptance-Criteria:
  - id: AC-1
    description: "`demand-mvp-radar review --opportunity-id ... --decision ... --reason ...` records an append-only decision with source dossier path."
    test: "tests/test_review_command.py::test_review_command_records_decision_with_dossier_path"
  - id: AC-2
    description: "The command rejects `build` decisions without an explicit operator reason."
    test: "tests/test_review_command.py::test_review_command_requires_reason_for_build"
  - id: AC-3
    description: "The command accepts `needs_more_evidence` and stores requested evidence gaps."
    test: "tests/test_review_command.py::test_review_command_records_needs_more_evidence"

Files:
  - demand_mvp_radar/cli.py
  - demand_mvp_radar/decisions.py
  - tests/test_review_command.py

Context-Refs:
  - docs/ARCHITECTURE.md#human-approval-boundaries
  - docs/PERSONAL_TO_PRODUCTION_PLAN.md#phase-5---decision-loop-and-memory

---

## Phase 9 - MVP Experiment Conversion

Business goal: convert selected opportunities into 7-14 day validation experiments and feed outcomes back into memory.

## T32: MVP Experiment Pack Model

Owner:      codex
Phase:      9
Type:       none
Depends-On: T31
Status:     [x]

Objective: |
  Define a structured experiment pack for one selected opportunity.

Acceptance-Criteria:
  - id: AC-1
    description: "The experiment pack validates opportunity_id, one_function_scope, target_user, validation_method, first_10_targets, success_threshold, kill_threshold, revisit_threshold, and timebox_days."
    test: "tests/test_experiments.py::test_experiment_pack_requires_validation_fields"
  - id: AC-2
    description: "Experiment packs cannot be generated for opportunities without a human `build` or `revisit` decision."
    test: "tests/test_experiments.py::test_experiment_pack_requires_human_decision"
  - id: AC-3
    description: "Experiment packs inherit citations and risk flags from the source dossier."
    test: "tests/test_experiments.py::test_experiment_pack_inherits_dossier_context"

Files:
  - demand_mvp_radar/experiments.py
  - demand_mvp_radar/models.py
  - tests/test_experiments.py

Context-Refs:
  - docs/PERSONAL_TO_PRODUCTION_PLAN.md#phase-6---mvp-experiment-pack
  - docs/AI_DEVELOPMENT_PACK.md#artifact-quality-bar

## T33: Experiment Renderer

Owner:      codex
Phase:      9
Type:       none
Depends-On: T32
Status:     [x]

Objective: |
  Render MVP experiment packs as actionable Markdown artifacts.

Acceptance-Criteria:
  - id: AC-1
    description: "The rendered experiment includes scope, target user, validation method, first 10 targets, success threshold, kill threshold, revisit threshold, and timebox."
    test: "tests/test_experiment_renderer.py::test_experiment_markdown_contains_required_sections"
  - id: AC-2
    description: "The experiment renderer includes source evidence citations and risk flags."
    test: "tests/test_experiment_renderer.py::test_experiment_markdown_includes_context"
  - id: AC-3
    description: "The renderer writes atomically and does not overwrite prior experiment artifacts unless the run ID matches."
    test: "tests/test_experiment_renderer.py::test_experiment_write_is_atomic_and_idempotent"

Files:
  - demand_mvp_radar/reports/experiment_markdown.py
  - tests/test_experiment_renderer.py

Context-Refs:
  - docs/PERSONAL_TO_PRODUCTION_PLAN.md#phase-6---mvp-experiment-pack

## T34: Experiment Outcome Recording

Owner:      codex
Phase:      9
Type:       none
Depends-On: T32, T33
Status:     [x]

Objective: |
  Record experiment outcomes and feed them back into decision history and future scoring.

Acceptance-Criteria:
  - id: AC-1
    description: "Recording an outcome stores experiment_id, opportunity_id, outcome, evidence_summary, actor, and created_at."
    test: "tests/test_experiment_outcomes.py::test_experiment_outcome_records_required_fields"
  - id: AC-2
    description: "A killed experiment suppresses matching opportunities until new evidence appears."
    test: "tests/test_experiment_outcomes.py::test_killed_experiment_suppresses_matching_opportunities"
  - id: AC-3
    description: "A validated experiment increases revisit/build confidence only through deterministic scoring rules."
    test: "tests/test_experiment_outcomes.py::test_validated_experiment_affects_score_deterministically"

Files:
  - demand_mvp_radar/experiments.py
  - demand_mvp_radar/decisions.py
  - demand_mvp_radar/scoring.py
  - tests/test_experiment_outcomes.py

Context-Refs:
  - docs/IMPLEMENTATION_CONTRACT.md#deterministic-ownership-of-scores
  - docs/PERSONAL_TO_PRODUCTION_PLAN.md#phase-6---mvp-experiment-pack

---

## Phase 10 - Operator Production Readiness

Business goal: make the local system reliable enough for weekly personal use before any private beta or SaaS work.

## T35: Operator Runbook

Owner:      codex
Phase:      10
Type:       docs
Depends-On: T34
Status:     [x]

Objective: |
  Write an operator runbook for weekly operation, failure recovery, source maintenance, budget review, and privacy checks.

Acceptance-Criteria:
  - id: AC-1
    description: "`docs/OPERATOR_RUNBOOK.md` documents weekly run steps, review steps, source failure handling, and recovery steps."
    test: "tests/test_docs_contracts.py::test_operator_runbook_contains_required_sections"
  - id: AC-2
    description: "The runbook documents how to inspect health, stale index warnings, source errors, cost, and generated artifacts."
    test: "tests/test_docs_contracts.py::test_operator_runbook_documents_health_checks"
  - id: AC-3
    description: "The runbook includes privacy and backup guidance for local SQLite, raw snapshots, reports, and notes."
    test: "tests/test_docs_contracts.py::test_operator_runbook_documents_privacy_and_backup"

Files:
  - docs/OPERATOR_RUNBOOK.md
  - tests/test_docs_contracts.py

Context-Refs:
  - docs/PERSONAL_TO_PRODUCTION_PLAN.md#phase-8---operator-grade-production
  - docs/IMPLEMENTATION_CONTRACT.md#local-first-data-hygiene

## T36: Scheduled Run Support

Owner:      codex
Phase:      10
Type:       none
Depends-On: T35
Status:     [x]

Objective: |
  Add documented and testable support for scheduled local weekly runs without requiring a hosted service.

Acceptance-Criteria:
  - id: AC-1
    description: "The project includes a systemd timer or cron template that runs the weekly command with environment-based configuration."
    test: "tests/test_scheduled_run.py::test_scheduled_run_template_contains_required_command_and_env"
  - id: AC-2
    description: "The scheduled run writes logs and manifests under configured local directories without exposing secrets."
    test: "tests/test_scheduled_run.py::test_scheduled_run_paths_are_local_and_secret_safe"
  - id: AC-3
    description: "The health command reports the timestamp and status of the last scheduled run when available."
    test: "tests/test_scheduled_run.py::test_health_reports_last_scheduled_run"

Files:
  - deploy/demand-mvp-radar.service
  - deploy/demand-mvp-radar.timer
  - demand_mvp_radar/cli.py
  - tests/test_scheduled_run.py
  - docs/OPERATOR_RUNBOOK.md

Context-Refs:
  - docs/ARCHITECTURE.md#runtime-and-isolation-model
  - docs/PERSONAL_TO_PRODUCTION_PLAN.md#phase-8---operator-grade-production

## T37: Backup and Recovery Guide

Owner:      codex
Phase:      10
Type:       docs
Depends-On: T35
Status:     [x]

Objective: |
  Add backup and recovery guidance for SQLite databases, retrieval indexes, reports, raw snapshots, and private source exports.

Acceptance-Criteria:
  - id: AC-1
    description: "`docs/BACKUP_RECOVERY.md` documents backup targets, restore steps, and verification commands."
    test: "tests/test_docs_contracts.py::test_backup_recovery_doc_contains_required_sections"
  - id: AC-2
    description: "The guide documents which files must remain ignored by git."
    test: "tests/test_docs_contracts.py::test_backup_recovery_doc_lists_git_ignored_private_artifacts"
  - id: AC-3
    description: "The guide includes a failed-run recovery checklist."
    test: "tests/test_docs_contracts.py::test_backup_recovery_doc_contains_failed_run_checklist"

Files:
  - docs/BACKUP_RECOVERY.md
  - tests/test_docs_contracts.py

Context-Refs:
  - docs/IMPLEMENTATION_CONTRACT.md#local-first-data-hygiene

## T38: Four-Run Readiness Review

Owner:      codex
Phase:      10
Type:       docs
Depends-On: T36, T37
Status:     [x]

Objective: |
  Define and run the readiness review for four weekly local runs before private beta.

Acceptance-Criteria:
  - id: AC-1
    description: "`docs/audit/PRODUCTION_READINESS_REVIEW.md` defines the four-run evidence checklist and readiness verdict."
    test: "tests/test_docs_contracts.py::test_production_readiness_review_contains_four_run_checklist"
  - id: AC-2
    description: "The readiness checklist includes run success, source failures, retrieval metrics, decision count, cost, backup status, and privacy checks."
    test: "tests/test_docs_contracts.py::test_production_readiness_review_covers_operational_metrics"
  - id: AC-3
    description: "The review explicitly gates private beta and SaaS work until personal weekly value is proven."
    test: "tests/test_docs_contracts.py::test_production_readiness_review_gates_beta_and_saas"

Files:
  - docs/audit/PRODUCTION_READINESS_REVIEW.md
  - tests/test_docs_contracts.py

Context-Refs:
  - docs/PERSONAL_TO_PRODUCTION_PLAN.md#phase-9---private-beta-readiness
  - docs/PERSONAL_TO_PRODUCTION_PLAN.md#phase-10---external-product-decision

---

## Phase 11 - Live Source Connector Foundation

Business goal: make fresh public-source collection the primary workflow, while keeping manual exports and snapshots as fallback modes.

## T39: Live Source Connector Protocol

Owner:      codex
Phase:      11
Type:       rag:ingestion
Depends-On: T38
Status:     [x]

Objective: |
  Define the shared connector protocol for live source collection, normalized evidence output, provenance, cursors, source health, and failure isolation.

Acceptance-Criteria:
  - id: AC-1
    description: "Live connector configuration validates source name, source type, trust level, freshness window, enabled state, cursor support, raw snapshot policy, rate-limit policy, and approval requirements."
    test: "tests/test_live_source_connector.py::test_live_source_config_validates_required_fields"
  - id: AC-2
    description: "Connector results expose normalized evidence rows, quarantined rows, source counts, error counts, cursor state, rate-limit state, and last-success metadata."
    test: "tests/test_live_source_connector.py::test_connector_result_preserves_collection_metadata"
  - id: AC-3
    description: "Every live evidence row carries source name, source URL or source locator, captured_at, content_hash, source_fingerprint, connector version, and run ID."
    test: "tests/test_live_source_connector.py::test_live_evidence_preserves_required_provenance"

Files:
  - demand_mvp_radar/sources/live.py
  - demand_mvp_radar/models.py
  - tests/test_live_source_connector.py

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#connector-contract
  - docs/IMPLEMENTATION_CONTRACT.md#evidence-and-provenance
  - docs/ARCHITECTURE.md#runtime-and-isolation-model

## T40: Credential Resolver and Secret Redaction

Owner:      codex
Phase:      11
Type:       security
Depends-On: T39
Status:     [x]

Objective: |
  Add credential resolution for live connectors without storing secret values in configs, logs, manifests, exceptions, or serialized models.

Acceptance-Criteria:
  - id: AC-1
    description: "Source configs reference environment variable names, not secret values, and credential resolution returns typed available/missing/invalid states."
    test: "tests/test_credentials.py::test_credentials_resolve_from_environment_names_only"
  - id: AC-2
    description: "Missing credentials disable only the affected source and produce a typed source error without failing unrelated sources."
    test: "tests/test_credentials.py::test_missing_credentials_are_source_scoped_errors"
  - id: AC-3
    description: "Secrets are redacted from logs, run manifests, exceptions, model dumps, and health output."
    test: "tests/test_credentials.py::test_secret_values_are_redacted_from_outputs"

Files:
  - demand_mvp_radar/credentials.py
  - demand_mvp_radar/config.py
  - demand_mvp_radar/sources/live.py
  - tests/test_credentials.py
  - docs/OPERATOR_RUNBOOK.md

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#credential-strategy
  - docs/OPERATOR_WORKFLOW.md#privacy-boundaries
  - docs/IMPLEMENTATION_CONTRACT.md#local-first-data-hygiene

## T41: collect-sources Command

Owner:      codex
Phase:      11
Type:       rag:ingestion
Depends-On: T39, T40, T24
Status:     [x]

Objective: |
  Add a `collect-sources` command that runs enabled live connectors, stores normalized evidence, updates retrieval, writes collection manifests, and isolates source failures.

Acceptance-Criteria:
  - id: AC-1
    description: "`collect-sources --config ...` runs enabled live connectors, persists new evidence, updates retrieval chunks, and does not generate opportunity reports."
    test: "tests/test_collect_sources_command.py::test_collect_sources_imports_live_evidence_without_reports"
  - id: AC-2
    description: "Per-source failures are recorded in the run manifest and health state without aborting successful sources."
    test: "tests/test_collect_sources_command.py::test_collect_sources_isolates_source_failures"
  - id: AC-3
    description: "Repeated collection with the same fixture/cursor state is idempotent by content hash and source fingerprint."
    test: "tests/test_collect_sources_command.py::test_collect_sources_is_idempotent_by_fingerprint"

Files:
  - demand_mvp_radar/cli.py
  - demand_mvp_radar/sources/live.py
  - demand_mvp_radar/storage.py
  - tests/test_collect_sources_command.py
  - docs/OPERATOR_RUNBOOK.md

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#p1---connector-sdk
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#p2---public-connector-wave
  - docs/retrieval_eval.md

## T42: Hacker News Live Connector

Owner:      codex
Phase:      11
Type:       rag:ingestion
Depends-On: T41
Status:     [x]

Objective: |
  Collect Hacker News discussion and story signals through fixture-first live connector behavior without requiring credentials in CI.

Acceptance-Criteria:
  - id: AC-1
    description: "The connector maps Hacker News stories/comments into normalized demand evidence with title, body, URL, author hash, captured_at, and source locator."
    test: "tests/test_hacker_news_connector.py::test_hacker_news_connector_maps_fixture_to_evidence"
  - id: AC-2
    description: "Pagination and cursor state prevent duplicate collection across runs."
    test: "tests/test_hacker_news_connector.py::test_hacker_news_connector_persists_cursor_state"
  - id: AC-3
    description: "Malformed or low-content rows are quarantined without blocking valid Hacker News evidence."
    test: "tests/test_hacker_news_connector.py::test_hacker_news_connector_quarantines_malformed_rows"

Files:
  - demand_mvp_radar/sources/hacker_news.py
  - tests/fixtures/hacker_news/
  - tests/test_hacker_news_connector.py

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#source-waves
  - docs/SOURCE_CATALOG.md

## T43: Stack Exchange Live Connector

Owner:      codex
Phase:      11
Type:       rag:ingestion
Depends-On: T41
Status:     [x]

Objective: |
  Collect Stack Exchange question and answer demand signals from configured sites and tags using fixture-first live connector behavior.

Acceptance-Criteria:
  - id: AC-1
    description: "The connector maps Stack Exchange questions and answers into normalized evidence with site, tags, score, accepted-answer state, URLs, and captured_at."
    test: "tests/test_stack_exchange_connector.py::test_stack_exchange_connector_maps_fixture_to_evidence"
  - id: AC-2
    description: "Configured sites/tags are validated and stored in source metadata for retrieval filtering and source health."
    test: "tests/test_stack_exchange_connector.py::test_stack_exchange_connector_validates_sites_and_tags"
  - id: AC-3
    description: "Backoff/rate-limit responses produce source-scoped errors and preserved cursor state."
    test: "tests/test_stack_exchange_connector.py::test_stack_exchange_connector_records_rate_limit_state"

Files:
  - demand_mvp_radar/sources/stack_exchange.py
  - tests/fixtures/stack_exchange/
  - tests/test_stack_exchange_connector.py

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#source-waves
  - docs/SOURCE_CATALOG.md

## T44: RSS Feed Connector

Owner:      codex
Phase:      11
Type:       rag:ingestion
Depends-On: T41
Status:     [x]

Objective: |
  Collect configured RSS/Atom feeds as low-risk public evidence with feed-level provenance, dedupe, and freshness metadata.

Acceptance-Criteria:
  - id: AC-1
    description: "The connector parses RSS and Atom fixtures into normalized evidence with feed URL, entry URL, title, summary/body, published_at, and captured_at."
    test: "tests/test_rss_connector.py::test_rss_connector_maps_feeds_to_evidence"
  - id: AC-2
    description: "Entry GUID, URL, and content hash are used to dedupe repeated feed entries across collection runs."
    test: "tests/test_rss_connector.py::test_rss_connector_dedupes_repeated_entries"
  - id: AC-3
    description: "Feed parse errors quarantine only the affected feed and appear in source health."
    test: "tests/test_rss_connector.py::test_rss_connector_records_feed_parse_errors"

Files:
  - demand_mvp_radar/sources/rss.py
  - tests/fixtures/rss/
  - tests/test_rss_connector.py

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#source-waves
  - docs/SOURCE_CATALOG.md

## T45: GitHub Public Search Connector

Owner:      codex
Phase:      11
Type:       rag:ingestion
Depends-On: T41, T23
Status:     [x]

Objective: |
  Collect public GitHub issue, discussion, and repository search signals using configured queries and optional token-based higher limits.

Acceptance-Criteria:
  - id: AC-1
    description: "The connector maps public GitHub search fixtures into normalized evidence with repository locator, issue/discussion URL, labels, timestamps, and captured_at."
    test: "tests/test_github_public_connector.py::test_github_public_connector_maps_search_results"
  - id: AC-2
    description: "The connector works without credentials in low-rate mode and uses `GITHUB_TOKEN` only when configured by env var name."
    test: "tests/test_github_public_connector.py::test_github_public_connector_supports_optional_token"
  - id: AC-3
    description: "Private repository URLs, local paths, and raw token values are excluded from evidence and manifests."
    test: "tests/test_github_public_connector.py::test_github_public_connector_redacts_private_values"

Files:
  - demand_mvp_radar/sources/github_public.py
  - tests/fixtures/github_public/
  - tests/test_github_public_connector.py

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#source-waves
  - docs/SOURCE_CATALOG.md
  - docs/IMPLEMENTATION_CONTRACT.md#local-first-data-hygiene

---

## Phase 12 - Source Health and Public Corpus Evaluation

Business goal: prove that the first public connector wave improves retrieval and decision quality before adding credentialed or noisy channels.

## T46: Source Health in health --json

Owner:      codex
Phase:      12
Type:       none
Depends-On: T41, T42, T43, T44, T45
Status:     [x]

Objective: |
  Extend health output with live source status, freshness, cursor, rate-limit, credential, and failure summaries.

Acceptance-Criteria:
  - id: AC-1
    description: "`health --json` reports per-source enabled state, last success, last error class, cursor age, freshness status, credential state, and rate-limit state."
    test: "tests/test_live_source_health.py::test_health_reports_live_source_status"
  - id: AC-2
    description: "Health output redacts credential names and secret values while still identifying missing credential requirements by source."
    test: "tests/test_live_source_health.py::test_health_redacts_live_source_credentials"
  - id: AC-3
    description: "Stale or repeatedly failing sources produce explicit warnings without marking the whole system unhealthy when other sources are current."
    test: "tests/test_live_source_health.py::test_health_distinguishes_source_failures_from_system_failure"

Files:
  - demand_mvp_radar/cli.py
  - demand_mvp_radar/health.py
  - tests/test_live_source_health.py
  - docs/OPERATOR_RUNBOOK.md

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#production-requirements
  - docs/OPERATOR_RUNBOOK.md

## T47: Live Public Corpus Retrieval Eval

Owner:      codex
Phase:      12
Type:       rag:evaluation
Depends-On: T42, T43, T44, T45
Status:     [x]

Objective: |
  Add a retrieval evaluation slice that measures whether live public connectors improve cited demand-signal retrieval and no-answer behavior.

Acceptance-Criteria:
  - id: AC-1
    description: "A public-live fixture corpus covers Hacker News, Stack Exchange, RSS, and GitHub public evidence across at least ten queries."
    test: "tests/test_live_public_retrieval_eval.py::test_live_public_eval_fixture_covers_required_sources"
  - id: AC-2
    description: "Retrieval evaluation reports hit@3, citation precision, no-answer accuracy, answer faithfulness, freshness compliance, source diversity, and public-source coverage."
    test: "tests/test_live_public_retrieval_eval.py::test_live_public_eval_reports_required_metrics"
  - id: AC-3
    description: "`docs/retrieval_eval.md` records the public-live baseline and regression thresholds."
    test: "tests/test_live_public_retrieval_eval.py::test_live_public_eval_updates_retrieval_docs"

Files:
  - scripts/eval_retrieval.py
  - tests/fixtures/retrieval_live_public_queries.json
  - tests/test_live_public_retrieval_eval.py
  - docs/retrieval_eval.md

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#p3---source-health-and-evaluation
  - docs/retrieval_eval.md

---

## Phase 13 - Credentialed Source Wave

Business goal: add higher-coverage sources only after the public-source baseline is measurable and secret handling is proven.

## T48: SERP Credentialed Connector

Owner:      codex
Phase:      13
Type:       rag:ingestion
Depends-On: T40, T47
Status:     [x]

Objective: |
  Collect search result evidence through a credentialed SERP provider behind fixture-first tests, strict budget controls, and source-scoped failure handling.

Acceptance-Criteria:
  - id: AC-1
    description: "The connector maps SERP fixtures into normalized evidence with query, rank, result URL, snippet, captured_at, and provider metadata."
    test: "tests/test_serp_connector.py::test_serp_connector_maps_fixture_to_evidence"
  - id: AC-2
    description: "The connector requires an env-var-named credential and fails source-scoped when it is missing."
    test: "tests/test_serp_connector.py::test_serp_connector_requires_credential_name"
  - id: AC-3
    description: "Configured daily and per-run budget limits prevent live calls after the cap is reached."
    test: "tests/test_serp_connector.py::test_serp_connector_enforces_budget_limits"

Files:
  - demand_mvp_radar/sources/serp.py
  - tests/fixtures/serp/
  - tests/test_serp_connector.py

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#credential-strategy
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#p4---credentialed-connector-wave

## T49: YouTube Connector

Owner:      codex
Phase:      13
Type:       rag:ingestion
Depends-On: T40, T47
Status:     [x]

Objective: |
  Collect YouTube search, video metadata, and comment signals for configured problem queries with quota-aware fixture-first behavior.

Acceptance-Criteria:
  - id: AC-1
    description: "The connector maps YouTube fixture data into normalized evidence with video URL, channel hash, title, description/comment text, timestamps, and captured_at."
    test: "tests/test_youtube_connector.py::test_youtube_connector_maps_fixture_to_evidence"
  - id: AC-2
    description: "Quota and page-token state are recorded so repeated runs resume safely."
    test: "tests/test_youtube_connector.py::test_youtube_connector_records_quota_and_page_state"
  - id: AC-3
    description: "The connector requires `YOUTUBE_API_KEY` by env var name for live calls and redacts all secret values."
    test: "tests/test_youtube_connector.py::test_youtube_connector_redacts_api_key"

Files:
  - demand_mvp_radar/sources/youtube.py
  - tests/fixtures/youtube/
  - tests/test_youtube_connector.py

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#credential-strategy
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#source-waves

## T50: Product Hunt Connector

Owner:      codex
Phase:      13
Type:       rag:ingestion
Depends-On: T40, T47
Status:     [x]

Objective: |
  Collect Product Hunt launches, comments, and category metadata as competitor and demand evidence using fixture-first connector behavior.

Acceptance-Criteria:
  - id: AC-1
    description: "The connector maps Product Hunt fixture data into normalized evidence with product URL, tagline/body, topics, launch date, vote/comment counts, and captured_at."
    test: "tests/test_product_hunt_connector.py::test_product_hunt_connector_maps_fixture_to_evidence"
  - id: AC-2
    description: "Credentialed and non-credentialed modes are explicit in source config and health output."
    test: "tests/test_product_hunt_connector.py::test_product_hunt_connector_reports_access_mode"
  - id: AC-3
    description: "Product Hunt evidence is capped in scoring so launch popularity alone cannot produce `build`."
    test: "tests/test_product_hunt_connector.py::test_product_hunt_only_evidence_cannot_trigger_build"

Files:
  - demand_mvp_radar/sources/product_hunt.py
  - demand_mvp_radar/scoring.py
  - tests/fixtures/product_hunt/
  - tests/test_product_hunt_connector.py

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#source-waves
  - docs/IMPLEMENTATION_CONTRACT.md#deterministic-ownership-of-scores

---

## Phase 14 - Community Source Wave

Business goal: add high-signal community channels only through allowlisted, auditable, and rate-limited connectors.

## T51: Reddit Connector

Owner:      codex
Phase:      14
Type:       rag:ingestion
Depends-On: T40, T47
Status:     [x]

Objective: |
  Collect Reddit subreddit/search evidence from allowlisted communities with strict public-only provenance, rate-limit handling, and scoring caps.

Acceptance-Criteria:
  - id: AC-1
    description: "The connector maps Reddit fixture posts/comments into normalized evidence with subreddit, thread URL, score/comment metadata, timestamps, and captured_at."
    test: "tests/test_reddit_connector.py::test_reddit_connector_maps_fixture_to_evidence"
  - id: AC-2
    description: "Only allowlisted subreddits or configured queries can be collected."
    test: "tests/test_reddit_connector.py::test_reddit_connector_enforces_allowlist"
  - id: AC-3
    description: "Reddit-only support cannot trigger `build` without independent non-Reddit evidence."
    test: "tests/test_reddit_connector.py::test_reddit_only_support_cannot_trigger_build"

Files:
  - demand_mvp_radar/sources/reddit.py
  - demand_mvp_radar/scoring.py
  - tests/fixtures/reddit/
  - tests/test_reddit_connector.py

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#source-waves
  - docs/SOURCE_CATALOG.md

## T52: Discord Allowlisted Channel Connector

Owner:      codex
Phase:      14
Type:       rag:ingestion
Depends-On: T40, T47
Status:     [x]

Objective: |
  Collect Discord messages only from explicitly approved channels using bot-token credentials, redaction, and private-data guardrails.

Acceptance-Criteria:
  - id: AC-1
    description: "The connector maps Discord fixture messages into normalized evidence with channel locator hash, message URL/locator, author hash, timestamps, and captured_at."
    test: "tests/test_discord_connector.py::test_discord_connector_maps_fixture_to_evidence"
  - id: AC-2
    description: "Collection is blocked unless the channel is allowlisted and marked approved in source config."
    test: "tests/test_discord_connector.py::test_discord_connector_requires_approved_allowlist"
  - id: AC-3
    description: "Author IDs, private channel names, and bot tokens are redacted from evidence, manifests, and health output."
    test: "tests/test_discord_connector.py::test_discord_connector_redacts_private_values"

Files:
  - demand_mvp_radar/sources/discord.py
  - tests/fixtures/discord/
  - tests/test_discord_connector.py

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#credential-strategy
  - docs/IMPLEMENTATION_CONTRACT.md#local-first-data-hygiene

## T53: Telegram Approved Channel Connector

Owner:      codex
Phase:      14
Type:       rag:ingestion
Depends-On: T40, T21, T47
Status:     [x]

Objective: |
  Add an approved-channel Telegram collector as an optional live alternative to sanitized export imports.

Acceptance-Criteria:
  - id: AC-1
    description: "The connector maps approved Telegram channel fixture messages into normalized evidence with channel locator hash, message locator, timestamps, and captured_at."
    test: "tests/test_telegram_live_connector.py::test_telegram_live_connector_maps_fixture_to_evidence"
  - id: AC-2
    description: "Only approved public or operator-owned channels can be collected; private chats remain unsupported."
    test: "tests/test_telegram_live_connector.py::test_telegram_live_connector_rejects_private_chats"
  - id: AC-3
    description: "Live Telegram evidence follows the same redaction, dedupe, and quarantine behavior as the existing Telegram export bridge."
    test: "tests/test_telegram_live_connector.py::test_telegram_live_connector_matches_export_redaction_contract"

Files:
  - demand_mvp_radar/sources/telegram_live.py
  - demand_mvp_radar/telegram_import.py
  - tests/fixtures/telegram_live/
  - tests/test_telegram_live_connector.py

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#source-waves
  - docs/OPERATOR_WORKFLOW.md#privacy-boundaries

---

## Phase 15 - Source Value and Review UX

Business goal: make the expanded source set manageable by showing which sources improve decisions and by reducing review friction.

## T54: Source Value Report

Owner:      codex
Phase:      15
Type:       rag:evaluation
Depends-On: T47, T48, T49, T50, T51, T52, T53
Status:     [x]

Objective: |
  Report which sources contribute useful, cited, decision-changing evidence and which sources should be disabled or demoted.

Acceptance-Criteria:
  - id: AC-1
    description: "The source value report summarizes per-source evidence count, cited count, decision influence, quarantine rate, freshness, failures, and estimated cost."
    test: "tests/test_source_value_report.py::test_source_value_report_contains_required_metrics"
  - id: AC-2
    description: "Sources with low value, high failure rate, stale evidence, or excessive cost are flagged with deterministic recommendations."
    test: "tests/test_source_value_report.py::test_source_value_report_flags_low_value_sources"
  - id: AC-3
    description: "The report redacts private source locators and credential-related fields."
    test: "tests/test_source_value_report.py::test_source_value_report_redacts_private_fields"

Files:
  - demand_mvp_radar/reports/source_value.py
  - tests/test_source_value_report.py
  - docs/OPERATOR_RUNBOOK.md

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#p5---source-value-and-noise-control
  - docs/IMPLEMENTATION_CONTRACT.md#deterministic-ownership-of-scores

## T55: Local Review Cockpit

Owner:      codex
Phase:      15
Type:       none
Depends-On: T31, T54
Status:     [x]

Objective: |
  Add a local review cockpit that lets the operator review dossiers, source value, missing evidence, and experiment actions without turning the product into a hosted SaaS.

Acceptance-Criteria:
  - id: AC-1
    description: "The cockpit serves local-only views for opportunities, dossiers, source value, missing evidence, and experiment packs."
    test: "tests/test_review_cockpit.py::test_review_cockpit_serves_required_local_views"
  - id: AC-2
    description: "Review actions use the existing decision-recording contract and preserve actor, timestamps, rationale, and requested evidence gaps."
    test: "tests/test_review_cockpit.py::test_review_cockpit_records_existing_decision_contract"
  - id: AC-3
    description: "The cockpit binds to localhost by default and does not expose raw private evidence or secrets."
    test: "tests/test_review_cockpit.py::test_review_cockpit_is_local_and_redacted_by_default"

Files:
  - demand_mvp_radar/review_cockpit.py
  - demand_mvp_radar/cli.py
  - tests/test_review_cockpit.py
  - docs/OPERATOR_RUNBOOK.md

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#p6---local-review-cockpit
  - docs/OPERATOR_WORKFLOW.md#review-time-target

---

## Phase 16 - Beta and Hosted Decision

Business goal: decide from evidence whether the product should remain a personal local tool, support private beta, or move toward hosted SaaS.

## T56: Private Beta Source Onboarding

Owner:      codex
Phase:      16
Type:       docs
Depends-On: T38, T55
Status:     [x]

Objective: |
  Define private beta onboarding for source setup, credential handling, local operation, support boundaries, and readiness evidence.

Acceptance-Criteria:
  - id: AC-1
    description: "`docs/PRIVATE_BETA_ONBOARDING.md` documents setup, source selection, credential environment variables, local scheduling, backup, privacy, and support boundaries."
    test: "tests/test_docs_contracts.py::test_private_beta_onboarding_contains_required_sections"
  - id: AC-2
    description: "Beta remains gated on the four-run readiness review and at least three useful personal decisions."
    test: "tests/test_docs_contracts.py::test_private_beta_onboarding_keeps_readiness_gate"
  - id: AC-3
    description: "The onboarding guide defines what data must never be sent to maintainers."
    test: "tests/test_docs_contracts.py::test_private_beta_onboarding_defines_private_data_boundary"

Files:
  - docs/PRIVATE_BETA_ONBOARDING.md
  - tests/test_docs_contracts.py

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#p8---private-beta-package
  - docs/audit/PRODUCTION_READINESS_REVIEW.md

## T57: Hosted/SaaS Decision ADR

Owner:      codex
Phase:      16
Type:       docs
Depends-On: T56
Status:     [x]

Objective: |
  Write the architecture decision record that decides whether to remain local-first, support team deployment, or start hosted SaaS work.

Acceptance-Criteria:
  - id: AC-1
    description: "`docs/adr/ADR_HOSTED_SAAS_DECISION.md` compares local-only, team self-hosted, and hosted SaaS options."
    test: "tests/test_docs_contracts.py::test_hosted_saas_adr_compares_required_options"
  - id: AC-2
    description: "The ADR requires evidence from personal readiness, private beta usage, source value, support burden, credential risk, and willingness-to-pay before hosted work can start."
    test: "tests/test_docs_contracts.py::test_hosted_saas_adr_requires_beta_evidence"
  - id: AC-3
    description: "The ADR lists hosted-only prerequisites: auth, tenant isolation, encrypted secrets, billing, audit logs, abuse controls, and data deletion."
    test: "tests/test_docs_contracts.py::test_hosted_saas_adr_lists_hosted_prerequisites"

Files:
  - docs/adr/ADR_HOSTED_SAAS_DECISION.md
  - tests/test_docs_contracts.py

Context-Refs:
  - docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md#p9---hostedsaas-decision-gate
  - docs/PERSONAL_TO_PRODUCTION_PLAN.md#phase-10---external-product-decision
