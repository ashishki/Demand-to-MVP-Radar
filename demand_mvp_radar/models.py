"""Domain models shared across the pipeline."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RunManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    started_at: datetime
    ended_at: datetime | None = None
    status: str
    source_counts: dict[str, int] = Field(default_factory=dict)
    error_counts: dict[str, int] = Field(default_factory=dict)
    duplicate_count: int = Field(default=0, ge=0)
    corpus_version: str
    index_schema_version: str = "retrieval-index-v1"
    max_weekly_llm_cost_usd: Decimal = Field(ge=0)


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    source_type: str
    source_id: str
    captured_at: datetime
    title: str
    snippet: str
    normalized_text: str
    content_hash: str
    source_fingerprint: str
    source_url: str | None = None


class OpportunityCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    opportunity_id: str
    normalized_pain: str
    target_audience: str
    workflow: str
    acquisition_channel: str
    source_evidence_ids: tuple[str, ...]
    candidate_title: str


class ScoreComponent(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    value: float = Field(ge=0, le=100)
    rationale: str


class OpportunityScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    opportunity_id: str
    recommendation: str
    total_score: float = Field(ge=0, le=100)
    confidence_band: str
    components: dict[str, ScoreComponent]
    threshold_reasons: tuple[str, ...] = ()
    decision_memory_notes: tuple[str, ...] = ()


class OpportunityExtraction(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_pain: str = Field(min_length=1)
    target_audience: str = Field(min_length=1)
    current_workaround: str = Field(min_length=1)
    competitor_shape: str = Field(min_length=1)
    mvp_function: str = Field(min_length=1)
    acquisition_angle: str = Field(min_length=1)
    risk_flags: tuple[str, ...] = ()
    confidence_note: str = Field(min_length=1)


class DecisionRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    opportunity_id: int
    decision: str
    actor: str
    decided_at: datetime | None = None
    created_at: datetime | None = None
    reason: str | None = None
    rationale: str | None = None
    source_report_path: str | None = None
