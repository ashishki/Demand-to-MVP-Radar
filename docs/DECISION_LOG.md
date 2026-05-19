# Decision Log

Status: retrieval index, not authority. Canonical decisions live in `docs/ARCHITECTURE.md`, ADRs, `docs/IMPLEMENTATION_CONTRACT.md`, and `docs/spec.md`.

| ID | Date | Decision | Canonical Source | Rationale | Superseded By |
|----|------|----------|------------------|-----------|---------------|
| D-001 | 2026-05-19 | Use a CLI-first local Python batch system for v1. | `docs/ARCHITECTURE.md#solution-shape` | The first workflow is weekly operator review; a web UI is premature before report quality is proven. | n/a |
| D-002 | 2026-05-19 | Use Standard governance, not Lean or Strict. | `docs/ARCHITECTURE.md#solution-shape` | The blast radius is low, but recurring evidence quality, provenance, and evaluation discipline matter. | n/a |
| D-003 | 2026-05-19 | Runtime tier is T1 bounded worker. | `docs/ARCHITECTURE.md#runtime-and-isolation-model` | The system needs normal network/file access but no privileged autonomous runtime or shell mutation. | n/a |
| D-004 | 2026-05-19 | RAG profile is ON with text-only retrieval. | `docs/ARCHITECTURE.md#profile-rag` | Prior evidence, rejected ideas, source snippets, and decision history must be retrieved with citations. | n/a |
| D-005 | 2026-05-19 | Tool-Use profile is ON. | `docs/ARCHITECTURE.md#profile-tool-use` | Bounded LLM paths may call read/report tools and must be schema-validated and audited. | n/a |
| D-006 | 2026-05-19 | Agentic and Planning profiles are OFF for v1. | `docs/ARCHITECTURE.md#capability-profiles` | The product runs a fixed workflow and produces briefs, not autonomous loops or execution plans. | n/a |
| D-007 | 2026-05-19 | SQLite WAL is the v1 persistence layer. | `docs/ARCHITECTURE.md#tech-stack` | Local-first single-operator usage does not justify PostgreSQL yet. | n/a |
| D-008 | 2026-05-19 | Scoring and recommendations thresholds are deterministic. | `docs/IMPLEMENTATION_CONTRACT.md#deterministic-ownership-of-scores` | Weekly rankings must be comparable and auditable. | n/a |

## Decision Log Rules

- Add a row when implementation changes architecture, runtime, active profiles, scoring policy, retrieval schema, tool schema, source trust policy, human approval boundary, or model strategy.
- Link each row to a canonical source.
- Do not use this file to override canonical docs.
