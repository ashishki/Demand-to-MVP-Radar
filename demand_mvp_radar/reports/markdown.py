"""Markdown report rendering and atomic local writes."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path

from demand_mvp_radar.briefs import OpportunityBrief
from demand_mvp_radar.observability import span

ReportWriter = Callable[[Path, str], None]


def render_markdown_report(
    briefs: Sequence[OpportunityBrief],
    *,
    top_n: int = 5,
    generated_at: datetime | None = None,
    title: str = "Demand-to-MVP Radar Weekly Report",
) -> str:
    timestamp = (generated_at or datetime.now(UTC)).isoformat()
    selected = sorted(briefs, key=lambda item: item.score.total_score, reverse=True)[:top_n]
    lines = [
        f"# {title}",
        "",
        f"Generated: {timestamp}",
        f"Included opportunities: {len(selected)}",
        "",
    ]
    for index, brief in enumerate(selected, start=1):
        lines.extend(_render_opportunity(index, brief))
    return "\n".join(lines).rstrip() + "\n"


def write_markdown_report(
    path: Path,
    content: str,
    *,
    writer: ReportWriter | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    write = writer or _write_text
    with span("reports.write_markdown"):
        try:
            write(temp_path, content)
            os.replace(temp_path, path)
        finally:
            if temp_path.exists():
                temp_path.unlink()


def _render_opportunity(index: int, brief: OpportunityBrief) -> list[str]:
    score = brief.score
    candidate = brief.candidate
    extraction = brief.extraction
    lines = [
        f"## {index}. {candidate.candidate_title}",
        "",
        f"Recommendation: **{score.recommendation}**",
        f"Total score: {score.total_score:.2f}",
        f"Confidence: {score.confidence_band}",
        "",
        "### Score Components",
        "",
        "| Component | Score | Rationale |",
        "|-----------|-------|-----------|",
    ]
    for name, component in score.components.items():
        lines.append(f"| {name} | {component.value:.2f} | {component.rationale} |")

    risk_flags = ", ".join(extraction.risk_flags) if extraction.risk_flags else "None"
    threshold_reasons = (
        "; ".join(score.threshold_reasons) if score.threshold_reasons else "No threshold blocks"
    )
    acquisition_line = (
        f"- Acquisition channel: {candidate.acquisition_channel} - {extraction.acquisition_angle}"
    )
    lines.extend(
        [
            "",
            "### Brief",
            "",
            f"- One-function MVP scope: {extraction.mvp_function}",
            acquisition_line,
            f"- Risk flags: {risk_flags}",
            f"- Current workaround: {extraction.current_workaround}",
            f"- Competitor shape: {extraction.competitor_shape}",
            f"- Rationale: {extraction.confidence_note}; {threshold_reasons}",
            "",
            "### Cited Evidence",
            "",
        ]
    )
    for packet in brief.evidence_packets:
        lines.append(
            f"[{packet.citation_number}] {packet.snippet} "
            f"({packet.captured_at.date().isoformat()}, score {packet.relevance_score:.2f}) "
            f"- {packet.source_url}"
        )
    lines.append("")
    return lines


def _write_text(path: Path, content: str) -> None:
    path.write_text(content)
