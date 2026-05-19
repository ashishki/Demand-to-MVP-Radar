"""Structured opportunity extraction from retrieved evidence packets."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, ValidationError

from demand_mvp_radar.llm.adapter import LLMProvider
from demand_mvp_radar.models import OpportunityExtraction
from demand_mvp_radar.observability import span
from demand_mvp_radar.retrieval.query import RetrievalResponse


class ExtractionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str
    extraction: OpportunityExtraction | None = None
    error_reason: str | None = None


def extract_opportunity_fields(
    retrieval_response: RetrievalResponse,
    *,
    provider: LLMProvider,
) -> ExtractionResult:
    if retrieval_response.status == "insufficient_evidence":
        return ExtractionResult(
            status="skipped",
            error_reason="insufficient_evidence",
        )

    prompt = _build_prompt()
    with span("llm.extract_opportunity_fields"):
        raw_output = provider.complete_json(
            prompt=prompt,
            evidence_packets=retrieval_response.evidence_packets,
        )

    try:
        extraction = OpportunityExtraction.model_validate_json(raw_output)
    except ValidationError as exc:
        return ExtractionResult(
            status="validation_error",
            error_reason=_validation_summary(exc),
        )

    return ExtractionResult(status="ok", extraction=extraction)


def _build_prompt() -> str:
    return (
        "Extract opportunity fields from the provided evidence packets. "
        "Return only JSON with user_pain, target_audience, current_workaround, "
        "competitor_shape, mvp_function, acquisition_angle, risk_flags, and confidence_note."
    )


def _validation_summary(error: ValidationError) -> str:
    fields = sorted(
        ".".join(str(part) for part in item["loc"])
        for item in error.errors(include_url=False, include_input=False)
    )
    if not fields:
        return "invalid extraction output"
    return f"invalid extraction fields: {', '.join(fields)}"
