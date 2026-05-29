# Telegram Channel Intelligence Bridge

Status: first safe bridge policy
Date: 2026-05-29
Source project: Demand-to-MVP Radar
Adjacent project: Telegram Research Agent / Entropy channel intelligence

## Purpose

This bridge defines how Demand-to-MVP Radar may hand useful channel-derived
signals to Telegram channel intelligence work without becoming a generic
Telegram scraper.

Demand Radar remains an opportunity radar. It uses Telegram-derived evidence to
identify possible product pains, missing evidence, source quality, and
one-function MVP candidates.

Telegram channel intelligence is a separate analysis surface. It may evaluate
channel reliability, author/source behavior, topic focus, signal quality, and
receipt-style evidence trails. It must not use Demand Radar handoffs as approval
to scrape private communities, publish channel reports, contact channel owners,
or trade on channel content.

## Approved Channel Source Policy

Allowed channel inputs:

- sanitized `telegram-research-agent` exports already produced by the operator;
- public Telegram channel links that the operator explicitly approves for
  opportunity-signal review;
- channel-level summaries that contain no credentials, cookies, private chat
  exports, private author identifiers, or raw local file paths;
- message references when the source is public or operator-owned and safe to
  store locally.

Forbidden channel inputs:

- private chats, private groups, paid channels, or credentialed channel exports
  without explicit human approval;
- raw session files, cookies, bot tokens, API IDs, API hashes, phone numbers, or
  account identifiers;
- broad channel crawling beyond an allowlisted source file;
- storing raw private message text in git;
- using Radar output to initiate outreach, publication, trading, paid access, or
  hosted SaaS behavior.

Approval rule: a channel is approved only for the specific source purpose and
data window recorded in the source register. Approval for opportunity-signal
review is not approval for trader/source intelligence, public publishing, or
contacting people.

## Evidence Requirements

Every bridge handoff must include:

| Field | Requirement |
|---|---|
| Channel/source reference | Public URL, approved export ID, or redacted source ID. |
| Data window | Start/end date or report week. |
| Capture method | `telegram-research-agent export`, manual public URL review, or other approved method. |
| Signal type | Opportunity pain, repeated question, workaround, competitor mention, platform timing, creator/content gap, or source-quality note. |
| Evidence count | Number of message/report items used. |
| Repeated signal count | Count of repeated variants of the same signal. |
| Source trust note | Why the source is high/medium/low trust for this use. |
| External corroboration | Required for Demand Radar build-worthy recommendations. |
| Missing evidence | What must be collected before stronger claims. |
| Privacy check | Confirmation that no private raw exports, credentials, or unsafe identifiers are in the handoff. |

Telegram-only evidence may seed an opportunity, but it cannot justify
`focused_experiment` or build-like language in Demand Radar. It must remain
`revisit_with_evidence_gap` or `needs_more_evidence` until non-Telegram evidence
corroborates the same pain.

## Bridge Report Fields

Use this minimal handoff shape when passing a channel signal to Telegram
intelligence work:

```yaml
bridge_type: telegram_channel_intelligence_signal
source_project: demand-to-mvp-radar
source_artifact: docs/report_eval.md
report_week: YYYY-WW
channel_scope:
  approval_status: approved_public | approved_operator_owned | not_approved
  source_ref: redacted-or-public-reference
  data_window: YYYY-MM-DD..YYYY-MM-DD
demand_radar_signal:
  opportunity_title: short title
  signal_type: repeated_question | workaround | competitor_mention | creator_content_gap | other
  recommendation: needs_more_evidence | revisit_with_evidence_gap | focused_experiment
  decision_gate_reason: source_mix_gate | insufficient_evidence | focused_experiment
source_quality:
  evidence_count: 0
  repeated_signal_count: 0
  evidence_density: 0.0
  rejection_reasons: []
required_corroboration:
  - public search/source family still needed
privacy:
  raw_private_data_included: false
  credentials_included: false
  safe_for_git: true
```

## Boundary: Demand Radar vs Channel Intelligence

| Boundary | Demand-to-MVP Radar | Telegram channel intelligence |
|---|---|---|
| Primary question | Is there a one-function MVP opportunity worth reviewing? | Is this channel/source useful, reliable, noisy, or risky? |
| Unit of analysis | Opportunity candidate, evidence packet, report section, decision gate. | Channel, author/source pattern, topic stream, source-quality receipt. |
| Strong output | `build`, `reject`, `revisit`, or `needs_more_evidence` recommendation for an opportunity. | Source trust/referee verdict, channel utility note, topic/source-quality report. |
| Required corroboration | Non-Telegram public evidence before build-like recommendations. | Multiple messages/windows or external checks before source-quality claims. |
| Forbidden leap | Telegram signal -> build-worthy opportunity. | Radar handoff -> generic scraping, outreach, publishing, trading, or paid-channel approval. |

Demand Radar may say: "Telegram Channel SEO Site Generator is interesting, but
it needs public-channel owner feedback and external competitor/pricing evidence."

Telegram channel intelligence may say: "This channel repeatedly surfaces
creator tooling gaps, but its evidence is noisy and should be downranked unless
corroborated."

Neither system may say: "The market is validated" from Telegram-only evidence.

## First Bridge Candidate

Initial candidate: Telegram Channel SEO Site Generator.

Why it is eligible for bridge review:

- It appeared in public/source-map research as a repeated creator/content
  discovery gap.
- It can be tested on public or operator-approved channels without private
  scraping.
- It is close to the operator's Telegram-native research and reporting stack.

Required before a focused experiment:

- at least one approved public channel sample;
- public competitor/pricing/use proof;
- channel-owner or creator feedback;
- explicit access/terms review for channel mirroring or static previews;
- source trust record showing repeated signal count and rejection reasons.

## Human Approval Boundaries

Human approval is required before:

- adding a new Telegram channel to an allowlist;
- using private, paid, or credentialed channel sources;
- publishing any channel-derived report externally;
- contacting channel owners, authors, or communities;
- changing source trust weights or recommendation thresholds;
- sharing raw Telegram exports outside the local operator environment.

This bridge approves only a document and data-shape handoff. It does not approve
collection expansion, private scraping, paid access, public publishing, or
outreach.

## T68 Acceptance Status

| AC | Status | Evidence |
|---|---|---|
| AC-1: approved channel source policy, evidence requirements, and report fields | PASS | Sections above define allowed/forbidden inputs, evidence requirements, and YAML report fields. |
| AC-2: distinguish Demand Radar signals from Telegram trader/source intelligence | PASS | Boundary table separates opportunity decisions from channel/source-quality intelligence. |
