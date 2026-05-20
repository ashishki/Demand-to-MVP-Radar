# Live Source Production Roadmap

Version: 1.0
Date: 2026-05-20
Status: Product roadmap for self-collecting production version

---

## Purpose

This roadmap moves Demand-to-MVP Radar from a local, snapshot-friendly decision system to a product that can collect demand signals by itself, normalize them, rank opportunities, and produce evidence-backed dossiers every week.

The target experience is:

1. The operator connects sources once.
2. Credentials stay in ignored local environment files or a secret manager.
3. Scheduled collectors fetch new signals automatically.
4. The evidence vault normalizes, deduplicates, and indexes records.
5. The weekly run produces reports, dossiers, missing-evidence gaps, and experiment packs.
6. The operator records decisions and experiment outcomes.

Exports and manual snapshots remain fallback modes. They are not the intended production UX.

## Current Gap

The current product has the evidence, retrieval, scoring, dossier, review, experiment, scheduling, and recovery foundation. It does not yet have live first-class connectors for most external channels.

The production gap is the source collection layer:

- connector configuration;
- credential handling;
- scheduled API fetches;
- source-specific pagination and rate limits;
- source-specific dedupe and quarantine;
- sanitized fixture generation for CI;
- connector health reporting;
- source value evaluation.

## Production Architecture

```text
source config
  -> credential resolver
  -> scheduled source collectors
  -> raw local snapshots
  -> normalizers
  -> evidence vault
  -> retrieval index
  -> clustering
  -> deterministic scoring
  -> dossier / weekly report / experiment pack
  -> operator decision + outcome memory
```

Production source collection must be pull-based and auditable. A connector may fetch from an API, bot, feed, or approved snapshot path, but every collected record must end as a normalized `EvidenceRecord` with provenance.

## Credential Strategy

Credentials are optional per connector and never required for tests.

| Source | Credential | Storage | Initial mode | Notes |
|--------|------------|---------|--------------|-------|
| GitHub | `GITHUB_TOKEN` | ignored env file or secret manager | optional for public search, required for higher rate limits/private repos | Use least scope first. |
| Hacker News | none | n/a | live public API | Good first live connector. |
| Stack Exchange | optional app key | ignored env file | live public API | Add key only when quota requires it. |
| RSS/blogs/newsletters | none | n/a | live feed polling | Low-risk corroboration source. |
| SERP | `SERPAPI_API_KEY` or `DATAFORSEO_*` | ignored env file | paid connector after approval | Strong intent signal, cost-controlled. |
| Reddit | OAuth client ID/secret + refresh token | ignored env file or secret manager | credentialed after approval | High-value but terms-sensitive. |
| YouTube | `YOUTUBE_API_KEY` | ignored env file | quota-controlled connector | Useful for tutorial/comment demand. |
| Product Hunt | `PRODUCT_HUNT_TOKEN` | ignored env file | credentialed connector | Competitor/launch context. |
| Discord | bot token + allowlisted guild/channel IDs | secret manager preferred | explicit opt-in connector | Private/community-sensitive. |
| Telegram | bot token or client session for approved channels | secret manager preferred | explicit opt-in connector | Avoid private channel leakage. |
| X/Twitter | API bearer token | secret manager preferred | late-stage connector only | Cost/terms volatility; not first wave. |
| G2/review sites | vendor API key or approved export | secret manager preferred | late-stage connector only | Commercial/terms review required. |

Credential rules:

- no credentials in code, docs examples with real values, fixtures, logs, reports, or commits;
- connector config stores credential variable names, not credential values;
- CI uses fixtures and mocked clients only;
- paid, credentialed, private, scraping, outreach, or publishing behavior requires explicit human approval.

## Connector Contract

Every source connector must implement the same lifecycle:

1. Validate config and required credential variable names.
2. Fetch a bounded page/window of source records.
3. Persist raw snapshots locally when allowed.
4. Normalize into evidence candidates.
5. Attach source type, source ID/URL, captured timestamp, content hash, source fingerprint, trust level, freshness window, and run ID.
6. Deduplicate by source fingerprint.
7. Quarantine malformed, private, or policy-disallowed records.
8. Report source counts, error counts, rate-limit status, and last successful fetch.

Connector tests must include config validation, missing credential behavior, happy-path fixture normalization, pagination/cursor handling, rate-limit/error handling, quarantine handling, provenance/redaction checks, and idempotent repeated import.

## Source Waves

### Wave 1 - Low-Friction Live Public Sources

Goal: prove automatic collection without sensitive credentials.

Connectors:

- Hacker News search/API;
- Stack Exchange API;
- RSS/blog feeds;
- public GitHub search with optional token.

Exit criteria:

- weekly scheduled run fetches live public records;
- source errors do not block all other sources;
- evidence delta report shows new and duplicate public records;
- top dossiers include at least one public corroborating source.

### Wave 2 - High-Value Credentialed Sources

Goal: add intent, developer pain, and competitor context with controlled credentials.

Connectors:

- GitHub authenticated search/issues/discussions;
- SERP provider such as SerpApi or DataForSEO;
- YouTube Data API;
- Product Hunt API.

Exit criteria:

- credentials are loaded only from ignored env/secret storage;
- connector health reports quota/cost status;
- source trust and type caps prevent one API from dominating;
- retrieval eval includes source-specific live-like fixtures.

### Wave 3 - Community Sources

Goal: collect high-signal community pain while respecting privacy and terms.

Connectors:

- Reddit official API;
- Discord bot for allowlisted servers/channels;
- Telegram bot/client for approved channels.

Exit criteria:

- every channel/server/subreddit is allowlisted;
- private author handles and channel identifiers are redacted where required;
- raw community snapshots stay local and ignored;
- build recommendations require corroborating non-community evidence.

### Wave 4 - Commercial Review and Market Sources

Goal: improve willingness-to-pay and competitor proof.

Connectors:

- app store review APIs where access is legitimate;
- G2 or review vendor API where approved;
- Chrome Web Store approved snapshots/API path;
- marketplace/pricing page monitors.

Exit criteria:

- legal/terms approval is documented;
- cost ceiling is enforced;
- review snippets are deduplicated and capped;
- willingness-to-pay signals are cited separately from generic complaints.

### Wave 5 - Productized Multi-User Sources

Goal: decide whether this remains local-first or becomes hosted.

Build only after four internal weekly runs and private beta evidence.

Capabilities:

- per-user source config;
- per-user secret storage;
- tenant-scoped evidence vaults;
- auth and authorization;
- source consent/onboarding flows;
- deletion/export flows.

Exit criteria:

- beta users repeatedly import sources, review dossiers, and make decisions;
- source compliance risks are understood;
- hosted convenience is worth auth, tenancy, privacy, support, and billing complexity.

## AI Development Phases

### P0 - Roadmap and Source Decision Record

Artifacts: this roadmap, an ADR for live-source collection boundaries, and an updated source catalog with selected first live connectors.

Acceptance:

- first four live connectors selected;
- credential and no-credential modes documented;
- human approval boundaries preserved.

### P1 - Connector SDK

Build shared connector protocol, connector config models, credential resolver, raw snapshot writer, connector run result model, and quarantine result model.

Tests:

- no live network in CI;
- missing credentials produce typed errors;
- raw snapshots stay under configured data directories;
- source counts and error counts are emitted.

### P2 - Public Connector Wave

Build Hacker News, Stack Exchange, RSS, and GitHub public connectors.

Tests:

- sanitized fixtures for every connector;
- pagination and rate-limit fixtures;
- idempotent repeated imports;
- retrieval eval rows for live-like public corpus.

### P3 - Connector Health and Scheduled Collection

Build `collect-sources`, per-source health state, source-specific last success, last error, next cursor, rate-limit status, and scheduled collector integration.

Tests:

- failed source does not fail entire run when other sources succeed;
- health JSON includes source status without secrets;
- scheduled runs write manifests and logs locally.

### P4 - Credentialed Connector Wave

Build GitHub authenticated, SERP provider, YouTube, and Product Hunt connectors.

Tests:

- credential variable names are validated;
- credentials never appear in logs or audit fields;
- cost/quota fields are recorded;
- paid connectors are disabled by default.

### P5 - Community Connector Wave

Build Reddit, Discord allowlisted-channel, and Telegram approved-channel connectors.

Tests:

- allowlists are required;
- private identifiers are redacted;
- deleted/private/unavailable records quarantine cleanly;
- community-only support cannot produce `build`.

### P6 - Evidence Quality Learning

Build source value reports, per-source precision and decision impact metrics, stale/noisy-source warnings, and source caps tuned by observed usefulness.

Tests:

- scoring stays deterministic;
- source weights/caps change only through reviewed config;
- eval artifacts distinguish code-change and corpus-change regressions.

### P7 - Local Review UX

Build local HTML review cockpit, source health panel, decision buttons, missing-evidence action queue, and experiment outcome entry.

Tests:

- no hidden external calls;
- decision writes are append-only;
- weak evidence remains visible.

### P8 - Private Beta Package

Build onboarding guide, source connection wizard for technical users, import/export boundaries, feedback template focused on actual decisions, and backup/restore instructions for beta users.

Tests:

- beta fixture can run without real credentials;
- source config export redacts secrets;
- one technical user can complete setup from docs.

### P9 - Hosted/SaaS Decision Gate

Build only if beta behavior proves it.

Decision inputs:

- repeated user decisions from dossiers;
- connector setup friction;
- source compliance risk;
- support burden;
- willingness to pay;
- whether hosted convenience beats local control.

Possible outcomes:

- keep as personal tool;
- sell local-first paid package;
- provide productized consulting;
- build hosted SaaS with auth/tenancy/compliance.

## Production Requirements

Production-ready local version requires:

- no manual exports for primary weekly operation;
- at least four active live connectors;
- source health in `health --json`;
- scheduled collection and weekly report generation;
- backup/recovery verified;
- four weekly local runs with completed readiness checklist;
- at least 10-20 real dossiers;
- at least one experiment launched, killed, or revisited because of the system;
- no private data in git;
- no unreviewed paid/credentialed source behavior.

Hosted production requires all local requirements plus authentication, authorization, tenant-scoped evidence/report/decision/credential storage, encrypted secret storage, user export/deletion, source terms review, abuse/rate-limit controls, billing/support boundaries, and incident response.

## Definition of Done for a Connector

A connector is production-ready only when:

- it can run unattended on a schedule;
- it has fixture-based CI coverage;
- live credentials are optional or safely resolved;
- it records source counts, error counts, latency, quota/cost where applicable;
- it preserves source provenance;
- it deduplicates and quarantines correctly;
- it contributes to at least one decision-grade dossier;
- it does not leak secrets or private source identifiers.

## Backlog Seeds

Suggested next task IDs after the current planned list:

- T39: Live Source Connector Protocol
- T40: Credential Resolver and Secret Redaction
- T41: `collect-sources` Command
- T42: Hacker News Live Connector
- T43: Stack Exchange Live Connector
- T44: RSS Feed Connector
- T45: GitHub Public Search Connector
- T46: Source Health in `health --json`
- T47: Live Public Corpus Retrieval Eval
- T48: SERP Credentialed Connector
- T49: YouTube Connector
- T50: Product Hunt Connector
- T51: Reddit Connector
- T52: Discord Allowlisted Channel Connector
- T53: Telegram Approved Channel Connector
- T54: Source Value Report
- T55: Local Review Cockpit
- T56: Private Beta Source Onboarding
- T57: Hosted/SaaS Decision ADR

## Hard Gates

Do not start private beta until:

- the live collector runs without manual exports for four weekly cycles;
- the operator makes repeated decisions from generated dossiers;
- at least one experiment outcome changes future scoring or suppression;
- backup and restore have been verified.

Do not start SaaS work until:

- private beta users show actual behavior, not just positive feedback;
- source credential, privacy, and compliance risks are documented;
- local-first packaging is insufficient for the target users;
- auth, tenancy, billing, and support are worth the cost.
