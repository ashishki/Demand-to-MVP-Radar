# ARCH_REPORT - Cycle 18
_Date: 2026-05-23_

## Component Verdicts

| Component | Verdict | Note |
|-----------|---------|------|
| Solo evidence research protocol | PASS | Public-source rules match source approval boundaries and do not add credentialed/private collection. |
| Solo evidence ledger | PASS | Records evidence/readiness state without pretending fixture or showcase artifacts satisfy the four-run gate. |
| Portfolio showcase report | PASS | Uses public citations and explicit `inference` / `insufficient_evidence` labels; no build approval. |
| Lead Response SLA handoff | PASS | Keeps scope local/reporting-only and preserves human approval boundaries. |
| Solo readiness review | PASS | Correctly blocks private beta and hosted/SaaS under existing ADR gates. |
| Portfolio taxonomy model | PASS | Optional dossier metadata; deterministic validation only. |

## Contract Compliance

| Rule | Verdict | Note |
|------|---------|------|
| Source provenance is mandatory | PASS | T62/T63 artifacts include source registers/links and captured dates. |
| Deterministic ownership of scores | PASS | Phase 17 does not alter scoring; portfolio fit guidance is deterministic and advisory. |
| Human-owned decisions | PASS | No `build` decision is recorded; T64 explicitly blocks beta/hosted work. |
| Local-first data hygiene | PASS | Artifacts are public-safe; no raw private exports, credentials, databases, or generated private reports were introduced. |
| Runtime tier guardrails | PASS | No runtime mutation, privileged actions, hosted surface, or long-lived worker behavior added. |
| RAG / Tool-Use gates | PASS | No retrieval semantics or tool schema behavior changed. |

## ADR Compliance

| ADR | Verdict | Note |
|-----|---------|------|
| ADR_HOSTED_SAAS_DECISION.md | PASS | T64 honours the local-first default and keeps hosted/SaaS blocked until evidence gates are complete. |
| docs/adr/README.md | N/A | Process guidance only. |

## Architecture Findings

### ARCH-1 [P2] - Architecture docs should mention Phase 17 public research/readiness artifacts
Symptom: Phase 17 added durable artifacts for public research protocol, solo evidence ledger, showcase report, handoff pack, and readiness review, but `docs/ARCHITECTURE.md` does not yet mention them in component/file-layout documentation.

Evidence: `docs/audit/META_ANALYSIS.md`

Root cause: Phase 17 focused on operating artifacts and deferred architecture doc refresh to the phase-boundary doc update.

Impact: Future agents may miss the canonical location of Phase 17 evidence-loop artifacts unless they read `docs/CODEX_PROMPT.md` or `docs/EVIDENCE_INDEX.md`.

Fix: During Step 6.5 doc update, add a concise Phase 17 artifact row/notes to `docs/ARCHITECTURE.md` component/file-layout sections.

## Right-Sizing / Runtime Checks

| Check | Verdict | Note |
|-------|---------|------|
| Solution shape still appropriate | PASS | Hybrid deterministic workflow remains appropriate; no autonomous product selection. |
| Deterministic-owned areas remain deterministic | PASS | Portfolio fit and readiness verdicts are deterministic docs/model validation, not LLM-owned scoring. |
| Runtime tier unchanged / justified | PASS | Still T1 local-first; no hosted, tenant, credential, or infra behavior added. |
| Human approval boundaries still valid | PASS | Handoff and readiness review explicitly block outreach, CRM mutation, public publishing, private beta, and hosted work. |
| Minimum viable control surface still proportionate | PASS | Added evidence-loop artifacts without expanding runtime control surface. |

## Retrieval Architecture Checks

| Check | Verdict | Note |
|-------|---------|------|
| Ingestion / query-time separation | PASS | No changes this cycle. |
| insufficient_evidence path defined | PASS | Existing architecture/spec define it; Phase 17 artifacts use the label for weak claims. |
| Corpus isolation explicit | PASS | No multi-corpus or hosted exposure added. |
| Evidence/citation contract defined | PASS | Existing evidence packet contract remains; Phase 17 adds public source register rows for manual research artifacts. |
| Freshness / max-index-age policy | PASS | No retrieval policy changes. |
| Index schema versioning | PASS | No index schema changes. |
| Retrieval mode and modality scope explicit | PASS | Text-only remains unchanged. |
| Multimodal justification / fallback documented | N/A | Multimodal remains out of scope. |
| Retrieval observability expectations | PASS | No observability behavior changed. |

## Tool-Use Architecture Checks

| Check | Verdict | Note |
|-------|---------|------|
| Tool Catalog complete (side effects, idempotency, permissions) | PASS | No LLM-callable tools added or changed. |
| Unsafe-Action Policy covers all destructive tools | PASS | Phase 17 adds no destructive tools and repeats approval boundaries. |
| Confirmation steps are distinct code paths | N/A | No destructive tool was added. |
| Tool schemas versioned and validated at generation time | PASS | No schema change. |
| Permission checked at each tool boundary | PASS | No tool boundary change. |

## Doc Patches Needed

| File | Section | Change |
|------|---------|--------|
| `docs/ARCHITECTURE.md` | Component Table / File Layout | Add concise references to `docs/open_source_research_protocol.md`, `docs/SOLO_EVIDENCE_LEDGER.md`, `reports/showcase/`, `docs/handoffs/`, and `docs/audit/SOLO_EVIDENCE_READINESS_REVIEW.md`. |

ARCH_REPORT.md written. Run PROMPT_2_CODE.md.
