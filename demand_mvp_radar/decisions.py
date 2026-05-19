"""Operator-owned decision recording and lookup."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from demand_mvp_radar.models import DecisionRecord
from demand_mvp_radar.storage.repositories import DecisionRepository


class RecordedDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision_id: int
    opportunity_id: int
    decision: Literal["build", "reject", "revisit"]
    reason: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    created_at: datetime
    source_report_path: str | None = None


class DecisionHistory(BaseModel):
    model_config = ConfigDict(frozen=True)

    opportunity_id: int
    current_decision: RecordedDecision | None
    prior_decisions: tuple[RecordedDecision, ...]


def record_operator_decision(
    repository: DecisionRepository,
    *,
    opportunity_id: int,
    decision: Literal["build", "reject", "revisit"],
    reason: str,
    actor: str,
    source_report_path: str | None = None,
    created_at: datetime | None = None,
) -> RecordedDecision:
    recorded_at = created_at or datetime.now(UTC)
    decision_id = repository.add(
        DecisionRecord(
            opportunity_id=opportunity_id,
            decision=decision,
            actor=actor,
            created_at=recorded_at,
            reason=reason,
            source_report_path=source_report_path,
        )
    )
    return RecordedDecision(
        decision_id=decision_id,
        opportunity_id=opportunity_id,
        decision=decision,
        reason=reason,
        actor=actor,
        created_at=recorded_at,
        source_report_path=source_report_path,
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


def _row_to_decision(row) -> RecordedDecision:
    return RecordedDecision(
        decision_id=int(row["id"]),
        opportunity_id=int(row["opportunity_id"]),
        decision=row["decision"],
        reason=row["reason"] or "No reason recorded",
        actor=row["actor"],
        created_at=datetime.fromisoformat(row["created_at"]),
        source_report_path=row["source_report_path"],
    )
