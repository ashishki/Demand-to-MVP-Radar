# Entropy Core And Gensyn Integration

Status: planned reference integration
Last updated: 2026-05-29

## Purpose

Demand-to-MVP Radar can use receipt-compatible artifacts for weekly report
quality: which opportunity was recommended, what evidence supported it, which
sources were weak, and what reviewer verdict was assigned.

Gensyn is only a reference for diverse analytical lenses and evaluator/referee
review. The Radar does not adopt Gensyn runtime, training, tokens, or on-chain
coordination.

Before building custom Gensyn-shaped logic, run the Gensyn OSS reuse gate from
`repo://AI_workflow_playbook/docs/entropy_core_and_gensyn_reference_policy.md`.
Check official Gensyn repos first and record whether the result is dependency,
vendored component, adapted code, pattern-only reuse, or rejection.

## Entropy Core Use

Default level: receipt-compatible now; evidence-lookup compatible next.

Planned local artifacts:

- `opportunity_report_receipt`
- `source_trust_receipt`
- `weekly_report_referee_verdict`
- `telegram_signal_bridge_receipt`

Example:

```yaml
type: opportunity_report_receipt
source_project: demand-to-mvp-radar
report_week: 2026-W22
opportunity_id: opp-001
recommendation: revisit
evidence:
  - source_id: src-001
    path: data/sources/example.md
    claim_supported: true
  - source_id: src-002
    path: data/sources/weak.md
    claim_supported: false
verifier:
  method: operator_review
  status: needs_more_evidence
entropy_core:
  use_level: evidence_lookup_compatible_candidate
  runtime_dependency: false
```

## Proof Layer Implementation

The Radar should use Entropy Core as a proof layer for reports, not as a
runtime dependency.

Implementation path:

1. Emit a weekly report receipt with schema id, report artifact refs, evidence
   refs, source trust verdicts, recommendation status, and blocked surfaces.
2. Keep source ranking, opportunity selection, and report wording product-local.
3. Add evidence rows that Core-style lookup can verify deterministically.
4. Use schema compatibility before changing receipt/report schema versions.
5. Route unsupported or weak evidence to `needs_more_evidence`, not to a
   confident recommendation.

Core value here: prevent unsupported weekly recommendations and make it obvious
why a report cannot yet become customer-facing.

## Required Context-Refs

```yaml
Context-Refs:
  - repo://AI_workflow_playbook/docs/entropy_core_and_gensyn_reference_policy.md
  - repo://Entropy_Protocol/docs/ENTROPY_CORE_AND_GENSYN_REFERENCES.md
  - repo://telegram-research-agent/docs/telegram_channel_intelligence.md
```

## Gensyn-Inspired Pattern

Allowed adaptation:

```text
market lens + source-trust lens + competition lens -> referee verdict -> report recommendation
```

This is useful for report review. It must not become autonomous product
selection or automated outreach.

Not adopted: decentralized runtime, tokens, P2P swarm, model training, or
on-chain coordination.
