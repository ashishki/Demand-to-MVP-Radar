# AI Development Pack

Version: 1.0
Date: 2026-05-19
Status: Active

---

## Purpose

This file gives an AI coding agent enough context to continue Demand-to-MVP Radar from the completed fixture-backed MVP into a personal production workflow.

The next work should not broaden the product into a SaaS. It should first produce confident personal artifacts from real operator-owned and low-risk sources.

---

## Current Baseline

- T01-T18 are complete.
- The system has a CLI, SQLite storage, source fixtures, retrieval, insufficient-evidence behavior, clustering, scoring, report generation, decision memory, weekly fixture run, health output, and evaluation baselines.
- RAG is ON.
- Tool-Use is ON.
- Agentic and Planning profiles are OFF.
- The product is local-first and single-operator.

---

## Development Principle

Every feature must improve one of these decisions:

1. What should the operator build now?
2. What should the operator reject?
3. What should the operator revisit when stronger evidence appears?
4. What evidence is missing before a decision is safe?

If a task does not improve one of these decisions, defer it.

---

## Required Document Map

| File | Role |
|------|------|
| `docs/PERSONAL_TO_PRODUCTION_PLAN.md` | Product development phases and exit criteria |
| `docs/SOURCE_CATALOG.md` | Source strategy, access risks, source priority |
| `docs/tasks.md` | Authoritative implementation task graph |
| `docs/CODEX_PROMPT.md` | Current implementation state and next task |
| `docs/ARCHITECTURE.md` | System boundaries, capability profiles, runtime model |
| `docs/spec.md` | Product feature areas and acceptance criteria |
| `docs/IMPLEMENTATION_CONTRACT.md` | Non-negotiable implementation rules |
| `docs/retrieval_eval.md` | RAG evaluation baseline and history |
| `docs/tool_eval.md` | Tool-use evaluation baseline and history |

---

## AI Agent Work Protocol

For every implementation task:

1. Read the task definition in `docs/tasks.md`.
2. Read only the referenced context files unless the task is architecture-shaping.
3. Run the baseline tests before edits when code changes are planned.
4. Add or update tests for every acceptance criterion.
5. Keep source adapters fixture-first; live credentials must not be required in CI.
6. Preserve provenance on every evidence path.
7. Keep scoring deterministic.
8. Keep LLM output schema-bounded.
9. Update eval docs for retrieval/tool changes.
10. Update `docs/CODEX_PROMPT.md` at phase boundaries.

---

## Next Implementation Sequence

### Sequence A - Personal Source Foundation

Implement:

- `T19: Operator Workflow Contract`
- `T20: Source Catalog Config Model`
- `T21: Telegram Research Agent Bridge`
- `T22: Operator Notes Source`
- `T23: Own GitHub Repository Source`

Expected result: the system can ingest non-fixture, operator-owned evidence safely.

### Sequence B - Live Evidence Trust

Implement:

- `T24: Live Evidence Import Command`
- `T25: Source Trust and Freshness Scoring`
- `T26: Live-Like Retrieval Evaluation Fixtures`
- `T27: Evidence Delta Report`

Expected result: the operator can see what evidence changed and whether retrieval support is strong enough.

### Sequence C - Decision-Grade Artifacts

Implement:

- `T28: Opportunity Dossier Schema`
- `T29: Dossier Renderer`
- `T30: Missing Evidence Section`
- `T31: Review Command`

Expected result: the operator can decide from dossiers and record outcomes.

### Sequence D - MVP Experiment Conversion

Implement:

- `T32: MVP Experiment Pack Model`
- `T33: Experiment Renderer`
- `T34: Experiment Outcome Recording`

Expected result: one opportunity can become a 7-14 day validation experiment.

### Sequence E - Operator Production

Implement:

- `T35: Operator Runbook`
- `T36: Scheduled Run Support`
- `T37: Backup and Recovery Guide`
- `T38: Four-Run Readiness Review`

Expected result: the system is ready for weekly personal use before beta.

---

## Source Expansion Sequence

Do not add all sources at once. Use this order:

1. Owned sources: `telegram-research-agent`, notes, own GitHub repos.
2. Manual competitor URLs and saved SERP snapshots.
3. GitHub public issues/search.
4. Hacker News and Stack Exchange.
5. Product Hunt.
6. YouTube and Google Trends.
7. Paid or credentialed sources such as SerpApi, G2, app-store APIs, Reddit.

Each source must prove it improves decisions before the next source wave is added.

---

## Artifact Quality Bar

An opportunity dossier is decision-grade only when it includes:

- at least the configured minimum independent evidence count;
- source links or source IDs;
- captured dates;
- pain and audience;
- current workaround;
- competitor shape;
- one-function MVP;
- acquisition angle;
- risk flags;
- missing evidence;
- deterministic score components;
- final recommendation;
- prior decision context where available.

An MVP experiment pack is decision-grade only when it includes:

- one-function scope;
- target user or segment;
- manual validation path;
- first 10 discovery targets or source queries;
- success threshold;
- kill threshold;
- revisit threshold;
- timebox.

---

## Product Risks to Watch

| Risk | Why it matters | Guardrail |
|------|----------------|-----------|
| Generic validation output | The market is crowded with generic idea validators | Require citations and missing-evidence sections |
| Source sprawl | More sources can lower signal quality | Add source trust and per-source caps |
| LLM-owned judgment | Makes rankings hard to compare week to week | Keep scoring deterministic |
| Weak decision memory | Repeated rejected ideas destroy trust | Enforce suppression and evidence delta logic |
| Premature SaaS | Auth, tenants, billing, and compliance distract from proving the workflow | Stay local-first until personal weekly value is proven |
| Private data leakage | Sources may include private notes and Telegram data | Keep raw data ignored, sanitized, and local |
