"""Shared contracts for live source connectors."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from demand_mvp_radar.models import EvidenceRecord, SourceTrustLevel
from demand_mvp_radar.sources.base import QuarantinedSourceRow

RawSnapshotPolicy = Literal["disabled", "metadata_only", "enabled"]


class RateLimitPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    requests_per_minute: int = Field(ge=1)
    burst_limit: int | None = Field(default=None, ge=1)


class LiveSourceConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_name: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    trust_level: SourceTrustLevel
    freshness_window_days: int = Field(ge=1)
    enabled: bool = False
    cursor_support: bool
    raw_snapshot_policy: RawSnapshotPolicy
    rate_limit_policy: RateLimitPolicy
    approval_required: bool = False


class RateLimitState(BaseModel):
    model_config = ConfigDict(frozen=True)

    limited: bool
    remaining: int | None = Field(default=None, ge=0)
    reset_at: datetime | None = None
    retry_after_seconds: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def limited_sources_need_retry_or_reset(self) -> RateLimitState:
        if self.limited and self.retry_after_seconds is None and self.reset_at is None:
            raise ValueError("limited rate-limit state requires retry_after_seconds or reset_at")
        return self


class LiveConnectorResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    evidence: tuple[EvidenceRecord, ...]
    quarantined: tuple[QuarantinedSourceRow, ...] = ()
    source_counts: dict[str, int]
    error_counts: dict[str, int]
    cursor_state: dict[str, str]
    rate_limit_state: RateLimitState
    last_success_at: datetime | None = None

    @model_validator(mode="after")
    def live_evidence_requires_live_provenance(self) -> LiveConnectorResult:
        for record in self.evidence:
            _validate_live_evidence_record(record)
        return self


class LiveSourceConnector(Protocol):
    connector_version: str

    def collect(
        self,
        config: LiveSourceConfig,
        *,
        run_id: str,
        cursor_state: dict[str, str],
    ) -> LiveConnectorResult:
        """Collect live source data into normalized evidence records."""


def _validate_live_evidence_record(record: EvidenceRecord) -> None:
    missing_fields = [
        field_name
        for field_name in (
            "run_id",
            "source_name",
            "source_type",
            "source_id",
            "source_url",
            "content_hash",
            "source_fingerprint",
            "connector_version",
        )
        if not _has_text(getattr(record, field_name))
    ]
    if missing_fields:
        raise ValueError(
            "live evidence record missing required provenance fields: "
            + ", ".join(missing_fields)
        )


def _has_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())
