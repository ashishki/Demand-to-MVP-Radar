# Specification - Demand-to-MVP Radar

Version: 1.0
Date: 2026-05-19
Status: Draft

---

## Overview

Demand-to-MVP Radar ingests demand signals from configured text sources, normalizes them into evidence records, retrieves related history, ranks product opportunities with deterministic score components, and generates weekly source-backed one-function MVP briefs for operator review. The system is advisory: it helps the operator make build / reject / revisit decisions faster, but it does not make commercial commitments or take external actions.

---

## User Roles

| Role | Capabilities |
|------|--------------|
| Operator | Configure sources, run weekly or on-demand analysis, review ranked opportunities, inspect evidence and score components, record build / reject / revisit decisions. |
| Reviewer | Read generated reports, inspect provenance, compare score rationale, and challenge weak recommendations. In v1 this may be the same person as the operator. |
| System maintainer | Update source adapters, scoring rules, tool schemas, retrieval evaluation, and model configuration through reviewed code changes. |

---

## Feature Area 1: Source Ingestion

### Description

The system reads configured text evidence from Telegram-derived exports, manual URLs, saved SERP/search-query snapshots, competitor pages, store listings, Reddit/X exports, and operator notes. Every imported item receives stable provenance and a source fingerprint.

### Acceptance Criteria

1. Given a Telegram export fixture with two messages, the ingestion command stores two evidence records with source type, source URL or message ID, captured timestamp, text snippet, and content hash.
2. Given a duplicate source fingerprint in the same run, the storage layer records one evidence item and increments the duplicate counter in the run manifest.
3. Given a malformed source row, the ingestion command records a quarantined row with error reason and continues importing valid rows.
4. Given a manual URL source, the fetcher uses configured timeout and records HTTP status, fetched_at timestamp, and content hash.
5. Given a disabled source in config, the run manifest records it as skipped and no adapter call is made for that source.

### Out of Scope for v1

- High-scale scraping.
- Browser automation.
- Paid source management.
- Automatically bypassing source rate limits or terms.

---

## Feature Area 2: Evidence Normalization and Storage

### Description

The system converts raw source records into typed evidence, stores them in SQLite, and preserves enough metadata for later retrieval, scoring, and audit.

### Acceptance Criteria

1. Evidence records require source_id, source_type, captured_at, title or summary, snippet, normalized_text, and content_hash before persistence.
2. SQLite writes are idempotent by stable source fingerprint and run ID.
3. Run manifests record start time, end time, source counts, error counts, duplicate counts, corpus version, and status.
4. Private raw snapshots are stored under the configured data directory and are not written under git-tracked paths.
5. Storage tests can create a fresh temporary database without depending on external services.

### Out of Scope for v1

- PostgreSQL migration.
- Multi-user tenant isolation.
- Long-term raw webpage archival beyond local snapshots and hashes.

---

## Feature Area 3: Text Retrieval

### Description

The system builds a text-only retrieval corpus from normalized evidence, prior briefs, and decision history. Query-time retrieval assembles evidence packets for candidate opportunities and returns `insufficient_evidence` when the minimum support threshold is not met.

### Acceptance Criteria

1. Retrieval ingestion chunks normalized text while preserving evidence ID, source type, source URL, captured_at, and corpus version metadata.
2. The index schema version is stored with every corpus build and exposed in run metadata.
3. Query-time retrieval returns evidence packets with numbered citations, source URLs, snippets, dates, and relevance scores.
4. Query-time retrieval returns `insufficient_evidence` when fewer than the configured independent source count is available.
5. The retrieval evaluation suite records hit@3, citation precision, no-answer accuracy, answer faithfulness, corpus version, eval source, and date.

### Out of Scope for v1

- Multimodal retrieval.
- Cross-tenant corpus isolation.
- Real-time index updates during report reading.

---

## Feature Area 4: Clustering and Scoring

### Description

The system groups related evidence into opportunity candidates and scores each candidate with deterministic, inspectable components.

### Acceptance Criteria

1. Duplicate and near-duplicate evidence are grouped under a stable opportunity fingerprint.
2. Score output contains demand, evidence diversity, freshness, competition, acquisition channel fit, risk, and confidence components.
3. Score aggregation is deterministic for the same input corpus, scoring configuration, and decision history.
4. The scoring module produces build / reject / revisit recommendations based on configured thresholds.
5. Score explanations include component values and threshold reasons for the final recommendation.

### Out of Scope for v1

- Revenue prediction.
- TAM modeling.
- Automated price optimization.
- Model-owned scoring arithmetic.

---

## Feature Area 5: LLM Extraction and Brief Synthesis

### Description

The system uses bounded LLM calls to extract semantic fields from messy text and synthesize source-grounded opportunity briefs for top candidates.

### Acceptance Criteria

1. LLM extraction outputs validate against a Pydantic schema before any result is stored.
2. Extraction captures user pain, target audience, current workaround, competitor shape, one-function MVP candidate, acquisition angle, risk flags, and confidence note.
3. Brief synthesis only receives assembled evidence packets and deterministic score components, not raw unconstrained source dumps.
4. If retrieval returns `insufficient_evidence`, synthesis is skipped and the candidate receives a rejection or revisit reason.
5. Generated briefs contain source links, cited snippets, score components, competitor notes, one-function MVP scope, acquisition channel, risk flags, and build / reject / revisit recommendation.

### Out of Scope for v1

- Fully automated market research.
- Autonomous product selection.
- Unsupported claims about revenue, win probability, or guaranteed demand.

---

## Feature Area 6: Reports and Operator Decisions

### Description

The system writes weekly ranked reports and records operator decisions so later runs can suppress repeated weak ideas, revisit promising ones, and improve scoring.

### Acceptance Criteria

1. A weekly report includes exactly the configured top N opportunities, defaulting to 5.
2. Each opportunity brief includes provenance links, snippets, score components, recommendation, and rejection/build rationale.
3. Reports are written as Markdown and optional static HTML under the configured report directory.
4. Operator decisions are stored append-only with opportunity ID, decision, reason, actor, and timestamp.
5. Recently rejected opportunities are suppressed or downgraded according to the configured suppression window.

### Out of Scope for v1

- Public publishing.
- Multi-user collaboration.
- Push delivery to Telegram or Slack.
- Automatic repository creation for selected MVPs.

---

## Feature Area 7: Evaluation and Operations

### Description

The system maintains CI, smoke tests, retrieval evaluation, tool-use evaluation, budget checks, and run health metadata from the start.

### Acceptance Criteria

1. CI runs ruff check, ruff format --check, and pytest on pushes and pull requests to `main`.
2. `demand-mvp-radar health` returns JSON with database status, report directory status, corpus version, index age, and configured-source count.
3. Retrieval evaluation can run offline against fixture data without external network access.
4. Tool-use evaluation validates tool schemas, permission checks, retry policy behavior, and audit field completeness.
5. Weekly run metadata includes estimated LLM spend and flags runs that exceed the configured budget ceiling.

### Out of Scope for v1

- Production SLO dashboards.
- Load testing gates.
- Multi-region deployment.

---

## Retrieval

### Sources Indexed

- Telegram-derived evidence exports.
- Manual URL snapshots.
- SERP/search-query snapshots.
- Competitor landing page text.
- App-store / Chrome-store / GPT-store listing text.
- Reddit/X exported threads or saved snippets.
- Operator notes.
- Prior opportunity briefs and operator decision history.

### Query Types

- Find evidence supporting a candidate opportunity.
- Retrieve prior rejected or deferred opportunities similar to a new candidate.
- Retrieve competitor examples for a target workflow.
- Retrieve source snippets that justify a build / reject / revisit recommendation.
- Retrieve missing-evidence reasons when a candidate falls below thresholds.

### Citation Format

Each evidence packet and generated brief citation uses:

```text
[EVIDENCE_ID] source_type | title | source_url | captured_at | snippet | score_contribution
```

### Insufficient-Evidence Behavior

If retrieval finds fewer than the configured minimum independent evidence points, stale-only evidence, or evidence without source links, the system returns:

```json
{
  "status": "insufficient_evidence",
  "missing": ["minimum independent source count", "fresh source link"],
  "candidate_id": "..."
}
```

LLM brief synthesis must not run for candidates in this state.

### Retrieval Mode

Retrieval mode is `text-only` for v1. Multimodal evidence is out of scope until text-only retrieval has a measured baseline and an ADR justifies additional modalities.
