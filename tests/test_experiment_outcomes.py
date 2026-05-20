from __future__ import annotations

from datetime import UTC, datetime

from demand_mvp_radar.experiments import record_experiment_outcome
from demand_mvp_radar.models import EvidenceRecord, OpportunityScore, ScoreComponent
from demand_mvp_radar.scoring import (
    ScoringConfig,
    apply_experiment_outcomes,
)


def test_experiment_outcome_records_required_fields() -> None:
    created_at = datetime(2026, 5, 20, 12, 0, tzinfo=UTC)

    outcome = record_experiment_outcome(
        experiment_id="exp-101-run-001",
        opportunity_id="101",
        outcome="validated",
        evidence_summary="4 of 10 operators submitted real samples.",
        actor="operator",
        created_at=created_at,
    )

    assert outcome.experiment_id == "exp-101-run-001"
    assert outcome.opportunity_id == "101"
    assert outcome.outcome == "validated"
    assert outcome.evidence_summary == "4 of 10 operators submitted real samples."
    assert outcome.actor == "operator"
    assert outcome.created_at == created_at
    assert outcome.decision_memory_value == "build"


def test_killed_experiment_suppresses_matching_opportunities() -> None:
    score = _score(total_score=82, recommendation="build")
    outcome = record_experiment_outcome(
        experiment_id="exp-101-run-001",
        opportunity_id="101",
        outcome="killed",
        evidence_summary="0 of 10 operators agreed to continue.",
        actor="operator",
        created_at=datetime(2026, 5, 20, 12, 0, tzinfo=UTC),
    )

    suppressed = apply_experiment_outcomes(
        score,
        (outcome,),
        evidence_records=(
            _evidence("old-signal", captured_at=datetime(2026, 5, 19, 12, 0, tzinfo=UTC)),
        ),
        config=ScoringConfig(experiment_kill_penalty=45),
    )
    refreshed = apply_experiment_outcomes(
        score,
        (outcome,),
        evidence_records=(
            _evidence("new-signal", captured_at=datetime(2026, 5, 21, 12, 0, tzinfo=UTC)),
        ),
        config=ScoringConfig(experiment_kill_penalty=45),
    )

    assert suppressed.recommendation == "reject"
    assert suppressed.total_score == 37
    assert suppressed.decision_memory_notes == (
        "killed experiment suppression: 0 of 10 operators agreed to continue.",
    )
    assert refreshed == score


def test_validated_experiment_affects_score_deterministically() -> None:
    score = _score(total_score=70, recommendation="revisit", confidence_value=70)
    outcome = record_experiment_outcome(
        experiment_id="exp-101-run-001",
        opportunity_id="101",
        outcome="validated",
        evidence_summary="4 of 10 operators submitted real samples.",
        actor="operator",
        created_at=datetime(2026, 5, 20, 12, 0, tzinfo=UTC),
    )
    config = ScoringConfig(
        experiment_validation_confidence_bonus=20,
        build_threshold=72,
        revisit_threshold=45,
    )

    first = apply_experiment_outcomes(score, (outcome,), config=config)
    second = apply_experiment_outcomes(score, (outcome,), config=config)

    assert first == second
    assert first.components["confidence"].value == 90
    assert first.confidence_band == "high"
    assert first.total_score > score.total_score
    assert first.recommendation in {"revisit", "build"}
    assert first.decision_memory_notes == (
        "validated experiment support: 4 of 10 operators submitted real samples.",
    )


def _score(
    *,
    total_score: float,
    recommendation: str,
    confidence_value: float = 80,
) -> OpportunityScore:
    return OpportunityScore(
        opportunity_id="101",
        recommendation=recommendation,
        total_score=total_score,
        confidence_band="medium",
        components={
            "demand": ScoreComponent(name="demand", value=75, rationale="supporting demand"),
            "evidence_diversity": ScoreComponent(
                name="evidence_diversity",
                value=80,
                rationale="two source types",
            ),
            "freshness": ScoreComponent(name="freshness", value=80, rationale="fresh evidence"),
            "competition": ScoreComponent(
                name="competition",
                value=65,
                rationale="some alternatives",
            ),
            "acquisition_fit": ScoreComponent(
                name="acquisition_fit",
                value=70,
                rationale="search channel",
            ),
            "risk": ScoreComponent(name="risk", value=70, rationale="manageable risk"),
            "confidence": ScoreComponent(
                name="confidence",
                value=confidence_value,
                rationale="pre-experiment confidence",
            ),
        },
    )


def _evidence(source_id: str, *, captured_at: datetime) -> EvidenceRecord:
    return EvidenceRecord(
        run_id="run-experiment-outcome-001",
        source_type="telegram_research_agent",
        source_id=source_id,
        source_url=f"https://example.local/{source_id}",
        captured_at=captured_at,
        title="Experiment follow-up signal",
        snippet="Operator evidence.",
        normalized_text="Operator evidence.",
        content_hash=f"hash-{source_id}",
        source_fingerprint=f"telegram:{source_id}:hash-{source_id}",
    )
