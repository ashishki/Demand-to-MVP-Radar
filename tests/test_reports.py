from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from demand_mvp_radar.briefs import build_opportunity_brief
from demand_mvp_radar.models import (
    OpportunityCandidate,
    OpportunityExtraction,
    OpportunityScore,
    ScoreComponent,
)
from demand_mvp_radar.reports.markdown import render_markdown_report, write_markdown_report
from demand_mvp_radar.retrieval.query import EvidencePacket


def test_markdown_report_includes_configured_top_n() -> None:
    briefs = [make_brief(index, total_score=100 - index) for index in range(6)]

    report = render_markdown_report(
        briefs,
        top_n=5,
        generated_at=datetime(2026, 5, 19, tzinfo=UTC),
    )

    assert report.count("\n## ") == 5
    assert "Opportunity 0" in report
    assert "Opportunity 4" in report
    assert "Opportunity 5" not in report


def test_opportunity_sections_include_required_fields() -> None:
    report = render_markdown_report(
        [make_brief(1, total_score=88)],
        generated_at=datetime(2026, 5, 19, tzinfo=UTC),
    )

    assert "Recommendation: **build**" in report
    assert "| Component | Score | Rationale |" in report
    assert "One-function MVP scope:" in report
    assert "Acquisition channel:" in report
    assert "Risk flags:" in report
    assert "Rationale:" in report
    assert "[1]" in report
    assert "https://example.com/evidence-1" in report


def test_report_write_is_atomic(tmp_path) -> None:
    target = tmp_path / "weekly.md"
    target.write_text("previous report")

    def failing_writer(path: Path, content: str) -> None:
        path.write_text(content)
        raise RuntimeError("interrupted write")

    try:
        write_markdown_report(target, "new partial report", writer=failing_writer)
    except RuntimeError:
        pass

    assert target.read_text() == "previous report"
    assert not (tmp_path / ".weekly.md.tmp").exists()

    write_markdown_report(target, "complete new report")

    assert target.read_text() == "complete new report"


def make_brief(index: int, *, total_score: float):
    candidate = OpportunityCandidate(
        opportunity_id=f"opp_{index}",
        normalized_pain=f"opportunity {index}",
        target_audience="operators",
        workflow="troubleshooting",
        acquisition_channel="search",
        source_evidence_ids=(f"evidence-{index}",),
        candidate_title=f"Opportunity {index}",
    )
    extraction = OpportunityExtraction(
        user_pain="Operators waste time on repeated workflow fixes.",
        target_audience="operators",
        current_workaround="Manual spreadsheet edits and search.",
        competitor_shape="Existing formula tools and add-ons.",
        mvp_function="Repair one broken spreadsheet formula.",
        acquisition_angle="Search pages for spreadsheet formula errors.",
        risk_flags=("spreadsheet edge cases",),
        confidence_note="Score is supported by cited demand evidence.",
    )
    score = OpportunityScore(
        opportunity_id=candidate.opportunity_id,
        recommendation="build" if total_score >= 75 else "revisit",
        total_score=total_score,
        confidence_band="high",
        components={
            "demand": ScoreComponent(
                name="demand",
                value=90,
                rationale="multiple supporting records",
            ),
            "evidence_diversity": ScoreComponent(
                name="evidence_diversity",
                value=80,
                rationale="two source types",
            ),
        },
    )
    evidence = (
        EvidencePacket(
            evidence_id=index,
            source_url=f"https://example.com/evidence-{index}",
            captured_at=datetime(2026, 5, 18, tzinfo=UTC) - timedelta(days=index),
            snippet="Operators ask for spreadsheet formula help.",
            relevance_score=0.91,
            citation_number=1,
        ),
    )
    return build_opportunity_brief(
        candidate=candidate,
        score=score,
        extraction=extraction,
        evidence_packets=evidence,
    )
