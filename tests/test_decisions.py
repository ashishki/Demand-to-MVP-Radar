from __future__ import annotations

from datetime import UTC, datetime

import pytest
from demand_mvp_radar.decisions import (
    decision_guidance_for_portfolio_fit,
    get_decision_history,
    record_operator_decision,
)
from demand_mvp_radar.models import PortfolioFit
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.storage.repositories import DecisionRepository, OpportunityRepository


def test_decision_record_contains_required_fields(tmp_path) -> None:
    repository, opportunity_id = make_repository(tmp_path)

    decision = record_operator_decision(
        repository,
        opportunity_id=opportunity_id,
        decision="build",
        reason="Strong search demand and low implementation risk.",
        actor="operator",
        created_at=datetime(2026, 5, 19, 12, 0, tzinfo=UTC),
        source_report_path="reports/weekly.md",
    )

    row = repository.list_for_opportunity(opportunity_id)[0]
    assert decision.opportunity_id == opportunity_id
    assert row["opportunity_id"] == opportunity_id
    assert row["decision"] == "build"
    assert row["reason"] == "Strong search demand and low implementation risk."
    assert row["actor"] == "operator"
    assert row["created_at"] == "2026-05-19T12:00:00+00:00"
    assert row["source_report_path"] == "reports/weekly.md"


def test_second_decision_appends_without_overwrite(tmp_path) -> None:
    repository, opportunity_id = make_repository(tmp_path)

    first = record_operator_decision(
        repository,
        opportunity_id=opportunity_id,
        decision="revisit",
        reason="Needs more evidence.",
        actor="operator",
        created_at=datetime(2026, 5, 19, 12, 0, tzinfo=UTC),
    )
    second = record_operator_decision(
        repository,
        opportunity_id=opportunity_id,
        decision="reject",
        reason="Demand did not repeat.",
        actor="operator",
        created_at=datetime(2026, 5, 20, 12, 0, tzinfo=UTC),
    )

    rows = repository.list_for_opportunity(opportunity_id)
    assert second.decision_id != first.decision_id
    assert len(rows) == 2
    assert rows[0]["decision"] == "revisit"
    assert rows[0]["reason"] == "Needs more evidence."
    assert rows[1]["decision"] == "reject"


def test_decision_history_returns_current_and_full_history(tmp_path) -> None:
    repository, opportunity_id = make_repository(tmp_path)
    record_operator_decision(
        repository,
        opportunity_id=opportunity_id,
        decision="revisit",
        reason="Needs more evidence.",
        actor="operator",
        created_at=datetime(2026, 5, 19, 12, 0, tzinfo=UTC),
    )
    record_operator_decision(
        repository,
        opportunity_id=opportunity_id,
        decision="build",
        reason="New evidence supports a focused MVP.",
        actor="operator",
        created_at=datetime(2026, 5, 21, 12, 0, tzinfo=UTC),
    )

    history = get_decision_history(repository, opportunity_id=opportunity_id)

    assert history.current_decision is not None
    assert history.current_decision.decision == "build"
    assert history.current_decision.reason == "New evidence supports a focused MVP."
    assert [decision.decision for decision in history.prior_decisions] == ["revisit", "build"]


def test_portfolio_fit_labels_drive_conservative_review_guidance() -> None:
    primary_fit = PortfolioFit(
        category="lead_response_sla",
        reason="Matches the current lead response showcase.",
        showcase_priority="primary",
    )
    off_strategy = PortfolioFit(
        category="out_of_scope",
        reason="Interesting, but not part of the current showcase portfolio.",
        showcase_priority="off_strategy",
    )

    assert decision_guidance_for_portfolio_fit(primary_fit) == "revisit"
    assert decision_guidance_for_portfolio_fit(off_strategy) == "reject"


def test_out_of_scope_portfolio_fit_cannot_be_marked_primary() -> None:
    with pytest.raises(ValueError, match="out_of_scope portfolio fit"):
        PortfolioFit(
            category="out_of_scope",
            reason="Attractive but outside the portfolio.",
            showcase_priority="primary",
        )


def make_repository(tmp_path) -> tuple[DecisionRepository, int]:
    connection = connect_database(tmp_path / "radar.sqlite3")
    create_schema(connection)
    opportunity_id = OpportunityRepository(connection).create("Spreadsheet formula helper")
    return DecisionRepository(connection), opportunity_id
