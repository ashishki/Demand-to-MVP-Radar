# Demand-to-MVP Radar - Compact Session State

Version: 2.1
Date: 2026-05-29
Status: active-production-observation

Full historical prompt archived at
`docs/archive/portfolio-cleanup-2026-05-29/CODEX_PROMPT_full_2026-05-29.md`.

## Current State

- Radar runs on VPS and should produce the first visible weekly report.
- Active focus: report quality, source trust, repeated signal scoring, and
  true Radar weekly operation from Telegram-derived seed intelligence.
- Active task source: `docs/tasks.md`, Phase 19.
- Last completed: Phase 19 boundary review and current task graph completion.
- T65 reviewed the first inspectable VPS weekly artifact from
  `../telegram-research-agent/data/output/digests/2026-W14.md` because no
  committed `reports/mvp_of_week/` Radar report or `/srv/openclaw-you` checkout
  was available on this machine.
- T65 verdict: useful Telegram intelligence input, not yet a decision-grade
  Radar weekly report. Next run needs an explicit Decision Gate block with
  Telegram seed count, external evidence count, source types, repeated-signal
  count, missing evidence, and recommendation gating.
- T66 added `docs/report_eval.md` with explicit scoring rules for useful signal
  rate, evidence quality, duplicate/noise rate, source diversity, and
  recommendation clarity. These scores measure operator report usefulness only;
  they do not prove commercial demand.
- T67 added deterministic source trust records and weekly report sections that
  expose repeated signal count, evidence density, rejection reasons, Decision
  Gate status, Build-Worthy Recommendations, and Interesting Signals.
- T68 added `docs/handoffs/telegram_channel_intelligence_bridge.md` and updated
  `docs/SOURCE_CATALOG.md` with approved channel source policy, evidence
  requirements, report fields, and the boundary between Demand Radar opportunity
  signals and Telegram channel/source intelligence.
- T69 added `demand_mvp_radar/telegram_digest.py` and the `digest-to-seeds`
  CLI command for deterministic local conversion from sanitized Telegram weekly
  digest JSON to Radar seed exports.
- T70 generated the first true Radar weekly artifact at
  `reports/mvp_of_week/mvp-weekly-2026-W14-radar.md` from
  `data/phase19/2026-W14-radar-seeds.json`. The report contains Decision Gate,
  Source Trust And Repeated Signals, Build-Worthy Recommendations, and
  Interesting Signals sections.
- T71 recorded the report-quality row and solo evidence ledger entry. Run 4 is
  useful pipeline evidence but does not count toward the four-run readiness gate
  because the source mix is Telegram-only and external evidence is 0.
- T72 created `docs/audit/PHASE19_OPERATING_DECISION.md`: next operating step is
  public corroboration research for Agent Instruction Conflict Review.
- Cross-repo RADAR-2 hardening added deterministic final-gate rewriting for
  `mvp-of-week`: LLM Markdown Decision Gate and Build-Worthy sections are
  replaced with gated source-mix truth, and JSON `result`/`selected`
  recommendations now agree with the rendered report.
- Cross-repo RADAR-1 changed `mvp-of-week` output to a Candidate Dossier with
  canonical reader-facing status, decision, confidence, next action, evidence,
  missing evidence, next experiment, kill criteria, operator fit, and
  anti-complexity sections. JSON result/selected objects expose the same
  `dossier_status`, and existing-project context cannot be framed as a new
  standalone MVP.
- Cross-repo RADAR-3 added a selected-candidate source-mix truth surface:
  Markdown now has a compact Source Mix card, JSON result/selected objects
  expose machine-readable `selected_source_mix` / `source_mix`, missing
  credentials remain visible, Reddit API usage is distinguished from
  SERP-indexed Reddit pages, and GitHub evidence is labeled as primary or
  repeated variants.
- Cycle 20 deep review passed with Stop-Ship: No, P0: 0, P1: 0, P2: 0.
- Current focused baseline: `tests/test_mvp_of_week.py` passes with 6 tests.

## Active Inputs

- `README.md`
- `docs/PROJECT_PLAN.md`
- `docs/tasks.md`
- `docs/LIVE_SOURCE_PRODUCTION_ROADMAP.md`
- `docs/audit/FIRST_VPS_WEEKLY_REPORT_REVIEW.md`
- `docs/report_eval.md`
- `demand_mvp_radar/source_trust.py`
- `demand_mvp_radar/telegram_digest.py`
- `docs/handoffs/telegram_channel_intelligence_bridge.md`
- `reports/mvp_of_week/mvp-weekly-2026-W14-radar.md`
- `docs/SOLO_EVIDENCE_LEDGER.md`
- `docs/audit/PHASE19_OPERATING_DECISION.md`

## Next Task

none - Phase 19 task graph complete.

## Fix Queue

empty

## Open Findings

none

## Rules

- Do not claim market validation from weak sources.
- Prefer evidence-backed source trust and repeated-signal scoring.
- Telegram intelligence is a bridge to Entropy/Telegram Research work, not a
  private scraping approval.
- The first true Radar weekly report is Telegram-seeded only. It is not a build
  approval and does not count toward the four-run readiness gate.
