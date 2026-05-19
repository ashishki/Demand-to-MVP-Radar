"""Deterministic opportunity scoring and recommendation thresholds."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from demand_mvp_radar.decisions import DecisionHistory
from demand_mvp_radar.models import (
    EvidenceRecord,
    OpportunityCandidate,
    OpportunityScore,
    ScoreComponent,
)
from demand_mvp_radar.observability import span

COMPONENT_NAMES = (
    "demand",
    "evidence_diversity",
    "freshness",
    "competition",
    "acquisition_fit",
    "risk",
    "confidence",
)


@dataclass(frozen=True)
class ScoringConfig:
    minimum_evidence_count: int = 2
    build_threshold: float = 75.0
    revisit_threshold: float = 45.0
    max_fresh_days: int = 30
    reject_suppression_days: int = 30
    revisit_after_days: int = 14
    rejection_penalty: float = 40.0
    component_weights: Mapping[str, float] | None = None

    def weights(self) -> Mapping[str, float]:
        return self.component_weights or {
            "demand": 0.25,
            "evidence_diversity": 0.20,
            "freshness": 0.15,
            "competition": 0.10,
            "acquisition_fit": 0.15,
            "risk": 0.10,
            "confidence": 0.05,
        }


def score_opportunity(
    candidate: OpportunityCandidate,
    evidence_records: Sequence[EvidenceRecord],
    *,
    config: ScoringConfig | None = None,
    as_of: datetime | None = None,
) -> OpportunityScore:
    scoring_config = config or ScoringConfig()
    scoring_as_of = as_of or datetime.now(UTC)
    evidence = tuple(
        record for record in evidence_records if record.source_id in candidate.source_evidence_ids
    )

    with span("scoring.score_opportunity"):
        components = {
            "demand": _demand_component(evidence),
            "evidence_diversity": _evidence_diversity_component(evidence),
            "freshness": _freshness_component(
                evidence,
                as_of=scoring_as_of,
                max_fresh_days=scoring_config.max_fresh_days,
            ),
            "competition": _competition_component(evidence),
            "acquisition_fit": _acquisition_fit_component(candidate),
            "risk": _risk_component(evidence),
        }
        components["confidence"] = _confidence_component(components, evidence)
        total_score = _weighted_total(components, scoring_config.weights())
        threshold_reasons = _threshold_reasons(candidate, evidence, scoring_config)
        recommendation = _recommendation(
            total_score=total_score,
            threshold_reasons=threshold_reasons,
            config=scoring_config,
        )

    return OpportunityScore(
        opportunity_id=candidate.opportunity_id,
        recommendation=recommendation,
        total_score=total_score,
        confidence_band=_confidence_band(components["confidence"].value),
        components=components,
        threshold_reasons=threshold_reasons,
    )


def apply_decision_memory(
    score: OpportunityScore,
    decision_history: DecisionHistory,
    *,
    config: ScoringConfig | None = None,
    as_of: datetime | None = None,
) -> OpportunityScore:
    if str(decision_history.opportunity_id) != score.opportunity_id:
        return score
    if decision_history.current_decision is None:
        return score

    scoring_config = config or ScoringConfig()
    scoring_as_of = as_of or datetime.now(UTC)
    decision = decision_history.current_decision
    age_days = max((_to_utc(scoring_as_of) - _to_utc(decision.created_at)).days, 0)

    if decision.decision == "reject" and age_days <= scoring_config.reject_suppression_days:
        total_score = max(score.total_score - scoring_config.rejection_penalty, 0)
        note = f"recent reject suppression: {decision.reason}"
        return score.model_copy(
            update={
                "recommendation": "reject",
                "total_score": round(total_score, 2),
                "threshold_reasons": (*score.threshold_reasons, note),
                "decision_memory_notes": (*score.decision_memory_notes, note),
            }
        )

    if decision.decision == "revisit" and age_days >= scoring_config.revisit_after_days:
        note = f"prior revisit rationale: {decision.reason}"
        return score.model_copy(
            update={
                "decision_memory_notes": (*score.decision_memory_notes, note),
            }
        )

    return score


def _demand_component(evidence: tuple[EvidenceRecord, ...]) -> ScoreComponent:
    value = min(len(evidence) * 35, 100)
    return ScoreComponent(
        name="demand",
        value=float(value),
        rationale=f"{len(evidence)} supporting evidence records",
    )


def _evidence_diversity_component(evidence: tuple[EvidenceRecord, ...]) -> ScoreComponent:
    source_types = {record.source_type for record in evidence}
    value = min(len(source_types) * 40, 100)
    return ScoreComponent(
        name="evidence_diversity",
        value=float(value),
        rationale=f"{len(source_types)} independent source types",
    )


def _freshness_component(
    evidence: tuple[EvidenceRecord, ...],
    *,
    as_of: datetime,
    max_fresh_days: int,
) -> ScoreComponent:
    if not evidence:
        return ScoreComponent(name="freshness", value=0, rationale="no evidence dates")

    newest = max(_to_utc(record.captured_at) for record in evidence)
    age_days = max((_to_utc(as_of) - newest).days, 0)
    if age_days <= max_fresh_days:
        value = 100
    elif age_days <= max_fresh_days * 3:
        value = 70
    elif age_days <= max_fresh_days * 6:
        value = 40
    else:
        value = 15
    return ScoreComponent(
        name="freshness",
        value=float(value),
        rationale=f"newest evidence is {age_days} days old",
    )


def _competition_component(evidence: tuple[EvidenceRecord, ...]) -> ScoreComponent:
    text = _combined_text(evidence)
    competitor_terms = {"competitor", "alternative", "pricing", "marketplace", "existing"}
    matches = sum(1 for term in competitor_terms if term in text)
    value = 80 if matches else 55
    return ScoreComponent(
        name="competition",
        value=float(value),
        rationale=f"{matches} competitor-shape signals found",
    )


def _acquisition_fit_component(candidate: OpportunityCandidate) -> ScoreComponent:
    values = {
        "search": 85,
        "marketplace": 75,
        "community": 70,
    }
    value = values.get(candidate.acquisition_channel, 55)
    return ScoreComponent(
        name="acquisition_fit",
        value=float(value),
        rationale=f"{candidate.acquisition_channel} acquisition channel",
    )


def _risk_component(evidence: tuple[EvidenceRecord, ...]) -> ScoreComponent:
    text = _combined_text(evidence)
    risk_terms = {"medical", "legal", "financial", "credential", "private", "compliance"}
    matches = sum(1 for term in risk_terms if term in text)
    value = max(100 - matches * 25, 25)
    return ScoreComponent(
        name="risk",
        value=float(value),
        rationale=f"{matches} risk terms found",
    )


def _confidence_component(
    components: dict[str, ScoreComponent],
    evidence: tuple[EvidenceRecord, ...],
) -> ScoreComponent:
    base = (
        components["demand"].value
        + components["evidence_diversity"].value
        + components["freshness"].value
    ) / 3
    penalty = 20 if len(evidence) < 2 else 0
    value = max(base - penalty, 0)
    return ScoreComponent(
        name="confidence",
        value=round(value, 2),
        rationale="derived from demand, diversity, freshness, and minimum support",
    )


def _weighted_total(
    components: dict[str, ScoreComponent],
    weights: Mapping[str, float],
) -> float:
    total = sum(components[name].value * weights[name] for name in COMPONENT_NAMES)
    return round(total, 2)


def _threshold_reasons(
    candidate: OpportunityCandidate,
    evidence: tuple[EvidenceRecord, ...],
    config: ScoringConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if len(evidence) < config.minimum_evidence_count:
        reasons.append(
            "minimum evidence count: "
            f"required {config.minimum_evidence_count}, found {len(evidence)}"
        )
    if len(set(candidate.source_evidence_ids)) != len(candidate.source_evidence_ids):
        reasons.append("duplicate source evidence ids")
    return tuple(reasons)


def _recommendation(
    *,
    total_score: float,
    threshold_reasons: tuple[str, ...],
    config: ScoringConfig,
) -> str:
    if threshold_reasons:
        return "revisit"
    if total_score >= config.build_threshold:
        return "build"
    if total_score >= config.revisit_threshold:
        return "revisit"
    return "reject"


def _confidence_band(value: float) -> str:
    if value >= 75:
        return "high"
    if value >= 45:
        return "medium"
    return "low"


def _combined_text(evidence: tuple[EvidenceRecord, ...]) -> str:
    return " ".join(
        f"{record.title} {record.snippet} {record.normalized_text}".lower() for record in evidence
    )


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
