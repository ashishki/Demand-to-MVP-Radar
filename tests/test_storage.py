from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from demand_mvp_radar.models import DecisionRecord, EvidenceRecord
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.storage.repositories import (
    DecisionRepository,
    EvidenceRepository,
    OpportunityRepository,
)


def open_test_database(tmp_path) -> sqlite3.Connection:
    connection = connect_database(tmp_path / "radar.sqlite3")
    create_schema(connection)
    return connection


def test_schema_contains_required_tables(tmp_path) -> None:
    connection = open_test_database(tmp_path)

    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = :type
        """,
        {"type": "table"},
    ).fetchall()

    assert {
        "runs",
        "evidence",
        "opportunities",
        "scores",
        "briefs",
        "decisions",
        "tool_audit_events",
        "retrieval_chunks",
    } <= {row["name"] for row in rows}


def test_evidence_write_is_idempotent_by_fingerprint(tmp_path) -> None:
    connection = open_test_database(tmp_path)
    repository = EvidenceRepository(connection)
    evidence = EvidenceRecord(
        run_id="run-001",
        source_type="telegram",
        source_id="message-1",
        captured_at=datetime(2026, 5, 19, 12, 0, tzinfo=UTC),
        title="Pain signal",
        snippet="A user describes a repetitive workflow.",
        normalized_text="A user describes a repetitive workflow.",
        content_hash="hash-001",
        source_fingerprint="telegram:message-1",
    )

    first_id = repository.write(evidence)
    second_id = repository.write(evidence)
    count = connection.execute(
        """
        SELECT COUNT(*) AS evidence_count
        FROM evidence
        WHERE source_fingerprint = :source_fingerprint
        """,
        {"source_fingerprint": evidence.source_fingerprint},
    ).fetchone()["evidence_count"]

    assert second_id == first_id
    assert count == 1


def test_decisions_are_append_only(tmp_path) -> None:
    connection = open_test_database(tmp_path)
    opportunity_id = OpportunityRepository(connection).create("Inbox triage assistant")
    decisions = DecisionRepository(connection)

    first_id = decisions.add(
        DecisionRecord(
            opportunity_id=opportunity_id,
            decision="revisit",
            actor="operator",
            decided_at=datetime(2026, 5, 19, 12, 0, tzinfo=UTC),
            rationale="Needs stronger evidence.",
        )
    )
    second_id = decisions.add(
        DecisionRecord(
            opportunity_id=opportunity_id,
            decision="reject",
            actor="operator",
            decided_at=datetime(2026, 5, 20, 12, 0, tzinfo=UTC),
            rationale="Demand did not repeat.",
        )
    )

    assert second_id != first_id
    assert decisions.count_for_opportunity(opportunity_id) == 2
