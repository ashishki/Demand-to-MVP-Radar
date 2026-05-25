# Open-Source Research Protocol

Status: active
Date: 2026-05-23

This protocol is mandatory for solo-showcase and weekly evidence tasks when the
existing repository fixtures or local source exports do not contain enough
decision-grade evidence.

## When To Research

The agent must collect additional public evidence instead of stopping when a
task requires:

- market demand examples;
- public complaints, workaround descriptions, or buying intent;
- competitor or alternative behavior;
- source diversity for an opportunity dossier;
- public examples for a portfolio showcase;
- missing corroboration for `build`, `reject`, `revisit`, or `needs_more_evidence`.

## Allowed Sources

- public web pages;
- public GitHub issues, discussions, repositories, and READMEs;
- public Hacker News, Stack Exchange, Reddit, Product Hunt, YouTube, RSS, and
  documentation pages;
- official public APIs and exports already represented in `docs/SOURCE_CATALOG.md`
  when their terms, cost, and credential requirements fit the current task;
- public competitor landing pages, pricing pages, changelogs, docs, app-store
  listings, and review pages when captured as short cited summaries;
- public Telegram channel exports only when explicitly approved by the
  operator;
- operator-owned notes after redaction.

Prefer sources with stable URLs, timestamps, source-owner context, and direct
user pain or workaround language. Broad trend articles can provide context, but
they do not count as direct demand proof unless they cite concrete user behavior.

## Forbidden Sources

- private Telegram groups, private Discord channels, private repositories, or
  credentialed sources without explicit human approval;
- paywalled or terms-risky scraping;
- automated scraping where an official API, RSS feed, export path, or manual
  cited snapshot is the safer path;
- paid APIs, credentialed APIs, private beta communities, or account-gated data
  unless the task explicitly records human approval;
- raw personal data, credentials, cookies, tokens, private channel IDs, or
  unredacted usernames in committed artifacts;
- local file paths, private note contents, raw source exports, and generated
  private reports unless sanitized and already allowed by the task scope;
- unsupported claims about market size, revenue, or buyer demand without cited
  evidence.

## Required Research Artifact

Each research task must produce a small source register, either as a generated
report or as a section in the task artifact. The register is the audit trail for
why a claim is allowed to influence a dossier, review, or handoff pack:

| Field | Required |
|---|---|
| source_id | yes |
| source_url_or_locator | yes |
| captured_at | yes |
| source_type | yes |
| source_family | yes |
| access_method | yes |
| trust_tier | yes |
| why_it_matters | yes |
| extracted_signal | yes |
| cited_claims_supported | yes |
| limitations | yes |
| private_or_sensitive_fields_redacted | yes |
| can_support_decision | yes/no |

Store links and short extracted snippets or summaries. Do not commit large raw
page dumps unless a task explicitly creates a sanitized fixture.

## Claim Rule

Every opportunity claim must be labeled as exactly one of:

- cited by a public source;
- cited by operator-owned evidence;
- marked as `inference`;
- marked as `insufficient_evidence`.

Claim handling rules:

- A cited claim must point to a source register row and explain what the source
  actually supports.
- An `inference` must name the cited facts it is derived from and must not be
  presented as direct market evidence.
- `insufficient_evidence` is the required label when the current sources do not
  support the claim, even if the opportunity still looks plausible.
- Search volume, launch copy, trend coverage, or one community thread is not
  enough to claim willingness to pay.
- Deterministic scoring, thresholds, and final decision routing remain owned by
  code and human review; research notes must not manually change scores.

The agent must not upgrade an opportunity to `build` from one source family
alone. Public research should improve the evidence pack, not replace human
decision ownership.

## Minimum Source Diversity

Before a researched opportunity can support `build`, collect at least two
independent source families unless the task explicitly records why that is not
possible. Good combinations include:

- developer pain source plus competitor/pricing source;
- forum or Q&A complaint plus GitHub issue/discussion evidence;
- official docs/changelog friction plus public workaround discussion;
- operator-owned signal plus public corroboration.

If diversity is missing, keep the decision as `revisit` or
`needs_more_evidence` and list the exact missing source family.
