# Operator Workflow Contract

Version: 1.0
Date: 2026-05-20
Status: Active personal operating contract

---

## Purpose

Demand-to-MVP Radar exists first to help the operator choose what to build next from recurring market evidence. A weekly report is worth reading only when it turns scattered personal research, public signals, and prior decisions into a small set of source-backed opportunities that can be accepted, rejected, revisited, or sent back for more evidence.

This document defines the personal workflow contract for Phase 6. Later source adapters, dossiers, and review commands must trace back to this contract.

---

## Personal Pain

The operator currently sees useful demand signals across Telegram research, saved links, search results, product listings, competitor pages, and personal notes. The pain is not a lack of ideas. The pain is that evidence is scattered, repeats are hard to recognize, and attractive ideas can feel convincing before there is enough visible demand to justify building.

The system must reduce weekly review time without hiding evidence quality. It advises the operator; it does not own the final product decision.

---

## Weekly Inputs

The weekly run may use only configured, operator-approved inputs:

- sanitized `telegram-research-agent` exports or reports
- operator notes intentionally placed in the configured data directory
- saved URL snapshots and public page text
- saved SERP snapshots
- saved store or marketplace listing metadata
- prior generated briefs
- append-only operator decision history

Raw private exports, local databases, credentials, unsanitized notes, and generated private reports remain outside git. Paid, credentialed, scraped, or externally published sources require human approval before use.

---

## Weekly Outputs

The weekly run should produce:

- a top 5 opportunity report ranked by deterministic score
- cited evidence for every material claim
- score components and threshold reasons
- missing-evidence reasons when support is weak
- prior decision state for repeated or revisited opportunities
- one recommended operator decision for each opportunity
- run metadata that shows source counts, duplicate counts, stale index status, and report path

The output must make weak evidence visible. If an opportunity lacks adequate independent, fresh, or trustworthy support, the system should return `needs_more_evidence` or an `insufficient_evidence` reason instead of a confident recommendation.

---

## Review Time Target

The operator should be able to review the weekly top 5 in under 15 minutes.

That target means each opportunity must be inspectable without reopening every raw source. A useful report shows what the pain is, who feels it, why now, what evidence supports it, what evidence is missing, why it might be wrong, and how prior operator decisions affect the recommendation.

---

## Decision Taxonomy

Every reviewed opportunity receives exactly one human-owned decision:

| Decision | Meaning | Required rationale |
|----------|---------|--------------------|
| `build` | Strong enough to turn into a small validation or MVP experiment. | Why the evidence, audience, distribution path, and build scope justify action now. |
| `reject` | Not worth pursuing on current evidence. | The dominant reason, such as weak demand, poor fit, poor distribution, or too much competition. |
| `revisit` | Plausible, but not ready now. | What future signal or time window would make it worth reviewing again. |
| `needs_more_evidence` | The idea may be interesting but support is inadequate. | The missing source type, source count, freshness, or competitor evidence. |
| `already_exists` | The opportunity is mostly covered by strong existing products. | Which competitor shape makes a new MVP unattractive. |
| `not_my_icp` | Demand may exist, but not from the operator's target customer profile. | Which audience mismatch matters. |
| `too_hard_to_distribute` | Building is feasible, but reaching users is unlikely for the operator. | Which channel or trust barrier blocks distribution. |

Only the human operator records the final decision. The system may recommend a decision, but it must preserve the operator rationale and report path in decision memory.

---

## Portfolio Fit Guidance

Every decision-grade dossier in the solo evidence loop should include a
portfolio fit label and a short reason. The label keeps the weekly showcase
focused on the operator's current portfolio instead of letting attractive but
off-strategy ideas crowd out near-term work.

| Portfolio fit category | Use when | Showcase priority |
|------------------------|----------|-------------------|
| `lead_response_sla` | The opportunity strengthens Lead Response SLA Agent or a related response-time workflow. | primary |
| `workflow_discovery` | The opportunity strengthens Workflow-to-Agent Studio or workflow discovery/automation mapping. | primary |
| `ai_rollout_training` | The opportunity supports AI rollout training, adoption enablement, or team workflow education. | secondary |
| `trading_research_reports` | The opportunity supports trading research report workflows without changing the risk boundary. | secondary |
| `cross_project` | The opportunity can become a handoff pack for more than one current portfolio project. | primary or secondary |
| `out_of_scope` | The opportunity may be attractive but does not fit the current showcase, ICP, distribution path, or approval boundary. | off_strategy |

Review rule: an `out_of_scope` opportunity should be rejected for the current
showcase unless the operator deliberately changes the portfolio strategy. A
primary-fit label does not automatically justify `build`; it only means the
opportunity is allowed to compete for deeper evidence review.

---

## Adoption Failure Conditions

A weekly report is not worth reading when any of these conditions dominate:

- it contains generic ideas that could have been produced without source evidence
- it recommends `build` without cited source support
- it hides missing evidence or stale evidence
- it repeats recently rejected ideas without a meaningful new evidence delta
- it ranks opportunities mostly because one noisy source produced many similar records
- it requires more than 15 minutes to inspect the top 5
- it mixes private notes, Telegram exports, or credentials into committed files
- it cannot explain why an opportunity was ranked above another
- it omits competitor shape, distribution risk, or "why this may be wrong" for top opportunities
- it fails to preserve the operator's prior decision and rationale
- it lets off-strategy ideas displace current portfolio opportunities without a recorded portfolio-fit reason

If these conditions appear repeatedly, the next implementation work should improve source quality, retrieval gates, scoring reasons, or report structure before adding more automation.

---

## Privacy Boundaries

### Telegram Exports

Telegram-derived data is private by default. The system may ingest sanitized exports from `telegram-research-agent`, but raw exports and channel-specific private context must stay in configured local data directories excluded from git. Imported records should preserve source IDs or links only when those identifiers are safe to store locally, and logs must not expose private author handles, private channel names, or raw message text.

### Operator Notes

Operator notes may include sensitive ideas, personal context, private URLs, and unreleased product plans. Notes are used only when the operator places them in the configured input location. Raw notes, unsanitized excerpts, and generated private reports must not be committed. Reports may quote notes only when the output stays local and the quote is needed for the operator's own decision.

### Credentials

Credentials, API keys, tokens, cookies, paid-source access, and account identifiers never appear in source code, docs examples, comments, fixtures, logs, reports, or committed config. They must come from environment variables or ignored local secrets files. Enabling credentialed sources requires explicit human approval.

---

## Operating Constraints

- The system remains local-first and single-operator in v1.
- Source provenance is mandatory for every opportunity claim.
- Scoring, thresholds, duplicate suppression, and decision-memory effects remain deterministic.
- LLM extraction and synthesis must be schema-bounded and source-grounded.
- Paid sources, credentialed sources, external publishing, outreach, repository creation, and scoring-weight changes require human approval.
- Weekly reports must surface `insufficient_evidence` rather than inventing confidence.

---

## Exit Criteria For Later Features

Later implementation is aligned with this contract only if it helps the operator:

- review the top 5 faster
- trust evidence quality more
- see why an opportunity is weak or strong
- remember prior decisions
- select one opportunity for a 7 to 14 day validation experiment

Features that do not improve those outcomes should wait.
