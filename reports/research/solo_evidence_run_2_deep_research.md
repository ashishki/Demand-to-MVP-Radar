# Solo Evidence Run 2 - Deep Research Backfill

Status: public-safe research artifact
Date: 2026-05-23
Run type: `backfilled-real`
Counts toward four-run evidence gate: yes, as a public research run
Decision owner: human operator

This run deepens the T62 showcase with current public evidence and competitor
context. It does not approve `build`, private beta, hosted/SaaS, outreach,
CRM mutation, or credentialed integrations.

## Source Register

| ID | Source URL / locator | Captured at | Source type | Source family | Access method | Trust tier | Why it matters | Extracted signal | Cited claims supported | Limitations | Redacted? | Can support decision? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R2-S1 | https://www.workato.com/the-connector/lead-response-time-study/ | 2026-05-23 | benchmark article | public B2B sales ops | public web | medium | Baseline pain anchor for slow B2B inbound response. | Workato's 2026 mystery-shopper study reports only one of 114 companies sent a personalized email within 5 minutes and average personalized email response was 11h54m. | B2B inbound follow-up gaps remain visible. | Vendor-authored and adjacent to Workato's product category. | yes | yes |
| R2-S2 | https://community.hubspot.com/t5/Reporting-Analytics/Lead-Response-Time-Reporting/td-p/1154905 | 2026-05-23 | public support/community thread | CRM operator workflow | public web | medium | Direct operator asks for lead response time reporting in a CRM reporting context. | A HubSpot community user describes trying to track rep lead response time from lead creation to first call/email/meeting. | Some CRM operators need first-response reporting and struggle to configure it. | Single thread; may be solvable in native HubSpot workflows. | yes | yes |
| R2-S3 | https://community.hubspot.com/t5/Lists-Lead-Scoring-Workflows/Tracking-Lead-Response-Time/td-p/1116900 | 2026-05-23 | public support/community thread | CRM operator workflow | public web | medium | Shows tracking response time can require workflow/report setup rather than being obvious. | A HubSpot community user asks how to determine how long it takes sales reps to respond to leads after creation. | Lead response tracking remains a practical setup problem for small CRM operators. | Single platform thread; not willingness-to-pay proof. | yes | yes |
| R2-S4 | https://www.chilipiper.com/distro | 2026-05-23 | competitor/product page | lead routing competitor | public web | medium | Shows established vendors frame inbound conversion around routing speed and qualification. | Chili Piper Distro is positioned around qualifying, routing, and converting inbound leads. | Lead response/routing is an existing commercial category. | Product page, not independent demand proof; may solve beyond diagnostic SLA scope. | yes | yes |
| R2-S5 | https://leandata.com/solutions/routing/ | 2026-05-23 | competitor/product page | lead routing competitor | public web | medium | Shows enterprise-grade lead routing and matching as a mature alternative. | LeanData positions routing around matching, assigning, and routing leads/accounts to the right reps. | Mature buyers may already expect routing platforms rather than a standalone report. | Enterprise-oriented; pricing and SMB fit need deeper validation. | yes | yes |
| R2-S6 | https://timetoreply.com/ | 2026-05-23 | competitor/product page | email response analytics competitor | public web | medium | Shows response-time analytics exist outside CRM-native reports. | timetoreply positions email response-time analytics and SLA monitoring for teams. | Response-time reporting has commercial alternatives; diagnostic wedge must be narrower. | Email-centric; not necessarily lead-form to first-response workflow. | yes | yes |
| R2-S7 | https://community.n8n.io/t/user-approval-workflow/6619 | 2026-05-23 | public support/community thread | automation operators | public web | medium | Direct workflow automation request for manual approval before continuing. | An n8n user asks how to wait for a user to approve or reject before proceeding. | Human approval gates are concrete automation workflow pain. | Older thread; may be partly solved by platform features. | yes | yes |
| R2-S8 | https://community.n8n.io/t/workflow-with-approval-process/4543 | 2026-05-23 | public support/community thread | automation operators | public web | medium | Repeated approval-process discussion in automation tooling. | n8n community discusses approval processes in workflows. | Approval mapping is recurring enough to track, but likely platform-feature shaped. | Community thread does not prove standalone buyer demand. | yes | yes |
| R2-S9 | https://zapier.com/blog/approval-automation/ | 2026-05-23 | product education article | automation competitor/content | public web | medium | Shows approval automation is already marketed by broad automation platforms. | Zapier frames approvals as a way to keep humans in the loop for sensitive workflow steps. | Approval pain is real but crowded; differentiation requires risk-map or design artifact. | Vendor education page, not neutral demand proof. | yes | yes |
| R2-S10 | https://docs.github.com/en/enterprise-cloud@latest/rest/about-the-rest-api/breaking-changes | 2026-05-23 | official docs | developer platform docs | public web | medium | Official proof that API breaking changes can require integration updates. | GitHub defines breaking changes as changes that can break integrations and require code or version updates. | API drift is structurally real for third-party integrations. | Official docs do not show buyer urgency. | yes | yes |
| R2-S11 | https://github.blog/changelog/label/breaking-change/ | 2026-05-23 | official changelog | developer platform changelog | public web | medium | Public changelog category demonstrates breaking changes are operationally announced over time. | GitHub maintains a changelog label for breaking changes. | Teams integrating with public APIs must monitor provider change streams. | GitHub-specific; not cross-provider demand proof. | yes | yes |
| R2-S12 | https://github.com/OpenAPITools/openapi-diff | 2026-05-23 | open-source repository | developer tooling alternative | public GitHub | medium | Shows open-source alternatives exist for OpenAPI spec diffing. | The project compares OpenAPI specs and identifies differences. | API-drift MVP must avoid being a generic spec diff clone. | Repository existence is not demand by itself; requires usage/issue review. | yes | yes |
| R2-S13 | https://www.useparagon.com/blog/api-integration-monitoring | 2026-05-23 | product education article | integration platform competitor/content | public web | medium | Shows integration vendors market monitoring and observability as a problem. | Paragon discusses monitoring API integrations for failures and performance. | API monitoring is a known commercial concern. | Vendor-authored; not proof for a tiny standalone report. | yes | yes |
| R2-S14 | https://www.microsoft.com/en-us/worklab/work-trend-index/ai-at-work-is-here-now-comes-the-hard-part/ | 2026-05-23 | research report | AI workplace adoption | public web | medium | Context for AI rollout planning gaps. | Microsoft/LinkedIn report broad AI use and leader concern about implementation plans. | AI rollout pressure is broad but not yet specific enough for this portfolio's first MVP. | Vendor-authored top-line report; not buyer proof. | yes | yes |
| R2-S15 | https://asana.com/resources/state-of-ai-work-2024 | 2026-05-23 | research report | AI workplace adoption | public web | medium | Cross-checks broad AI adoption context. | Asana/Anthropic report weekly genAI adoption at work and perceived productivity gains. | AI training/workflow enablement is plausible but crowded. | Gated/full methodology not fully captured here. | yes | yes |

## Verdict

Lead Response SLA Gap Radar remains the strongest first experiment. It has a
clear ICP, concrete data shape, fast manual validation path, and enough public
evidence to justify collecting operator-owned sample data next.

The decision is still `revisit`, not `build`: public sources show pain and
market category, but they do not prove willingness to pay for a lightweight
independent diagnostic.

## Scorecard

| Opportunity | Pain intensity | Buyer clarity | Urgency | Differentiation | Speed to validate | Founder advantage | Read |
|---|---:|---:|---:|---:|---:|---:|---|
| Lead Response SLA Gap Radar | 4/5 | 4/5 | 4/5 | 3/5 | 5/5 | 4/5 | Best first test; needs sample lead data and two target calls. |
| Human Approval Map for AI Automations | 4/5 | 3/5 | 3/5 | 2/5 | 4/5 | 4/5 | Real pain, but likely a Workflow-to-Agent Studio feature rather than standalone product. |
| Third-Party API Drift Watch | 4/5 | 3/5 | 3/5 | 2/5 | 3/5 | 3/5 | Real technical pain, but crowded by tests, monitoring, and OpenAPI diff tools. |
| AI Rollout Training Gap Tracker | 3/5 | 2/5 | 3/5 | 2/5 | 3/5 | 2/5 | Broad adoption trend, weak specific buyer wedge. |

## Opportunity 1 - Lead Response SLA Gap Radar

Decision status: `revisit`
Experiment readiness: highest

Claims:

- [cited] Public benchmark evidence says many B2B teams respond slowly to inbound requests (R2-S1).
- [cited] HubSpot community users ask how to track time from lead creation to first sales response (R2-S2, R2-S3).
- [cited] Lead routing and response optimization is already a commercial category with vendors like Chili Piper and LeanData (R2-S4, R2-S5).
- [cited] Response-time analytics products exist, including email/SLA-focused tools such as timetoreply (R2-S6).
- [inference] The wedge should not be "another routing platform"; it should be a local diagnostic that tells small teams whether they actually have a speed-to-lead leak before they buy routing automation.
- [insufficient_evidence] No public source yet proves a small B2B team would pay for this diagnostic as a standalone product.

Core assumption:

Small B2B teams have timestamped lead and first-response data, but do not have a simple daily exception report that changes behavior.

Fatal flaws:

| Risk | Severity | Why it matters | Fast test |
|---|---|---|---|
| CRM-native reporting already solves it | High | If HubSpot/Salesforce users can produce this in minutes, standalone value is weak. | Ask 5 HubSpot/Salesforce operators to show current SLA report setup. |
| No clean first-response timestamp | High | Without data, the product becomes integration work before value proof. | Request one anonymized CSV from each target profile. |
| Buyer wants routing/outreach, not diagnostics | Medium | That would push the project into unsafe/external-action scope too early. | Offer only a report and see whether users still care. |

Smallest MVP test:

- Input: CSV export with lead created timestamp, first response timestamp, source, owner, and optional status.
- Output: Markdown SLA report with breach count, median/p90 response time, unresponded leads, source/owner clusters, and data quality issues.
- Timebox: 7-10 days.

Next evidence needed from the user:

- one anonymized or synthetic-like CSV schema from a real lead flow;
- target list of 10 small B2B SaaS/agencies/service firms;
- screenshots or notes of current CRM report setup, if any.

## Opportunity 2 - Human Approval Map for AI Automations

Decision status: `needs_more_evidence`
Experiment readiness: medium

Claims:

- [cited] Automation operators publicly ask how to pause workflows for approval/rejection before proceeding (R2-S7, R2-S8).
- [cited] Zapier markets approval automation as keeping humans in the loop for sensitive steps (R2-S9).
- [inference] The useful artifact may be an approval map: action, risk class, approver, timeout, escalation, and rollback.
- [insufficient_evidence] Current evidence does not prove this should be a standalone MVP instead of a feature inside Workflow-to-Agent Studio.

Core assumption:

Operators designing AI automations need help deciding where approval is required before they need help running the approval queue.

Fast test:

- Review 5 real automation workflows and mark irreversible/customer-impacting/high-cost steps.
- Produce a one-page approval map.
- Ask whether the map changes what the operator would automate or delegate to an agent.

## Opportunity 3 - Third-Party API Drift Watch

Decision status: `revisit`
Experiment readiness: medium-low

Claims:

- [cited] GitHub docs and changelogs show breaking API changes are real and require integration updates (R2-S10, R2-S11).
- [cited] Existing tools such as `openapi-diff` already compare API specs (R2-S12).
- [cited] Integration platforms discuss monitoring API integrations for failures and performance (R2-S13).
- [inference] A tiny MVP could digest provider changelogs plus OpenAPI diff output into a "what might break this week" report.
- [insufficient_evidence] Current sources show the problem exists, but not that a small team would buy a separate API drift report.

Core assumption:

Teams with multiple third-party integrations lack a lightweight way to notice provider changes before production failures.

Fast test:

- Pick 3 public APIs used by a target project.
- Track changelogs/specs for two weeks.
- Produce one weekly drift report and ask whether it would have prevented a real incident or saved triage time.

## Opportunity 4 - AI Rollout Training Gap Tracker

Decision status: `reject for now`
Experiment readiness: low

Claims:

- [cited] Microsoft/LinkedIn and Asana/Anthropic report broad workplace AI adoption and rollout/planning gaps (R2-S14, R2-S15).
- [inference] A tracker for team use cases, policies, examples, and blockers could be useful.
- [insufficient_evidence] The buyer segment is too broad and the category is crowded; there is no specific underserved workflow in this run.

Why reject for now:

- It depends on broad trend evidence rather than direct operator pain.
- It is likely to turn into consulting, LMS content, or enterprise enablement tooling.
- It is less aligned with the current portfolio than Lead Response SLA or workflow-agent design.

## Competition And Current Behavior

| Problem | Current behavior | Direct alternatives | Indirect alternatives | Wedge to test |
|---|---|---|---|---|
| Lead response SLA | CRM reports, spreadsheets, manual RevOps checks, routing tools | Chili Piper, LeanData, timetoreply, CRM-native dashboards | Hiring SDR ops, Zapier/Make automations, inbox rules | Local diagnostic report before routing automation. |
| AI approval mapping | Ad hoc workflow pauses, Slack/email approvals, platform-specific approval steps | Zapier approvals, n8n workflows, Make/manual approvals | SOP docs, security review, manual execution | Risk-classification map before runtime queue. |
| API drift | Contract tests, changelog watching, observability alerts after failure | OpenAPI diff tools, integration platforms, API monitoring | Manual release-note review, vendor support emails | Human-readable weekly drift digest. |
| AI rollout training | Training docs, Slack tips, workshops, LMS, consultants | AI literacy platforms, internal enablement tools | Manager coaching, policy docs | No strong wedge from this run. |

## First 10 Targets For Lead Response SLA

1. Founder-led B2B SaaS with demo/contact form and under 20 sales employees.
2. RevOps consultant managing HubSpot for SMB clients.
3. Agency owner receiving quote requests through website forms.
4. Marketing ops freelancer setting up routing/notifications.
5. HubSpot admin at a small sales team.
6. Salesforce admin for a founder-led sales org.
7. Service business owner with high-value inbound quote forms.
8. Startup sales manager using shared inbox plus CRM.
9. CRM implementation consultant.
10. Customer success/support lead handling sales/support handoff.

## Data Request For The Operator

To move from `revisit` to a real experiment, collect one of:

- anonymized CSV export from a lead/contact form and CRM response log;
- sample rows with column names only, if raw data cannot be shared;
- screenshots/field names showing where created timestamp and first-response timestamp live.

Minimum columns:

- `lead_id` or row number;
- `created_at`;
- `first_response_at`;
- `source` or form name;
- `owner` or team, if available;
- optional `status`.

Privacy rules:

- redact names, emails, company names, phone numbers, message bodies, and URLs;
- keep only timestamps, coarse source labels, owner/team labels, and status;
- hash row IDs if needed.

## Rollup

| Opportunity | Decision | Evidence strength | Next action |
|---|---|---|---|
| Lead Response SLA Gap Radar | `revisit` / experiment-ready | medium | Ask for operator-owned sample data and run 7-10 day local CSV report test. |
| Human Approval Map | `needs_more_evidence` | medium-low | Treat as Workflow-to-Agent Studio feature discovery, not standalone MVP. |
| Third-Party API Drift Watch | `revisit` | medium-low | Track 3 public APIs for two weeks and test whether drift digest prevents work. |
| AI Rollout Training Gap Tracker | `reject for now` | low | Do not pursue until a narrower buyer/workflow appears. |

Health verdict: `WARN`

Reason: the research is public-safe and source-diverse enough to count as a
backfilled evidence run, but it still lacks human-owned decisions and
operator-owned workflow data. Private beta and hosted/SaaS remain blocked.
