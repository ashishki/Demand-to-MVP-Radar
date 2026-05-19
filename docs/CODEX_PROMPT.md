# CODEX_PROMPT.md

Version: 1.0
Date: 2026-05-19
Phase: 1

This file is the session handoff and state authority for Codex implementation roles.

---

## Execution Model

- Active executor: current Codex session only.
- Claude Code layer: not used.
- Nested Codex subprocesses: forbidden. Do not call `codex exec` from inside Codex.
- Orchestration, implementation, review, consolidation, and doc updates are performed sequentially in the same Codex session using local tools.

---

## Current State

- Phase: 1
- Baseline: 0 passing tests (pre-implementation)
- Ruff: not yet configured
- Last CI: not yet configured
- Last updated: 2026-05-19
- Session tokens (approx): not yet tracked
- Cumulative phase tokens (approx): not yet tracked

---

## Continuity Pointers

- Decision log: `docs/DECISION_LOG.md`
- Implementation journal: `docs/IMPLEMENTATION_JOURNAL.md`
- Evidence index: `docs/EVIDENCE_INDEX.md`
- Implementation reference map: `docs/IMPLEMENTATION_REFERENCE_MAP.md`
- Retrieval evaluation: `docs/retrieval_eval.md`
- Tool-use evaluation: `docs/tool_eval.md`
- Task-scoped context: read `Context-Refs` in `docs/tasks.md` before broad searching.

---

## Next Task

T01: Project Skeleton

Before implementation, the orchestrator should hand Codex a narrow task digest inline:

- assignment and acceptance criteria
- file scope
- applicable contract rules only
- dependency facts from prior tasks
- immediate pipeline or flow if one matters

Only send Codex to full documents when the task is architecture-shaping, security-sensitive, ambiguous, changes retrieval/tool semantics, or is marked `Execution-Mode: heavy`.

---

## Fix Queue

empty

---

## Open Findings

none

---

## Completed Tasks

none

---

## Phase History

none

---

## Summary State

Bootstrap package generated on 2026-05-19. Implementation has not started. The first implementation task is T01. Dream Motif Interpreter is available as a RAG implementation pattern reference through `docs/IMPLEMENTATION_REFERENCE_MAP.md`. The active workflow is Codex-only: no Claude Code layer and no nested `codex exec` calls.

---

## Profile State: RAG

- RAG Status: ON
- Active corpora: local single-operator text evidence corpus
- Retrieval baseline: not yet measured
- Open retrieval findings: none
- Index schema version: retrieval-index-v1
- Pending reindex actions: none
- Retrieval-related next tasks: T09, T10, T18
- Retrieval-driven tasks: none

---

## Tool-Use State

- Tool-Use Profile: ON
- Registered tool schemas: planned in T06
- Unsafe-action guardrails: v1 has no destructive external tools; credentialed sources, public publishing, outreach, repository creation, scoring-weight changes, and deletion require human approval.
- Open tool findings: none

---

## Agentic State

- Agentic Profile: OFF
- Active agent roles: n/a
- Loop termination contract version: n/a
- Cross-iteration state mechanism: n/a
- Open agent findings: none

---

## Planning State

- Planning Profile: OFF
- Plan schema version: n/a
- Plan validation method: n/a
- Open plan findings: none

---

## Compliance State

- Compliance Status: OFF
- Active frameworks: n/a
- Controls implemented: n/a
- Controls partial: n/a
- Controls not started: n/a
- Evidence artifact: n/a
- Open compliance findings: none

---

## NFR Baseline

- API p99 latency: not yet measured
- Error rate: not yet measured
- Throughput: not yet measured
- Last measured: n/a
- NFR regression open: No

---

## Evaluation State

### Last Evaluation

- Profile: n/a
- Task: n/a
- Date: n/a
- Eval Source: n/a
- Metric(s): n/a
- Score: n/a
- Baseline: n/a
- Delta: n/a
- Regression: n/a

### Regression Thresholds

- Retrieval hit@3 drop greater than 15 percent vs baseline: P0
- Retrieval hit@3 drop greater than 5 percent vs baseline: P1
- Citation precision drop greater than 10 percent vs baseline: P1
- No-answer accuracy below 0.90 after baseline: P1
- Tool schema validation pass rate below 1.00 after baseline: P1
- Tool audit field completeness below 1.00 after baseline: P1

### Open Evaluation Issues

none

### Evaluation History

none

---

## Instructions for Codex

1. Read `docs/IMPLEMENTATION_CONTRACT.md` before starting any task.
2. Read the full task definition in `docs/tasks.md` before writing code.
3. Read all Depends-On tasks to understand interface contracts.
4. Read task `Context-Refs` and relevant continuity artifacts when the task depends on prior decisions, proof, retrieval semantics, tool semantics, or findings.
5. Execute work directly in the current Codex session; do not call `codex exec` or spawn a nested Codex process.
6. Run `pytest -q` to capture the current baseline before making changes.
7. Run `ruff check` before implementation once ruff is configured. If ruff is not configured yet, implement T01/T02 first and record that state.
8. Write tests before or alongside implementation. Every acceptance criterion has a passing test.
9. Update this file at every phase boundary and after capability evaluation tasks.
10. Commit with format `type(scope): description`; one logical change per commit.
11. When done, return `IMPLEMENTATION_RESULT: DONE` with baseline before and after, files changed, tests added, and AC status.
12. When blocked, return `IMPLEMENTATION_RESULT: BLOCKED` with the exact blocker and the smallest next action needed.

---

## Compaction Protocol

- Trigger compaction when Completed Tasks exceeds 20 entries or Phase History exceeds 5 phase summaries.
- Keep Summary State current before archiving older detail.
- Do not delete audit reports, ADRs, evaluation artifacts, or task definitions.
