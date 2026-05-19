# Audit Index - Demand-to-MVP Radar

Append-only. One row per review cycle.

---

## Review Schedule

| Cycle | Phase | Date | Scope | Stop-Ship | P0 | P1 | P2 |
|-------|-------|------|-------|-----------|----|----|-----|
| bootstrap | Phase 1 | 2026-05-19 | Phase 1 governance package generated; validation not yet run | No | 0 | 0 | 0 |
| phase1-validation | Phase 1 | 2026-05-19 | Phase 1 artifact validation before T01 | No | 0 | 0 | 0 |

---

## Archive

| Cycle | File | Phase | Health |
|-------|------|-------|--------|
| bootstrap | docs/audit/AUDIT_INDEX.md | Phase 1 | Initialized |
| phase1-validation | docs/audit/PHASE1_AUDIT.md | Phase 1 | PASS |

---

## Notes

- Phase 1 validation should write `docs/audit/PHASE1_AUDIT.md` before T01 starts.
- Optional simplification passes use a separate row prefix (`SIMP-N`) and live in `docs/audit/SIMPLIFICATION_REPORT.md`. They do not interleave with deep review cycles in this index.
