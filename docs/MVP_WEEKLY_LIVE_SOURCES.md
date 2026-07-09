# MVP Weekly Live Sources

Status: Active weekly production contract
Date: 2026-07-09

## Purpose

`mvp-of-week` is the weekly product-opportunity artifact. It uses Telegram
Research Agent output only as the seed layer, then collects independent market
evidence before selecting or downgrading an MVP candidate.

The weekly report is not an implementation-upgrade brief for existing repos.
It must answer:

- what one-function MVP is interesting this week;
- which public sources support the same pain;
- what evidence is missing before a focused experiment;
- why the idea fits or mismatches the operator's current stack and story.

## Active Source Bundle

The active weekly source config is `config/mvp_weekly_sources.json`.

| Source | Type | Role | Credential |
|---|---|---|---|
| RSS/HN feeds | `rss` | trend and HN-style corroboration | none |
| GitHub public search | `github_public` | developer pain, feature requests, integration friction | optional `GITHUB_TOKEN` |
| Stack Exchange | `stack_exchange` | repeated questions and workaround language | optional `STACK_EXCHANGE_KEY` |
| SERP / SerpApi | `serp` | search intent, alternatives, competitor pages | `SERPAPI_API_KEY` |
| YouTube Data API | `youtube` | tutorial/creator demand and how-to intent | `YOUTUBE_API_KEY` |
| Product Hunt | `product_hunt` | launch and competitor traction | `PRODUCT_HUNT_TOKEN` |
| Reddit | `reddit` | community pain, repeated complaints, and manual workaround language | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` |
| Competitor/workaround crawler | `crawl4ai` | bounded landing pages, pricing hints, competitor/workaround pages | none, disabled until explicit URLs/domains are configured |
| X/Twitter corroboration | `x` | lower-confidence corroborating discussion only | `XAI_API_KEY`, disabled by default |

Enabled weekly sources should not disappear silently. If a source cannot run
because a credential is missing, the run records it in `source_errors`. If a
source is intentionally disabled, it appears in `skipped_sources`.

For RVE validation, SERP, Reddit, crawler, and X/Twitter sources can also run
in bounded non-live operation:

- `cache_only: true` reads a configured fixture/cache file without requiring
  the live source credential;
- `dry_run: true` validates config and records adapter status without reading a
  fixture or making a live request;
- live mode remains credential-gated and missing credentials are reported as
  `credential_limited` in `validation_adapter_status`;
- Reddit/forum live rate limits are reported as `rate_limited`, not as weekly
  report failures;
- crawler live mode fetches only explicit `urls` under `allowed_domains`,
  `max_pages_per_run`, and `max_pages_per_domain`;
- X/Twitter is disabled by default and cache-first. Matched X items are
  lower-confidence corroboration and do not satisfy gates by themselves.

## Credential File

Recommended VPS location:

```bash
/etc/demand-mvp-radar.env
```

Use `config/live_sources.env.example` as the template. Do not commit real
values.

The Telegram Research Agent systemd unit also loads this file:

```ini
EnvironmentFile=-/etc/demand-mvp-radar.env
```

The leading `-` means the service still starts when the file is absent. In that
case credentialed sources are reported as missing instead of being skipped.

## Where To Get Keys

- SerpApi: create an account and copy the dashboard API key.
  Docs: https://serpapi.com/search-api
- GitHub: create a Personal Access Token for higher public API quota.
  Docs: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- YouTube: create a Google Cloud API key with YouTube Data API v3 enabled.
  Docs: https://developers.google.com/youtube/v3/docs
- Product Hunt: create a developer token and review usage/commercial terms.
  Docs: https://api.producthunt.com/v2/docs
- Reddit: create a read-only Reddit app and user agent for official API use.
  Docs: https://developers.reddit.com/docs/capabilities/server/reddit-api
- Stack Exchange: optional app key for higher quota.
  Docs: https://api.stackexchange.com/docs/throttle

## Run Commands

From the Radar repo:

```bash
.venv/bin/python -m demand_mvp_radar.cli mvp-of-week \
  --telegram-export ../telegram-research-agent/data/output/opportunity_seeds/2026-W22.json \
  --source-config config/mvp_weekly_sources.json \
  --run-id mvp-weekly-YYYY-WW
```

For a no-LLM source contract check:

```bash
DMR_LLM_PROVIDER=none .venv/bin/python -m demand_mvp_radar.cli mvp-of-week \
  --telegram-export ../telegram-research-agent/data/output/opportunity_seeds/2026-W22.json \
  --source-config config/mvp_weekly_sources.json \
  --run-id mvp-weekly-source-check
```

Expected source contract in a healthy broad run:

- `skipped_sources` is empty unless a source was intentionally disabled.
- public sources collect evidence even without paid/community credentials.
- missing credentials appear under `source_errors`.
- `external_evidence_count` is greater than zero.
- strong recommendations still require candidate-level matched external
  corroboration.

## Decision Gates

The weekly MVP synthesis is gated after the LLM response:

- Telegram-only candidates cannot become `focused_experiment`.
- A confident experiment requires at least two non-Telegram evidence items from
  at least two independent matched external source types for the selected
  candidate.
- Unmatched SERP snippets remain `decision_context.external_research_context`
  and do not satisfy gates.
- Unmatched or adjacent-pain Reddit/forum complaints remain
  `decision_context.external_research_context` and do not satisfy gates.
- Matched Reddit/forum evidence keeps query provenance, subreddit/forum label,
  public URL, source-created date, and privacy-preserving author metadata when
  available.
- Unmatched, adjacent-pain, or irrelevant crawler pages do not satisfy gates.
  Matched competitor/integration pages support gates only when they carry target
  ICP metadata; pricing copy is a hint, not standalone WTP proof.
- Matched X/Twitter evidence is rendered as lower-confidence corroboration and
  remains non-gating. Trend chatter without pain, workaround, or WTP content is
  shown as negative evidence.
- Ideas outside the operator profile, such as Java/JVM-heavy or mobile-native
  builds, are downgraded unless they have a narrow Python/LLM workflow wedge.
- The report must include Source Mix, Validation Query Pack, Matched External
  Evidence, and Operator Fit sections.

The operator profile lives in `config/operator_fit_profile.md`.

## Demand Source Map

`docs/DEMAND_SOURCE_MAP.md` defines where to look for pain inside sources:

- search intent;
- store/category demand;
- competitor traction;
- repeated questions;
- manual workarounds;
- creator/content discovery gaps;
- platform timing events;
- monetization bottlenecks.

Use that document to adjust weekly queries, not generic brainstorming.
