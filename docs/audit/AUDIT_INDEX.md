# Audit Index - Demand-to-MVP Radar

Append-only. One row per review cycle.

---

## Review Schedule

| Cycle | Phase | Date | Scope | Stop-Ship | P0 | P1 | P2 |
|-------|-------|------|-------|-----------|----|----|-----|
| bootstrap | Phase 1 | 2026-05-19 | Phase 1 governance package generated; validation not yet run | No | 0 | 0 | 0 |
| phase1-validation | Phase 1 | 2026-05-19 | Phase 1 artifact validation before T01 | No | 0 | 0 | 0 |
| cycle-1 | Phase 1 | 2026-05-19 | Phase 1 implementation deep review after T01-T04 | No | 0 | 0 | 0 |
| cycle-2 | Phase 2 | 2026-05-19 | Targeted Tool-Use deep review after T06 `tool:schema` | No | 0 | 0 | 0 |
| cycle-3 | Phase 2 | 2026-05-19 | Phase 2 implementation deep review after T05-T08 | No | 0 | 0 | 0 |
| cycle-4 | Phase 3 | 2026-05-19 | Targeted RAG deep review after T09 `rag:ingestion` | No | 0 | 0 | 0 |
| cycle-5 | Phase 3 | 2026-05-19 | Targeted RAG deep review after T10 `rag:query` | No | 0 | 0 | 0 |
| cycle-6 | Phase 3 | 2026-05-19 | Phase 3 implementation deep review after T09-T11 | No | 0 | 0 | 0 |
| cycle-7 | Phase 4 | 2026-05-19 | Phase 4 implementation deep review after T12-T14 | No | 0 | 0 | 0 |
| cycle-8 | Phase 5 | 2026-05-19 | Targeted RAG and Tool-Use deep review after T18 `rag:query tool:call` | No | 0 | 0 | 0 |
| cycle-9 | Phase 5 | 2026-05-19 | Phase 5 final implementation deep review after T15-T18 | No | 0 | 0 | 0 |

---

## Archive

| Cycle | File | Phase | Health |
|-------|------|-------|--------|
| bootstrap | docs/audit/AUDIT_INDEX.md | Phase 1 | Initialized |
| phase1-validation | docs/audit/PHASE1_AUDIT.md | Phase 1 | PASS |
| cycle-1 | docs/archive/PHASE1_REVIEW.md | Phase 1 | PASS |
| cycle-2 | docs/archive/CYCLE2_T06_REVIEW.md | Phase 2 | PASS |
| cycle-3 | docs/archive/PHASE2_REVIEW.md | Phase 2 | PASS |
| cycle-4 | docs/archive/CYCLE4_T09_REVIEW.md | Phase 3 | PASS |
| cycle-5 | docs/archive/CYCLE5_T10_REVIEW.md | Phase 3 | PASS |
| cycle-6 | docs/archive/PHASE3_REVIEW.md | Phase 3 | PASS |
| cycle-7 | docs/archive/PHASE4_REVIEW.md | Phase 4 | PASS |
| cycle-8 | docs/archive/CYCLE8_T18_REVIEW.md | Phase 5 | PASS |
| cycle-9 | docs/archive/PHASE5_REVIEW.md | Phase 5 | PASS |

---

## Notes

- Phase 1 validation should write `docs/audit/PHASE1_AUDIT.md` before T01 starts.
- Optional simplification passes use a separate row prefix (`SIMP-N`) and live in `docs/audit/SIMPLIFICATION_REPORT.md`. They do not interleave with deep review cycles in this index.
