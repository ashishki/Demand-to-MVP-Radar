# Solo Evidence Ledger

Status: active operating record; readiness gate incomplete
Updated: 2026-07-13

This ledger records the four real weekly or backfilled weekly runs required
before private beta or hosted work can resume. It is an operating record, not a
demo checklist: every filled run row must point to public or operator-owned
evidence, generated artifacts, reviewed opportunities, decisions, missing
evidence, cost, backup, and privacy checks.

Fixture/demo runs may verify code behavior, but they do not count toward the
four-run readiness gate.

Current reconciled state: `2/4` counting evidence cycles and `0`
human-recorded decisions. The four named slots are not four distinct weekly
windows. The machine-readable reconciliation and artifact checks are in
`reports/evidence/portfolio-audit-2026-07-13/four_slot_decision_log.json`;
the reviewer summary is
`reports/evidence/portfolio-audit-2026-07-13/FOUR_SLOT_DECISION_LOG.md`.

## Run Type Rules

| Run type | Counts toward four-run gate? | Allowed purpose | Required label |
|---|---:|---|---|
| Fixture/demo | no | CI, smoke checks, deterministic examples, development regressions | `fixture/demo` |
| Backfilled real evidence | yes | Historical public/operator-owned evidence reviewed after collection | `backfilled-real` |
| Weekly real evidence | yes | Current weekly public/operator-owned evidence collected for operator review | `weekly-real` |

Real evidence means the source register points to public sources or
operator-owned sources allowed by `docs/open_source_research_protocol.md`.
Credentialed, paid, private community, publishing, outreach, and hosted/SaaS
work still require explicit human approval.

## Four-Run Ledger

| Slot | Run type | Run ID / date | Source families | Report paths | Top opportunities reviewed | Decisions recorded | Missing evidence / gaps | Outcome notes | Counts? |
|---|---|---|---|---|---|---|---|---|---|
| Run 1 | backfilled-real | T62-showcase / 2026-05-23 | public B2B sales ops, AI workplace adoption, workflow/team operations, AI automation operators, backend/API operators, trader workflow | `reports/showcase/portfolio_opportunity_showcase.md` | 5 | 0 human-recorded; report suggests 3 `revisit` and 2 `needs_more_evidence` | buyer proof, competitor scans, operator-owned lead data, compliance review for trading | Public-safe showcase drafted; not yet an operator-reviewed weekly run | no - showcase backfill only |
| Run 2 | backfilled-real | R2-deep-research / 2026-05-23 | public B2B sales ops, CRM operator workflow, lead routing competitors, email response analytics, automation operators, developer platform docs, developer tooling alternatives, AI workplace adoption | `reports/research/solo_evidence_run_2_deep_research.md`, `docs/handoffs/lead_response_sla_gap_radar_handoff.md` | 4 | 0 human-recorded; research recommends Lead Response SLA `revisit` / experiment-ready, Human Approval Map `needs_more_evidence`, API Drift Watch `revisit`, AI Rollout Tracker `reject for now` | operator-owned lead data, CRM-native report examples, first 10 target feedback, API buyer proof | Public-safe deep research completed; Lead Response SLA remains best first experiment, but no build approval | yes |
| Run 3 | backfilled-real | DSM-search-test / 2026-05-25 | search intent, store/category demand, competitor traction, repeated questions, manual workarounds, creator/content discovery gaps | `reports/research/demand_source_map_search_test.md` | 4 | 0 human-recorded; research promotes Telegram Channel SEO Site Generator to next public-data experiment candidate | willingness-to-pay proof, channel-owner feedback, public-channel terms/access review, competitor pricing/use proof | Source-map search found a better public-data test than Lead Response SLA; Lead SLA remains technical/proxy-tested only | yes |
| Run 4 | weekly-real, Telegram-seeded only | mvp-weekly-2026-W14-radar / 2026-05-29 | Telegram weekly intelligence seed export | `reports/mvp_of_week/mvp-weekly-2026-W14-radar.md`, `data/phase19/2026-W14-radar-seeds.json` | 5 report-level candidates | 0 human-recorded; report recommends `revisit_with_evidence_gap` / `needs_more_evidence` only | public corroboration, competitor/workaround proof, non-Telegram evidence for same pain | True Radar report generated and reviewed; build-worthy gate stayed closed because source diversity is one family and external evidence is 0 | no - Telegram-only source mix does not count toward four-run gate |

The Run 4 report and seed paths above describe the historical operator record,
but those generated files are absent from a clean clone. Their contents and
checksums therefore cannot be independently verified from this repository and
must not be counted as published evidence. The reconciliation records this as
a documentation defect instead of copying ignored, workstation-owned output.

## Per-Run Detail Template

Copy this section for each filled run slot.

### Run N - pending

| Field | Value |
|---|---|
| Run type | `fixture/demo` / `backfilled-real` / `weekly-real` |
| Counts toward gate | yes/no |
| Run ID | pending |
| Run date | pending |
| Data window | pending |
| Source families | pending |
| Source register path | pending |
| Weekly report path | pending |
| Dossier paths | pending |
| Source value report path | pending |
| Evidence delta report path | pending |
| Retrieval corpus version | pending |
| Index age at review | pending |
| Estimated cost / budget ceiling | pending |
| Backup verification | pending |
| Privacy check | pending |

Reviewed opportunities:

| Opportunity | Portfolio fit | Decision | Evidence basis | Missing evidence | Outcome note |
|---|---|---|---|---|---|
| pending | pending | pending | pending | pending | pending |

Run verdict:

- Useful decisions: pending
- Source families that helped: pending
- Source families to keep/demote/disable: pending
- Follow-up evidence to collect: pending
- Operator review time: pending
- Gate status: pending

### Run 4 - Telegram-Seeded Radar Weekly Report

| Field | Value |
|---|---|
| Run type | `weekly-real`, Telegram-seeded only |
| Counts toward gate | no - real Telegram digest input, but single-family evidence and 0 external corroboration |
| Run ID | mvp-weekly-2026-W14-radar |
| Run date | 2026-05-29 |
| Data window | Telegram digest `2026-W14` from `telegram-research-agent` |
| Source families | Telegram weekly intelligence seed export |
| Source register path | `data/phase19/2026-W14-radar-seeds.json` |
| Weekly report path | `reports/mvp_of_week/mvp-weekly-2026-W14-radar.md` |
| Dossier paths | n/a |
| Source value report path | n/a |
| Evidence delta report path | n/a |
| Retrieval corpus version | n/a - local seed-to-weekly-report run |
| Index age at review | n/a |
| Estimated cost / budget ceiling | USD 0 / LLM disabled with `DMR_LLM_PROVIDER=none` |
| Backup verification | not run |
| Privacy check | local generated artifact from sanitized Telegram-derived digest; no private channels, paid sources, outreach, publishing, hosted/SaaS, or raw credentialed exports approved |

Reviewed opportunities:

| Opportunity | Portfolio fit | Decision | Evidence basis | Missing evidence | Outcome note |
|---|---|---|---|---|---|
| Agent Instruction Conflict Review | `evaluation_first_delivery` | `revisit_with_evidence_gap` | 1 Telegram seed from `@llm_under_hood`; score 65; Decision Gate reason `source_mix_gate` | competitor/workaround corroboration; non-Telegram public evidence for the same pain | selected report topic but not build-worthy |
| OpenClaw assistant setup signal | `workflow_discovery` | `revisit_with_evidence_gap` | 1 Telegram seed; score 53 | competitor/workaround corroboration; non-Telegram public evidence | interesting signal only |
| Model comparison signal | `workflow_discovery` | `revisit_with_evidence_gap` | 1 Telegram seed; score 53 | competitor/workaround corroboration; non-Telegram public evidence | interesting signal only |
| Course/content signal | `workflow_discovery` | `needs_more_evidence` | 1 Telegram seed; score 48 | competitor/workaround corroboration; non-Telegram public evidence | weak single-family signal |
| AI-native company workflow signal | `workflow_discovery` | `needs_more_evidence` | 1 Telegram seed; score 48 | competitor/workaround corroboration; non-Telegram public evidence | weak single-family signal |

Run verdict:

- Useful decisions: 0 human-recorded; report-level recommendations only.
- Source families that helped: Telegram weekly intelligence was useful for seed generation and topical clustering.
- Source families to keep/demote/disable: keep Telegram seed export as an input; demote Telegram-only candidates until public corroboration exists.
- Follow-up evidence to collect: public examples of instruction-conflict review pain, competitor/workaround pages, repeated non-Telegram questions, and one operator-owned example if available.
- Operator review time: pending.
- Gate status: no-count weekly real run; useful for pipeline proof, insufficient for four-run readiness.

### Run 1 - T62 Showcase Backfill

| Field | Value |
|---|---|
| Run type | `backfilled-real` |
| Counts toward gate | no - public showcase artifact, not a full weekly pipeline run |
| Run ID | T62-showcase |
| Run date | 2026-05-23 |
| Data window | Public sources captured on 2026-05-23 |
| Source families | public B2B sales ops; AI workplace adoption; workflow/team operations; AI automation operators; backend/API operators; trader workflow |
| Source register path | `reports/showcase/portfolio_opportunity_showcase.md#source-register` |
| Weekly report path | n/a |
| Dossier paths | `reports/showcase/portfolio_opportunity_showcase.md` |
| Source value report path | n/a |
| Evidence delta report path | n/a |
| Retrieval corpus version | n/a - manual public research artifact |
| Index age at review | n/a |
| Estimated cost / budget ceiling | USD 0 / n/a |
| Backup verification | not run |
| Privacy check | public URLs only; no private exports, credentials, raw notes, or private reports |

Reviewed opportunities:

| Opportunity | Portfolio fit | Decision | Evidence basis | Missing evidence | Outcome note |
|---|---|---|---|---|---|
| Lead Response SLA Gap Radar | `lead_response_sla` | `revisit` | Workato lead-response benchmark plus portfolio fit | operator-owned lead data; competitor/pricing proof | selected for 10-day MVP experiment candidate |
| Human Approval Map for AI Automations | `workflow_discovery` | `needs_more_evidence` | public AI automation discussion | more source families; buyer proof | likely Workflow-to-Agent Studio feature |
| Third-Party API Drift Watch | `workflow_discovery` | `revisit` | public backend/API discussion plus GitHub API docs | repeated demand; competitor scan | possible workflow discovery handoff |
| AI Rollout Training Gap Tracker | `ai_rollout_training` | `revisit` | Microsoft/LinkedIn and Asana/Anthropic AI adoption reports | manager pain; willingness-to-pay proof | useful but crowded |
| Trader Research Review Digest | `trading_research_reports` | `needs_more_evidence` | public trader journaling discussions | compliance review; non-Reddit sources | keep secondary/off-risk until validated |

Run verdict:

- Useful decisions: 0 human-recorded; 5 report-level provisional decisions.
- Source families that helped: B2B sales ops, AI adoption reports, Reddit operator discussions, official API docs.
- Source families to keep/demote/disable: keep public research reports and official docs; demote Reddit-only opportunities until corroborated.
- Follow-up evidence to collect: operator-owned lead-response data, competitor scans, first 10 target feedback, compliance review for trading workflow.
- Operator review time: pending.
- Gate status: partial showcase artifact; does not count toward the four-run readiness gate yet.

### Run 2 - Deep Research Backfill

| Field | Value |
|---|---|
| Run type | `backfilled-real` |
| Counts toward gate | yes - public source register, privacy check, and reviewed opportunities are present |
| Run ID | R2-deep-research |
| Run date | 2026-05-23 |
| Data window | Public sources captured on 2026-05-23 |
| Source families | public B2B sales ops; CRM operator workflow; lead routing competitors; email response analytics; automation operators; developer platform docs; developer tooling alternatives; AI workplace adoption |
| Source register path | `reports/research/solo_evidence_run_2_deep_research.md#source-register` |
| Weekly report path | `reports/research/solo_evidence_run_2_deep_research.md` |
| Dossier paths | `reports/research/solo_evidence_run_2_deep_research.md` |
| Source value report path | n/a - manual public research artifact |
| Evidence delta report path | n/a - manual public research artifact |
| Retrieval corpus version | n/a - manual public research artifact |
| Index age at review | n/a |
| Estimated cost / budget ceiling | USD 0 / n/a |
| Backup verification | not run |
| Privacy check | public URLs only; no private exports, credentials, raw notes, CRM data, or private reports |

Reviewed opportunities:

| Opportunity | Portfolio fit | Decision | Evidence basis | Missing evidence | Outcome note |
|---|---|---|---|---|---|
| Lead Response SLA Gap Radar | `lead_response_sla` | `revisit` / experiment-ready | Workato benchmark, HubSpot community operator questions, lead-routing competitors, response-time analytics competitor | operator-owned sample CSV; CRM-native report examples; first 10 target feedback | strongest first experiment; keep scope local CSV-to-Markdown report |
| Human Approval Map for AI Automations | `workflow_discovery` | `needs_more_evidence` | n8n approval workflow discussions plus Zapier approval automation positioning | real workflow examples; proof standalone artifact changes behavior | likely feature discovery for Workflow-to-Agent Studio |
| Third-Party API Drift Watch | `workflow_discovery` | `revisit` | GitHub breaking-change docs/changelog, OpenAPI diff alternative, integration monitoring content | repeated buyer pain; target project API list; competitor/pricing scan | plausible but crowded; test with weekly drift digest |
| AI Rollout Training Gap Tracker | `ai_rollout_training` | `reject` for now | Microsoft/LinkedIn and Asana/Anthropic adoption reports | specific buyer/workflow pain; willingness-to-pay proof | too broad and crowded for current portfolio |

Run verdict:

- Useful decisions: 0 human-recorded; 4 research-level recommendations.
- Source families that helped: CRM operator workflow, lead-routing competitors, public benchmark articles, official changelogs/docs.
- Source families to keep/demote/disable: keep CRM/community operator workflow and competitor pages; demote broad AI workplace reports unless tied to direct buyer pain.
- Follow-up evidence to collect: anonymized lead-response CSV schema, first 10 target feedback, examples of existing CRM SLA reports, and two proof points that a diagnostic report changes operator behavior.
- Operator review time: pending.
- Gate status: counts as one public backfilled evidence run; human-decision and private-beta gates remain blocked.

### Run 3 - Demand Source Map Search Test

| Field | Value |
|---|---|
| Run type | `backfilled-real` |
| Counts toward gate | yes - public source register and reviewed opportunities are present |
| Run ID | DSM-search-test |
| Run date | 2026-05-25 |
| Data window | Public sources captured on 2026-05-25 |
| Source families | search intent; store/category demand; competitor traction; repeated questions; manual workarounds; creator/content discovery gaps |
| Source register path | `reports/research/demand_source_map_search_test.md#source-register` |
| Weekly report path | `reports/research/demand_source_map_search_test.md` |
| Dossier paths | `reports/research/demand_source_map_search_test.md` |
| Source value report path | n/a - manual public research artifact |
| Evidence delta report path | n/a - manual public research artifact |
| Retrieval corpus version | n/a - manual public research artifact |
| Index age at review | n/a |
| Estimated cost / budget ceiling | USD 0 / n/a |
| Backup verification | not run |
| Privacy check | public URLs only; no private exports, credentials, raw notes, CRM data, or private reports |

Reviewed opportunities:

| Opportunity | Portfolio fit | Decision | Evidence basis | Missing evidence | Outcome note |
|---|---|---|---|---|---|
| Telegram Channel SEO Site Generator | `workflow_discovery` | `revisit` / experiment-ready | Telagon, Teleblog, Telegram SEO article, Reddit builder question | channel-owner feedback; competitor pricing/use proof; public-channel terms/access review | best next public-data experiment |
| YouTube-to-Podcast Feed for Niche Channels | `workflow_discovery` | `revisit` | Blubrry Vid2Pod, YouCaster, Listenbox, Reddit listener question | YouTube policy/terms review; creator/listener feedback; conversion risk | promising but terms-sensitive |
| Hotkey Dictation Into Any Text Field | `workflow_discovery` | `needs_more_evidence` | multiple product pages and recent Reddit launch/question threads | differentiated segment; distribution wedge | too crowded for first build |
| Offline Page Saver for Broken Docs/PDF Workflows | `workflow_discovery` | `needs_more_evidence` | SingleFile category evidence, Stack Overflow question, recent Chrome extension discussion | sharper missing workflow proof | existing incumbents are strong |

Run verdict:

- Useful decisions: 0 human-recorded; 4 research-level recommendations.
- Source families that helped: competitor traction, repeated questions, creator/content discovery gaps, manual workaround threads.
- Source families to keep/demote/disable: keep demand-source-map query seeds; demote broad trend searches unless tied to one-function MVPs.
- Follow-up evidence to collect: public Telegram channel sample, owner feedback, competitor pricing and use proof, access/terms boundary for channel mirroring.
- Operator review time: pending.
- Gate status: counts as one public backfilled evidence run; human-decision and private-beta gates remain blocked.

## Fixture / Demo Run Register

Use this section for runs that are useful for testing but must not be counted as
real operating evidence.

| Run ID / date | Fixture or demo input | Purpose | Result | Why it does not count |
|---|---|---|---|---|
| lead-sla-open-proxy / 2026-05-25 | `tests/fixtures/lead_sla/open_proxy_leads.csv` | Test Lead Response SLA CSV analysis, PII redaction, invalid-row quarantine, and Markdown report output with public/proxy support-ticket schema. | `reports/private/lead_sla_open_proxy_report.md`; 10 valid rows, 7 SLA misses, 2 invalid rows; command completed. | Uses a small proxy fixture based on public support-ticket/CRM schemas, not row-level sales lead evidence. |

## Readiness Rollup

| Gate | Current status | Evidence |
|---|---|---|
| Four real/backfilled runs complete | not complete | 2/4 counting runs complete: Runs 2 and 3. Run 1 is showcase-only and Run 4 is Telegram-only/no-count. |
| At least 20 opportunities reviewed | not complete | 8 gate-counting opportunities reviewed across Runs 2-3; 5 showcase-only opportunities in Run 1; 5 Telegram-seeded no-count opportunities in Run 4. |
| At least three useful operator decisions | not complete | 0 human-recorded decisions; Run 2 has research-level recommendations only. |
| One selected opportunity has a 7-14 day MVP experiment pack | partial | Lead Response SLA has a 7-10 day local CSV report experiment candidate and handoff, but no executed experiment yet. |
| One cross-project handoff pack ready | complete | `docs/handoffs/lead_response_sla_gap_radar_handoff.md` updated by Run 2. |
| Private beta gate | blocked | Needs 4 counting runs, useful human decisions, backup verification, support-burden proof, and operator-owned evidence. |

## Update Procedure

1. Run or backfill the weekly evidence loop with public/operator-owned sources.
2. Record source families and source register paths before reviewing decisions.
3. Add report, dossier, evidence delta, source value, and experiment artifact
   paths after generation.
4. Record every reviewed opportunity with a human-owned decision:
   `build`, `reject`, `revisit`, or `needs_more_evidence`.
5. Keep unsupported claims marked as `insufficient_evidence` and list missing
   source families.
6. Mark `Counts?` as `yes` only when the run uses real public or
   operator-owned evidence and passes privacy checks.
7. Update `docs/audit/PRODUCTION_READINESS_REVIEW.md` only after all four run
   slots and the readiness rollup are backed by artifacts.
