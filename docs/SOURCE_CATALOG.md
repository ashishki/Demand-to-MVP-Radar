# Source Catalog and Access Strategy

Version: 1.0
Date: 2026-05-19
Status: Active planning baseline

---

## Purpose

This catalog ranks sources by their value for deciding what to build. A source is useful only if it helps identify pain, workarounds, active demand, competition, distribution channels, or willingness to pay.

Sources are not equal. First-party and operator-curated sources should outrank broad public feeds. Broad public feeds are useful for corroboration, not for replacing judgment.

---

## Source Priority Model

| Tier | Meaning | Examples | Default trust |
|------|---------|----------|---------------|
| T0 | Owned or operator-curated sources | `telegram-research-agent`, notes, bookmarks, project repos | High |
| T1 | Public sources with official APIs or stable exports | GitHub, Hacker News, Stack Exchange, Product Hunt, YouTube Data API | Medium |
| T2 | Commercial or credentialed market sources | SerpApi, G2, App Store Connect, Google Play Developer API | Medium to High |
| T3 | Scraping or terms-sensitive sources | Public web pages without API, communities without export paths | Low until reviewed |

---

## Recommended Initial Sources Beyond Telegram

| Priority | Source | Signal Type | Access Method | Why It Helps | Risk / Notes |
|----------|--------|-------------|---------------|--------------|--------------|
| P0 | Operator notes | Raw personal pain, half-formed ideas, rejected ideas | Local Markdown/JSON import | Highest founder-market signal; captures what the operator keeps noticing | Must stay private and ignored by git |
| P0 | Own GitHub repositories | Active project direction, recurring implementation friction, TODOs, issues | GitHub REST API or local repo scan | Connects market signals to what the operator can actually build | Avoid committing private repo metadata |
| P0 | `telegram-research-agent` weekly outputs | Curated research signals, project relevance, prior study loop | Exported JSON/SQLite/report bridge | Existing production-like personal signal pipeline | Treat as upstream; avoid tight internal coupling |
| P1 | GitHub issues/discussions/search | Developer pain, feature requests, integration complaints, abandoned workflows | GitHub REST API/search | Strong for devtools, AI infra, automation, OSS pain | Search API limits and noisy duplicate issues |
| P1 | Hacker News | Founder/developer discussion, launch reactions, pain language | Official HN Firebase API and Algolia/HN search | Good for early adopter language and trend emergence | Comments are noisy; needs source-quality filters |
| P1 | Stack Exchange / Stack Overflow | Repeated technical problems and workaround patterns | Stack Exchange API | Useful for automation/devtool pain where people ask exact questions | Not always commercial demand |
| P1 | Product Hunt | New product launches, positioning, comments, makers | Product Hunt GraphQL API | Good for competitor discovery and launch timing | API is token-gated and commercial use may require contact |
| P1 | Manual competitor URLs | Landing page claims, pricing, feature scope, positioning | Manual URL snapshot tool | Best low-risk way to build competitor context | Manual curation required |
| P2 | SerpApi / SERP snapshots | Search demand, alternatives queries, competitor pages, ads | SerpApi Google Search API or saved snapshots | Good proxy for active intent and SEO competition | Paid API; terms/cost approval required |
| P2 | Google Trends | Trend direction for known terms | Google Trends API alpha where available, or manual snapshot | Helps avoid overreacting to stale topics | Alpha/current availability must be verified before implementation |
| P2 | YouTube | Creator/tutorial pain, comments, product alternatives | YouTube Data API search/list/comment threads | Useful for "how do I..." and tool comparison demand | API quota and search representativeness limits |
| P2 | App stores | Reviews, complaints, ratings, feature gaps | Apple App Store Connect API for owned apps; public/manual snapshots otherwise; Google Play Developer API reviews for owned apps | Good for consumer/mobile extension ideas and complaint mining | Official review APIs often apply to owned apps |
| P2 | Chrome Web Store | Extension categories, reviews, install counts, competitor metadata | Manual snapshots first; Chrome Web Store API is mainly publish/manage | Useful for browser-extension opportunities | Public data access may require careful source-specific design |
| P2 | G2 / software review sites | B2B complaints, alternatives, buyer language | G2 API if available/approved; manual public snapshots first | Strong for B2B pain and competitor comparison | Commercial/credentialed; approval required |
| P3 | Reddit | Pain language, workarounds, community questions | Official Reddit API or approved export/snapshot path | High-value human pain source for some markets | API access and terms changed; credential/access approval required |
| P3 | Newsletters/RSS/blogs | Trend and competitor emergence | RSS feeds, manual URL snapshots | Good for context, weak as demand proof | Usually secondary evidence only |

---

## Source Implementation Order

### Wave 1 - Owned and Low-Risk

1. `telegram-research-agent` bridge.
2. Operator notes import.
3. Own GitHub repository scan/import.
4. Manual competitor URL snapshots.

Reason: these sources are high-control, high-context, and enough to produce the first real dossiers.

### Wave 2 - Public Developer Demand

1. GitHub issues/search.
2. Hacker News.
3. Stack Exchange.
4. Product Hunt.

Reason: this adds public corroboration for developer, AI, automation, and indie-builder opportunities.

### Wave 3 - Market Intent and Reviews

1. SERP snapshots or SerpApi.
2. YouTube Data API.
3. Store listings/reviews where access is legitimate.
4. G2 or similar review data where approved.

Reason: this adds demand triangulation, competitor discovery, and user complaint language.

### Wave 4 - Sensitive or Paid Sources

1. Reddit official API or approved exports.
2. Paid review/search APIs.
3. Credentialed app-store or marketplace data.

Reason: these sources may be valuable, but access, cost, and terms risk should be handled only after the product proves value with easier sources.

---

## Evidence Weighting Guidance

| Source type | Suggested use | Suggested cap |
|-------------|---------------|---------------|
| Operator notes | Hypothesis seed, founder-fit signal | Cannot alone justify `build` |
| Telegram curated signal | Strong early signal | Needs one public corroborating source for `build` |
| GitHub issues | Pain/workaround evidence | Deduplicate by repo/topic |
| HN/Reddit comments | Pain language and objections | Require source-quality and recency filters |
| Product Hunt | Competitor/launch evidence | Treat positive launch copy as competitor evidence, not demand proof |
| SERP/search | Intent and competition evidence | Avoid treating search volume alone as product demand |
| Reviews | Complaint and willingness-to-pay hints | Strong when complaint repeats across products |
| News/RSS/blogs | Trend context | Secondary evidence only |

---

## Source Adapter Acceptance Contract

Every new source adapter must provide:

- stable source ID or URL;
- source type;
- captured timestamp;
- title or summary;
- normalized text;
- snippet;
- content hash;
- raw snapshot reference when applicable;
- trust level;
- freshness window;
- source-specific error/quarantine reason.

Every adapter must be testable with fixtures before live credentials are required.

---

## Human Approval Boundaries

Human approval is required before:

- adding paid sources;
- adding credentialed sources;
- scraping sites without a clear allowed path;
- storing private raw exports;
- publishing source-derived reports externally;
- contacting people or communities from mined sources;
- changing source trust weights or build thresholds.

---

## Reference Links

- GitHub REST API: https://docs.github.com/en/rest
- Hacker News API: https://github.com/HackerNews/API
- Reddit API docs: https://www.reddit.com/dev/api/
- Reddit Data API terms: https://redditinc.com/policies/data-api-terms
- Product Hunt API v2: https://www.producthunt.com/v2/docs
- Stack Exchange API: https://api.stackexchange.com/docs
- YouTube Data API search: https://developers.google.com/youtube/v3/docs/search/list
- Google Trends API alpha: https://developers.google.com/search/apis/trends
- SerpApi Google Search API: https://serpapi.com/search-api
- Chrome Web Store API: https://developer.chrome.com/docs/webstore/api
- Apple App Store Connect API apps endpoint: https://developer.apple.com/documentation/appstoreconnectapi/get-v1-apps
- Google Play Developer API reviews: https://developers.google.com/android-publisher/api-ref/rest/v3/reviews/list
- G2 API documentation: https://documentation.g2.com/docs/g2-api
