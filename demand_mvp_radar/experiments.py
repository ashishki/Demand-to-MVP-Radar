"""MVP experiment pack validation and generation."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from demand_mvp_radar.decisions import DecisionHistory, decision_for_experiment_outcome
from demand_mvp_radar.models import ExperimentOutcomeRecord, MVPExperimentPack, OpportunityDossier

EXPERIMENT_APPROVAL_DECISIONS = {"build", "revisit"}


def build_experiment_pack(payload: dict[str, object]) -> MVPExperimentPack:
    """Validate and return a decision-grade MVP experiment pack."""

    return MVPExperimentPack.model_validate(payload)


def create_experiment_pack(
    dossier: OpportunityDossier,
    decision_history: DecisionHistory,
    *,
    one_function_scope: str,
    target_user: str,
    validation_method: str,
    first_10_targets: Sequence[str],
    success_threshold: str,
    kill_threshold: str,
    revisit_threshold: str,
    timebox_days: int,
) -> MVPExperimentPack:
    current_decision = decision_history.current_decision
    if (
        current_decision is None
        or current_decision.decision not in EXPERIMENT_APPROVAL_DECISIONS
        or str(decision_history.opportunity_id) != dossier.opportunity_id
    ):
        raise ValueError("experiment pack requires a human build or revisit decision")

    return MVPExperimentPack(
        opportunity_id=dossier.opportunity_id,
        one_function_scope=one_function_scope,
        target_user=target_user,
        validation_method=validation_method,
        first_10_targets=tuple(first_10_targets),
        success_threshold=success_threshold,
        kill_threshold=kill_threshold,
        revisit_threshold=revisit_threshold,
        timebox_days=timebox_days,
        source_citations=dossier.evidence,
        risk_flags=tuple(risk.text for risk in dossier.risks),
        human_decision=current_decision.decision,
        human_decision_reason=current_decision.reason,
    )


def record_experiment_outcome(
    *,
    experiment_id: str,
    opportunity_id: str,
    outcome: str,
    evidence_summary: str,
    actor: str,
    created_at: datetime | None = None,
) -> ExperimentOutcomeRecord:
    return ExperimentOutcomeRecord(
        experiment_id=experiment_id,
        opportunity_id=opportunity_id,
        outcome=outcome,
        evidence_summary=evidence_summary.strip(),
        actor=actor,
        created_at=created_at or datetime.now(UTC),
        decision_memory_value=decision_for_experiment_outcome(outcome),
    )
