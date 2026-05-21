# Private Beta Source Onboarding

Status: gated
Date: 2026-05-21

Private beta is allowed only after the four-run production readiness review is green and the operator has recorded at least three useful personal decisions from the local system.

## Setup

Beta users run the product locally. They install the CLI, configure local `DMR_DATA_DIR` and `DMR_REPORT_DIR`, run `demand-mvp-radar health --json`, and verify that generated reports stay outside git.

## Source Selection

Start with low-risk sources: RSS, Hacker News, Stack Exchange, GitHub public search, and sanitized owned exports. Add SERP, YouTube, Product Hunt, Reddit, Discord allowlisted channels, and Telegram approved channels only when the beta user explicitly approves each source.

## Credential Environment Variables

Credentials must be provided only as environment variable values in ignored local files or shell state. Supported names include `GITHUB_TOKEN`, `SERPAPI_API_KEY`, `YOUTUBE_API_KEY`, `PRODUCT_HUNT_TOKEN`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `DISCORD_BOT_TOKEN`, and `TELEGRAM_BOT_TOKEN`.

## Local Scheduling

Use the user-level systemd templates for weekly local runs. Beta users own their schedule, source scope, and budget ceilings. Maintainers should not run scheduled collection on behalf of beta users.

## Backup

Before onboarding new sources, beta users back up the SQLite database, report directory, raw snapshot directory, and ignored local source configs. Backups must be encrypted or kept on trusted local storage.

## Privacy

Never send maintainers raw exports, SQLite databases, generated private reports, raw Discord or Telegram messages, private notes, cookies, API keys, bot tokens, OAuth refresh tokens, ignored env files, channel IDs, guild IDs, private repository URLs, or unredacted source locators.

## Support Boundaries

Maintainers may review redacted health JSON, source value summaries, stack traces without secrets, and sanitized fixture reproductions. Maintainers do not collect sources, hold credentials, receive private datasets, or provide hosted access during private beta.

## Readiness Gate

Private beta remains blocked until:

- `docs/audit/PRODUCTION_READINESS_REVIEW.md` marks the four-run readiness review as ready.
- At least three useful personal decisions are recorded with cited evidence.
- Source value reports show that at least two source families improve decisions.
- Backup and restore have been tested locally.
- The operator confirms that support burden is manageable without hosted infrastructure.
