from __future__ import annotations

import json
from datetime import UTC, datetime

from demand_mvp_radar.llm.adapter import FakeLLMProvider
from demand_mvp_radar.llm.extraction import extract_opportunity_fields
from demand_mvp_radar.retrieval.query import EvidencePacket, RetrievalResponse


def test_extraction_output_requires_expected_fields() -> None:
    provider = FakeLLMProvider(
        json.dumps(
            {
                "user_pain": "Operators waste time fixing broken spreadsheet formulas.",
                "target_audience": "operators",
                "current_workaround": "Manual searching and trial-and-error formula edits.",
                "competitor_shape": "Formula explainers and spreadsheet add-ons.",
                "mvp_function": "Explain and repair one broken formula at a time.",
                "acquisition_angle": "Search-led pages for Excel formula errors.",
                "risk_flags": ["spreadsheet edge cases"],
                "confidence_note": "Supported by two cited evidence packets.",
            }
        )
    )

    result = extract_opportunity_fields(supported_response(), provider=provider)

    assert result.status == "ok"
    assert result.extraction is not None
    assert result.extraction.user_pain.startswith("Operators waste")
    assert result.extraction.mvp_function == "Explain and repair one broken formula at a time."
    assert len(provider.calls) == 1


def test_malformed_provider_output_is_rejected() -> None:
    provider = FakeLLMProvider(
        json.dumps(
            {
                "user_pain": "Operators waste time fixing broken spreadsheet formulas.",
                "target_audience": "operators",
            }
        )
    )

    result = extract_opportunity_fields(supported_response(), provider=provider)

    assert result.status == "validation_error"
    assert result.extraction is None
    assert "current_workaround" in (result.error_reason or "")


def test_extraction_skips_insufficient_evidence() -> None:
    provider = FakeLLMProvider("{}")
    response = RetrievalResponse(
        status="insufficient_evidence",
        corpus_version="corpus-test",
        missing_evidence_reasons=("minimum independent source count",),
    )

    result = extract_opportunity_fields(response, provider=provider)

    assert result.status == "skipped"
    assert result.error_reason == "insufficient_evidence"
    assert result.extraction is None
    assert provider.calls == []


def supported_response() -> RetrievalResponse:
    return RetrievalResponse(
        status="ok",
        corpus_version="corpus-test",
        evidence_packets=(
            EvidencePacket(
                evidence_id=1,
                source_url="https://example.com/1",
                captured_at=datetime(2026, 5, 18, 10, 0, tzinfo=UTC),
                snippet="Operators ask for spreadsheet formula help.",
                relevance_score=0.9,
                citation_number=1,
            ),
            EvidencePacket(
                evidence_id=2,
                source_url="https://example.com/2",
                captured_at=datetime(2026, 5, 18, 11, 0, tzinfo=UTC),
                snippet="Search snippets show Excel formula helper demand.",
                relevance_score=0.8,
                citation_number=2,
            ),
        ),
    )
