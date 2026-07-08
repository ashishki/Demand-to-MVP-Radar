# Architecture - Demand-to-MVP Radar

Version: 1.0
Last updated: 2026-05-23
Status: Draft

---

## System Overview

Demand-to-MVP Radar is a local-first demand-intelligence system that turns market demand signals into ranked, evidence-backed one-function MVP briefs for solo AI builders, indie hackers, and automation engineers. It runs as a CLI-first Python batch pipeline, stores normalized evidence and operator decisions in SQLite, retrieves prior evidence through a text-only corpus, applies deterministic scoring, and uses LLMs only for bounded extraction and synthesis where messy text evidence needs interpretation.

---

## Problem Fit and Adoption Reality

### Problem-First Entry Gate

| Question | Answer |
|----------|--------|
| Concrete operational pain | Opportunity research is manual, inconsistent, and easy to bias toward ideas that feel interesting but have no visible demand. Evidence gets scattered across Telegram posts, search results, store listings, Reddit/X threads, competitor pages, and personal notes. |
| Current workaround | The operator manually reads Telegram channels, browses search queries, inspects stores and competitor pages, saves ad hoc notes, and reasons from memory. `telegram-research-agent` captures some weekly signals but does not structure them for opportunity validation. |
| Why existing process is insufficient | Notes and checklists do not enforce provenance, demand thresholds, source freshness, competitor comparison, scoring consistency, or decision memory. Generic LLM brainstorming can produce plausible ideas without proving that people already search for the solution. |
| First user / operator who feels the pain | A solo AI engineer or indie builder selecting a small, buildable product idea from recurring market signals. The first internal user is the project owner. |
| What would make v1 not worth adopting | Generic idea lists, weak or missing source links, no rejection logic, no ranked comparison, no inspectable score rationale, or outputs that still require hours of manual validation. |
| First proof of value | The operator can review the weekly top 5 opportunities and make a build / reject / revisit decision for each in under 15 minutes, with at least 3 decision-grade opportunities per week. |

### Adoption Reality Gate

| Boundary | Decision |
|----------|----------|
| Work AI is expected to improve | Extraction of pain, audience, workaround, competitor shape, acquisition angle, risks, and concise brief synthesis from messy text evidence. |
| Work AI will not replace | Final commercial judgment, ethical review, legal interpretation, source credibility judgment when evidence conflicts, and the decision to spend engineering time. |
| Claims not allowed before evidence | Do not claim revenue prediction, guaranteed demand, replacement of founder judgment, full market-research automation, winning-idea selection, or a production-ready venture studio. |
| Demo-to-production evidence required | Weekly run metrics, retrieval evaluation, source provenance completeness, operator review time, and operator acceptance of build / reject / revisit rationale. |

Fit verdict: **Use as-is** with Standard governance. The project has a concrete recurring workflow, a named first operator, a current workaround, clear adoption failure conditions, and measurable first proof.

---

## Solution Shape

| Decision | Selection | Justification |
|----------|-----------|---------------|
| Primary shape | Hybrid: deterministic workflow with bounded LLM extraction and synthesis | The steps are known and should stay auditable. Deterministic code owns ingestion, validation, deduplication, scoring, persistence, and report assembly; LLMs help interpret messy text and draft source-grounded summaries. |
| Governance level | Standard | The blast radius is low operationally, but decision quality, provenance, recurring evidence, and evaluation discipline matter enough for full Phase 1 artifacts, CI, eval docs, and review gates. |
| Runtime tier | T1 | A local CLI/systemd or containerized batch worker is sufficient. The runtime needs normal network egress to configured sources and LLM providers, but no shell mutation, privileged worker, microVM, or persistent autonomous execution. |

### Rejected Lower-Complexity Options

| Rejected option | Why it is insufficient |
|-----------------|------------------------|
| Manual checklist only | It does not preserve source provenance, scoring history, rejection memory, or comparable weekly rankings. |
| Deterministic-only parser | The input is messy market text from posts, pages, notes, and listings; extracting pain, workaround, audience, and differentiation from unstructured sources needs bounded LLM interpretation. |
| Generic LLM brainstorming | It cannot prove visible demand, enforce thresholds, preserve evidence links, or compare opportunities across weeks. |
| Higher-autonomy agent | The workflow does not need open-ended planning, delegation, repository mutation, or autonomous product decisions. A fixed pipeline with human approval is enough. |

### Minimum Viable Control Surface

- Source provenance is mandatory for every evidence item and every brief claim.
- Deterministic score components, thresholds, freshness windows, and rejection reasons are stored and inspectable.
- LLM outputs use structured schemas and may not write decisions directly.
- Human approval is required for "build now", paid or credentialed sources, public publishing, repository creation, outbound contact, and scoring weight changes.
- Retrieval has an `insufficient_evidence` path and a baseline evaluation set.
- Tool calls are listed in a Tool Catalog with side-effect class, idempotency, retry policy, permission level, and audit fields.

### Human Approval Boundaries

| Boundary | Human approval required? | Why |
|----------|--------------------------|-----|
| Marking an opportunity as "build now" | Yes | A plausible idea can still waste weeks of engineering effort. |
| Adding paid or credentialed data sources | Yes | This can spend money, expose credentials, or violate source terms. |
| Publishing briefs externally | Yes | Outputs may imply commercial or competitive claims before validation. |
| Creating repositories or product assets | Yes | The system advises; it does not initiate product work. |
| Contacting users, competitors, or communities | Yes | Outreach has reputation and compliance risk. |
| Changing scoring weights or thresholds | Yes | Weight changes affect ranking and decision priority. |
| Ingestion, normalization, clustering, first-pass scoring, and weekly report generation | No | These are bounded, reversible, auditable internal operations. |

### Deterministic vs LLM-Owned Subproblems

| Subproblem | Owner | Reason |
|------------|-------|--------|
| URL validation, source classification, freshness windows, allowlists, denylists | Deterministic | These are policy and validation rules with testable outcomes. |
| Evidence normalization, stable IDs, duplicate detection, run IDs, retries, timestamps | Deterministic | Repeatability and auditability matter more than flexible reasoning. |
| Score aggregation, confidence bands, build / reject / revisit thresholds | Deterministic | Rankings must be comparable across weeks. |
| Retrieval indexing, corpus versioning, insufficient-evidence thresholds | Deterministic | Retrieval quality must be measurable and reproducible. |
| Pain, audience, workaround, competitor-shape, risk-flag extraction from messy text | LLM-owned, schema-bounded | These fields require semantic interpretation but are validated against source snippets. |
| Brief synthesis and conflict explanation | LLM-owned, schema-bounded | The output benefits from synthesis, but every claim must cite evidence. |
| Final product decision | Human-owned | The system is advisory and cannot commit engineering time. |

### Runtime and Isolation Model

| Property | Decision |
|----------|----------|
| Isolation boundary | T1 bounded worker: local CLI, systemd timer, or Docker container once the runtime stabilizes. |
| Persistence model | SQLite WAL for structured data, local filesystem for reports and optional raw snapshots, vector index stored locally. |
| Network model | Egress only to configured source URLs/APIs, Telegram-derived exports, search/store providers, and LLM/embedding providers. No high-scale scraping without source-specific design. |
| Secrets model | Secrets live in environment variables or a local secrets directory excluded from git. LLM, search, Reddit, store, and Telegram credentials are scoped per source. |
| Runtime mutation boundary | Application runtime does not install packages, alter toolchains, create repositories, or mutate infrastructure. Dependency changes occur only through reviewed code commits. |
| Rollback / recovery model | Runs are idempotent by run ID and source fingerprint. Failed runs can be retried; previous reports and decisions remain append-only. SQLite backups or copied database files provide recovery for local v1. |

---

## Inference / Model Strategy

| Path / Task | Model class | Why this class | Fallback / escalation | Budget / latency constraint |
|-------------|-------------|----------------|-----------------------|-----------------------------|
| Search-query variant generation | Small structured-output model | Low-risk generation with deterministic validation and dedupe after output. | Skip query expansion or use saved operator-provided queries. | Keep weekly cost negligible; batch latency is acceptable. |
| Evidence extraction from posts/pages/listings | Small or mid-tier structured-output model | Needs semantic extraction from messy text but not deep planning. | Escalate only when required fields conflict or confidence is low. | Prefer cheaper model first; log token and cost per run. |
| Cluster summary and opportunity brief synthesis | Stronger reasoning/synthesis model only for top candidates | Final top 5 briefs need concise comparison, conflict handling, and source-grounded recommendations. | Fall back to extraction-only report with deterministic score tables. | Target total LLM spend under USD 2-5 per weekly run for v1. |
| Scoring, thresholds, freshness, dedupe, persistence | No model | These must be deterministic for repeatable rankings. | Not applicable. | Must be testable without LLM calls. |

---

## Capability Profiles

| Profile | Status | Evaluation Artifact | Justification |
|---------|--------|---------------------|---------------|
| RAG | ON | `docs/retrieval_eval.md` | The product must retrieve prior opportunity briefs, rejected ideas, source snippets, Telegram evidence, competitor notes, and decision history with citations and freshness checks. |
| Tool-Use | ON | `docs/tool_eval.md` | LLM-owned extraction and synthesis may call bounded read tools for evidence lookup, URL fetches, SERP snapshots, store metadata, and report writes. Tool contracts need side-effect and schema governance. |
| Agentic | OFF | `docs/agent_eval.md` | v1 is a fixed batch workflow with bounded tool calls, not an open-ended observe-decide-act loop. |
| Planning | OFF | `docs/plan_eval.md` | The primary deliverable is an opportunity brief and decision recommendation, not a reusable structured execution plan. |
| Compliance | OFF | `docs/compliance_eval.md` | No named regulatory framework is a v1 launch gate. Secrets and private notes still follow project PII/secrets rules. |

### Active Profile Justifications

RAG is active because retrieval quality, insufficient-evidence behavior, source freshness, and citation traceability directly determine whether the operator can trust the weekly top 5. Retrieval is text-only for v1.

Tool-Use is active because LLM paths may call bounded functions to fetch or inspect evidence and write reports. Even read-mostly tools need schema validation, permission checks, retries, and audit logging. No destructive external tools are planned for v1.

Agentic and Planning stay off to keep the architecture proportional. The system executes a known workflow and recommends decisions to a human; it does not loop autonomously or emit task plans as the main product.

---

## Profile: RAG

### RAG Architecture

Ingestion pipeline:

```text
extract -> normalize -> chunk -> embed -> index
```

| Stage | Description | Technology |
|-------|-------------|------------|
| Extract | Read Telegram-derived exports, manual URLs, saved SERP snapshots, store listings, Reddit/X exports, competitor pages, and operator notes. | Source adapters using Python, httpx, and local file readers. |
| Normalize | Convert source records into typed evidence items with source URL, source type, captured_at, snippet, title, author/channel when available, and raw snapshot reference. | Pydantic models and deterministic normalizers. |
| Chunk | Split longer posts/pages by semantic sections and preserve source metadata on every chunk. | Custom text chunker with token/character bounds. |
| Embed | Embed normalized text chunks for retrieval. | Stable text embedding provider selected during implementation; provider and dimensions recorded in `docs/retrieval_eval.md`. |
| Index | Store vectors and metadata in a local index tied to SQLite evidence IDs. | Local vector index for v1, with schema version `retrieval-index-v1`. |

Query-time pipeline:

```text
query analyze -> retrieve -> filter -> assemble evidence -> answer | insufficient_evidence
```

| Stage | Description | Technology |
|-------|-------------|------------|
| Query analyze | Use deterministic filters for source type, date, audience, and opportunity status; optional LLM query rewrite only for ambiguous operator queries. | Python filters; optional structured LLM output. |
| Retrieve | Similarity search over text chunks scoped to local single-operator corpus. | Local vector index plus metadata filters. |
| Filter | Apply freshness, minimum independent source count, source trust, and duplicate suppression. | Deterministic scoring/filtering module. |
| Assemble evidence | Build numbered evidence packets with source ID, URL, snippet, date, and score contribution. | Evidence assembler module. |
| Answer / insufficient_evidence | Generate a brief only when minimum evidence coverage is met; otherwise return `insufficient_evidence` with missing-evidence reasons. | Deterministic gate before LLM synthesis. |

The `insufficient_evidence` path is mandatory. A retrieval-backed synthesis path must not draft a recommendation when evidence coverage fails.

Phase 7 added live evidence trust controls around this path: `import-sources` can ingest owned-source fixtures into storage and retrieval without generating weekly briefs, query-time retrieval can apply source freshness windows and source trust downranking, scoring applies trust-adjusted support and source-type caps, and import runs expose an evidence delta report before generated briefs are trusted.

### RAG Reference Implementation Guidance

The RAG implementation may use `ashishki/Dream_Motif_Interpreter` as a pattern reference for source connectors, normalized document contracts, staged ingestion, ingestion/query separation, `insufficient_evidence`, and retrieval evaluation. The reference is not a source of truth for this project and does not change v1 choices: Demand-to-MVP Radar remains local-first, SQLite-backed, text-only, and opportunity-research focused.

Portable rules from the reference:

- Source adapters return source documents with provenance; they do not parse opportunities and do not start embeddings.
- Normalization is a side-effect-free boundary with required source metadata before chunking or indexing.
- Embeddings run only after validation, duplicate handling, and corpus/schema metadata assignment.
- Ingestion and query code stay in separate modules and tests must enforce that separation.
- Query-time retrieval can combine lexical/exact recall and vector retrieval, but synthesis receives only assembled evidence packets.
- Retrieval evaluation keeps retrieval quality, answer quality, and operator-reported regression slices separate.
- External research/search evidence is lower trust than first-party saved evidence and must carry source URL, retrieval timestamp, and cautious framing.

See `docs/IMPLEMENTATION_REFERENCE_MAP.md` for file-level mapping from the reference repository to current tasks.

### Corpus Description

| Property | Value |
|----------|-------|
| Source documents | Telegram-derived research signals, manual URLs, SERP/search snapshots, competitor pages, store listings, Reddit/X exports, operator notes, prior briefs, and decision logs. |
| Update frequency | Weekly batch runs with optional manual on-demand imports. |
| Estimated size | v1 starts with 100-500 evidence items per weekly run; historical backfills may reach thousands of text records. |
| Access control | Local single-operator corpus in v1. If exposed as a web app later, corpus access becomes authenticated and tenant-scoped. |

### Retrieval / Embedding Strategy

| Decision | Selection | Why |
|----------|-----------|-----|
| Retrieval mode | text-only | v1 evidence is usable as text. Screenshots may be useful later but are not required for the first useful workflow. |
| Modalities in scope | Text from posts, pages, listings, notes, and reports | Text captures demand statements, competitor copy, pricing, and source snippets needed for v1. |
| Text-only baseline considered? | yes | Text-only is cheaper, simpler to evaluate, and sufficient for source-grounded opportunity briefs. |
| Embedding provider / model | Stable text embedding model selected during implementation and recorded in eval artifacts | Cost-sensitive weekly batch needs stable behavior and predictable index schema. |
| Stability status | stable required | Preview embedding models are not acceptable for v1 decision memory. |
| Fallback / migration path | Keep raw normalized text and source metadata; re-index the corpus under a new schema version after ADR approval. | Retrieval can be rebuilt without losing evidence history. |

### Index Strategy

- Embedding model: stable text embedding model, chosen in T11 and recorded in `docs/retrieval_eval.md`.
- Chunking: source-aware text chunks that preserve source ID, URL, source type, captured date, and evidence item ID.
- Vector dimensions / representation contract: recorded when the embedding provider is selected; schema changes require ADR and full re-index.
- Index schema version: `retrieval-index-v1`.
- Max index age: 7 days for weekly runs; a stale index must be surfaced in report metadata and health output.
- Evaluation plan: a 10-query evaluation set measuring hit@3, citation precision, no-answer accuracy, freshness compliance, and answer faithfulness for top opportunity workflows.

### RAG Risks

| Risk | Mitigation |
|------|------------|
| Hallucination on weak evidence | Deterministic minimum evidence gate and required `insufficient_evidence` output. |
| Schema drift | Version index schema; ADR and full re-index required for embedding, chunking, metadata, or modality changes. |
| Stale index | 7-day max index age with report/health warnings. |
| Corpus isolation failure | Single local corpus in v1; if multi-user later, add tenant namespace filters before exposing retrieval. |
| Retrieval latency regression | Track retrieval latency in eval runs; batch use tolerates minutes but interactive review must load generated reports quickly. |
| Multimodal overreach | Keep screenshots out of v1; require text-only baseline comparison and ADR before adding image retrieval. |
| Cost overrun | Use deterministic filters before embedding/synthesis and evaluate retrieval on a small fixed query set. |

---

## Profile: Tool-Use

### Tool Catalog

| Tool | Side-effect class | Idempotency | Permission level | Retry policy | Audit fields |
|------|-------------------|-------------|------------------|--------------|--------------|
| `read_telegram_evidence` | read | Idempotent by source message ID/export row | Local operator | Retry local read once; malformed rows are quarantined | run_id, source_id, path, row_count, error_count |
| `fetch_url_snapshot` | read with local snapshot write | Idempotent by normalized URL and capture date | Local operator; credentialed sources require approval | Bounded retries with backoff; respect robots/source terms where applicable | run_id, url, status_code, content_hash, fetched_at |
| `read_serp_snapshot` | read | Idempotent by query and snapshot timestamp | Local operator | No network retry for saved snapshots; provider retries only when configured | run_id, query, provider, snapshot_id |
| `read_store_metadata` | read | Idempotent by store, listing ID, and captured_at | Local operator; credentialed source approval required | Bounded retries; rate-limit aware | run_id, store, listing_id, status |
| `read_github_repo_snapshot` | read | Idempotent by repository identifier | Local operator | No retry for local snapshots | run_id, repository_id_hash, source_count, error_count |
| `retrieve_evidence` | read | Idempotent for corpus version, query, filters, and top_k | Internal pipeline | No retry unless index read fails transiently | run_id, corpus_version, query_hash, top_k, hit_count |
| `write_report` | local write | Idempotent by report run ID and output path | Local operator | Atomic write to temp file then rename | run_id, report_path, content_hash |
| `record_operator_decision` | local write | Idempotent by opportunity_id and decision timestamp | Human-approved action | No automatic retry after validation failure | opportunity_id, decision, actor, timestamp, source_report_path, requested_evidence_gaps |

### Unsafe-Action Policy

No destructive external tools are in v1. The following actions are treated as unsafe and require a separate human approval path before execution:

- adding paid or credentialed sources
- publishing reports externally
- contacting users, competitors, or communities
- creating repositories or product assets
- changing score weights or thresholds
- deleting evidence, reports, decisions, or raw snapshots

### Tool Schema Rules

- Tool schemas are versioned under `demand_mvp_radar/tools/schemas.py`.
- LLM-produced tool calls are validated before execution.
- Tool permissions are checked at the tool boundary, not only at workflow entry.
- Tool results include enough provenance for the report and audit log.
- Any future MCP-backed integration must add a Tool Catalog row with MCP server name, pinned version, retry policy, audit fields, side-effect class, idempotency note, and rollback behavior if destructive.

---

## Component Table

| Component | File / Directory | Responsibility |
|-----------|------------------|----------------|
| CLI entrypoint | `demand_mvp_radar/cli.py` | Run weekly ingestion, scoring, report generation, evaluation, and decision commands. |
| Configuration | `demand_mvp_radar/config.py` | Load env vars, paths, budgets, source settings, and validation thresholds. |
| Domain models | `demand_mvp_radar/models.py` | Define evidence, opportunity, score, brief, decision, and run manifest schemas. |
| Storage | `demand_mvp_radar/storage/` | Manage SQLite schema, migrations, repositories, and idempotent writes. |
| Source adapters | `demand_mvp_radar/sources/` | Import Telegram exports, including Knowledge Thread provenance from Telegram Research Agent, plus manual URLs, SERP snapshots, store listings, competitor pages, and notes. |
| Telegram digest bridge | `demand_mvp_radar/telegram_digest.py` | Convert sanitized Telegram weekly digest JSON into local Radar seed exports without network, credentials, or source-trust policy changes. |
| Source document contracts | `demand_mvp_radar/sources/base.py` | Define source refs, fetched source documents, normalized documents, and connector protocols before parsing or embedding. |
| Tool layer | `demand_mvp_radar/tools/` | Define LLM-callable tool schemas, validation, permission checks, audit logging, and bounded execution. |
| Retrieval ingestion | `demand_mvp_radar/retrieval/ingestion.py` | Normalize, chunk, embed, and index text evidence. |
| Retrieval query | `demand_mvp_radar/retrieval/query.py` | Retrieve evidence, enforce filters, assemble evidence packets, and return `insufficient_evidence` when needed. |
| Clustering | `demand_mvp_radar/clustering.py` | Deduplicate and cluster evidence into opportunity candidates. |
| Scoring | `demand_mvp_radar/scoring.py` | Calculate deterministic demand, competition, freshness, acquisition, confidence, and risk scores. |
| Source trust records | `demand_mvp_radar/source_trust.py` | Track evidence count, unique/repeated signal count, evidence density, and rejection reasons for report review. |
| LLM extraction | `demand_mvp_radar/llm/extraction.py` | Produce structured extraction from messy text using bounded schemas. |
| Brief synthesis | `demand_mvp_radar/briefs.py` | Generate source-grounded opportunity briefs and recommendations. |
| Reporting | `demand_mvp_radar/reports/` | Write Markdown/HTML reports and machine-readable run outputs. |
| Public-safe showcase artifacts | `reports/showcase/` | Store sanitized portfolio opportunity dossiers, source registers, missing-evidence notes, and experiment candidates produced from public/operator-owned evidence. |
| Operating readiness artifacts | `docs/open_source_research_protocol.md`, `docs/SOLO_EVIDENCE_LEDGER.md`, `docs/audit/` | Define solo research rules, track four-run evidence readiness, and preserve readiness/audit decisions. |
| Cross-project handoffs | `docs/handoffs/` | Package selected opportunities for adjacent projects without approving outreach, hosted deployment, or external side effects. |
| Observability | `demand_mvp_radar/observability.py` | Provide shared tracing, metrics hooks, and run audit logging. |
| Evaluation | `scripts/eval_retrieval.py`, `scripts/eval_tools.py` | Run retrieval and tool-use evaluations and update eval artifacts. |

---

## Data Flow

1. Operator runs `demand-mvp-radar run --config config/local.toml`.
2. Configuration loads source paths, network-enabled sources, thresholds, budgets, and output directory.
3. Source adapters read Telegram-derived evidence, operator notes, owned GitHub repository snapshots, manual URLs, saved search/store snapshots, competitor pages, and Reddit/X exports. When the input is a sanitized Telegram weekly digest, `digest-to-seeds` can first convert it into the `mvp-of-week` seed export shape. When the input is a Telegram Research Agent opportunity seed, the bridge preserves KIR metadata such as `source_kind`, `knowledge_thread_slug`, `knowledge_thread_status`, `knowledge_atom_types`, `source_atom_ids`, and `source_urls`.
4. Normalizers convert each source into typed evidence records with source provenance and stable fingerprints.
5. Storage writes a run manifest, raw snapshot references, normalized evidence records, and audit events idempotently.
6. Retrieval ingestion chunks, embeds, and indexes text evidence under the current corpus and schema version.
7. Clustering deduplicates near-identical ideas and groups evidence by pain, workflow, audience, and acquisition channel.
8. Scoring computes deterministic score components, source trust records, repeated-signal counts, evidence density, rejection reasons, and confidence bands for each candidate.
9. Query-time retrieval assembles evidence packets for top candidates and returns `insufficient_evidence` for candidates below evidence thresholds.
10. LLM extraction and synthesis produce bounded fields and final briefs only from assembled evidence packets.
11. Report generation writes ranked Markdown/HTML output with source links, snippets, score components, Decision Gate, source trust/repeated-signal notes, KIR gate state for Telegram-seeded candidates, risk flags, and build / reject / revisit recommendations.
12. Operator records decisions; future runs use decision history to suppress repeats and revisit promising ideas.

---

## Tech Stack

| Component | Technology choice | Rationale |
|-----------|-------------------|-----------|
| Language | Python 3.12 | Strong ecosystem for CLI, data processing, SQLite, HTTP, Pydantic, and LLM integrations. |
| Interface | CLI-first with optional FastAPI later | v1 is a batch research workflow; a web UI is premature before scoring/report loop proves value. |
| Packaging | `pyproject.toml`, setuptools, console script | Standard Python packaging and CI-friendly install path. |
| Storage | SQLite WAL | Local-first, cheap, inspectable, enough for one operator and weekly batch volumes. |
| Validation | Pydantic | Structured evidence, tool inputs, LLM outputs, briefs, and decisions. |
| HTTP | httpx | Bounded network fetches with timeouts and testable client injection. |
| Retrieval | Local text vector index plus SQLite metadata | Keeps v1 simple and avoids multi-service operations until retrieval quality is proven. |
| LLM access | Provider adapter behind interfaces | Allows model selection per workload and deterministic testing with fakes. |
| Reports | Markdown and optional static HTML | Easy to inspect, diff, copy, and archive. |
| Tests | pytest | Standard Python test runner with clear function-level acceptance criteria. |
| Lint / format | ruff | Fast linting and formatting in CI. |
| CI | GitHub Actions | Existing remote is GitHub; CI should verify every commit after Phase 1. |

---

## Security Boundaries

- v1 is local single-operator. No public web routes are planned.
- If a web app is added later, every non-health route requires authentication before reading evidence, reports, decisions, or source credentials.
- Secrets come only from environment variables or an ignored local secrets directory.
- `.env`, local database files, raw private notes, source exports, and generated reports are not committed unless explicitly sanitized.
- PII-like fields include source author handles, private notes, credentials, operator identity, and account-specific source data. These values must not appear in logs, span attributes, metrics labels, or public reports unless intentionally included by the operator.
- Raw fetched page bodies may be pruned or content-hashed after extraction when storage grows.
- Credentialed source additions require human approval and a source-specific design note.

---

## External Integrations

| Integration | Used for | Credential required? | v1 posture |
|-------------|----------|----------------------|------------|
| Telegram-derived exports / `telegram-research-agent` output | Initial demand signal corpus and KIR-backed opportunity seeds | Maybe, depending on export path | Prefer local exports or files produced by the existing agent; preserve Knowledge Thread provenance and require KIR plus external corroboration before build-like recommendations. |
| Owned GitHub repositories | Active project direction, TODOs, issue snapshots, recent implementation friction | No for local snapshots; maybe for GitHub REST | Prefer local repository snapshots first; audit by repository identifier hash rather than local path. |
| Manual URLs and competitor pages | Source evidence and positioning notes | No for public pages | Fetch politely with timeouts and source terms awareness. |
| Search / SERP snapshots | Demand and query evidence | Optional provider key | Saved snapshots first; live provider later with approval. |
| Reddit API or exports | Social proof and pain language | Optional | Use saved exports or API only after source-specific configuration. |
| App / Chrome / GPT store metadata | Competitor and demand signals | Optional | Read public metadata or saved snapshots in v1. |
| LLM provider | Extraction, query expansion, final synthesis | Yes | Cost-capped and adapter-backed. |
| Embedding provider | Text retrieval index | Yes if external | Stable model only; provider choice recorded in eval artifacts. |

---

## File Layout

```text
Demand-to-MVP-Radar/
  demand_mvp_radar/
    __init__.py
    cli.py
    config.py
    models.py
    observability.py
    telegram_digest.py
    storage/
      __init__.py
      db.py
      migrations.py
      repositories.py
    sources/
      __init__.py
      base.py
      telegram_export.py
      manual_urls.py
      serp_snapshot.py
      store_metadata.py
      telegram_research_agent.py
      operator_notes.py
      github_repo.py
    tools/
      __init__.py
      schemas.py
      executor.py
      audit.py
    retrieval/
      __init__.py
      ingestion.py
      query.py
      chunking.py
      embeddings.py
      index.py
    llm/
      __init__.py
      adapter.py
      extraction.py
      synthesis.py
    reports/
      __init__.py
      markdown.py
      html.py
    clustering.py
    scoring.py
    decisions.py
  scripts/
    eval_retrieval.py
    eval_tools.py
  tests/
    test_smoke.py
    test_config.py
    test_storage.py
    test_sources.py
    test_tools.py
    test_retrieval.py
    test_scoring.py
    test_reports.py
    eval/
      test_retrieval_eval.py
      test_tool_eval.py
  docs/
    ARCHITECTURE.md
    spec.md
    tasks.md
    CODEX_PROMPT.md
    IMPLEMENTATION_CONTRACT.md
    DECISION_LOG.md
    IMPLEMENTATION_JOURNAL.md
    EVIDENCE_INDEX.md
    open_source_research_protocol.md
    SOLO_EVIDENCE_LEDGER.md
    retrieval_eval.md
    tool_eval.md
    audit/
      SOLO_EVIDENCE_READINESS_REVIEW.md
    prompts/
    handoffs/
      lead_response_sla_gap_radar_handoff.md
  reports/
    showcase/
      portfolio_opportunity_showcase.md
  .github/workflows/ci.yml
  pyproject.toml
  requirements.txt
  requirements-dev.txt
```

---

## Runtime Contract

| Name | Description | Example value |
|------|-------------|---------------|
| `DMR_DATA_DIR` | Base directory for SQLite database, raw snapshots, indexes, and reports. | `/srv/openclaw-you/demand-mvp-radar/data` |
| `DMR_CONFIG_PATH` | Optional config file path for source settings and thresholds. | `config/local.toml` |
| `DMR_DATABASE_URL` | SQLite database URL. | `sqlite:////srv/openclaw-you/demand-mvp-radar/data/radar.sqlite3` |
| `DMR_REPORT_DIR` | Directory for Markdown/HTML report outputs. | `/srv/openclaw-you/demand-mvp-radar/reports` |
| `DMR_LLM_PROVIDER` | LLM provider key used by adapter selection. Empty disables LLM synthesis. | `anthropic` |
| `DMR_LLM_API_KEY` | API key for selected LLM provider. | `env-secret` |
| `DMR_LLM_MODEL_MVP_WEEKLY` | Strong reasoning model for the weekly MVP report. | `claude-opus-4-7` |
| `DMR_LLM_FALLBACK_MODEL_MVP_WEEKLY` | Fallback model if the primary alias is unavailable. | `claude-opus-4-1-20250805` |
| `DMR_EMBEDDING_PROVIDER` | Embedding provider key. | `openai` |
| `DMR_EMBEDDING_API_KEY` | API key for embedding provider if external. | `env-secret` |
| `SERPAPI_API_KEY` | SerpApi key for weekly search-intent collection. | `env-secret` |
| `GITHUB_TOKEN` | Optional GitHub token for higher public search quota. | `env-secret` |
| `YOUTUBE_API_KEY` | YouTube Data API key for tutorial/creator demand collection. | `env-secret` |
| `PRODUCT_HUNT_TOKEN` | Product Hunt API token for launch/competitor collection. | `env-secret` |
| `REDDIT_CLIENT_ID` | Reddit API client ID. | `env-secret` |
| `REDDIT_CLIENT_SECRET` | Reddit API secret. | `env-secret` |
| `REDDIT_USER_AGENT` | Reddit API user agent identifying this private client. | `Demand-to-MVP-Radar/0.1 by user` |
| `STACK_EXCHANGE_KEY` | Optional Stack Exchange API key for higher quota. | `env-secret` |
| `DMR_MAX_WEEKLY_LLM_COST_USD` | Budget ceiling for a weekly run. | `5.00` |
| `DMR_FETCH_TIMEOUT_SECONDS` | HTTP timeout for source fetches. | `20` |
| `DMR_MAX_INDEX_AGE_DAYS` | Retrieval index freshness limit. | `7` |

---

## Observability

- Every run creates a run manifest with run ID, input sources, corpus version, index schema version, model IDs, budget ceiling, start time, end time, and status.
- External calls to HTTP, SQLite, LLM, embedding, and tool execution use the shared tracing module in `demand_mvp_radar/observability.py`.
- Metrics include ingestion success/error counts, duplicate rate, retrieval latency, insufficient-evidence count, tool call success/error counts, LLM cost estimate, and report generation status.
- `demand-mvp-radar health` returns machine-readable health with database status, report directory writability, corpus version, index age, and configured-source status.

---

## Continuity and Retrieval Model

Canonical truth:

- `docs/ARCHITECTURE.md`
- `docs/spec.md`
- `docs/tasks.md`
- `docs/IMPLEMENTATION_CONTRACT.md`
- `docs/CODEX_PROMPT.md`
- ADRs under `docs/adr/`
- evaluation artifacts (`docs/retrieval_eval.md`, `docs/tool_eval.md`)
- code, tests, and CI

Retrieval convenience:

- `docs/DECISION_LOG.md`
- `docs/IMPLEMENTATION_JOURNAL.md`
- `docs/EVIDENCE_INDEX.md`
- task-level `Context-Refs`
- audit reports under `docs/audit/`

Scoped retrieval is mandatory before tasks that change architecture, runtime, retrieval semantics, tool schemas, scoring weights, source trust policy, human approval boundaries, or open findings. Retrieval surfaces point to canonical sources; they do not override them.

---

## Non-Goals

- Do not automate product launch, paid ads, outbound outreach, or repository creation.
- Do not predict revenue or guarantee demand.
- Do not replace founder/operator judgment.
- Do not build a broad startup ideation platform in v1.
- Do not add a web UI before the CLI report loop proves useful.
- Do not enable multimodal retrieval until text-only retrieval has a measured baseline and a clear gap.
- Do not introduce a higher-autonomy agent or mutable runtime for v1.
- Do not perform high-scale scraping without source-specific legal, technical, and rate-limit design.
- Do not store credentials, raw private notes, local databases, or unsanitized reports in git.
