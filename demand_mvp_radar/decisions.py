"""Operator-owned decision recording and lookup."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from demand_mvp_radar.models import DecisionRecord
from demand_mvp_radar.storage.repositories import DecisionRepository

DecisionValue = Literal[
    "build",
    "reject",
    "revisit",
    "needs_more_evidence",
    "already_exists",
    "not_my_icp",
    "too_hard_to_distribute",
]
EXPERIMENT_OUTCOME_DECISIONS: dict[str, DecisionValue] = {
    "validated": "build",
    "killed": "reject",
    "inconclusive": "revisit",
}


class RecordedDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision_id: int
    opportunity_id: int
    decision: DecisionValue
    reason: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    created_at: datetime
    source_report_path: str | None = None
    requested_evidence_gaps: tuple[str, ...] = ()


class DecisionHistory(BaseModel):
    model_config = ConfigDict(frozen=True)

    opportunity_id: int
    current_decision: RecordedDecision | None
    prior_decisions: tuple[RecordedDecision, ...]


def record_operator_decision(
    repository: DecisionRepository,
    *,
    opportunity_id: int,
    decision: DecisionValue,
    reason: str,
    actor: str,
    source_report_path: str | None = None,
    requested_evidence_gaps: tuple[str, ...] = (),
    created_at: datetime | None = None,
) -> RecordedDecision:
    normalized_reason = reason.strip()
    normalized_gaps = tuple(gap.strip() for gap in requested_evidence_gaps if gap.strip())
    if not normalized_reason:
        raise ValueError("operator reason is required")
    recorded_at = created_at or datetime.now(UTC)
    decision_id = repository.add(
        DecisionRecord(
            opportunity_id=opportunity_id,
            decision=decision,
            actor=actor,
            created_at=recorded_at,
            reason=normalized_reason,
            source_report_path=source_report_path,
            requested_evidence_gaps=normalized_gaps,
        )
    )
    return RecordedDecision(
        decision_id=decision_id,
        opportunity_id=opportunity_id,
        decision=decision,
        reason=normalized_reason,
        actor=actor,
        created_at=recorded_at,
        source_report_path=source_report_path,
        requested_evidence_gaps=normalized_gaps,
    )


def get_decision_history(
    repository: DecisionRepository,
    *,
    opportunity_id: int,
) -> DecisionHistory:
    rows = repository.list_for_opportunity(opportunity_id)
    decisions = tuple(_row_to_decision(row) for row in rows)
    current = decisions[-1] if decisions else None
    return DecisionHistory(
        opportunity_id=opportunity_id,
        current_decision=current,
        prior_decisions=decisions,
    )


def decision_for_experiment_outcome(outcome: str) -> DecisionValue:
    try:
        return EXPERIMENT_OUTCOME_DECISIONS[outcome]
    except KeyError as exc:
        raise ValueError(f"unsupported experiment outcome: {outcome}") from exc


def _row_to_decision(row) -> RecordedDecision:
    return RecordedDecision(
        decision_id=int(row["id"]),
        opportunity_id=int(row["opportunity_id"]),
        decision=row["decision"],
        reason=row["reason"] or "No reason recorded",
        actor=row["actor"],
        created_at=datetime.fromisoformat(row["created_at"]),
        source_report_path=row["source_report_path"],
        requested_evidence_gaps=_decode_requested_evidence_gaps(
            row["requested_evidence_gaps"] if "requested_evidence_gaps" in row.keys() else None
        ),
    )


def _decode_requested_evidence_gaps(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    decoded = json.loads(value)
    if not isinstance(decoded, list):
        return ()
    return tuple(str(item) for item in decoded if str(item).strip())
