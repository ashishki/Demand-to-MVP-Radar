# Personal-to-Production Development Plan

Version: 1.0
Date: 2026-05-19
Status: Active planning baseline

---

## Purpose

Demand-to-MVP Radar should first solve the operator's own recurring pain: too many scattered market signals, too little confidence about what is worth building next, and no durable memory of why prior ideas were built, rejected, or deferred.

The product should not start as a generic startup idea validator. The first wedge is a local-first decision system for a solo AI builder that turns trusted personal and public evidence into decision-grade opportunity dossiers.

---

## North Star

The operator can review a weekly top 5 opportunity report in under 15 minutes and make a clear `build`, `reject`, `revisit`, or `needs_more_evidence` decision for each opportunity, with cited evidence and prior decision memory.

### First Confident Artifacts

The first phase of maturity is reached when the project can produce:

1. A live evidence import from `telegram-research-agent`.
2. A source-backed opportunity dossier from real, non-fixture evidence.
3. A decision journal entry for each top opportunity.
4. A rejected/revisited idea memory effect in a later run.
5. One selected opportunity converted into a 7-14 day MVP experiment plan.

---

## Product Thesis

Most idea-validation tools produce fast reports from a user-entered idea. That market is crowded and easy to copy. Demand-to-MVP Radar should differentiate by starting upstream:

- observe recurring demand signals before the operator has committed to an idea;
- preserve source provenance and evidence freshness;
- rank opportunities deterministically before synthesis;
- use RAG to show supporting and missing evidence;
- remember prior decisions and suppress repeated weak ideas;
- convert only the strongest opportunities into one-function MVP experiments.

The product wins if it becomes a trusted decision loop, not a brainstorming tool.

---

## Phase 0 - Personal Operating Contract

Business goal: define the exact personal workflow and adoption failure conditions before adding more automation.

### Build

- Document the operator's current research workflow and weekly review pain.
- Define the minimum decision taxonomy: `build`, `reject`, `revisit`, `needs_more_evidence`, `already_exists`, `not_my_icp`, `too_hard_to_distribute`.
- Define weekly review constraints: maximum review time, top N opportunities, minimum evidence threshold, maximum acceptable generic content.
- Define private-data boundaries for personal notes, Telegram exports, and source credentials.

### Artifact

`docs/OPERATOR_WORKFLOW.md`

### Exit Criteria

- The operator can say what output is worth reading every week.
- The system has explicit failure conditions for generic or unsupported recommendations.
- Every later feature can be traced back to a decision the operator needs to make.

---

## Phase 1 - Source Strategy and Access Map

Business goal: choose sources by decision value, not by availability.

### Build

- Create a source catalog with source type, trust level, access method, credential risk, freshness window, expected signal, and implementation priority.
- Start with owned and low-risk sources before paid or credentialed platforms.
- Add human approval boundaries for paid, credentialed, scraped, or externally published sources.
- Define source quality scoring so weak sources cannot dominate ranking by volume.

### Artifact

`docs/SOURCE_CATALOG.md`

### Exit Criteria

- At least one owned source and two public/low-risk sources are ready for adapter implementation.
- Every source has a clear "why this helps decide what to build" field.
- Sources with legal, credential, or terms risk are marked as approval-required.

---

## Phase 2 - Telegram Research Agent Bridge

Business goal: convert the existing personal research system into the first live upstream evidence source.

### Build

- Read sanitized outputs from `telegram-research-agent` without coupling to its internals.
- Support one of these bridge modes first: exported JSON, exported SQLite view, or generated weekly report import.
- Map Telegram research signals into Demand-to-MVP evidence records.
- Preserve original channel/post/report provenance where available.
- Record source fingerprints so repeated imports are idempotent.

### Artifact

First live evidence import from `telegram-research-agent`.

### Exit Criteria

- A real week of Telegram-derived research can be ingested without fixtures.
- Imported records include source type, source ID/link, captured timestamp, text, content hash, and bridge run ID.
- Malformed or private rows are quarantined instead of blocking the import.

---

## Phase 3 - Evidence Vault and RAG Trust Layer

Business goal: make evidence quality visible before any attractive brief is generated.

### Build

- Store normalized evidence from live sources in SQLite.
- Build retrieval corpus from evidence, prior briefs, and decisions.
- Enforce `insufficient_evidence` when support is weak, stale, duplicated, or source-poor.
- Add source trust and freshness filters to retrieval.
- Extend retrieval evaluation with live-like fixtures from sanitized exports.

### Artifact

`Evidence Vault` plus updated `docs/retrieval_eval.md`.

### Exit Criteria

- The system can explain why it has enough evidence or why it does not.
- Top opportunities cite evidence from at least the configured minimum independent source count.
- Retrieval regressions are caught before weekly report generation is trusted.

---

## Phase 4 - Opportunity Dossier

Business goal: create the first decision-grade artifact.

### Build

- Generate one dossier per top opportunity.
- Include pain, audience, workaround, source evidence, competitor shape, one-function MVP, acquisition angle, risks, and confidence.
- Separate deterministic score reasons from LLM synthesis.
- Include "missing evidence" and "why this may be wrong" sections.

### Artifact

`Opportunity Dossier` in Markdown and optional HTML.

### Exit Criteria

- The operator can make a decision from the dossier without reopening all raw sources.
- Every claim has a citation or is explicitly marked as an inference.
- Generic ideas without source support are downgraded or rejected.

---

## Phase 5 - Decision Loop and Memory

Business goal: close the loop so the system learns from operator decisions without pretending to own the final judgment.

### Build

- Add review commands for accepting/rejecting/revisiting opportunities.
- Preserve reasons and source report path in append-only decision records.
- Suppress recently rejected ideas unless new evidence appears.
- Surface prior decisions inside new dossiers.
- Add a revisit queue with a configurable time window and rationale.

### Artifact

`Decision Journal` and `Revisit Queue`.

### Exit Criteria

- A rejected idea does not return unchanged in later reports.
- A revisited idea carries its old rationale and new evidence delta.
- The operator can inspect decision history per opportunity.

---

## Phase 6 - MVP Experiment Pack

Business goal: turn the strongest opportunity into a small build/test decision.

### Build

- Generate a one-function MVP scope from a selected opportunity.
- Define the first validation experiment: landing page, manual workflow, script, prototype, or concierge test.
- Define the first 10 user/contact/source discovery plan.
- Define success, kill, and revisit thresholds.
- Add experiment results back into decision memory.

### Artifact

`MVP Experiment Pack`

### Exit Criteria

- At least one opportunity becomes a concrete 7-14 day experiment.
- The experiment has a measurable outcome, not just a build checklist.
- Results feed back into scoring and future suppression/revisit logic.

---

## Phase 7 - Personal Review UX

Business goal: reduce weekly decision friction without hiding evidence quality.

### Build

- Add a compact weekly review surface.
- Show top 5 opportunities, evidence count, confidence, decision buttons, and prior decision state.
- Keep raw evidence and score details one click or command away.
- Prefer static HTML or local CLI first; avoid a multi-user web app until the workflow is proven.

### Artifact

Local weekly review cockpit.

### Exit Criteria

- Weekly review is faster than reading Markdown manually.
- The UI does not obscure missing evidence or weak confidence.
- Decision actions remain human-owned and audit logged.

---

## Phase 8 - Operator-Grade Production

Business goal: make the local system reliable enough to run every week without heroics.

### Build

- Add scheduled weekly run support.
- Add health checks for source status, stale indexes, failed imports, cost, and report freshness.
- Add SQLite backup/export guidance.
- Add source-specific failure reporting.
- Add budget and token reporting for LLM paths.
- Add a recovery guide for failed runs.

### Artifact

`docs/OPERATOR_RUNBOOK.md`

### Exit Criteria

- Four weekly runs complete with no manual code changes.
- Failed sources do not block all other sources.
- The operator can restore or inspect state after a failed run.

---

## Phase 9 - Private Beta Readiness

Business goal: decide whether the personal workflow generalizes to other solo builders.

### Build

- Sanitize private assumptions from configuration.
- Define what can and cannot be shared with beta users.
- Add import/export boundaries for user-owned source data.
- Add onboarding docs for one technical beta user.
- Add a feedback template focused on actual decisions made, not compliments.

### Artifact

Private beta package for 3-5 trusted users.

### Exit Criteria

- The product has at least four internal weekly runs.
- At least 10-20 dossiers exist from real evidence.
- At least one MVP experiment was launched or killed because of the system.
- The beta asks users for decision outcomes, not vanity feedback.

---

## Phase 10 - External Product Decision

Business goal: choose whether this remains a personal tool, becomes a productized local-first tool, or becomes a hosted service.

### Decision Options

| Option | When to choose |
|--------|----------------|
| Personal tool | It reliably helps the operator but other users do not have enough source access or discipline. |
| Local-first paid tool | Other technical builders want the same source-backed decision loop and can bring their own data. |
| Hosted product | Users need convenience more than local control, and auth, tenancy, privacy, and source compliance are worth the complexity. |
| Consulting/productized service | Users want the outcome but do not want to configure sources or interpret evidence. |

### Exit Criteria

- The operator has evidence of repeated personal value.
- Beta users show actual behavior: importing sources, reviewing dossiers, and making decisions.
- The product has a sharper position than generic AI idea validators.
