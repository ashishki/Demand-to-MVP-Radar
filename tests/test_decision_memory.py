from __future__ import annotations

from datetime import UTC, datetime

from demand_mvp_radar.decisions import DecisionHistory, RecordedDecision
from demand_mvp_radar.models import OpportunityScore, ScoreComponent
from demand_mvp_radar.scoring import ScoringConfig, apply_decision_memory


def test_recent_reject_suppresses_matching_candidate() -> None:
    score = make_score(total_score=82)
    history = make_history(
        "reject",
        reason="Already tried; demand did not repeat.",
        created_at=datetime(2026, 5, 10, tzinfo=UTC),
    )

    adjusted = apply_decision_memory(
        score,
        history,
        config=ScoringConfig(rejection_penalty=35, reject_suppression_days=30),
        as_of=datetime(2026, 5, 19, tzinfo=UTC),
    )

    assert adjusted.total_score == 47
    assert adjusted.total_score < score.total_score
    assert adjusted.recommendation == "reject"
    assert adjusted.decision_memory_notes == (
        "recent reject suppression: Already tried; demand did not repeat.",
    )
    assert adjusted.threshold_reasons[-1] == adjusted.decision_memory_notes[0]


def test_revisit_candidate_includes_prior_rationale() -> None:
    score = make_score(total_score=82, recommendation="build")
    history = make_history(
        "revisit",
        reason="Promising, but wait for more source diversity.",
        created_at=datetime(2026, 5, 1, tzinfo=UTC),
    )

    adjusted = apply_decision_memory(
        score,
        history,
        config=ScoringConfig(revisit_after_days=14),
        as_of=datetime(2026, 5, 19, tzinfo=UTC),
    )

    assert adjusted.total_score == score.total_score
    assert adjusted.recommendation == "build"
    assert adjusted.decision_memory_notes == (
        "prior revisit rationale: Promising, but wait for more source diversity.",
    )


def test_suppression_is_deterministic() -> None:
    score = make_score(total_score=82)
    history = make_history(
        "reject",
        reason="Already tried; demand did not repeat.",
        created_at=datetime(2026, 5, 10, tzinfo=UTC),
    )
    config = ScoringConfig(rejection_penalty=35, reject_suppression_days=30)
    as_of = datetime(2026, 5, 19, tzinfo=UTC)

    first = apply_decision_memory(score, history, config=config, as_of=as_of)
    second = apply_decision_memory(score, history, config=config, as_of=as_of)

    assert second == first


def make_score(*, total_score: float, recommendation: str = "build") -> OpportunityScore:
    return OpportunityScore(
        opportunity_id="1",
        recommendation=recommendation,
        total_score=total_score,
        confidence_band="high",
        components={
            "demand": ScoreComponent(
                name="demand",
                value=90,
                rationale="multiple supporting records",
            )
        },
    )


def make_history(
    decision: str,
    *,
    reason: str,
    created_at: datetime,
) -> DecisionHistory:
    recorded = RecordedDecision(
        decision_id=1,
        opportunity_id=1,
        decision=decision,
        reason=reason,
        actor="operator",
        created_at=created_at,
    )
    return DecisionHistory(
        opportunity_id=1,
        current_decision=recorded,
        prior_decisions=(recorded,),
    )
