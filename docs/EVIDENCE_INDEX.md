# Evidence Index

Status: retrieval index, not authority. Evidence rows point to canonical artifacts or future generated outputs.

| ID | Date | Evidence Type | Artifact | Scope | Notes |
|----|------|---------------|----------|-------|-------|
| E-001 | 2026-05-19 | Project brief | `templates/PROJECT_BRIEF.md` | Problem fit, users, scope, AI boundaries, data, integrations, constraints, success metrics | Input used to generate Phase 1 architecture package. |
| E-002 | 2026-05-19 | Architecture package | `docs/ARCHITECTURE.md` | Solution shape, profiles, runtime, RAG/tool design | Canonical system design. |
| E-003 | 2026-05-19 | Task graph | `docs/tasks.md` | Full implementation sequence and acceptance criteria | Implementation authority. |
| E-004 | 2026-05-19 | Retrieval evaluation plan | `docs/retrieval_eval.md` | RAG baseline, query set, regression criteria | Must be updated by RAG-tagged tasks. |
| E-005 | 2026-05-19 | Tool-use evaluation plan | `docs/tool_eval.md` | Tool schema, permission, audit, retry checks | Must be updated by Tool-Use-tagged tasks. |

## Evidence Index Rules

- Add a row when a task produces retrieval metrics, tool metrics, source-quality findings, audit reports, or decision-grade opportunity examples.
- Every row must point to an actual artifact.
- This file helps agents find proof; it does not replace the underlying artifact.
