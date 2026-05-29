# Report Quality Evaluation

Status: active
Date: 2026-05-29
Scope: weekly Radar and Telegram-bridge report usefulness

This artifact tracks whether weekly reports are becoming more useful to the
operator. It is an operator-quality evaluation, not commercial proof.

Scores below only describe report usefulness, evidence hygiene, and decision
clarity for the current operator workflow. They must not be used to claim market
validation, revenue likelihood, product-market fit, or private beta readiness.

## Evaluation Method

Evaluate each weekly report after review. Count only report sections or
opportunities that are visible to the operator in the artifact under review.

Required review inputs:

- report path and run ID;
- source-mix summary when available;
- source errors and skipped sources when available;
- section-level review labels: useful, noisy, missing evidence, too broad, and
  actionable;
- final operator decision, if one exists.

If a source field is unavailable, mark it `missing` instead of estimating it.

## Metrics

| Metric | Scale | Scoring rule | What it means | What it does not mean |
|---|---:|---|---|---|
| Useful signal rate | 0.00-1.00 | `useful_sections / reviewed_sections`; a section is useful when it teaches the operator something specific enough to change a follow-up, ranking, or rejection. | Measures how much of the report deserved operator attention. | Does not prove the underlying idea has demand. |
| Evidence quality | 0-5 | 0 = no citations; 1 = mostly Telegram/private or uncited claims; 2 = cited but single-family evidence; 3 = cited plus some external corroboration; 4 = cited, fresh, multi-source, with missing evidence stated; 5 = 4 plus competitor/workaround and countercase evidence. | Measures whether claims are source-grounded and inspectable. | Does not prove willingness to pay or market size. |
| Duplicate/noise rate | 0.00-1.00 | `(noisy_sections + duplicate_sections + too_broad_sections) / reviewed_sections`; count repeated variants of the same weak signal as duplicates. Lower is better. | Measures review friction from broad, repeated, or low-action signal. | Does not mean a low-noise report is commercially strong. |
| Source diversity | 0-5 | 0 = no visible sources; 1 = one source family; 2 = two families with one dominant source; 3 = at least three families; 4 = at least three independent external families plus Telegram/owned sources separated; 5 = 4 plus source errors/skips disclosed. | Measures whether the report avoids one-source overconfidence. | Does not imply sources are representative of the market. |
| Recommendation clarity | 0-5 | 0 = no recommendation; 1 = generic recommendation; 2 = recommendation exists but missing gate reason; 3 = build/reject/revisit/needs_more_evidence with reason; 4 = 3 plus missing evidence and next action; 5 = 4 plus Decision Gate fields and operator-fit reason. | Measures whether the operator can act or reject quickly. | Does not authorize build, outreach, publishing, paid sources, or hosted/SaaS work. |

## Decision Gate Fields

Every scored weekly Radar report should expose these fields before any strong
recommendation:

| Field | Required value |
|---|---|
| Telegram seed evidence | integer count or `missing` |
| External evidence | integer count or `missing` |
| External source types | list or `missing` |
| Repeated signal count | integer count or `missing` |
| Missing evidence | list, empty list, or `missing` |
| Recommendation allowed | `yes` or `no` |
| Reason | `source_mix_gate`, `operator_fit_gate`, `insufficient_evidence`, `focused_experiment`, or `missing_gate_fields` |

Telegram-only or single-family reports cannot receive a report-quality verdict
above:

- Evidence quality: 2
- Source diversity: 1
- Recommendation clarity: 3, unless the recommendation is explicitly
  `needs_more_evidence` with a clear next action.

## Evaluation History

| Date | Task/run | Report artifact | Useful signal rate | Evidence quality | Duplicate/noise rate | Source diversity | Recommendation clarity | Verdict | Notes |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| 2026-05-29 | T65 bridge review | `../telegram-research-agent/data/output/digests/2026-W14.md` | 0.67 | 1 | 0.44 | 1 | 2 | seed input only | Useful Telegram intelligence, but not a decision-grade Radar report. Missing external corroboration, source-mix gate, scoring, repeated-signal count, and operator-fit reason. |
| 2026-05-29 | T70 mvp-weekly-2026-W14-radar | `reports/mvp_of_week/mvp-weekly-2026-W14-radar.md` | 0.80 | 2 | 0.40 | 1 | 3 | true Radar artifact; needs public corroboration | First generated Radar `mvp-of-week` artifact from the Telegram weekly digest seed export. Decision Gate is present and blocks build-worthy framing because external evidence is 0, external source types are none, and missing evidence remains competitor/workaround corroboration plus non-Telegram public evidence. |

## Implementation Notes

| Date | Task | Change | Quality impact |
|---|---|---|---|
| 2026-05-29 | T67 | Added deterministic source trust records with evidence count, unique signal count, repeated signal count, evidence density, and rejection reasons. Weekly reports now show Decision Gate, Source Trust And Repeated Signals, Build-Worthy Recommendations, and Interesting Signals sections. | Makes repeated Telegram/source noise visible and separates interesting signals from build-worthy recommendations before operator review. |
| 2026-05-29 | T69-T70 | Added a deterministic Telegram digest-to-seed adapter and generated `mvp-weekly-2026-W14-radar` from `../telegram-research-agent/data/output/digests/2026-W14.json`. | Confirms the Radar weekly report path can consume inspectable Telegram intelligence while keeping Telegram-only ideas outside build-worthy recommendations. |

## Regression Notes

- 2026-05-29: Baseline row is intentionally conservative because the reviewed
  artifact is a Telegram weekly digest, not a full Radar `mvp-of-week` output.
  The next true Radar weekly report should improve evidence quality, source
  diversity, and recommendation clarity before any build-like recommendation is
  trusted.

## Update Rules

- Add one row per reviewed weekly report.
- Keep metric values numeric and reproducible from the reviewed artifact.
- Do not invent missing source counts or decisions.
- Record source gaps as `missing`; do not fill them from memory.
- Treat the evaluation as report-quality evidence only. Product, beta, hosted,
  paid-source, publishing, and outreach decisions still require their own gates.
