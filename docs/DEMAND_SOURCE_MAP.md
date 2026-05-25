# Demand Source Map

Version: 1.0
Date: 2026-05-25
Status: Active source-selection guidance

---

## Purpose

`docs/SOURCE_CATALOG.md` defines which connectors and source types the Radar
can use. This map defines where to look for visible pain and demand inside
those sources.

The distinction matters:

- a source answers "where can the system collect evidence?"
- a demand surface answers "what market behavior inside that source is worth
  treating as pain, demand, distribution, or willingness-to-pay evidence?"

This map is seeded from the one-year `@its_capitan` Telegram backfill and
manual synthesis. It should guide source queries, missing-evidence requests,
dossier review, and future scoring-rubric changes.

---

## Current Radar Fit

The current product already has source connectors, source trust controls,
evidence caps, retrieval, dossiers, operator review, source value reports, and
live-source roadmap work. This map should therefore be treated as an overlay on
the existing source system, not as a replacement for it.

Use this document to decide:

- which query seeds to run through SERP, YouTube, Reddit, HN, Product Hunt, or
  Stack Exchange;
- which store, marketplace, or competitor pages should be manually snapshotted;
- which missing evidence a dossier should ask for before `build`;
- which opportunities are just interesting anecdotes and should stay
  `revisit` or `needs_more_evidence`.

Do not change source trust weights or build thresholds from this document
alone. Weight changes remain human-approved scoring policy changes.

---

## Demand Surfaces

| Surface | Existing source types | What to look for | Strong evidence | MVP interpretation | Captain anchors |
|---------|----------------------|------------------|-----------------|--------------------|-----------------|
| Search intent | `serp`, `youtube`, saved search snapshots | Users phrase the desired outcome as a query: "how to", "converter", "listen", "save", "download", "without internet", "alternative" | Query volume, repeated long-tail phrases, similar questions across sources | Build the smallest tool that satisfies the query directly | `https://t.me/its_capitan/511`, `https://t.me/its_capitan/512`, `https://t.me/its_capitan/523`, `https://t.me/its_capitan/525` |
| Store and marketplace demand | `app_stores`, manual snapshots, future Chrome Web Store / GPT-store snapshots | Existing apps/extensions with installs, reviews, rankings, paid plans, or weak incumbents | High installs, many reviews, paid ranking, repeated review complaints | Ship one narrow app/extension into an existing search/store channel | `https://t.me/its_capitan/474`, `https://t.me/its_capitan/507`, `https://t.me/its_capitan/521`, `https://t.me/its_capitan/523` |
| Competitor traction | `product_hunt`, manual URLs, landing pages, pricing pages, store snapshots | Existing products with visible users, launches, revenue claims, or category momentum | Revenue/user claims, Product Hunt ranking, visible pricing, strong launch response | Copy the demand, not the product; narrow the first feature and improve positioning/distribution | `https://t.me/its_capitan/501`, `https://t.me/its_capitan/503`, `https://t.me/its_capitan/504`, `https://t.me/its_capitan/521` |
| Platform timing events | `telegram_research_agent`, RSS/news, HN, Reddit, manual URLs | New model/device capability, policy change, outage, blocking, migration, or platform shift | Users are forced to change behavior now; old workflow becomes fragile | Build a bridge, converter, migration helper, or new-capability utility while timing is fresh | `https://t.me/its_capitan/474`, `https://t.me/its_capitan/485`, `https://t.me/its_capitan/505`, `https://t.me/its_capitan/522` |
| Creator/content discovery gaps | `youtube`, `telegram_research_agent`, RSS, manual URLs | Valuable posts/videos/audio are trapped where search, reuse, or repackaging is weak | Many existing assets plus visible desire for search traffic, transcription, audio, SEO, or reuse | Turn existing content into searchable, reusable, or multi-format assets | `https://t.me/its_capitan/506`, `https://t.me/its_capitan/511`, `https://t.me/its_capitan/512`, `https://t.me/its_capitan/523` |
| Social distribution channels | `reddit`, `product_hunt`, `hacker_news`, `youtube`, `telegram_research_agent`, Habr/manual URLs | A reachable community already discusses the workflow, alternatives, or launch category | Comments, launch reactions, community questions, repeated objections, traffic/credibility evidence | Treat first distribution channel as part of MVP scope before building | `https://t.me/its_capitan/494`, `https://t.me/its_capitan/503`, `https://t.me/its_capitan/504`, `https://t.me/its_capitan/514` |
| Repeated user questions | `stack_exchange`, `reddit`, `youtube`, comments, operator notes, Telegram exports | Same question repeats in beginner/professional language | Multiple independent examples of the same question or confusion | Convert repeated advice into a narrow diagnostic, checklist, or self-serve workflow | `https://t.me/its_capitan/512`, `https://t.me/its_capitan/524` |
| Manual workarounds | `stack_exchange`, `github`, `reddit`, `operator_note`, manual URLs, Telegram exports | Users copy, collect, transcribe, save, convert, block, rewrite, compare, or research manually | Clear before/after task and repeated workaround steps | Automate one step, not the whole workflow | `https://t.me/its_capitan/483`, `https://t.me/its_capitan/487`, `https://t.me/its_capitan/501`, `https://t.me/its_capitan/509` |
| Monetization bottlenecks | pricing pages, paywalls, store listings, competitor URLs, operator notes | Existing traffic exists but conversion, paywall, pricing, or activation is weak | Revenue change tied to one screen/offer/checkout step | Build diagnostics or optimization tooling only after traffic exists | `https://t.me/its_capitan/482` |
| Owned audience leverage | `operator_note`, own GitHub repos, existing reports, product analytics snapshots | The builder already has users, subscribers, traffic, or a portfolio of small tools | Reusable distribution, cross-sell path, repeated user base | Add a small utility that reuses existing demand instead of starting cold | `https://t.me/its_capitan/517`, `https://t.me/its_capitan/523` |

---

## Priority Order

When time, budget, or connector coverage is limited, prefer surfaces in this
order:

1. Search intent with explicit query language and volume.
2. Store/category demand with visible competitors, installs, paid ranking, or
   reviews.
3. Competitor traction with revenue, users, launch, pricing, or category
   momentum evidence.
4. Manual workaround evidence from posts, comments, forums, reviews, support
   threads, or operator notes.
5. Platform timing events with temporary urgency.
6. Distribution surfaces where the audience is already reachable.
7. Founder anecdotes without independent external verification.

Founder anecdotes are useful as hypothesis seeds, but they should not justify
`build` until the Radar attaches at least one independent demand surface.

---

## Extraction Hints

When evidence is normalized or reviewed, preserve these concepts in snippets,
tags, dossier notes, or future schema fields:

| Concept | Meaning |
|---------|---------|
| `source_surface` | Search intent, store demand, competitor traction, platform timing, creator/content gap, social distribution, repeated question, manual workaround, monetization bottleneck, owned audience |
| `demand_signal_type` | Query volume, review complaint, competitor revenue, repeated question, platform shock, manual task, visible traffic, launch response |
| `pain_statement` | The concrete problem in user language |
| `current_workaround` | How the user solves it now |
| `proof_metric` | Query count, installs, reviews, revenue claim, traffic, ranking, comment count, repeated mentions |
| `mvp_shape` | The one-function MVP implied by the evidence |
| `first_distribution_channel` | Search, App Store, Chrome Web Store, Reddit, Product Hunt, YouTube, Telegram, Habr, SEO page |
| `verification_needed` | The next source needed before build/reject |
| `anti_complexity_note` | What must not be built in v1 |

These are not all first-class schema fields today. Until they are, capture
them in dossier notes, missing-evidence reasons, and operator review comments.

---

## Scoring Guidance

These are qualitative signals for future scoring policy, not immediate code
changes.

| Signal | Suggested impact |
|--------|------------------|
| Exact query phrase plus monthly volume | Very high |
| Competitor with visible revenue/users and weak narrow positioning | Very high |
| Store listing with many reviews complaining about one missing workflow | High |
| Manual workaround repeated across independent sources | High |
| Platform shock with clear deadline or forced migration | Medium-high, decays quickly |
| Product Hunt/Reddit/HN attention without purchase or search evidence | Medium |
| "Cool technology" with no search, competitor, or workaround evidence | Low |
| Broad B2B platform idea from imagination | Reject until buyer pain and sales path are proven |

Use this guidance primarily to improve missing-evidence prompts and review
comments. Deterministic score weights still change only through reviewed code
and human approval.

---

## Anti-Patterns

Downrank or reject opportunities when they show these patterns:

- The idea starts from a broad market narrative, not a visible user task.
- v1 requires many features before a user can get value.
- The product depends on paid ads before there is retention or conversion
  proof.
- The founder wants to build a platform before validating one workflow.
- The opportunity ignores distribution until after implementation.
- The opportunity depends on a fragile platform integration without a fallback
  path.
- The only evidence is an appealing Telegram anecdote with no corroborating
  source.

---

## Query Seeds

Use these as starting patterns for SERP, YouTube, Reddit, HN, Stack Exchange,
store, and manual snapshot exploration:

- `how to {task}`
- `{task} converter`
- `{task} online`
- `{task} without internet`
- `{task} Chrome extension`
- `{task} app`
- `{task} alternative`
- `{task} for {niche}`
- `listen to {content_type}`
- `save {content_type} offline`
- `transcribe {content_type}`
- `rewrite selected text`
- `block distracting sites`
- `{language} pronunciation tones`

---

## One-Function MVP Heuristic

When a signal is strong, reduce it to the smallest user-visible action:

- YouTube-to-podcast: paste link -> get audio/listenable version.
- Telegram-to-SEO: connect channel -> get searchable site.
- Voice dictation: hold hotkey -> text appears in current field.
- Offline page saver: click extension -> page is available offline.
- Chinese pronunciation: speak phrase -> see tone mistakes.
- Land ownership lookup: tap parcel -> see owner/property facts.
- eSIM travel: choose country/dates -> get usable plan.

The Radar should preserve this one-action shape in every opportunity brief.
If the brief needs multiple modules to explain v1, it is probably too large.
