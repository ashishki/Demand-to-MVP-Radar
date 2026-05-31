# Entropy Core And Gensyn Integration

Status: implemented local proof receipt; Core runtime not adopted
Last updated: 2026-05-31

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

Default level: evidence-lookup compatible for weekly report receipts.

Local artifacts:

- `weekly_report_receipt` implemented in `demand_mvp_radar/proof.py`
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

Implemented now:

- `build_weekly_report_proof_receipt(...)` hashes the generated report content,
  records the report artifact ref, and maps every cited evidence packet into a
  Core-compatible evidence ref.
- Scheduled `run` reports and `mvp-of-week` reports persist
  `<report>.receipt.json` next to the generated Markdown artifact.
- Receipts fail validation when a report has no cited evidence.
- `tests/test_proof_receipts.py` covers the report hash, evidence refs,
  receipt hash, and missing-evidence rejection.

Next implementation tasks:

1. Keep source ranking, opportunity selection, and report wording product-local.
2. Add source-trust receipt rows that Core-style lookup can verify
   deterministically.
3. Use schema compatibility before changing receipt/report schema versions.
4. Route unsupported or weak evidence to `needs_more_evidence`, not to a
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
