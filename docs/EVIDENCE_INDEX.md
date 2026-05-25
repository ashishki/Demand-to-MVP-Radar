# Evidence Index

Status: retrieval index, not authority. Evidence rows point to canonical artifacts or future generated outputs.

| ID | Date | Evidence Type | Artifact | Scope | Notes |
|----|------|---------------|----------|-------|-------|
| E-001 | 2026-05-19 | Project brief | `templates/PROJECT_BRIEF.md` | Problem fit, users, scope, AI boundaries, data, integrations, constraints, success metrics | Input used to generate Phase 1 architecture package. |
| E-002 | 2026-05-19 | Architecture package | `docs/ARCHITECTURE.md` | Solution shape, profiles, runtime, RAG/tool design | Canonical system design. |
| E-003 | 2026-05-19 | Task graph | `docs/tasks.md` | Full implementation sequence and acceptance criteria | Implementation authority. |
| E-004 | 2026-05-19 | Retrieval evaluation plan | `docs/retrieval_eval.md` | RAG baseline, query set, regression criteria | Must be updated by RAG-tagged tasks. |
| E-005 | 2026-05-19 | Tool-use evaluation plan | `docs/tool_eval.md` | Tool schema, permission, audit, retry checks | Must be updated by Tool-Use-tagged tasks. |
| E-006 | 2026-05-19 | RAG reference repo | `docs/IMPLEMENTATION_REFERENCE_MAP.md` | Maps `ashishki/Dream_Motif_Interpreter` RAG patterns to current implementation tasks | Use as implementation guidance, not canonical authority. |
| E-007 | 2026-05-23 | Public showcase opportunity report | `reports/showcase/portfolio_opportunity_showcase.md` | Five portfolio-relevant opportunity dossiers, public source register, claim labels, missing evidence, and selected 10-day MVP experiment candidate | T62 artifact; public-safe research only, not a human-recorded build decision. |
| E-008 | 2026-05-23 | Cross-project handoff pack | `docs/handoffs/lead_response_sla_gap_radar_handoff.md` | Lead Response SLA Gap Radar handoff with problem, ICP, public evidence, workflow assumptions, MVP scope, risks, and missing data requests | T63 artifact for Lead Response SLA Agent; not a build approval. |
| E-009 | 2026-05-23 | Solo evidence readiness review | `docs/audit/SOLO_EVIDENCE_READINESS_REVIEW.md` | Phase 17 readiness verdict, four-run ledger status, useful-decision count, source value notes, support burden, and hosted/SaaS gate | T64 artifact; verdict is continue personal evidence cycle, private beta and hosted/SaaS blocked. |
| E-010 | 2026-05-23 | Phase 17 deep review and project completion report | `docs/archive/PHASE17_REVIEW.md`, `docs/audit/PHASE_REPORT_LATEST.md`, `docs/audit/PROJECT_COMPLETE.md` | Cycle 18 review, Phase 17 completion status, and project task-queue completion verdict | Deep review passed with Stop-Ship: No; private beta and hosted/SaaS remain blocked pending real operating evidence. |
| E-011 | 2026-05-23 | Solo evidence deep research backfill | `reports/research/solo_evidence_run_2_deep_research.md`, `docs/handoffs/lead_response_sla_gap_radar_handoff.md` | Public source register, pressure-test scorecard, competitor/current-behavior map, Lead Response SLA data request, and updated handoff | Counts as Run 2 public backfilled evidence; no human build decision recorded. |
| E-012 | 2026-05-25 | Lead SLA open-data technical test | `reports/research/lead_sla_open_data_test.md`, `reports/private/lead_sla_open_proxy_report.md`, `tests/fixtures/lead_sla/open_proxy_leads.csv` | Public/proxy source register, local CSV SLA analyzer, PII-redacted Markdown report, and fixture/demo ledger entry | Technical MVP test passed; does not count as market evidence because row-level sales lead data is still missing. |
| E-013 | 2026-05-25 | Demand source map search test | `reports/research/demand_source_map_search_test.md`, `docs/DEMAND_SOURCE_MAP.md` | Public source-map search run across search intent, competitor traction, repeated questions, manual workarounds, and creator/content discovery gaps | Counts as Run 3 public backfilled evidence; promotes Telegram Channel SEO Site Generator as the next public-data experiment candidate. |

## Evidence Index Rules

- Add a row when a task produces retrieval metrics, tool metrics, source-quality findings, audit reports, or decision-grade opportunity examples.
- Every row must point to an actual artifact.
- This file helps agents find proof; it does not replace the underlying artifact.
