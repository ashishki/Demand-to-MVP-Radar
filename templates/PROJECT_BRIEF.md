# Project Brief: Demand-to-MVP Radar

Use this document before running `prompts/STRATEGIST.md`. The goal is not to pre-design the system, but to give the Strategist enough context to choose the right solution shape, governance level, runtime tier, and model strategy without guessing.

---

## 1. Project

- **Project name:** Demand-to-MVP Radar
- **One-sentence summary:** A demand-intelligence system that turns market demand signals into ranked, evidence-backed one-function MVP briefs for indie builders and AI automation engineers.
- **Why this project exists:** Builders often start from interesting ideas instead of proven demand. The `@its_capitan` research showed a repeatable product pattern: find existing search/store/social demand first, choose one narrow audience, ship one useful function, and spend most of the launch effort on distribution rather than feature breadth.
- **What success looks like in v1:** Each weekly run produces 5 ranked opportunity briefs with source links, demand evidence, competitor notes, one-function MVP scope, likely acquisition channel, risk flags, and a clear build / reject / revisit recommendation.

## 1b. Problem Fit and Adoption Reality

Answer these before describing the desired architecture. The Strategist uses
this section to avoid designing a polished AI system around an unproven or
demo-only need.

- **Concrete operational pain:** Opportunity research is manual, inconsistent, and easy to bias toward ideas that feel interesting but have no visible demand. Evidence gets scattered across Telegram posts, search results, store listings, Reddit/X threads, competitor pages, and personal notes. The operator cannot reliably compare one idea against another after a few days.
- **Current workaround:** Manually read Telegram channels, browse search queries, inspect app stores and competitor sites, save ad hoc notes, and reason from memory. `telegram-research-agent` already captures some signals, but it is optimized for weekly project-aware research rather than structured product-opportunity validation.
- **Why existing process is insufficient:** Ordinary notes and checklists do not enforce source provenance, demand thresholds, repeatable scoring, source freshness, competitor comparison, or decision memory. Generic LLM brainstorming produces plausible ideas but does not prove that people already search for the solution.
- **First user / buyer / operator who feels the pain:** A solo AI engineer or indie builder who wants to select a small, buildable product idea without spending weeks on unstructured market research. First internal user is the project owner.
- **What would make v1 not worth adopting:** Generic idea lists, weak or missing source links, no clear rejection logic, no comparison across opportunities, no way to inspect why an idea was ranked, or output that still requires hours of manual validation before deciding.
- **Adoption proof metric:** The operator can review the weekly top 5 opportunities and make a build / reject / revisit decision for each in under 15 minutes, with at least 3 opportunities per week containing enough evidence to be decision-grade.
- **Claims that are out of bounds before evidence:** "Predicts revenue", "guarantees demand", "replaces founder judgment", "fully automates market research", "selects winning ideas", "production-ready venture studio".
- **Work AI will not replace:** Final commercial judgment, ethical review, legal/compliance interpretation, source credibility judgment when evidence conflicts, and the decision to commit engineering time.

## 2. Users and Workflows

- **Primary users / operators:** Solo AI builders, indie hackers, automation consultants, and technical founders looking for narrow product opportunities with existing demand.
- **Main workflow 1:** Collect demand signals from configured sources, normalize them into evidence records, deduplicate near-identical ideas, and cluster them by user pain / workflow / acquisition channel.
- **Main workflow 2:** Score each opportunity with deterministic criteria, then use LLM synthesis to produce a concise opportunity brief with source-backed reasoning and one-function MVP scope.
- **Main workflow 3:** Record operator decisions and follow-up outcomes, so later runs can suppress repeated weak ideas, revisit promising ones, and improve the scoring rubric.

## 3. Scope

- **In scope for v1:** Ingest Telegram research signals, manually supplied URLs, search-query snapshots, competitor landing pages, simple store listings, and notes; produce ranked opportunity briefs; persist evidence and decisions; expose CLI reports and copyable Markdown output.
- **Out of scope / non-goals:** Automatic product launch, paid ad management, automated scraping at high scale, revenue prediction, full SEO platform, autonomous cold outreach, investor-style TAM modeling, and broad startup ideation.

## 4. AI Scope

- **Where AI may be needed:** Extracting the user pain, target audience, current workaround, competitor shape, MVP function, acquisition angle, and risk flags from messy text evidence; generating search-query variants; summarizing clusters into a brief; comparing conflicting evidence.
- **Where AI is explicitly not wanted:** URL validation, source deduplication, scoring arithmetic, threshold checks, freshness windows, source allowlists/denylists, run scheduling, audit timestamps, and decision persistence.
- **Possible retrieval / RAG need:** Yes. The system must retrieve prior opportunity briefs, rejected ideas, source snippets, Telegram evidence, competitor notes, and decision history.
- **If retrieval is needed, is text-only likely sufficient or is multimodal evidence truly required:** Text-only is sufficient for v1. Screenshots may become useful later for landing-page / store-listing analysis, but they are not required for the first useful version.
- **If multimodal may be needed, which modalities and why:** Optional later: webpage screenshots and app-store screenshots to inspect positioning, paywall copy, visual hierarchy, and onboarding friction.
- **Possible tool-use need:** Yes. Tools may fetch URLs, query search APIs or saved SERP snapshots, read Telegram-derived evidence, inspect app-store/chrome-store metadata, and write structured reports.
- **Possible planning / agentic behavior need:** Limited. The system can run a fixed research pipeline and request missing evidence, but it should not autonomously decide to build products or mutate repositories.

## 5. Deterministic Candidates

List the parts that probably should stay deterministic unless the Strategist proves otherwise.

- **Validation / policy checks:** Source URL validity, source type classification, minimum evidence count, required fields, date freshness, duplicate detection, and forbidden claims.
- **Routing / decision rules:** Opportunity bucket assignment, build / reject / revisit thresholds, source-priority weights, confidence bands, and suppression of recently rejected ideas.
- **Calculations / transformations:** Search volume normalization, competitor count, pricing extraction when explicit, recency weighting, source coverage counts, and score aggregation.
- **Retries / idempotency / audit triggers:** Fetch retries, per-source run IDs, raw evidence snapshots, stable opportunity fingerprints, decision log writes, and report versioning.

## 6. Human Approval Boundaries

- **What actions must require human approval:** Marking an idea as "build now", adding paid or credentialed data sources, publishing any output externally, creating new repositories, contacting users, and changing scoring weights that affect decision priority.
- **What can be automated safely:** Ingestion, normalization, clustering, first-pass scoring, brief drafting, duplicate suppression, and weekly report generation.
- **Why these boundaries matter:** A plausible product idea can still waste weeks of engineering time. The system should compress research and surface evidence, not make investment decisions on behalf of the operator.

## 7. Risk and Error Cost

- **What is expensive if the system is wrong:** Building the wrong MVP, overvaluing noisy demand, ignoring acquisition difficulty, or presenting copied ideas without enough differentiation.
- **What is expensive if the system is slow:** Less critical than correctness, because this is mostly batch research. Slow runs become a problem only if they block a weekly planning ritual.
- **What is expensive if the system is inconsistent / variable:** The operator cannot compare opportunities across weeks, scoring becomes untrusted, and decision memory stops being useful.
- **Blast radius if it fails badly:** Low operational blast radius but high opportunity cost. It may cause wasted product work or misleading portfolio positioning.
- **Audit / explainability needs:** High. Every recommendation must show evidence links, source snippets, score components, and rejection/build rationale.

## 8. Data

- **Primary data sources:** Telegram posts from `telegram-research-agent`, manual URLs, SERP/search-query snapshots, competitor landing pages, app-store / Chrome-store / GPT-store listings, Reddit/X threads, pricing pages, and operator notes.
- **Approximate data volume:** v1 can start with 100-500 evidence items per weekly run. Historical backfills may include thousands of text records.
- **Does data change frequently:** Yes. Search results, store rankings, competitor positioning, and trend language can change weekly.
- **Sensitive / regulated data present:** Mostly no. Sensitive data may include API keys, private notes, and possibly account-specific search/store credentials if added later.
- **Retention / deletion expectations:** Keep normalized evidence, source metadata, and decision logs. Raw fetched page bodies can be pruned or hashed after extraction if storage grows.

## 8b. Continuity and Evidence

- **Which decisions are likely to be revisited later:** Rejected opportunities, deferred opportunities, scoring rubric changes, source trust decisions, and selected MVPs after the operator runs experiments.
- **What prior evidence or proof will future agents need to find quickly:** Source links, extracted demand statements, competitor examples, pricing data, search-volume snapshots, opportunity score history, and why an idea was accepted or rejected.
- **Will work span multiple sessions / agents / weeks:** Yes. Opportunity discovery and product selection are recurring weekly/monthly workflows.
- **Any existing docs, ADRs, audits, or notes that should become retrieval anchors:** `telegram-research-agent` evidence memory, the one-year `@its_capitan` channel analysis, and source examples such as Excel Formula Bot (`https://t.me/its_capitan/426`), Prerender (`https://t.me/its_capitan/420`), YouTube-to-podcast bot (`https://t.me/its_capitan/511`), PDF converter (`https://t.me/its_capitan/424`), and "10,000 steps" experimentation framing (`https://t.me/its_capitan/465`).

## 9. Integrations

- **External APIs / services:** Telegram-derived evidence, optional Yandex/Google SERP provider, Reddit API or saved exports, app-store/chrome-store metadata sources, webpage fetcher, and optional search-volume providers.
- **Databases / storage:** SQLite for local-first v1; PostgreSQL if the project becomes multi-user or needs heavier concurrent ingestion; local file outputs for Markdown/HTML briefs.
- **Auth / identity provider:** Local single-operator auth for v1. If exposed as a web app, use simple authenticated access before considering multi-tenant identity.
- **Webhooks / messaging / queues:** Optional. v1 can run by CLI/systemd timer. Later versions can push weekly briefs to Telegram or Slack.

## 10. Constraints

- **Preferred stack:** Python, FastAPI or CLI-first service layer, SQLite WAL for v1, Pydantic structured outputs, httpx/requests, deterministic scoring modules, Markdown/HTML report output.
- **Deployment target:** Local workstation or VPS under `/srv/openclaw-you`, run by CLI or systemd timer. Docker is acceptable once the runtime stabilizes.
- **Budget constraints:** High cost sensitivity. Use deterministic filters and cheap models for first pass; reserve stronger models for final brief synthesis.
- **Latency / throughput expectations:** Batch-oriented. A weekly run can take minutes. Interactive review should load quickly once reports are generated.
- **Compliance requirements:** No regulated-domain claims in v1. Respect source terms and avoid high-scale scraping without explicit source-specific design.
- **Network / security restrictions:** Store API keys in environment files or secrets directory. Do not commit credentials or raw private notes.

## 11. Runtime and Operations

- **Should runtime stay simple (managed service / container) if possible:** Yes. Prefer CLI + systemd timer first; move to a web UI only after the scoring/report loop proves useful.
- **Any need for shell, package, or toolchain mutation at runtime:** No for v1. Runtime should fetch/read evidence and write reports, not install packages or mutate tools.
- **Any need for privileged actions or long-lived isolated workers:** No. A periodic batch job is sufficient.
- **Recovery / rollback expectations:** Runs should be idempotent by source URL/message ID and run ID. Failed fetches should be retried without corrupting prior evidence.

## 12. Model and Cost Expectations

Only fill what you know. The Strategist should still make the final recommendation.

- **Cost sensitivity:** high
- **Latency sensitivity:** low for batch generation, medium for interactive review
- **Expected request / task volume:** Low to medium. Initial target is weekly runs over hundreds of evidence items, plus manual on-demand analysis.
- **If AI is used, should the system prefer smaller / cheaper models by default:** Yes. Use smaller models for extraction/classification and stronger models only for final synthesis or ambiguous evidence.
- **Any required capabilities:** Structured output, source-grounded summarization, function calling/tool use, moderate reasoning, long enough context to compare multiple evidence snippets.
- **Preview-model tolerance:** low. Use stable models for repeatable scoring and decision logs.

## 13. Success Metrics

- **Business success metric:** Number of decision-grade opportunities produced per week and number of opportunities selected for real MVP experiments.
- **Quality metric:** Percentage of top-ranked opportunities with at least 3 independent evidence points and explicit build/reject rationale accepted by the operator.
- **Latency metric:** Weekly batch completes in under 30 minutes for v1 data volume; generated report opens immediately from local output.
- **Cost metric:** Average LLM cost per weekly run stays below a configured budget ceiling, initially target under USD 2-5 per run.
- **Operational metric:** Evidence ingestion success rate, duplicate rate, rejected-idea recurrence rate, and percentage of recommendations with complete source provenance.

---

## Usage

1. Send this completed brief to the Strategist.
2. Let the Strategist ask one batch of clarifying questions.
3. Use the resulting architecture package as the Phase 1 input to the rest of the playbook.
