"""Markdown rendering for lead response SLA reports."""

from __future__ import annotations

from demand_mvp_radar.lead_sla import LeadSlaAnalysis, LeadSlaBreakdown, LeadSlaRecord


def render_lead_sla_report(analysis: LeadSlaAnalysis, *, top_n: int = 20) -> str:
    lines = [
        "# Lead Response SLA Report",
        "",
        f"Dataset: {analysis.dataset_label}",
        f"Source CSV: `{analysis.source_path}`",
    ]
    if analysis.public_source_url:
        lines.append(f"Public/proxy source: {analysis.public_source_url}")
    lines.extend(
        [
            f"SLA threshold: {analysis.sla_minutes:g} minutes",
            "",
            "## Summary",
            "",
            f"- Total valid leads/tickets: {analysis.total_leads}",
            f"- Responded: {analysis.responded_leads}",
            f"- No first response: {analysis.unresponded_leads}",
            f"- Responded over SLA: {analysis.response_breach_count}",
            f"- Total SLA misses including no response: {analysis.total_sla_miss_count}",
            f"- Median response: {_fmt_minutes(analysis.median_response_minutes)}",
            f"- P90 response: {_fmt_minutes(analysis.p90_response_minutes)}",
            f"- Max response: {_fmt_minutes(analysis.max_response_minutes)}",
            "",
            "## SLA Health",
            "",
            _health_sentence(analysis),
            "",
            "## Slowest Responded Leads",
            "",
        ]
    )
    lines.extend(_record_table(_slowest_records(analysis.records, top_n=top_n)))
    lines.extend(
        [
            "",
            "## Leads Without Response",
            "",
        ]
    )
    lines.extend(
        _record_table([record for record in analysis.records if record.unresponded][:top_n])
    )
    lines.extend(["", "## Breakdown By Source", ""])
    lines.extend(_breakdown_table(analysis.by_source))
    lines.extend(["", "## Breakdown By Owner", ""])
    lines.extend(_breakdown_table(analysis.by_owner))
    lines.extend(["", "## Breakdown By Status", ""])
    lines.extend(_breakdown_table(analysis.by_status))
    lines.extend(["", "## Data Quality Issues", ""])
    if analysis.warnings:
        for warning in analysis.warnings:
            lines.append(f"- {warning}")
    if analysis.invalid_rows:
        for issue in analysis.invalid_rows[:top_n]:
            lines.append(f"- Row {issue.row_number}: {issue.reason}")
    if not analysis.warnings and not analysis.invalid_rows:
        lines.append("- None found.")

    lines.extend(["", "## Suggested Next Actions", ""])
    lines.extend(f"- {action}" for action in _suggested_actions(analysis))
    lines.extend(
        [
            "",
            "## Evidence Limits",
            "",
            "- This report can validate the calculation workflow and surface bottlenecks.",
            "- Public/proxy data does not prove willingness to pay for a sales lead SLA product.",
            "- A real experiment still needs operator-owned or target-user sample data.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _slowest_records(records: tuple[LeadSlaRecord, ...], *, top_n: int) -> list[LeadSlaRecord]:
    responded = [record for record in records if record.response_minutes is not None]
    return sorted(responded, key=lambda record: record.response_minutes or 0, reverse=True)[:top_n]


def _record_table(records: list[LeadSlaRecord]) -> list[str]:
    if not records:
        return ["No rows."]
    lines = [
        "| Lead | Source | Owner | Status | Response | SLA miss |",
        "|---|---|---|---|---:|---:|",
    ]
    for record in records:
        lines.append(
            "| "
            f"{record.lead_id} | {record.source} | {record.owner} | {record.status} | "
            f"{_fmt_minutes(record.response_minutes)} | {'yes' if record.breached_sla else 'no'} |"
        )
    return lines


def _breakdown_table(items: tuple[LeadSlaBreakdown, ...]) -> list[str]:
    if not items:
        return ["No rows."]
    lines = [
        "| Segment | Total | Responded | No response | SLA misses | Median | P90 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in items:
        lines.append(
            f"| {item.key} | {item.total} | {item.responded} | {item.unresponded} | "
            f"{item.breach_count} | {_fmt_minutes(item.median_response_minutes)} | "
            f"{_fmt_minutes(item.p90_response_minutes)} |"
        )
    return lines


def _suggested_actions(analysis: LeadSlaAnalysis) -> list[str]:
    actions: list[str] = []
    if analysis.unresponded_leads:
        actions.append(
            f"Inspect {analysis.unresponded_leads} rows without first response timestamps before "
            "changing routing logic."
        )
    if analysis.by_source:
        source = analysis.by_source[0]
        actions.append(
            f"Review source `{source.key}` first: it has {source.breach_count} SLA misses."
        )
    if analysis.by_owner:
        owner = analysis.by_owner[0]
        actions.append(f"Review owner/team `{owner.key}`: it has {owner.breach_count} SLA misses.")
    if analysis.invalid_rows:
        actions.append(
            f"Fix or quarantine {len(analysis.invalid_rows)} invalid rows so reporting does not hide data-quality problems."
        )
    if not actions:
        actions.append("No immediate SLA bottleneck found in this dataset.")
    return actions


def _health_sentence(analysis: LeadSlaAnalysis) -> str:
    if analysis.total_leads == 0:
        return "No valid rows were available for SLA analysis."
    miss_rate = analysis.total_sla_miss_count / analysis.total_leads
    if miss_rate >= 0.5:
        return f"WARN: {miss_rate:.0%} of valid rows miss SLA or have no first response."
    if miss_rate > 0:
        return f"CAUTION: {miss_rate:.0%} of valid rows miss SLA or have no first response."
    return "OK: no SLA misses found in valid rows."


def _fmt_minutes(value: float | None) -> str:
    if value is None:
        return "n/a"
    if value < 60:
        return f"{value:.1f}m"
    return f"{value / 60:.1f}h"
