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

## Entropy Core Use

Default level: receipt-compatible.

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
  use_level: receipt_compatible
  runtime_dependency: false
```

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
