# Demand-to-MVP Radar - Project Plan

Status: active live product
Role: evidence-backed weekly market/opportunity radar
Priority: P0

## Strategic Role

Demand-to-MVP Radar is one of the portfolio's strongest product bets because it
has a real operating loop on the VPS and will produce weekly reports.

The product should remain advisory-only: it does not choose what to build, but it
compresses noisy demand signals into evidence-backed MVP candidates.

## Near-Term Roadmap

### P0 - First Report Review

- Review the first VPS-generated weekly report.
- Mark each section:
  - useful
  - noisy
  - missing evidence
  - too broad
  - actionable
- Capture false positives and weak sources.

### P0 - Report Quality Loop

- Add sanitized example report.
- Persist a `weekly_report_receipt` for every scheduled report using
  `demand_mvp_radar/proof.py`.
- Add `docs/report_eval.md` or extend retrieval eval for:
  - useful signal rate
  - evidence quality
  - duplicate/noise rate
  - source diversity
  - recommendation clarity
- Add weekly operator notes.

### P1 - Source Trust

- Improve source scoring.
- Track repeated signals across sources.
- Separate "interesting" from "build-worthy".
- Add rejection reasons.
- Add `source_trust_receipt` after weekly report receipts are persisted.

### P1 - Telegram/Channel Integration

- Reuse patterns from Telegram Research Agent.
- Add source classes for channel-derived demand signals only after evidence
  quality is acceptable.
- Use `docs/entropy_core_gensyn_integration.md` for report receipts,
  source-trust receipts, and bounded multi-lens review.

### P2 - Productization

- Create private beta report format.
- Test manual paid report workflow before SaaS UI.
- Add lightweight dashboard only when reports prove recurring value.

## AI-Development Tasks

- Use AI for report synthesis and clustering, but keep citations mandatory.
- Use deterministic checks for source existence and duplicate signals.
- Require evidence links for every `build` recommendation.
- Require a proof receipt before treating a weekly report as decision-grade.
- Use reviewer pass for weekly report quality until stable.

## Stop Conditions

- Stop any recommendation that lacks evidence.
- Do not automate outreach.
- Do not build UI before report value is proven.
