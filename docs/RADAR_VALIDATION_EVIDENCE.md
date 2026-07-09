# Radar Validation Evidence Contract

Status: active contract for RVE-0/RVE-2
Date: 2026-07-09

## Purpose

Radar Validation Evidence (RVE) makes `mvp-of-week` validate the selected
candidate against candidate-specific external demand evidence. It is not an
idea-generation layer and not raw external RAG.

The selected Candidate Dossier can become `build` or `focused_experiment` only
when external records are explicitly matched to the selected candidate,
classified as decision-grade validation evidence, and accepted by existing
source/KIR/operator-fit gates.

## JSON Shape

`mvp-of-week` JSON exposes these top-level fields:

- `validation_queries`: deterministic candidate-specific query pack.
- `matched_external_evidence`: external evidence records accepted by the RVE
  matcher for the selected candidate.
- `missing_evidence_by_category`: missing validation categories and the next
  query to run for each category.
- `validation_adapter_status`: per-source status for future validation
  adapters.
- `decision_context.external_research_context`: unmatched or context-only
  research that can explain the decision but cannot satisfy gates.

The selected candidate also repeats its own `validation_queries` and
`matched_external_evidence` so downstream consumers can read the candidate
object without chasing the top-level contract.

## `validation_queries`

The query planner is deterministic and makes no live external API calls. It
uses the selected candidate title, demand surfaces, and current
`missing_evidence` to produce grouped searches:

- `search_demand`
- `manual_workarounds`
- `competitors`
- `wtp_signals`
- `reddit_forum_complaints`
- `github_discussions`
- `x_discussions`

Each query record contains:

- `query`
- `intent`
- `expected_evidence_kind`
- `target_candidate`
- `source_types`
- `priority`
- `rationale`
- `lower_confidence`

`x_discussions` is lower-confidence by default and can only corroborate
lower-noise sources.

## `matched_external_evidence`

The RVE-2 matcher emits records that are explicitly tied to the selected
candidate. Expected evidence kinds are:

- `repeated_complaint`
- `manual_workaround`
- `search_demand`
- `competitor_traction`
- `wtp_signal`
- `developer_issue`
- `negative_signal`

Required matcher fields for each record:

- `evidence_kind`
- `source_type`
- `source_name`
- `source_url`
- `captured_at`
- `query`
- `matched_candidate_title`
- `match_basis`
- `decision_grade`
- `supports_gate`
- `negative_signal`

Only records with `decision_grade=true`, `supports_gate=true`, and a concrete
candidate match can affect source gates. Negative evidence must remain visible
and must not be hidden by the matcher.

## Context-Only Research

`decision_context.external_research_context` is where useful but unmatched
external research goes. It can help the operator understand why Radar stayed in
`investigate` or `reject`, but it cannot satisfy source gates.

These records never satisfy gates:

- context-only market/business lens records;
- live source intelligence snapshots;
- unmatched SERP, Reddit, crawler, GitHub, Product Hunt, YouTube, or X results;
- broad market trend records that are not tied to the selected candidate pain.

## Adapter Status

`validation_adapter_status` must report adapter state without crashing the
weekly run. Allowed statuses:

- `ok`
- `adapter_disabled`
- `credential_limited`
- `rate_limited`
- `cache_only`
- `error`

Missing credentials and disabled adapters degrade to `credential_limited` or
`adapter_disabled`. External validation adapters must support cache-first and
dry-run operation before they are allowed into the weekly run.

## Gate Rules

- Context-only market records never satisfy gates.
- Unmatched external results never satisfy gates.
- External adapter results must be matched to the selected candidate before
  they can affect `source_gate_satisfied`, `dossier_status`, score, or final
  recommendation.
- Search demand alone can support `investigate` or `focused_experiment` only
  when matched to the selected candidate and corroborated as required by
  existing gates.
- Do not weaken existing source/KIR/operator-fit gates to make candidates look
  stronger.
- If no matched external evidence exists, the report must show missing
  evidence and the next repeatable validation query.

## Current Implementation

RVE-1 adds deterministic query planning in
`demand_mvp_radar/validation_queries.py` and renders a `Validation Query Pack`
section in `mvp-of-week` Markdown. RVE-2 adds candidate-level matching in
`demand_mvp_radar/validation_evidence.py`, renders a `Matched External
Evidence` section, writes matched evidence into JSON, and gates candidate
external evidence counts/source types through `supports_gate=true` matches.
Both layers are deterministic and make no live external calls.

All validation adapters currently report `adapter_disabled`. Later RVE tasks
will add adapters in this order:

1. Search/SERP demand.
2. Reddit/forum complaints.
3. Competitor/workaround crawler.
4. X/Twitter corroboration.
