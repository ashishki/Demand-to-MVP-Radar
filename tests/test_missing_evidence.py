from __future__ import annotations

from datetime import UTC, datetime

from demand_mvp_radar.dossiers import analyze_missing_evidence, build_opportunity_dossier


def test_missing_evidence_identifies_required_gap_types() -> None:
    dossier = build_opportunity_dossier(_weak_dossier_payload())

    gaps = analyze_missing_evidence(
        dossier,
        retrieval_missing_reasons=(
            "minimum independent source count: required 2, found 1",
            "fresh relevant evidence",
        ),
        as_of=datetime(2026, 5, 20, tzinfo=UTC),
        max_fresh_days=30,
    )
    gap_types = {gap.gap_type for gap in gaps}

    assert {
        "absent_independent_sources",
        "stale_evidence",
        "weak_competitor_proof",
        "missing_acquisition_proof",
        "missing_willingness_to_pay_signal",
    } <= gap_types


def test_missing_evidence_suggests_next_collection_targets() -> None:
    dossier = build_opportunity_dossier(_weak_dossier_payload())

    gaps = analyze_missing_evidence(
        dossier,
        retrieval_missing_reasons=("minimum independent source count: required 2, found 1",),
        as_of=datetime(2026, 5, 20, tzinfo=UTC),
    )
    all_source_types = {source_type for gap in gaps for source_type in gap.suggested_source_types}
    all_queries = [query for gap in gaps for query in gap.suggested_queries]
    all_rationales = " ".join(gap.rationale.lower() for gap in gaps)

    assert {"serp", "reviews"} <= all_source_types
    assert any("LedgerPulse Invoice Reconciliation" in query for query in all_queries)
    assert "collect" in all_rationales
    assert "is confirmed" not in all_rationales
    assert "will work" not in all_rationales


def _weak_dossier_payload() -> dict[str, object]:
    captured_at = datetime(2026, 4, 1, tzinfo=UTC).isoformat()
    return {
        "opportunity_id": "opp-ledgerpulse",
        "title": "LedgerPulse Invoice Reconciliation",
        "pain": {
            "text": "Operators mention invoice reconciliation pain.",
            "citation_numbers": [1],
        },
        "audience": {
            "text": "The audience is finance operators.",
            "citation_numbers": [1],
        },
        "workaround": {
            "text": "Teams currently reconcile duplicate payments manually.",
            "citation_numbers": [1],
        },
        "evidence": [
            {
                "citation_number": 1,
                "source_type": "operator_note",
                "source_title_or_id": "note-001",
                "captured_at": captured_at,
                "snippet": "Private note mentions duplicate payment reconciliation.",
                "source_ref": "operator_note:redacted",
            }
        ],
        "competitor_shape": {
            "text": "Competitor proof is still inferred from sparse evidence.",
            "inference": True,
        },
        "one_function_mvp": {
            "text": "Flag likely duplicate payments in uploaded ledger rows.",
            "inference": True,
        },
        "acquisition_angle": {
            "text": "Search-led acquisition might work for reconciliation templates.",
            "inference": True,
        },
        "risks": (
            {
                "text": "Accounting data may create compliance concerns.",
                "inference": True,
            },
        ),
        "missing_evidence": (
            "competitor proof",
            "acquisition proof",
            "willingness-to-pay signal",
        ),
        "score_components": {
            "demand": {
                "name": "demand",
                "value": 20,
                "rationale": "single low-trust record",
            }
        },
        "recommendation": "insufficient_evidence",
        "prior_decisions": (),
        "confidence": "low",
        "why_this_may_be_wrong": ("Only private note evidence is available.",),
    }
