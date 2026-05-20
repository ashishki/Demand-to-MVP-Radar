from __future__ import annotations

import json
import sqlite3

from demand_mvp_radar.cli import main
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.storage.repositories import OpportunityRepository


def test_review_command_records_decision_with_dossier_path(tmp_path, capsys) -> None:
    opportunity_id = _create_opportunity(tmp_path)

    exit_code = main(
        [
            "review",
            "--opportunity-id",
            str(opportunity_id),
            "--decision",
            "revisit",
            "--reason",
            "Promising but needs fresher evidence.",
            "--dossier-path",
            "reports/dossiers/opportunity-001.md",
            "--data-dir",
            str(tmp_path / "data"),
        ]
    )
    output = json.loads(capsys.readouterr().out)
    row = _latest_decision(tmp_path)

    assert exit_code == 0
    assert output["opportunity_id"] == opportunity_id
    assert row["opportunity_id"] == opportunity_id
    assert row["decision"] == "revisit"
    assert row["reason"] == "Promising but needs fresher evidence."
    assert row["source_report_path"] == "reports/dossiers/opportunity-001.md"


def test_review_command_requires_reason_for_build(tmp_path, capsys) -> None:
    opportunity_id = _create_opportunity(tmp_path)

    exit_code = main(
        [
            "review",
            "--opportunity-id",
            str(opportunity_id),
            "--decision",
            "build",
            "--dossier-path",
            "reports/dossiers/opportunity-001.md",
            "--data-dir",
            str(tmp_path / "data"),
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert "build decisions require --reason" in output["error"]
    assert _decision_count(tmp_path) == 0


def test_review_command_records_needs_more_evidence(tmp_path, capsys) -> None:
    opportunity_id = _create_opportunity(tmp_path)

    exit_code = main(
        [
            "review",
            "--opportunity-id",
            str(opportunity_id),
            "--decision",
            "needs_more_evidence",
            "--reason",
            "Need independent competitor and payment proof.",
            "--dossier-path",
            "reports/dossiers/opportunity-001.md",
            "--data-dir",
            str(tmp_path / "data"),
            "--evidence-gap",
            "weak_competitor_proof",
            "--evidence-gap",
            "missing_willingness_to_pay_signal",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    row = _latest_decision(tmp_path)

    assert exit_code == 0
    assert output["decision"] == "needs_more_evidence"
    assert output["requested_evidence_gaps"] == [
        "weak_competitor_proof",
        "missing_willingness_to_pay_signal",
    ]
    assert row["decision"] == "needs_more_evidence"
    assert json.loads(row["requested_evidence_gaps"]) == [
        "weak_competitor_proof",
        "missing_willingness_to_pay_signal",
    ]


def _create_opportunity(tmp_path) -> int:
    connection = connect_database(tmp_path / "data" / "radar.sqlite3")
    create_schema(connection)
    return OpportunityRepository(connection).create("Review command opportunity")


def _latest_decision(tmp_path) -> sqlite3.Row:
    connection = _connection(tmp_path)
    row = connection.execute(
        """
        SELECT *
        FROM decisions
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()
    assert row is not None
    return row


def _decision_count(tmp_path) -> int:
    return int(_connection(tmp_path).execute("SELECT COUNT(*) FROM decisions").fetchone()[0])


def _connection(tmp_path) -> sqlite3.Connection:
    connection = sqlite3.connect(tmp_path / "data" / "radar.sqlite3")
    connection.row_factory = sqlite3.Row
    return connection
