# Cognition Manifest - Demand-to-MVP Radar

---
artifact_kind: retrieval_manifest
project: demand-to-mvp-radar
source_repo: Demand-to-MVP-Radar
status: active
canonical: false
generated: false
tags: [market-research, rag, tool-use, evidence]
---

Version: 1.0
Last updated: 2026-05-25

## Purpose

Repo-local map for source-grounded market evidence, decision memory, retrieval/tool evals, and production-readiness continuity.

## Authority Rules

- Canonical repo artifacts win over this manifest.
- Generated indexes, Obsidian notes, and context packets are convenience surfaces only.
- No opportunity, source trust, or production decision is authoritative unless backed by canonical evidence.

## Project Identity

| Field | Value |
|-------|-------|
| Primary shape | Local deterministic batch workflow with bounded LLM synthesis |
| Governance level | Standard |
| Runtime tier | T0/T1 local |
| Active profiles | RAG, Tool-Use, evidence/decision memory |

## Canonical Truth

| Surface | Path | Notes |
|---------|------|-------|
| Architecture | `docs/ARCHITECTURE.md` | Pipeline and boundaries |
| Contract | `docs/IMPLEMENTATION_CONTRACT.md` | Implementation rules |
| Task graph | `docs/tasks.md` | Execution history and future work |
| Session state | `docs/CODEX_PROMPT.md` | Current status and findings |
| Decisions | `docs/DECISION_LOG.md` | Decision memory |
| Journal | `docs/IMPLEMENTATION_JOURNAL.md` | Handoff continuity |
| Evidence | `docs/EVIDENCE_INDEX.md`, `docs/SOLO_EVIDENCE_LEDGER.md` | Proof and solo-run evidence |
| Retrieval eval | `docs/retrieval_eval.md`, `scripts/eval_retrieval.py` | Retrieval quality |
| Tool eval | `docs/tool_eval.md`, `scripts/eval_tools.py` | Tool safety and schema memory |
| Source catalog | `docs/SOURCE_CATALOG.md` | Source trust and scope |
| Demand source map | `docs/DEMAND_SOURCE_MAP.md` | Demand surfaces and pain/source heuristics |
| Audits | `docs/audit/`, `docs/archive/` | Findings and review history |

## Retrieval Scopes

| Scope | Start here | Include next |
|-------|------------|--------------|
| Opportunity decision | `docs/DECISION_LOG.md`, `docs/SOLO_EVIDENCE_LEDGER.md` | source catalog, dossier/report evidence |
| Retrieval regression | `docs/retrieval_eval.md` | evidence index, fixtures, recent tasks |
| Tool-use change | `docs/tool_eval.md` | tool schemas, audit rows, decision log |
| Production readiness | `docs/audit/PRODUCTION_READINESS_REVIEW.md` | backup/recovery, source health, evidence ledger |
| Reviewer packet | task ACs and contract | prior review for same boundary, eval artifacts |

## Known Gaps

| Gap | Impact | Migration step |
|-----|--------|----------------|
| Active dirty work exists | Existing files may change outside this migration | Keep cognition migration additive and avoid touching modified files |
| Context packets are not standardized | Regression investigations rely on manual assembly | Generate packets for source trust, retrieval, and tool-use regressions only |

## Generated Artifacts

| Artifact | Path | Policy |
|----------|------|--------|
| Cognition index | `generated/cognition/index.json` | Optional generated artifact |
| Context packets | `docs/context-packets/` | Commit only major review/regression packets |
