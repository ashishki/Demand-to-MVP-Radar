from __future__ import annotations

from datetime import UTC, datetime

import pytest
from demand_mvp_radar.dossiers import build_opportunity_dossier
from demand_mvp_radar.models import OpportunityDossier
from pydantic import ValidationError


def test_dossier_schema_requires_decision_grade_fields() -> None:
    dossier = build_opportunity_dossier(_dossier_payload())

    assert isinstance(dossier, OpportunityDossier)
    assert dossier.pain.text
    assert dossier.audience.text
    assert dossier.workaround.text
    assert dossier.evidence[0].source_type == "telegram_research_agent"
    assert dossier.competitor_shape.text
    assert dossier.one_function_mvp.text
    assert dossier.acquisition_angle.text
    assert dossier.risks
    assert dossier.missing_evidence == ("willingness-to-pay proof",)
    assert "demand" in dossier.score_components
    assert dossier.recommendation == "revisit"
    assert dossier.prior_decisions[0].decision == "reject"


def test_dossier_rejects_uncited_claims() -> None:
    payload = _dossier_payload()
    payload["pain"] = {"text": "Operators need reconciliation help."}

    with pytest.raises(ValidationError, match="citation or explicit inference"):
        build_opportunity_dossier(payload)


def test_dossier_includes_confidence_and_countercase() -> None:
    dossier = build_opportunity_dossier(_dossier_payload())

    assert dossier.confidence == "medium"
    assert dossier.why_this_may_be_wrong == (
        "Evidence may overrepresent internal operator workflows.",
    )
    assert dossier.acquisition_angle.inference is True


def _dossier_payload() -> dict[str, object]:
    captured_at = datetime(2026, 5, 20, tzinfo=UTC).isoformat()
    cited_claim = {
        "text": "Operators repeatedly mention invoice reconciliation pain.",
        "citation_numbers": [1],
    }
    return {
        "opportunity_id": "opp-ledgerpulse",
        "title": "LedgerPulse Invoice Reconciliation",
        "pain": cited_claim,
        "audience": {
            "text": "The audience is finance operators.",
            "citation_numbers": [1],
        },
        "workaround": {
            "text": "Teams currently reconcile duplicate payments manually.",
            "citation_numbers": [2],
        },
        "evidence": [
            {
                "citation_number": 1,
                "source_type": "telegram_research_agent",
                "source_title_or_id": "telegram-live-001",
                "captured_at": captured_at,
                "snippet": "Operators repeatedly ask for invoice reconciliation help.",
                "source_ref": "https://t.me/operators/ledgerpulse-001",
            },
            {
                "citation_number": 2,
                "source_type": "github_repo",
                "source_title_or_id": "issue-12",
                "captured_at": captured_at,
                "snippet": "GitHub snapshot tracks duplicate payment reconciliation bugs.",
                "source_ref": "https://github.example.local/operator/ledgerpulse/issues/12",
            },
        ],
        "competitor_shape": {
            "text": "Existing tools are priced as broader accounting platforms.",
            "citation_numbers": [2],
        },
        "one_function_mvp": {
            "text": "Upload ledger rows and flag likely duplicate payments.",
            "inference": True,
        },
        "acquisition_angle": {
            "text": "Search-led acquisition may work for reconciliation templates.",
            "inference": True,
        },
        "risks": [
            {
                "text": "Accounting data may create compliance concerns.",
                "inference": True,
            }
        ],
        "missing_evidence": ("willingness-to-pay proof",),
        "score_components": {
            "demand": {
                "name": "demand",
                "value": 70,
                "rationale": "two source-backed demand records",
            }
        },
        "recommendation": "revisit",
        "prior_decisions": [
            {
                "decision": "reject",
                "reason": "not enough public corroboration",
                "decided_at": captured_at,
            }
        ],
        "confidence": "medium",
        "why_this_may_be_wrong": (
            "Evidence may overrepresent internal operator workflows.",
        ),
    }
