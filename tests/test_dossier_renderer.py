from __future__ import annotations

from datetime import UTC, datetime

from demand_mvp_radar.dossiers import build_opportunity_dossier
from demand_mvp_radar.reports.dossier_html import render_dossier_html
from demand_mvp_radar.reports.dossier_markdown import render_dossier_markdown


def test_markdown_dossier_contains_required_sections() -> None:
    dossier = build_opportunity_dossier(_dossier_payload())

    markdown = render_dossier_markdown(dossier)

    expected_sections = [
        "# LedgerPulse Invoice Reconciliation",
        "## Decision Summary",
        "## Pain",
        "## Audience",
        "## Current Workaround",
        "## Evidence",
        "## Competitor Shape",
        "## One-Function MVP",
        "## Acquisition Angle",
        "## Risks",
        "## Missing Evidence",
        "## Score Components",
        "## Prior Decisions",
        "## Why This May Be Wrong",
    ]
    positions = [markdown.index(section) for section in expected_sections]

    assert positions == sorted(positions)
    assert "Recommendation: **revisit**" in markdown
    assert "This dossier is advisory; the operator owns the final decision." in markdown
    assert "Upload ledger rows and flag likely duplicate payments. _(inference)_" in markdown


def test_dossier_citations_include_required_provenance() -> None:
    dossier = build_opportunity_dossier(_dossier_payload())

    markdown = render_dossier_markdown(dossier)

    assert "| [1] | telegram_research_agent | telegram-live-001 | 2026-05-20 |" in markdown
    assert "https://t.me/operators/ledgerpulse-001" in markdown
    assert "Operators repeatedly ask for invoice reconciliation help." in markdown
    assert "[1]" in markdown
    assert "[2]" in markdown
    assert "<pre>" in render_dossier_html(dossier)


def test_renderer_handles_insufficient_evidence_dossier() -> None:
    payload = _dossier_payload()
    payload["recommendation"] = "insufficient_evidence"
    payload["evidence"] = []
    payload["pain"] = {
        "text": "Invoice reconciliation pain is not sufficiently corroborated.",
        "inference": True,
    }
    payload["audience"] = {
        "text": "The likely audience is finance operators.",
        "inference": True,
    }
    payload["workaround"] = {
        "text": "Current workaround is unknown.",
        "inference": True,
    }
    payload["competitor_shape"] = {
        "text": "Competitor proof is absent.",
        "inference": True,
    }
    dossier = build_opportunity_dossier(payload)

    markdown = render_dossier_markdown(dossier)

    assert "Recommendation: **insufficient_evidence**" in markdown
    assert "must not be treated as a build recommendation" in markdown
    assert "| Citation | Source Type | Source | Captured | Reference | Snippet |" in markdown
    assert "## Missing Evidence" in markdown
    assert "willingness-to-pay proof" in markdown


def _dossier_payload() -> dict[str, object]:
    captured_at = datetime(2026, 5, 20, tzinfo=UTC).isoformat()
    return {
        "opportunity_id": "opp-ledgerpulse",
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
