# Tool-Use Evaluation

Project: Demand-to-MVP Radar
Profile: Tool-Use
Status: initialized before implementation

---

## Evaluation Purpose

Tool-use evaluation verifies that LLM-callable tools are schema-validated, permission-checked, audited, and bounded by retry and side-effect rules. This artifact is separate from unit tests because tool safety depends on schema and audit completeness across the catalog.

---

## Tool Evaluation Dataset

Initial fixture set to be created during T06/T08/T18:

| Fixture ID | Tool | Scenario | Expected Behavior |
|------------|------|----------|-------------------|
| TOOL-Q01 | `read_telegram_evidence` | valid local export fixture | accepted, audited |
| TOOL-Q02 | `fetch_url_snapshot` | mocked HTTP 200 | accepted, audited |
| TOOL-Q03 | `fetch_url_snapshot` | timeout from mocked client | bounded retry, structured error, audited |
| TOOL-Q04 | `read_serp_snapshot` | valid saved SERP fixture | accepted, audited |
| TOOL-Q05 | `read_store_metadata` | valid store fixture | accepted, audited |
| TOOL-Q06 | `retrieve_evidence` | valid query against fixture corpus | accepted, audited |
| TOOL-Q07 | `write_report` | local report write | atomic write, audited |
| TOOL-Q08 | `record_operator_decision` | missing human approval marker | rejected before write |

---

## Metrics

| Metric | Definition | Initial Target |
|--------|------------|----------------|
| schema_validation_pass_rate | Valid fixtures pass and invalid fixtures fail before tool execution. | 1.00 after baseline |
| permission_check_pass_rate | Tools enforce declared permission rules at the tool boundary. | 1.00 after baseline |
| audit_field_completeness | Audit event includes all fields declared by the tool schema. | 1.00 after baseline |
| retry_policy_pass_rate | Retryable failures follow declared retry policy and non-retryable failures do not retry. | 1.00 after baseline |

---

## Evaluation History

| Date | Task | Eval Source | schema_validation_pass_rate | permission_check_pass_rate | audit_field_completeness | retry_policy_pass_rate | Notes |
|------|------|-------------|-----------------------------|----------------------------|--------------------------|------------------------|-------|
| 2026-05-19 | bootstrap | not yet run - dataset initialized before implementation | n/a | n/a | n/a | n/a | Baseline will be established by T06/T08/T18. |

---

## Regression Notes

None.

---

## Open Tool Findings

None.
