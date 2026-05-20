"""Opportunity dossier construction helpers."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field

from demand_mvp_radar.models import OpportunityDossier
from demand_mvp_radar.retrieval.query import classify_missing_evidence_reasons


class MissingEvidenceGap(BaseModel):
    model_config = ConfigDict(frozen=True)

    gap_type: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    suggested_source_types: tuple[str, ...]
    suggested_queries: tuple[str, ...]


def build_opportunity_dossier(payload: dict[str, object]) -> OpportunityDossier:
    """Validate and return a decision-grade opportunity dossier."""

    return OpportunityDossier.model_validate(payload)


def analyze_missing_evidence(
    dossier: OpportunityDossier,
    *,
    retrieval_missing_reasons: Sequence[str] = (),
    as_of: datetime | None = None,
    max_fresh_days: int = 30,
) -> tuple[MissingEvidenceGap, ...]:
    analysis_as_of = as_of or datetime.now(UTC)
    gaps: dict[str, MissingEvidenceGap] = {}
    for gap_type in classify_missing_evidence_reasons(tuple(retrieval_missing_reasons)):
        gaps[gap_type] = _gap_for_type(gap_type, dossier)

    source_types = {evidence.source_type for evidence in dossier.evidence}
    if len(source_types) < 2:
        gaps.setdefault(
            "absent_independent_sources",
            _gap_for_type("absent_independent_sources", dossier),
        )

    if dossier.evidence and all(
        _to_utc(evidence.captured_at) < _to_utc(analysis_as_of) - timedelta(days=max_fresh_days)
        for evidence in dossier.evidence
    ):
        gaps.setdefault("stale_evidence", _gap_for_type("stale_evidence", dossier))

    missing_text = " ".join(dossier.missing_evidence).lower()
    if dossier.competitor_shape.inference or "competitor" in missing_text:
        gaps.setdefault("weak_competitor_proof", _gap_for_type("weak_competitor_proof", dossier))
    if dossier.acquisition_angle.inference or "acquisition" in missing_text:
        gaps.setdefault(
            "missing_acquisition_proof",
            _gap_for_type("missing_acquisition_proof", dossier),
        )
    if any(term in missing_text for term in ("willingness", "pay", "pricing", "payment")):
        gaps.setdefault(
            "missing_willingness_to_pay_signal",
            _gap_for_type("missing_willingness_to_pay_signal", dossier),
        )

    return tuple(gaps[gap_type] for gap_type in sorted(gaps))


def _gap_for_type(gap_type: str, dossier: OpportunityDossier) -> MissingEvidenceGap:
    query_seed = dossier.title
    templates = {
        "absent_independent_sources": MissingEvidenceGap(
            gap_type=gap_type,
            rationale=(
                "Collect corroboration from another independent source type before upgrading."
            ),
            suggested_source_types=("reviews", "github_repo", "hacker_news", "serp"),
            suggested_queries=(f"{query_seed} user pain", f"{query_seed} alternative workflow"),
        ),
        "absent_source_link": MissingEvidenceGap(
            gap_type=gap_type,
            rationale="Collect inspectable source links or stable source IDs for the claim.",
            suggested_source_types=("serp", "reviews", "github_repo"),
            suggested_queries=(f"{query_seed} source examples",),
        ),
        "stale_evidence": MissingEvidenceGap(
            gap_type=gap_type,
            rationale="Collect fresh evidence before trusting the current opportunity shape.",
            suggested_source_types=("telegram_research_agent", "hacker_news", "serp"),
            suggested_queries=(f"{query_seed} current demand",),
        ),
        "weak_competitor_proof": MissingEvidenceGap(
            gap_type=gap_type,
            rationale="Collect competitor or alternative proof instead of assuming market shape.",
            suggested_source_types=("serp", "product_hunt", "reviews"),
            suggested_queries=(f"{query_seed} competitors", f"{query_seed} alternatives"),
        ),
        "missing_acquisition_proof": MissingEvidenceGap(
            gap_type=gap_type,
            rationale=(
                "Collect acquisition-channel evidence before relying on the proposed channel."
            ),
            suggested_source_types=("serp", "hacker_news", "reddit"),
            suggested_queries=(f"{query_seed} search intent", f"{query_seed} community discussion"),
        ),
        "missing_willingness_to_pay_signal": MissingEvidenceGap(
            gap_type=gap_type,
            rationale=(
                "Collect pricing, paid-tool, or budget evidence before inferring "
                "willingness to pay."
            ),
            suggested_source_types=("reviews", "serp", "product_hunt"),
            suggested_queries=(f"{query_seed} pricing", f"{query_seed} paid alternative"),
        ),
    }
    return templates[gap_type]


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
