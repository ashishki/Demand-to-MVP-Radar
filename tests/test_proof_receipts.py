from __future__ import annotations

from datetime import UTC, datetime

import pytest
from demand_mvp_radar.briefs import OpportunityBrief
from demand_mvp_radar.proof import (
    WeeklyReportProofReceipt,
    build_weekly_report_proof_receipt,
)
from pydantic import ValidationError
from tests.test_reports import make_brief


def test_weekly_report_proof_receipt_links_report_hash_and_evidence_refs() -> None:
    brief = make_brief(1, total_score=88)
    receipt = build_weekly_report_proof_receipt(
        report_markdown="# Weekly\n\nbody\n",
        report_path="reports/weekly/2026-W22.md",
        briefs=[brief],
        generated_at=datetime(2026, 5, 31, tzinfo=UTC),
    )

    assert receipt.type == "weekly_report_receipt"
    assert receipt.schema_version == "entropy_core.product_receipt.v1"
    assert receipt.product_id == "demand-to-mvp-radar"
    assert receipt.artifact_ref == "reports/weekly/2026-W22.md"
    assert len(receipt.artifact_sha256) == 64
    assert receipt.verifier_status == "passed"
    assert receipt.evidence_refs[0].evidence_id == "evidence:1"
    assert receipt.evidence_refs[0].supports == brief.candidate.opportunity_id
    assert receipt.evidence_refs[0].source_url == "https://example.com/evidence-1"
    assert len(receipt.receipt_sha256()) == 64


def test_weekly_report_receipt_rejects_missing_evidence_refs() -> None:
    brief = make_brief(1, total_score=88)
    empty_brief = OpportunityBrief(
        candidate=brief.candidate,
        score=brief.score,
        extraction=brief.extraction,
        evidence_packets=(),
    )

    with pytest.raises(ValidationError):
        build_weekly_report_proof_receipt(
            report_markdown="# Weekly\n",
            report_path="reports/weekly/empty.md",
            briefs=[empty_brief],
            generated_at=datetime(2026, 5, 31, tzinfo=UTC),
        )


def test_non_passed_receipt_requires_verifier_notes() -> None:
    with pytest.raises(ValidationError, match="verifier_notes"):
        WeeklyReportProofReceipt(
            artifact_ref="reports/weekly/manual.md",
            artifact_sha256="a" * 64,
            generated_at=datetime(2026, 5, 31, tzinfo=UTC),
            evidence_refs=[
                {
                    "evidence_id": "evidence:1",
                    "source_url": "https://example.com",
                    "supports": "opp-1",
                }
            ],
            verifier_status="needs_review",
        )
