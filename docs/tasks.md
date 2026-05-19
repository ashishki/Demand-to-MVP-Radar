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
