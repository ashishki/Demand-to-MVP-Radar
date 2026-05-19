from __future__ import annotations

from datetime import UTC, datetime

from demand_mvp_radar.models import EvidenceRecord, OpportunityCandidate
from demand_mvp_radar.scoring import ScoringConfig, score_opportunity


def test_score_output_contains_components() -> None:
    evidence = make_evidence_fixture()
    candidate = make_candidate("msg-001", "serp-001")

    score = score_opportunity(
        candidate,
        evidence,
        config=ScoringConfig(),
        as_of=datetime(2026, 5, 19, tzinfo=UTC),
    )

    assert set(score.components) == {
        "demand",
        "evidence_diversity",
        "freshness",
        "competition",
        "acquisition_fit",
        "risk",
        "confidence",
    }
    assert score.total_score > 0
    assert score.confidence_band in {"low", "medium", "high"}
    assert score.recommendation in {"build", "reject", "revisit"}
    assert score.components["demand"].rationale


def test_scoring_is_deterministic_for_same_input() -> None:
    evidence = make_evidence_fixture()
    candidate = make_candidate("msg-001", "serp-001")
    config = ScoringConfig(build_threshold=70, revisit_threshold=40)
    as_of = datetime(2026, 5, 19, tzinfo=UTC)

    first = score_opportunity(candidate, evidence, config=config, as_of=as_of)
    second = score_opportunity(candidate, evidence, config=config, as_of=as_of)

    assert second.total_score == first.total_score
    assert second.recommendation == first.recommendation
    assert second.components == first.components


def test_low_evidence_candidate_gets_threshold_reason() -> None:
    evidence = make_evidence_fixture()[:1]
    candidate = make_candidate("msg-001")

    score = score_opportunity(
        candidate,
        evidence,
        config=ScoringConfig(minimum_evidence_count=2),
        as_of=datetime(2026, 5, 19, tzinfo=UTC),
    )

    assert score.recommendation in {"reject", "revisit"}
    assert score.threshold_reasons == ("minimum evidence count: required 2, found 1",)


def make_evidence_fixture() -> tuple[EvidenceRecord, ...]:
    return (
        make_evidence(
            "msg-001",
            "telegram",
            "Operators need spreadsheet formula helpers that explain broken Excel formulas.",
        ),
        make_evidence(
            "serp-001",
            "serp",
            "Search snippets show Excel formula helper demand and competitor alternatives.",
        ),
    )


def make_candidate(*source_evidence_ids: str) -> OpportunityCandidate:
    return OpportunityCandidate(
        opportunity_id="opp_scoring_fixture",
        normalized_pain="spreadsheet formula troubleshooting",
        target_audience="operators",
        workflow="troubleshooting",
        acquisition_channel="search",
        source_evidence_ids=tuple(source_evidence_ids),
        candidate_title="Spreadsheet Formula Troubleshooting for Operators",
    )


def make_evidence(source_id: str, source_type: str, text: str) -> EvidenceRecord:
    return EvidenceRecord(
        run_id="run-scoring-001",
        source_type=source_type,
        source_id=source_id,
        source_url=f"https://example.com/{source_id}",
        captured_at=datetime(2026, 5, 18, 12, 0, tzinfo=UTC),
        title="Spreadsheet formula helper",
        snippet=text,
        normalized_text=text,
        content_hash=f"hash-{source_id}",
        source_fingerprint=f"{source_type}:{source_id}:hash-{source_id}",
    )
