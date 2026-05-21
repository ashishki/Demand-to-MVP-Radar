from __future__ import annotations

from datetime import UTC, datetime

import pytest
from demand_mvp_radar.reports.source_value import SourceValueInput, build_source_value_report
from demand_mvp_radar.review_cockpit import (
    ReviewCockpitConfig,
    build_review_cockpit_payload,
    record_review_cockpit_decision,
    render_review_cockpit_html,
)
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.storage.repositories import DecisionRepository, OpportunityRepository


def test_review_cockpit_serves_required_local_views() -> None:
    payload = _payload()
    html = render_review_cockpit_html(payload)

    assert payload.bind_host == "127.0.0.1"
    assert {
        "opportunities",
        "dossiers",
        "source_value",
        "missing_evidence",
        "experiments",
    } <= set(payload.views)
    assert "Opportunities" in html
    assert "Dossiers" in html
    assert "Source Value" in html
    assert "Missing Evidence" in html
    assert "Experiment Actions" in html


def test_review_cockpit_records_existing_decision_contract(tmp_path) -> None:
    connection = connect_database(tmp_path / "radar.sqlite3")
    create_schema(connection)
    opportunity_id = OpportunityRepository(connection).create("Webhook replay debugger")
    decision = record_review_cockpit_decision(
        DecisionRepository(connection),
        opportunity_id=opportunity_id,
        decision="needs_more_evidence",
        reason="Need non-Reddit corroboration.",
        actor="operator",
        source_report_path="reports/dossiers/opportunity-101.md",
        requested_evidence_gaps=("independent_source",),
        created_at=datetime(2026, 5, 21, 12, 0, tzinfo=UTC),
    )

    assert decision.opportunity_id == opportunity_id
    assert decision.decision == "needs_more_evidence"
    assert decision.actor == "operator"
    assert decision.reason == "Need non-Reddit corroboration."
    assert decision.requested_evidence_gaps == ("independent_source",)
    assert decision.created_at.isoformat() == "2026-05-21T12:00:00+00:00"


def test_review_cockpit_is_local_and_redacted_by_default() -> None:
    with pytest.raises(ValueError):
        ReviewCockpitConfig(host="0.0.0.0")

    payload = _payload()
    serialized = payload.model_dump_json()
    html = render_review_cockpit_html(payload)

    assert "raw private text" not in serialized
    assert "discord-secret-token-value-1234567890" not in serialized
    assert "DISCORD_BOT_TOKEN" not in serialized
    assert "raw private text" not in html
    assert "discord-secret-token-value-1234567890" not in html


def _payload():
    report = build_source_value_report(
        (
            SourceValueInput(
                source_name="discord-live",
                source_type="discord",
                evidence_count=1,
                cited_count=0,
                decision_influence_count=0,
                quarantined_count=0,
                failure_count=0,
                freshness_days=1,
            ),
        )
    )
    return build_review_cockpit_payload(
        opportunities=(
            {
                "id": 101,
                "title": "Webhook replay debugger",
                "raw_evidence": "raw private text discord-secret-token-value-1234567890",
            },
        ),
        dossiers=(
            {
                "path": "reports/dossiers/opportunity-101.md",
                "summary": "Needs independent evidence. DISCORD_BOT_TOKEN",
            },
        ),
        source_value_report=report,
        missing_evidence=("Need non-Reddit corroboration.",),
        experiment_actions=("Create 7 day smoke test.",),
    )
