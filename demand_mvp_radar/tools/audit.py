"""Tool audit persistence."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

from demand_mvp_radar.observability import span


@dataclass(frozen=True)
class ToolAuditEvent:
    run_id: str
    tool_name: str
    version: str
    success: bool
    latency_ms: int
    audit_fields: dict[str, object]


def record_tool_audit_event(connection: sqlite3.Connection, event: ToolAuditEvent) -> None:
    with span("sqlite.record_tool_audit_event"):
        connection.execute(
            """
            INSERT INTO tool_audit_events (
                run_id,
                tool_name,
                version,
                success,
                latency_ms,
                audit_fields
            )
            VALUES (
                :run_id,
                :tool_name,
                :version,
                :success,
                :latency_ms,
                :audit_fields
            )
            """,
            {
                "run_id": event.run_id,
                "tool_name": event.tool_name,
                "version": event.version,
                "success": int(event.success),
                "latency_ms": event.latency_ms,
                "audit_fields": json.dumps(event.audit_fields, sort_keys=True, default=str),
            },
        )
        connection.commit()
