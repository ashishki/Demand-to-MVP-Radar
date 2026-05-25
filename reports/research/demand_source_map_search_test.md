# Demand Source Map Search Test

Status: public-safe search test
Date: 2026-05-25
Run type: `backfilled-real`
Counts toward four-run evidence gate: yes, as public search/source-map evidence
Decision owner: human operator

This run tests the new `docs/DEMAND_SOURCE_MAP.md` overlay. The goal is to
search by demand surface instead of by broad idea category, then see whether the
Radar finds clearer one-function MVP candidates than the previous Lead Response
SLA path.

## Source Register

| ID | Source URL / locator | Captured at | Source type | Source family | Demand surface | Access method | Trust tier | Extracted signal | Limitations | Can support decision? |
|---|---|---|---|---|---|---|---|---|---|---|
| DSM-S1 | https://blubrry.com/support/getting-started/getting-started-with-vid2pod/ | 2026-05-25 | product docs | creator/content tool | competitor traction | public web | medium | Blubrry documents Vid2Pod, a YouTube playlist-to-podcast workflow. | Existing vendor; not independent demand proof. | yes |
| DSM-S2 | https://alternativeto.net/software/youcaster/about/ | 2026-05-25 | product listing | creator/content tool | store/category demand | public web | medium | YouCaster is listed as a YouTube-channel-to-audio/podcast-style tool. | Listing quality varies; needs direct usage/pricing proof. | yes |
| DSM-S3 | https://www.reddit.com/r/Standup/comments/10fg5au/how_to_listen_to_youtube_shows_as_podcasts/ | 2026-05-25 | public discussion | podcast listeners | repeated question | public web | low | User asks how to listen to YouTube shows as podcasts; comments mention link-to-listen workflows. | Anecdotal, older thread. | yes, cautiously |
| DSM-S4 | https://www.producthunt.com/posts/listenbox | 2026-05-25 | launch page | product launch | competitor traction | public web | medium | Listenbox launched as a way to play YouTube in the background using podcast apps. | Launch response not equal to paid demand. | yes |
| DSM-S5 | https://telagon.io/website | 2026-05-25 | product page | Telegram creator tooling | competitor traction | public web | medium | Telagon turns Telegram posts into SEO-indexed web pages with auto-sync and Telegram Stars pricing. | Vendor positioning; no independent buyer proof. | yes |
| DSM-S6 | https://teleblog.webinest.com/teleblog_net/ | 2026-05-25 | product write-up | Telegram creator tooling | competitor traction | public web | medium | Teleblog claims Telegram-to-website, history import, SEO metadata, sitemap, search, analytics, and custom domains. | Vendor/partner write-up; not neutral. | yes |
| DSM-S7 | https://www.reddit.com/r/TelegramBots/comments/1snlwh2/do_telegram_channel_owners_actually_need_websites/ | 2026-05-25 | public discussion | Telegram builders | repeated question | public web | low | Builder asks whether Telegram channel owners need websites and describes a searchable archive experiment. | Early experiment thread; needs creator feedback. | yes, cautiously |
| DSM-S8 | https://northpennnow.com/news/2026/apr/16/telegram-channel-seo-why-your-channel-isnt-indexed-how-to-fix-it-fast/ | 2026-05-25 | article | Telegram SEO | search intent / discovery gap | public web | medium | Article frames Telegram SEO/indexing as a visibility problem for channel owners. | SEO article; may be content-marketing. | yes |
| DSM-S9 | https://dybur.com/ | 2026-05-25 | product page | voice dictation | competitor traction | public web | medium | Dybur positions hotkey voice dictation that works in any text field on macOS/Windows. | Product page, not demand proof. | yes |
| DSM-S10 | https://murmurtype.com/ | 2026-05-25 | product page | voice dictation | competitor traction | public web | medium | Murmur offers hold-hotkey local dictation for Mac with direct cursor insertion. | Crowded category; no public usage proof. | yes |
| DSM-S11 | https://www.reddit.com/r/MacOS/comments/1rzsya2/steno_hold_a_hotkey_speak_and_text_appears_at/ | 2026-05-25 | public discussion | macOS users | social distribution / repeated question | public web | low | Recent launch/discussion around hold-hotkey dictation into any Mac app. | Launch thread; noisy. | yes, cautiously |
| DSM-S12 | https://www.reddit.com/r/macapps/comments/1tb0dv7/dictation_app_that_inserts_text_in_real_time/ | 2026-05-25 | public discussion | macOS users | repeated question | public web | low | User asks for dictation that inserts text in real time rather than delayed paste. | Single thread; exact buyer segment unclear. | yes, cautiously |
| DSM-S13 | https://browserpowers.com/extensions/singlefile | 2026-05-25 | extension analysis | browser extension | store/category demand | public web | medium | SingleFile is an established extension for saving complete web pages offline. | Existing strong incumbent. | yes |
| DSM-S14 | https://stackoverflow.com/questions/36057350/chrome-offline-pages | 2026-05-25 | Q&A thread | browser users/developers | repeated question | public web | medium | User asks about Chrome offline pages and how to access pages offline. | Older; browser behavior changed. | yes |
| DSM-S15 | https://www.reddit.com/r/chrome_extensions/comments/1t9w6uh/chromes_save_as_pdf_kept_ruining_webpages_for_me/ | 2026-05-25 | public discussion | browser extension users | manual workaround | public web | low | User says Chrome Save as PDF ruins pages; built a small extension for offline documentation/tutorial saving. | Recent but anecdotal. | yes, cautiously |

## Search Test Method

The run used `docs/DEMAND_SOURCE_MAP.md` priority order:

1. exact search intent and repeated phrases;
2. store/category and competitor demand;
3. competitor traction;
4. manual workaround evidence;
5. social distribution where the audience is reachable.

Queries were seeded from the map's one-function examples:

- `YouTube to podcast`;
- `Telegram channel to website SEO searchable archive`;
- `voice dictation hotkey any text field`;
- `save page offline Chrome extension`.

## Opportunity Rankings

| Rank | Opportunity | Demand surfaces hit | Decision | Read |
|---:|---|---|---|---|
| 1 | Telegram Channel SEO Site Generator | search intent, competitor traction, repeated question, creator/content discovery gap | `revisit` / experiment-ready | Strongest source-map fit; narrow one-function MVP and visible competitors. |
| 2 | YouTube-to-Podcast Feed for Niche Channels | search intent, competitor traction, product launch, repeated question | `revisit` | Clear demand, but crowded and possibly terms-sensitive around YouTube extraction. |
| 3 | Hotkey Dictation Into Any Text Field | search intent, competitor traction, social distribution, repeated question | `needs_more_evidence` | Very visible demand but heavily crowded; differentiation is weak. |
| 4 | Offline Page Saver for Broken Docs/PDF Workflows | repeated question, manual workaround, store/category demand | `needs_more_evidence` | Real utility pain, but mature incumbents like SingleFile make the wedge narrow. |

## Opportunity 1 - Telegram Channel SEO Site Generator

Portfolio fit: `workflow_discovery`
Decision status: `revisit` / experiment-ready

Claims:

- [cited] Telagon markets a Telegram-to-website flow where every post becomes an SEO-optimized page and new posts auto-sync (DSM-S5).
- [cited] Teleblog positions a similar Telegram channel-to-site product with history import, SEO metadata, sitemap, search, analytics, and custom domains (DSM-S6).
- [cited] A Reddit builder recently asked whether Telegram channel owners need websites and framed the site as a searchable archive (DSM-S7).
- [cited] Telegram SEO/indexing articles frame discoverability as a channel-owner problem (DSM-S8).
- [inference] The one-function MVP is: paste public channel link -> get a static searchable archive preview with sitemap/meta output.
- [insufficient_evidence] Willingness to pay is not proven; current evidence shows competitor existence and creator-discovery pain, not conversion.

Why it moved up:

- It matches several new source-map surfaces at once: creator/content gap,
  search intent, competitor traction, repeated question, and one-function MVP.
- It is closer to the `@its_capitan` source-map anchors than Lead Response SLA.
- It can be tested without private CRM data if using public Telegram channels
  with explicit operator-approved/public-only boundaries.

Fast test:

1. Select 3 public Telegram channels with at least 100 posts.
2. Generate a static archive preview for the latest 30 posts.
3. Produce an SEO/readability report: titles, slugs, missing headings,
   duplicate topics, sitemap preview, and search snippets.
4. Ask channel owners or operators whether this would change publishing or
   monetization behavior.

Kill conditions:

- Telegram website competitors already solve the exact workflow cheaply enough.
- Channel owners care about Telegram-native growth, not Google/search traffic.
- Public channel extraction/sync has terms or access risk that exceeds the
  local static-preview test.

## Opportunity 2 - YouTube-to-Podcast Feed for Niche Channels

Portfolio fit: `workflow_discovery`
Decision status: `revisit`

Claims:

- [cited] Blubrry documents Vid2Pod as a YouTube playlist-to-podcast workflow (DSM-S1).
- [cited] YouCaster and Listenbox position YouTube channel/show listening through podcast-style apps or feeds (DSM-S2, DSM-S4).
- [cited] Reddit users ask how to listen to YouTube shows as podcasts (DSM-S3).
- [inference] The one-function MVP is: paste YouTube channel/playlist -> get private RSS/audio feed preview.
- [insufficient_evidence] The category may be too crowded and terms-sensitive; extraction, hosting, copyright, and YouTube policy risks need review.

Fast test:

- Do not download or redistribute video/audio in v1.
- Build only a playlist audit: episode duration, missing podcast equivalent,
  RSS availability, and "listenability" score.
- Validate with creators/listeners before touching media conversion.

## Opportunity 3 - Hotkey Dictation Into Any Text Field

Portfolio fit: `workflow_discovery`
Decision status: `needs_more_evidence`

Claims:

- [cited] Multiple products market the same workflow: press or hold hotkey,
  speak, and text appears in any text field (DSM-S9, DSM-S10).
- [cited] Recent Reddit discussions show active interest in hotkey dictation,
  local/offline processing, and real-time insertion (DSM-S11, DSM-S12).
- [inference] Demand is visible, but the product category is crowded and
  differentiation likely requires platform-specific polish, privacy, latency,
  or accessibility.
- [insufficient_evidence] No clear portfolio edge or distribution wedge emerged
  from this run.

Verdict:

Reject as a first Radar handoff for now. Keep as competitor-tracking evidence
unless a narrow underserved segment appears, such as `Windows terminal/code
dictation with local model and command-safe paste`.

## Opportunity 4 - Offline Page Saver for Broken Docs/PDF Workflows

Portfolio fit: `workflow_discovery`
Decision status: `needs_more_evidence`

Claims:

- [cited] SingleFile is an established offline page saver extension (DSM-S13).
- [cited] Users ask how to save/access Chrome pages offline (DSM-S14).
- [cited] Recent extension-builder discussion says Chrome Save as PDF can ruin
  documentation/tutorial layouts (DSM-S15).
- [inference] A narrow wedge might be "save developer docs/tutorials as clean
  offline Markdown/PDF with working code blocks," not a generic page saver.
- [insufficient_evidence] Existing incumbents are strong and the missing
  workflow needs sharper proof.

## Comparison With Lead Response SLA

| Candidate | Needs private/operator data? | Source-map fit | Technical difficulty | Current best use |
|---|---:|---|---|---|
| Lead Response SLA Gap Radar | yes | medium | low | Keep as technical MVP/proxy-tested path. |
| Telegram Channel SEO Site Generator | no, if using approved public channels | high | medium | Best next public-data experiment. |
| YouTube-to-Podcast Feed | no for audit; yes/risky for conversion | high | medium-high | Research only until policy/terms boundary is clear. |
| Hotkey Dictation | no | high but crowded | high polish burden | Watch category; do not build first. |
| Offline Page Saver | no | medium | medium | Needs narrower wedge. |

## New Best Test

The next search/source-map test should move from Lead Response SLA to:

**Telegram Channel SEO Site Generator**

One-function MVP:

> public channel URL -> static searchable site preview + SEO gap report

Why:

- It can use public data.
- It matches the new source map directly.
- Existing competitors prove category demand.
- It avoids the missing private CRM data blocker from Lead Response SLA.
- It is easy to kill if channel owners do not care about Google/search traffic.

## Ledger Verdict

Run status: `backfilled-real`

Counts toward evidence gate: yes

Useful human decisions: 0

Research-level decision:

- Promote Telegram Channel SEO Site Generator as the next public-data
  experiment candidate.
- Keep Lead Response SLA as a valid technical MVP, but block further market
  validation until sales lead data or operator feedback exists.
