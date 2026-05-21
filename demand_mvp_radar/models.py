"""Domain models shared across the pipeline."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SourcePriority = Literal["P0", "P1", "P2", "P3"]
SourceTrustLevel = Literal["high", "medium", "low"]
SourceAccessMethod = Literal[
    "local_file",
    "local_repo",
    "public_api",
    "manual_snapshot",
    "saved_snapshot",
    "approved_export",
    "credentialed_api",
    "paid_api",
]


class SourceCatalogEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_type: str = Field(min_length=1)
    priority: SourcePriority
    trust_level: SourceTrustLevel
    freshness_window_days: int = Field(ge=1)
    access_method: SourceAccessMethod
    enabled: bool = False
    approval_required: bool = False
    credential_env_vars: tuple[str, ...] = ()

    @field_validator("credential_env_vars")
    @classmethod
    def credential_env_vars_must_be_names(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        for env_var_name in value:
            if not env_var_name.isidentifier() or env_var_name.upper() != env_var_name:
                raise ValueError("credential_env_vars must contain environment variable names")
        return value

    @model_validator(mode="after")
    def enabled_credentialed_sources_require_approval(
        self,
    ) -> SourceCatalogEntry:
        credentialed_methods = {"credentialed_api", "paid_api"}
        if (
            self.enabled
            and self.access_method in credentialed_methods
            and not self.approval_required
        ):
            raise ValueError("enabled credentialed sources require approval")
        return self


class RunManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    started_at: datetime
    ended_at: datetime | None = None
    status: str
    source_counts: dict[str, int] = Field(default_factory=dict)
    error_counts: dict[str, int] = Field(default_factory=dict)
    source_errors: dict[str, str] = Field(default_factory=dict)
    duplicate_count: int = Field(default=0, ge=0)
    corpus_version: str
    index_schema_version: str = "retrieval-index-v1"
    max_weekly_llm_cost_usd: Decimal = Field(ge=0)


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    source_name: str | None = None
    source_type: str
    source_id: str
    captured_at: datetime
    title: str
    snippet: str
    normalized_text: str
    content_hash: str
    source_fingerprint: str
    source_url: str | None = None
    connector_version: str | None = None
    author_hash: str | None = None
    source_site: str | None = None
    tags: tuple[str, ...] = ()
    score: int | None = None
    accepted_answer: bool | None = None
    feed_url: str | None = None
    published_at: datetime | None = None
    repository_locator: str | None = None
    labels: tuple[str, ...] = ()
    created_at: datetime | None = None
    updated_at: datetime | None = None
    search_query: str | None = None
    result_rank: int | None = None
    provider: str | None = None
    provider_metadata: dict[str, str] = Field(default_factory=dict)
    channel_hash: str | None = None
    video_id: str | None = None
    comment_id: str | None = None
    topics: tuple[str, ...] = ()
    launch_date: datetime | None = None
    vote_count: int | None = None
    comment_count: int | None = None
    subreddit: str | None = None


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


class DossierEvidenceItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    citation_number: int = Field(ge=1)
    source_type: str = Field(min_length=1)
    source_title_or_id: str = Field(min_length=1)
    captured_at: datetime
    snippet: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)


class DossierClaim(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str = Field(min_length=1)
    citation_numbers: tuple[int, ...] = ()
    inference: bool = False

    @model_validator(mode="after")
    def claim_requires_citation_or_inference_marker(self) -> DossierClaim:
        if not self.citation_numbers and not self.inference:
            raise ValueError("dossier claim requires citation or explicit inference marker")
        return self


class DossierPriorDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    decided_at: datetime | None = None


class OpportunityDossier(BaseModel):
    model_config = ConfigDict(frozen=True)

    opportunity_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    pain: DossierClaim
    audience: DossierClaim
    workaround: DossierClaim
    evidence: tuple[DossierEvidenceItem, ...]
    competitor_shape: DossierClaim
    one_function_mvp: DossierClaim
    acquisition_angle: DossierClaim
    risks: tuple[DossierClaim, ...]
    missing_evidence: tuple[str, ...]
    score_components: dict[str, ScoreComponent]
    recommendation: Literal["build", "reject", "revisit", "insufficient_evidence"]
    prior_decisions: tuple[DossierPriorDecision, ...] = ()
    confidence: str = Field(min_length=1)
    why_this_may_be_wrong: tuple[str, ...]

    @model_validator(mode="after")
    def cited_claims_reference_known_evidence(self) -> OpportunityDossier:
        available_citations = {item.citation_number for item in self.evidence}
        for claim in self._claims():
            unknown_citations = set(claim.citation_numbers) - available_citations
            if unknown_citations:
                raise ValueError(
                    "dossier claim references unknown citation number: "
                    f"{min(unknown_citations)}"
                )
        return self

    def _claims(self) -> tuple[DossierClaim, ...]:
        return (
            self.pain,
            self.audience,
            self.workaround,
            self.competitor_shape,
            self.one_function_mvp,
            self.acquisition_angle,
            *self.risks,
        )


class MVPExperimentPack(BaseModel):
    model_config = ConfigDict(frozen=True)

    opportunity_id: str = Field(min_length=1)
    one_function_scope: str = Field(min_length=1)
    target_user: str = Field(min_length=1)
    validation_method: str = Field(min_length=1)
    first_10_targets: tuple[str, ...] = Field(min_length=10, max_length=10)
    success_threshold: str = Field(min_length=1)
    kill_threshold: str = Field(min_length=1)
    revisit_threshold: str = Field(min_length=1)
    timebox_days: int = Field(ge=7, le=14)
    source_citations: tuple[DossierEvidenceItem, ...]
    risk_flags: tuple[str, ...] = ()
    human_decision: str = Field(min_length=1)
    human_decision_reason: str = Field(min_length=1)


class ExperimentOutcomeRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    experiment_id: str = Field(min_length=1)
    opportunity_id: str = Field(min_length=1)
    outcome: Literal["validated", "killed", "inconclusive"]
    evidence_summary: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    created_at: datetime
    decision_memory_value: str = Field(min_length=1)


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
    requested_evidence_gaps: tuple[str, ...] = ()
