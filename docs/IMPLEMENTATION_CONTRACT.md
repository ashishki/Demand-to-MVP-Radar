# Implementation Contract

Status: IMMUTABLE - changes to this document require an Architectural Decision Record filed in `docs/adr/`.
Version: 1.0
Effective date: 2026-05-19

Any Codex or review agent may cite this document as the authority on implementation rules. Any finding that this contract was violated is automatically P1 unless a stricter severity is stated.

---

## Universal Rules

These rules apply to every project using the AI Workflow Playbook. They are not negotiable and are not changed without an ADR.

### SQL Safety

- All SQL is parameterized. Use `text()` with named params: `text("SELECT ... WHERE id = :id")`.
- Never interpolate variables into SQL strings.
- Never use string concatenation to build queries.
- Violation: automatic P1.

### Multi-Tenant Systems

- Demand-to-MVP Radar is single-operator and local-first in v1.
- If the project becomes multi-tenant, every database call touching tenant-scoped tables must be preceded by tenant context (`SET LOCAL app.tenant_id = :tid` or equivalent RLS setup).
- No query executes without tenant context in multi-tenant code paths.
- Session-level `SET` is forbidden in multi-tenant code paths.
- Violation after multi-tenancy is introduced: automatic P1.

### Async Redis

- Redis is not part of v1.
- If Redis is introduced later, it is accessed only in `async def` functions using `redis.asyncio`.
- Never import or call the synchronous Redis client in async code paths.
- Violation after Redis is introduced: automatic P1.

### Authorization

- v1 has no public web routes.
- Every future route handler that reads evidence, reports, decisions, source config, or credentials must enforce authentication and authorization before accessing data.
- `GET /health` or CLI health output may be public/non-authenticated only if it does not expose secrets, raw evidence, private notes, or PII.
- Authorization is never deferred to "we'll add it later."
- Violation: automatic P1.

### PII Policy

- No PII in log messages, span attributes, or metrics labels.
- Where identifiers must be logged, use hashes (SHA-256 or equivalent).
- This applies to logs, traces, metrics, errors, run manifests, and audit events.
- Fields considered PII or private in this project: operator identity, private notes, source account names, author handles when linked to private exports, API keys, access tokens, credentialed source identifiers, raw private URLs, local file paths containing user names, and unsanitized report drafts.
- Violation: automatic P1.

### Credentials and Secrets

- No credentials, API keys, tokens, passwords, or secrets in source code.
- No credentials in comments.
- No credentials in test fixtures; use placeholder strings such as `test-key`.
- All secrets come from environment variables or ignored local secrets files.
- `.env`, local databases, raw source exports, private notes, and unsanitized generated reports must not be committed.
- Required environment variables are documented in `docs/ARCHITECTURE.md#runtime-contract`.
- Violation: automatic P1 and a security incident.

### Shared Tracing Module

- One shared tracing module: `demand_mvp_radar/observability.py`.
- All code that creates spans imports from this module.
- No inline noop span implementations in individual files.
- No copy-pasted tracer initialization in individual modules.
- Violation: P2, escalating to P1 at age cap.

### CI Gate

- CI must pass before any PR is merged.
- A PR with failing CI is never merged.
- If CI is flaky, the flakiness is fixed before merge.
- CI setup is part of Phase 1 and must not be deferred.
- Violation: automatic P1.

### Observability

- Every external call (SQLite, HTTP, LLM inference, embedding provider, tool execution) must be wrapped in a span with trace ID and operation name using `demand_mvp_radar/observability.py`.
- For each external call type, emit a success/error counter and latency metric or structured equivalent in the run manifest.
- RAG paths must record `insufficient_evidence` count, retrieval latency, generation latency, corpus version, and index schema version.
- Tool-use paths must record tool name, version, success, latency, side-effect class, and audit fields.
- Health output must not log PII and must expose stale-index status without exposing raw evidence.
- Violation for missing profile-specific metrics: P2.

---

## Project-Specific Rules

### Source Provenance Is Mandatory

Every evidence record, retrieval chunk, score explanation, brief claim, and recommendation must trace back to source metadata: source type, source ID or URL, captured timestamp, content hash, and run ID where available.

Violation: P1 for generated recommendations without provenance; P2 for internal intermediate records missing non-critical metadata.

### Deterministic Ownership of Scores

Scoring arithmetic, threshold checks, freshness windows, duplicate suppression, budget checks, and build / reject / revisit routing are deterministic code paths. LLM output may inform extracted fields but must not directly set final score totals or threshold decisions.

Violation: P1.

### Bounded LLM Output

Every LLM output used by the application must validate against a typed schema before storage, tool execution, scoring, or report generation. Invalid output is rejected and logged as a structured error without raw private data.

Violation: P1.

### Human-Owned Decisions

The system may recommend build, reject, or revisit, but only a human operator may record a final "build now" decision, add paid/credentialed sources, publish externally, create repositories, contact users, or change scoring weights.

Violation: P1; destructive or public external action without approval is P0.

### Local-First Data Hygiene

SQLite database files, vector indexes, raw snapshots, private notes, and generated reports live under configured data/report directories and are excluded from git unless intentionally sanitized and reviewed.

Violation: P1 for secrets/private data; P2 for benign generated artifacts.

---

## Control Surface and Runtime Boundaries

| Boundary | Rule |
|----------|------|
| Secrets scope | LLM, embedding, search, Reddit, store, and Telegram credentials are scoped by env var and accessed only by the source/tool that needs them. |
| Network egress | Egress is limited to configured sources and providers. Live source additions require config and human approval when credentials, spend, or terms risk exists. |
| Privileged actions | Public publishing, outreach, repository creation, paid/credentialed sources, scoring-weight changes, and deletion require human approval. |
| Runtime mutation | Runtime code must not install packages, alter tools, mutate infrastructure, or create repositories. Dependency changes occur through reviewed commits only. |
| Persistence | SQLite data, raw snapshot references, indexes, reports, decisions, run manifests, and audit events persist locally. Run writes must be idempotent by source fingerprint and run ID. |
| Auditability | Tool calls, source reads/fetches, report writes, decisions, eval runs, and budget checks record audit fields sufficient for later review. |

### Runtime Tier Guardrails

- Implement only within T1 as declared in `docs/ARCHITECTURE.md`.
- Runtime-tier expansion is a governance change, not an implementation detail.
- The project must not silently acquire T2/T3 behavior such as broad shell mutation, ad-hoc package installs, privileged runtime management, autonomous repository mutation, or long-lived mutable workers.

### Conditional Rules for T2 / T3

Not active for v1. If T2 or T3 is introduced later, add an ADR and update `docs/ARCHITECTURE.md` before implementation begins.

---

## RAG Rules (Profile Rules: RAG)

Applies because `docs/ARCHITECTURE.md` declares RAG Status = ON.

### Corpus Isolation

- v1 has a single local operator corpus.
- Every retrieval query must be scoped to the active corpus version.
- If multi-user or multi-corpus support is introduced, retrieval must enforce corpus boundaries at the retrieval layer, not only at application entry.
- Cross-corpus retrieval after multi-corpus support exists is a data leak and automatic P1.

### Insufficient Evidence Path

- Every query-time retrieval handler must implement the `insufficient_evidence` path.
- When retrieved evidence does not meet the minimum confidence, freshness, or independent-source threshold, the system returns `insufficient_evidence` and missing-evidence reasons.
- The system must not fabricate a recommendation from weak retrieval.
- This path must have explicit tests.
- Omitting this path is automatic P1.

### Index Schema Versioning

- The index schema is versioned as `retrieval-index-v1`.
- Changing embedding model, chunking strategy, metadata fields, vector dimensions, retrieval mode, or supported modalities requires an ADR.
- After such an ADR, the corpus must be fully re-indexed before the new schema is used for reports.
- Mixed old/new schema indexes are forbidden.

### Embedding Strategy Declaration

- Retrieval mode is `text-only`.
- Text-only is the default baseline and must be evaluated before any multimodal retrieval proposal.
- Preview or experimental embedding models are not allowed for v1.
- The selected embedding model, dimensions or representation contract, provider, and fallback/re-index plan must be recorded in `docs/retrieval_eval.md` when T09/T10 establish the baseline.

### Max Index Age

- Maximum allowed index age is 7 days for weekly reports.
- Health output and report metadata must expose index age.
- A stale index beyond 7 days must produce an explicit warning in health/report output.
- Index age beyond 14 days is P1 unless the operator explicitly runs in offline review mode.

### Retrieval-Generation Separation

- Ingestion pipeline code and query-time retrieval code live in separate modules.
- A function or class must not mix ingestion responsibilities (extract, normalize, chunk, embed, index) with query-time responsibilities (retrieve, filter, assemble evidence, answer).
- Violation: P2.

### Retrieval Evaluation Gate

A retrieval-related task tagged `rag:ingestion` or `rag:query`, or touching chunking, embedding, ranking, evidence assembly, index schema, retrieval mode, corpus versioning, or `insufficient_evidence`, is not complete unless:

1. `docs/retrieval_eval.md` is updated with current metrics for the affected pipeline stage.
2. Current metrics are compared to the baseline row when a baseline exists.
3. Any regression is documented in Regression Notes.
4. Eval Source records the exact command, fixture, or method used.
5. Date records the run date.
6. Corpus Version records the corpus version active during evaluation.

Submitting a task as done without these fields is P1.

### Retrieval Regression Policy

- Hit@3 drop greater than 15 percent vs baseline: P0.
- Hit@3 drop greater than 5 percent vs baseline: P1.
- Citation precision drop greater than 10 percent vs baseline: P1.
- No-answer accuracy below 0.90 after baseline: P1.
- A regression must classify root cause as code-change-induced or corpus-change-induced.

---

## Tool-Use Rules (Profile Rules: Tool-Use)

Applies because `docs/ARCHITECTURE.md` declares Tool-Use Status = ON.

### Tool Schema Versioning

- Every LLM-callable tool schema is versioned.
- Schema changes require a task entry in `docs/tasks.md` and tests validating schema generation and execution-time validation.
- Callers must not depend on undocumented fields.
- The schema is the contract.

### Unsafe-Action Confirmation

- Every tool classified as destructive, public, paid, credentialed, or irreversible requires a distinct human confirmation code path before execution.
- Confirmation must be a separate branch or command path, not a boolean flag buried in a schema.
- v1 does not include destructive external tools. If one is added later, add an ADR or task-level architecture update first.
- Missing confirmation for a destructive tool is P0.

### Side-Effect Documentation

- Every tool that writes, modifies, publishes, deletes, spends money, sends messages, or records decisions must document side effects in `docs/ARCHITECTURE.md#tool-catalog`.
- Local report writes and decision records are side effects and must be audited.
- Undocumented side effects are P1.

### Idempotency

- Read tools must be idempotent for the same input and captured source state.
- Write tools must be idempotent where technically feasible.
- Non-idempotent writes must be explicitly marked in the Tool Catalog with rationale.

### Tool Permission Boundary

- Permission is checked at each tool boundary.
- Entry-point-only permission checks are not sufficient.
- Tool execution must record audit events with run ID, tool name, version, success, latency, side-effect class, and declared audit fields.

### Tool Evaluation Gate

A task tagged `tool:schema`, `tool:unsafe`, or `tool:call` is not complete unless:

1. `docs/tool_eval.md` is updated when schema, permission, audit, or unsafe-action behavior changes.
2. Current results are compared to the baseline when a baseline exists.
3. Eval Source records the exact command, fixture, or method used.
4. Date records the run date.

Missing tool evaluation on a tool-profile task is P2, escalating to P1 if repeated.

### MCP-Backed Tool Integrity

No MCP-backed runtime integration is planned for v1. If any MCP-shaped integration is introduced, its Tool Catalog row must include MCP server name, pinned version, side-effect class, idempotency note, retry policy, audit fields, and rollback behavior for destructive actions.

---

## Continuity and Retrieval Rules

- Canonical authority remains: `docs/ARCHITECTURE.md`, `docs/IMPLEMENTATION_CONTRACT.md`, `docs/spec.md`, `docs/tasks.md`, `docs/CODEX_PROMPT.md`, ADRs, review reports, evaluation artifacts, code, tests, and CI.
- `docs/DECISION_LOG.md`, `docs/IMPLEMENTATION_JOURNAL.md`, and `docs/EVIDENCE_INDEX.md` are retrieval aids. They summarize, index, and point; they do not overrule canonical files.
- A task with `Context-Refs` must read those references before implementation begins.
- Retrieval is mandatory when changing architecture, runtime, auth, retrieval semantics, tool schemas, scoring weights, source trust policy, compliance controls, migrations, or any open review finding.
- If work supersedes a prior decision or invalidates evidence, update the relevant retrieval artifact in the same task.
- Violation: P2. Repeated violation becomes P1 at age cap.

---

## Mandatory Pre-Task Protocol

Every Codex agent must execute these steps before writing implementation code. No exceptions.

1. Read `docs/IMPLEMENTATION_CONTRACT.md` from top to bottom.
2. Read the full task in `docs/tasks.md`, including all acceptance criteria, the Depends-On list, Context-Refs, and Notes.
3. Read all Depends-On tasks to understand interface contracts.
4. Read the task's `Context-Refs` and relevant entries in `docs/DECISION_LOG.md`, `docs/IMPLEMENTATION_JOURNAL.md`, `docs/EVIDENCE_INDEX.md`, `docs/retrieval_eval.md`, or `docs/tool_eval.md` when the task depends on prior decisions, proof, retrieval behavior, tool behavior, or findings.
5. Run `pytest -q`. Record the output as `{N} passing, {M} failed`. If M > 0, stop and report the broken baseline.
6. Run `ruff check` after T02 configures ruff. It must exit 0 before implementation begins. If not, create a separate lint-fix commit, then restart the pre-task protocol.
7. Confirm that every acceptance criterion in the task will have a corresponding test before implementation is considered complete.

Skipping any step is a P1 finding in the next review cycle.

---

## Forbidden Actions

The following actions are never permitted. Violating them generates a P1 finding in the next review cycle unless a stricter severity is stated.

| Forbidden Action | Reason |
|------------------|--------|
| String interpolation in SQL | SQL injection; parameterized queries are unconditional. |
| Session-level `SET` in future multi-tenant code paths | Leaks tenant context across requests. |
| Skipping pre-task baseline capture | Cannot verify implementation did not break existing tests. |
| Self-closing a review finding without code verification | Findings are verified by reading code, not by assertion. |
| Modifying this document without an ADR | The contract is immutable by design. |
| Deferring CI setup past Phase 1 | Every commit after Phase 1 must be CI-verified. |
| Merging a PR with failing CI | CI gate is non-negotiable. |
| Committing credentials or secrets of any kind | Irreversible exposure risk. |
| Expanding runtime tier or privilege surface without updating ARCHITECTURE.md and ADRs | Runtime escalation is a governance change. |
| Treating decision logs, journals, or evidence indexes as authority over canonical docs | Retrieval surfaces are convenience, not source of truth. |
| Leaving commented-out code in a commit | Dead code degrades readability and review quality. |
| Adding a TODO without a task reference | Orphaned TODOs accumulate and are never addressed. |
| Running LLM synthesis when retrieval status is `insufficient_evidence` | Fabricates confidence from weak evidence. |
| Executing destructive, public, paid, credentialed, or outreach actions without human approval | Violates human-owned decision boundaries; may be P0. |

---

## Quality Process Rules

### P2 Age Cap

Any P2 finding that remains open for more than 3 consecutive review cycles must be:

- closed with a code change and passing test, or
- escalated to P1 and resolved before the next phase gate, or
- formally deferred to v2 with an ADR filed in `docs/adr/`.

Retrieval-critical P2 findings related to corpus isolation, `insufficient_evidence`, schema drift, or evaluation validity escalate after 1 review cycle.

### Commit Granularity

One logical change per commit. Do not bundle unrelated changes. Use commit messages in the format `type(scope): description`.

### Sandbox Isolation

Tests do not share state. Each test touching SQLite uses a temporary database or an isolated transaction. Tests touching file outputs use temporary directories.

### Evaluation Validity

An evaluation artifact entry in `docs/retrieval_eval.md` or `docs/tool_eval.md` is invalid if either `Eval Source` or `Date` is absent or blank. Invalid entries are treated as missing evaluation.

Acceptable Eval Source examples:

- `python scripts/eval_retrieval.py --fixture tests/fixtures/retrieval_queries.json, run 2026-05-19`
- `pytest tests/eval/test_retrieval_eval.py::test_query_eval_row_has_required_metrics, run 2026-05-19`
- `python scripts/eval_tools.py --fixture tests/fixtures/tool_eval.json, run 2026-05-19`

`Ran evaluation` or `updated metrics` without specifics is not acceptable.

### Review Cycle Integrity

Review agents close findings only after verifying the fix in code and confirming a test exists that would fail without the fix.

---

## Governing Documents

| Document | Path | Role |
|----------|------|------|
| Architecture | `docs/ARCHITECTURE.md` | System design authority: what the system is and why. |
| Specification | `docs/spec.md` | Feature authority: what the system does. |
| Task graph | `docs/tasks.md` | Implementation authority: what each agent builds. |
| Session handoff | `docs/CODEX_PROMPT.md` | State authority: current baseline, open findings, next task. |
| This document | `docs/IMPLEMENTATION_CONTRACT.md` | Rule authority: immutable implementation rules. |
| Retrieval eval | `docs/retrieval_eval.md` | RAG evaluation authority. |
| Tool eval | `docs/tool_eval.md` | Tool-use evaluation authority. |
| Review reports | `docs/audit/CYCLE{N}_REVIEW.md` | Finding authority: official review cycle record. |
| ADRs | `docs/adr/ADR{NNN}.md` | Decision authority: architectural decisions and rationale. |

Precedence order:

1. `docs/IMPLEMENTATION_CONTRACT.md`
2. `docs/adr/`
3. `docs/ARCHITECTURE.md`
4. `docs/spec.md`
5. `docs/tasks.md`
6. `docs/CODEX_PROMPT.md`
