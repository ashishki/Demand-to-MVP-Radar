from __future__ import annotations

from datetime import UTC, datetime

import pytest
from demand_mvp_radar.decisions import DecisionHistory, RecordedDecision
from demand_mvp_radar.dossiers import build_opportunity_dossier
from demand_mvp_radar.experiments import build_experiment_pack, create_experiment_pack
from demand_mvp_radar.models import MVPExperimentPack
from pydantic import ValidationError


def test_experiment_pack_requires_validation_fields() -> None:
    pack = build_experiment_pack(_experiment_payload())

    assert isinstance(pack, MVPExperimentPack)
    assert pack.opportunity_id == "101"
    assert len(pack.first_10_targets) == 10
    assert pack.timebox_days == 10

    invalid_payload = _experiment_payload()
    invalid_payload.pop("success_threshold")
    with pytest.raises(ValidationError, match="success_threshold"):
        build_experiment_pack(invalid_payload)


def test_experiment_pack_requires_human_decision() -> None:
    dossier = build_opportunity_dossier(_dossier_payload())

    with pytest.raises(ValueError, match="human build or revisit decision"):
        create_experiment_pack(
            dossier,
            _decision_history(decision="reject"),
            **_experiment_inputs(),
        )

    with pytest.raises(ValueError, match="human build or revisit decision"):
        create_experiment_pack(
            dossier,
            DecisionHistory(opportunity_id=101, current_decision=None, prior_decisions=()),
            **_experiment_inputs(),
        )


def test_experiment_pack_inherits_dossier_context() -> None:
    dossier = build_opportunity_dossier(_dossier_payload())

    pack = create_experiment_pack(
        dossier,
        _decision_history(decision="build"),
        **_experiment_inputs(),
    )

    assert [item.citation_number for item in pack.source_citations] == [1, 2]
    assert pack.risk_flags == ("Accounting data may create compliance concerns.",)
    assert pack.human_decision == "build"
    assert pack.human_decision_reason == "Operator approved a focused validation run."


def _experiment_payload() -> dict[str, object]:
    return {
        "opportunity_id": "101",
        **_experiment_inputs(),
        "source_citations": _dossier_payload()["evidence"],
        "risk_flags": ("Accounting data may create compliance concerns.",),
        "human_decision": "build",
        "human_decision_reason": "Operator approved a focused validation run.",
    }


def _experiment_inputs() -> dict[str, object]:
    return {
        "one_function_scope": "Upload ledger rows and flag likely duplicate payments.",
        "target_user": "Finance operators reconciling invoices weekly.",
        "validation_method": "concierge_test",
        "first_10_targets": tuple(f"finance operator {index}" for index in range(1, 11)),
        "success_threshold": "3 of 10 operators submit real ledger samples.",
        "kill_threshold": "0 operators agree to a follow-up workflow review.",
        "revisit_threshold": "2 operators want it but need stronger privacy guarantees.",
        "timebox_days": 10,
    }


def _decision_history(*, decision: str) -> DecisionHistory:
    recorded = RecordedDecision(
        decision_id=1,
        opportunity_id=101,
        decision=decision,
        reason="Operator approved a focused validation run.",
        actor="operator",
        created_at=datetime(2026, 5, 20, 12, 0, tzinfo=UTC),
        source_report_path="reports/dossiers/opportunity-101.md",
    )
    return DecisionHistory(
        opportunity_id=101,
        current_decision=recorded,
        prior_decisions=(recorded,),
    )


def _dossier_payload() -> dict[str, object]:
    captured_at = datetime(2026, 5, 20, tzinfo=UTC).isoformat()
    return {
        "opportunity_id": "101",
        "title": "LedgerPulse Invoice Reconciliation",
        "pain": {
            "text": "Operators repeatedly mention invoice reconciliation pain.",
            "citation_numbers": [1],
        },
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
        "recommendation": "build",
        "prior_decisions": (),
        "confidence": "medium",
        "why_this_may_be_wrong": (
            "Evidence may overrepresent internal operator workflows.",
        ),
    }
