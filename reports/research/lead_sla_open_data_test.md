# Lead SLA Open-Data Test

Status: technical MVP test
Date: 2026-05-25
Decision owner: human operator

This artifact records how the Lead Response SLA Gap Radar was tested without
operator-owned CRM data. The test uses a public/proxy support-ticket schema and
a small fixture to validate calculation, redaction, and report usefulness. It
does not count as market proof for sales lead response willingness to pay.

## Source Register

| ID | Source URL / locator | Captured at | Source type | Source family | Access method | Trust tier | Why it matters | Extracted signal | Cited claims supported | Limitations | Redacted? | Can support decision? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ODT-S1 | https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset/data?select=customer_support_tickets.csv | 2026-05-25 | public dataset page | support ticket dataset | public web / account-gated file download | medium | Closest open proxy found for first-response analysis. | Dataset page lists customer support tickets with first response time, channel, status, priority, and customer fields. | Public support-ticket data can test first-response calculations and PII redaction. | Kaggle file access may require account/API; support tickets are proxy data, not sales leads. | yes | no - technical proxy only |
| ODT-S2 | https://count.co/integration/salesforce/lead-response-time | 2026-05-25 | product analysis page | CRM lead response analysis | public web | medium | Describes real Salesforce lead response data shape and analysis questions. | Count says Salesforce has lead creation timestamps, first contact activities, owner/source dimensions, and CSV analysis use cases. | Lead SLA reports need created timestamp, first activity timestamp, source, owner, and segmentation. | Vendor page; not open row-level data. | yes | yes, for schema guidance |
| ODT-S3 | https://www.metricgen.io/blog/lead-response-time-complete-guide | 2026-05-25 | guide | sales ops metric guide | public web | medium | Defines the metric and reporting cuts. | Formula: first meaningful contact timestamp minus lead creation timestamp; recommended outputs include median and distribution buckets. | The MVP should report median, p90/distribution, and SLA buckets. | Guide content, not row-level data or buyer proof. | yes | yes, for metric shape |
| ODT-S4 | https://docs.gorgias.com/en-US/export-tickets-from-gorgias-404844 | 2026-05-25 | official docs | support ticket export docs | public web | medium | Shows common export fields for first-response analysis. | Gorgias CSV exports can include creation date, assignee/customer fields, first response time, and resolution time. | Helpdesk exports commonly expose response-time fields and PII that must be redacted. | Support-ticket workflow, not sales leads. | yes | yes, for redaction/schema guidance |
| ODT-S5 | https://documentation.qiscus.com/helpdesk/overall-analytics | 2026-05-25 | official docs | support analytics export docs | public web | medium | Shows granular first-response table fields. | Qiscus docs list ticket created timestamp, channel, customer/agent fields, first response timestamp, and response time seconds; charts/tables can export CSV/XLSX/JSON. | Public docs validate the CSV field aliases supported by the MVP. | Support-ticket workflow, not sales leads. | yes | yes, for schema guidance |
| ODT-S6 | https://www.kixie.com/sales-blog/how-to-accurately-track-lead-response-time-in-salesforce/ | 2026-05-25 | product education article | CRM lead response analysis | public web | medium | Explains why Salesforce lead response reporting can be hard. | Kixie describes response time as earliest Task timestamp minus Lead.CreatedDate and notes native reporting/data-entry challenges. | The MVP should expose data-quality issues and avoid assuming timestamps are clean. | Vendor-authored; not open row-level data. | yes | yes, for risk guidance |

## What Was Built

Implemented a local CLI command:

```bash
demand-mvp-radar lead-sla-report \
  --input tests/fixtures/lead_sla/open_proxy_leads.csv \
  --output reports/private/lead_sla_open_proxy_report.md \
  --sla-minutes 5 \
  --hash-lead-id \
  --dataset-label "Open support-ticket proxy fixture" \
  --public-source-url "https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset"
```

Code paths:

- `demand_mvp_radar/lead_sla.py`
- `demand_mvp_radar/reports/lead_sla.py`
- `demand_mvp_radar/cli.py`
- `tests/test_lead_sla.py`
- `tests/fixtures/lead_sla/open_proxy_leads.csv`

Generated report:

- `reports/private/lead_sla_open_proxy_report.md`

## Test Result

CLI output:

```json
{"invalid_rows": 2, "output": "reports/private/lead_sla_open_proxy_report.md", "sla_misses": 7, "status": "completed", "total_leads": 10}
```

Report summary:

- 10 valid rows from 12 CSV rows.
- 8 responded rows.
- 2 rows with no first response.
- 5 responded rows over the 5-minute SLA.
- 7 total SLA misses including no response.
- Median response: 18 minutes.
- P90 response: 3 hours.
- Private columns `email` and `company_name` were ignored.
- Invalid timestamp rows were quarantined instead of breaking the run.

## Interpretation

[cited] Public/proxy support data and docs show that first-response analytics
usually need creation timestamp, first response timestamp or duration, source or
channel, owner or agent, and status.

[inference] The same report mechanics can support sales lead SLA analysis when
lead-created and first-meaningful-response timestamps exist.

[insufficient_evidence] This test does not prove the Lead Response SLA product
will sell, because the fixture is proxy/support-shaped and not an operator-owned
sales lead export.

## Next Test

Use public data one level closer to sales leads:

1. Find a downloadable, license-clear CRM/sales activity sample with lead
   creation and first activity timestamps; or
2. Build a transparent simulation from public benchmark distributions and mark
   it as synthetic; or
3. Ask target operators for only schema/field names, not data values.

The current MVP is ready for any CSV with:

- `created_at` or equivalent;
- `first_response_at` or first-response duration;
- optional `lead_id`, `source`, `owner`, and `status`.

## Verdict

Technical test: pass.

Evidence gate: does not count as a real/backfilled market run. It belongs in
the fixture/demo register until row-level public sales lead data or
operator-owned anonymized data exists.
