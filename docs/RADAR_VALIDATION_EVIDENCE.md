# Radar Validation Evidence Contract

Status: active contract for RVE-0/RVE-6
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
- `source_title`
- `source_snippet`
- `captured_at`
- `source_created_at`
- `query`
- optional forum provenance such as `subreddit`, `comment_id`, and
  privacy-preserving `author_hash`
- optional crawler provenance such as `page_kind`, `positioning`,
  `pricing_hint`, and `target_icp`
- optional X/Twitter provenance such as `discussion_kind`,
  `lower_confidence`, and `corroboration_required`
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
dry-run operation before they are allowed into the weekly run. Search/SERP
validation reports `cache_only` when it uses a fixture/cache or dry-run mode
without live external calls. Reddit/forum validation reports:

- `credential_limited` when Reddit/forum credentials are missing;
- `rate_limited` when the live source health payload reports a provider rate
  limit or a rate-limit source error;
- `cache_only` when it uses a fixture/cache or dry-run mode without live API
  calls.

Competitor/workaround crawler validation reports:

- `cache_only` when it uses a fixture/cache or dry-run mode without live page
  fetches;
- `error` when configured URLs, domains, or fixture rows violate the bounded
  crawler contract.

X/Twitter corroboration reports:

- `credential_limited` when live X/xAI credentials are missing;
- `rate_limited` when the live source health payload reports provider limits;
- `cache_only` when it uses a fixture/cache or dry-run mode without live calls.

## Gate Rules

- Context-only market records never satisfy gates.
- Unmatched external results never satisfy gates.
- External adapter results must be matched to the selected candidate before
  they can affect `source_gate_satisfied`, `dossier_status`, score, or final
  recommendation.
- Search demand alone can support `investigate` or `focused_experiment` only
  when matched to the selected candidate and corroborated as required by
  existing gates.
- Reddit/forum complaint evidence must describe the same selected candidate
  pain. Adjacent but different workflow pain remains context-only.
- Competitor/workaround crawler evidence must be bounded by explicit
  domain/page limits. Competitor/integration pages support gates only when they
  are matched to the same candidate and carry target ICP metadata. Pricing copy
  is recorded as a hint, not treated as standalone WTP proof.
- Irrelevant or hype-only crawler pages are visible as `negative_signal` and do
  not support gates.
- X/Twitter results are lower-confidence corroboration only. They can be
  matched and rendered, but they do not satisfy gates by themselves. Trend
  chatter without pain, workaround, or WTP content is shown as
  `negative_signal`.
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
RVE-3 wires the existing SERP source boundary into this contract: source config
supports `cache_only` and `dry_run`, missing live credentials surface as
`credential_limited`, SERP `search_query` provenance is persisted through
SQLite, and Matched External Evidence lines show the query that produced each
matched item.

RVE-4 wires the Reddit/forum complaint boundary into the same contract. Reddit
posts and comments capture complaint text, public URL, subreddit/forum label,
created date, score/comment metadata, privacy-preserving author hash for
comments, and search-query provenance. Cache-only and dry-run modes bypass live
credential requirements, missing live credentials surface as
`credential_limited`, rate-limit state surfaces as `rate_limited`, repeated
complaints and manual workaround mentions are classified separately, and
adjacent-pain Reddit/forum results remain external research context only.

RVE-5 wires the competitor/workaround crawler boundary as `crawl4ai`.
Fixture/cache mode records landing URL, title, positioning, pricing/WTP hints,
target ICP, page kind (`competitor`, `workaround`, `integration`,
`irrelevant`), query provenance, and bounded source metadata. Live mode only
fetches explicitly configured URLs under allowed-domain and page-count limits.
Competitor/integration evidence is decision-grade only when tied to the same
candidate and target ICP; irrelevant pages are shown as negative evidence.

RVE-6 wires X/Twitter corroboration as source type `x`. It is disabled by
default in the weekly source config, supports cache-only and dry-run operation,
surfaces missing credentials and rate limits in `validation_adapter_status`,
hashes author IDs, marks every matched X item as `lower_confidence` and
`corroboration_required`, and prevents X results from satisfying gates. Broad
trend chatter is classified as `negative_signal`.

RVE-7 should improve the Weekly Brief and Radar validation surface for these
adapter states.
