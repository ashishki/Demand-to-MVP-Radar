from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.tools.executor import ToolExecutor, ToolPermissionError
from demand_mvp_radar.tools.schemas import (
    TOOL_CATALOG,
    FetchUrlSnapshotInput,
    FetchUrlSnapshotOutput,
)
from pydantic import BaseModel, ValidationError

ARCHITECTURE_TOOL_NAMES = {
    "read_telegram_evidence",
    "fetch_url_snapshot",
    "read_serp_snapshot",
    "read_store_metadata",
    "retrieve_evidence",
    "write_report",
    "record_operator_decision",
}


def test_tool_catalog_schema_entries_are_complete() -> None:
    assert set(TOOL_CATALOG) == ARCHITECTURE_TOOL_NAMES
    for name, schema in TOOL_CATALOG.items():
        assert schema.name == name
        assert schema.version
        assert issubclass(schema.input_model, BaseModel)
        assert issubclass(schema.output_model, BaseModel)
        assert schema.side_effect_class
        assert schema.idempotency_key_fields
        assert schema.permission_level
        assert schema.retry_policy
        assert schema.audit_fields


def test_invalid_tool_input_is_rejected_before_execution() -> None:
    called = False

    def implementation(_tool_input: BaseModel) -> dict[str, object]:
        nonlocal called
        called = True
        return {}

    executor = ToolExecutor({"fetch_url_snapshot": implementation})

    with pytest.raises(ValidationError):
        executor.execute("fetch_url_snapshot", {"run_id": "run-001"})

    assert called is False


def test_tool_executor_records_audit_event(tmp_path) -> None:
    connection = connect_database(tmp_path / "radar.sqlite3")
    create_schema(connection)

    def implementation(tool_input: BaseModel) -> FetchUrlSnapshotOutput:
        assert isinstance(tool_input, FetchUrlSnapshotInput)
        return FetchUrlSnapshotOutput(
            status_code=200,
            content_hash="hash-001",
            fetched_at=datetime(2026, 5, 19, 12, 0, tzinfo=UTC),
            normalized_text="normalized",
        )

    executor = ToolExecutor({"fetch_url_snapshot": implementation}, connection=connection)
    executor.execute("fetch_url_snapshot", {"run_id": "run-001", "url": "https://example.com"})

    row = connection.execute(
        """
        SELECT run_id, tool_name, version, success, latency_ms, audit_fields
        FROM tool_audit_events
        WHERE tool_name = :tool_name
        """,
        {"tool_name": "fetch_url_snapshot"},
    ).fetchone()
    audit_fields = json.loads(row["audit_fields"])

    assert row["run_id"] == "run-001"
    assert row["version"] == TOOL_CATALOG["fetch_url_snapshot"].version
    assert row["success"] == 1
    assert row["latency_ms"] >= 0
    assert audit_fields["url"] == "https://example.com"
    assert audit_fields["status_code"] == 200


def test_human_approved_tool_requires_permission_before_execution() -> None:
    called = False

    def implementation(_tool_input: BaseModel) -> dict[str, object]:
        nonlocal called
        called = True
        return {"decision_id": 1}

    executor = ToolExecutor({"record_operator_decision": implementation})

    with pytest.raises(ToolPermissionError):
        executor.execute(
            "record_operator_decision",
            {
                "opportunity_id": 1,
                "decision": "build",
                "actor": "operator",
                "timestamp": datetime(2026, 5, 19, 12, 0, tzinfo=UTC),
            },
        )

    assert called is False
