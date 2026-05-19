from __future__ import annotations

from datetime import UTC, datetime

from demand_mvp_radar.clustering import cluster_evidence
from demand_mvp_radar.models import EvidenceRecord


def test_near_duplicate_evidence_maps_to_one_opportunity() -> None:
    records = [
        make_evidence(
            "msg-001",
            "telegram",
            "https://example.com/spreadsheet-thread",
            "Operators need spreadsheet formula helpers that explain broken Excel formulas.",
        ),
        make_evidence(
            "msg-002",
            "telegram",
            "https://example.com/spreadsheet-thread",
            "Operators ask for Excel formula troubleshooting for broken spreadsheet sheets.",
        ),
    ]

    candidates = cluster_evidence(records)

    assert len(candidates) == 1
    assert candidates[0].normalized_pain == "spreadsheet formula troubleshooting"
    assert candidates[0].source_evidence_ids == ("msg-001", "msg-002")


def test_audience_difference_splits_opportunities() -> None:
    records = [
        make_evidence(
            "msg-001",
            "telegram",
            "https://example.com/operator-sheet",
            "Operators need spreadsheet formula helpers that explain broken Excel formulas.",
        ),
        make_evidence(
            "msg-002",
            "telegram",
            "https://example.com/student-sheet",
            "Students need spreadsheet formula helpers that explain broken Excel formulas.",
        ),
    ]

    candidates = cluster_evidence(records)

    assert len(candidates) == 2
    assert {candidate.normalized_pain for candidate in candidates} == {
        "spreadsheet formula troubleshooting"
    }
    assert {candidate.target_audience for candidate in candidates} == {"operators", "students"}
    assert len({candidate.opportunity_id for candidate in candidates}) == 2


def test_cluster_output_contains_required_fields() -> None:
    candidates = cluster_evidence(
        [
            make_evidence(
                "serp-001",
                "serp",
                "https://example.com/prerender-seo",
                "Indie teams search for prerender SEO rendering fixes for indexing problems.",
            )
        ]
    )

    candidate = candidates[0]
    assert candidate.opportunity_id.startswith("opp_")
    assert candidate.normalized_pain == "javascript seo prerendering"
    assert candidate.target_audience == "indie teams"
    assert candidate.source_evidence_ids == ("serp-001",)
    assert candidate.candidate_title == "Javascript Seo Prerendering for Indie Teams"


def make_evidence(
    source_id: str,
    source_type: str,
    source_url: str,
    text: str,
) -> EvidenceRecord:
    return EvidenceRecord(
        run_id="run-clustering-001",
        source_type=source_type,
        source_id=source_id,
        source_url=source_url,
        captured_at=datetime(2026, 5, 19, 12, 0, tzinfo=UTC),
        title="Evidence title",
        snippet=text,
        normalized_text=text,
        content_hash=f"hash-{source_id}",
        source_fingerprint=f"{source_type}:{source_id}:hash-{source_id}",
    )
