"""Markdown rendering for MVP experiment packs."""

from __future__ import annotations

from pathlib import Path

from demand_mvp_radar.models import MVPExperimentPack
from demand_mvp_radar.reports.markdown import ReportWriter, write_markdown_report


def render_experiment_markdown(pack: MVPExperimentPack) -> str:
    lines = [
        f"# MVP Experiment: {pack.opportunity_id}",
        "",
        f"Opportunity ID: `{pack.opportunity_id}`",
        f"Human decision: **{pack.human_decision}** - {pack.human_decision_reason}",
        f"Timebox: {pack.timebox_days} days",
        "",
        "## Scope",
        "",
        pack.one_function_scope,
        "",
        "## Target User",
        "",
        pack.target_user,
        "",
        "## Validation Method",
        "",
        pack.validation_method,
        "",
        "## First 10 Targets",
        "",
    ]
    lines.extend(f"{index}. {target}" for index, target in enumerate(pack.first_10_targets, 1))
    lines.extend(
        [
            "",
            "## Thresholds",
            "",
            f"- Success: {pack.success_threshold}",
            f"- Kill: {pack.kill_threshold}",
            f"- Revisit: {pack.revisit_threshold}",
            "",
            "## Source Evidence",
            "",
        ]
    )
    lines.extend(_render_citations(pack))
    lines.extend(
        [
            "",
            "## Risk Flags",
            "",
        ]
    )
    if pack.risk_flags:
        lines.extend(f"- {risk}" for risk in pack.risk_flags)
    else:
        lines.append("- None")
    return "\n".join(lines).rstrip() + "\n"


def write_experiment_markdown(
    report_dir: Path,
    pack: MVPExperimentPack,
    *,
    run_id: str,
    writer: ReportWriter | None = None,
) -> Path:
    path = report_dir / f"{pack.opportunity_id}-{run_id}.md"
    write_markdown_report(path, render_experiment_markdown(pack), writer=writer)
    return path


def _render_citations(pack: MVPExperimentPack) -> list[str]:
    lines = [
        "| Citation | Source Type | Source | Captured | Reference | Snippet |",
        "|----------|-------------|--------|----------|-----------|---------|",
    ]
    for citation in pack.source_citations:
        lines.append(
            "| "
            f"[{citation.citation_number}] | "
            f"{citation.source_type} | "
            f"{citation.source_title_or_id} | "
            f"{citation.captured_at.date().isoformat()} | "
            f"{citation.source_ref} | "
            f"{citation.snippet} |"
        )
    return lines
