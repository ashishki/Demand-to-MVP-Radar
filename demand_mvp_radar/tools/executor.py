"""Bounded tool execution with validation and audit."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from time import perf_counter

from pydantic import BaseModel

from demand_mvp_radar.observability import span
from demand_mvp_radar.tools.audit import ToolAuditEvent, record_tool_audit_event
from demand_mvp_radar.tools.schemas import TOOL_CATALOG, ToolDefinition

ToolImplementation = Callable[[BaseModel], BaseModel | dict[str, object]]


class ToolPermissionError(PermissionError):
    """Raised when a tool call lacks required permission."""


class ToolExecutor:
    def __init__(
        self,
        implementations: dict[str, ToolImplementation],
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self.implementations = implementations
        self.connection = connection

    def execute(
        self,
        tool_name: str,
        payload: dict[str, object],
        *,
        human_approved: bool = False,
    ) -> BaseModel:
        schema = TOOL_CATALOG[tool_name]
        tool_input = schema.input_model.model_validate(payload)
        self._check_permission(schema, human_approved=human_approved)
        implementation = self.implementations[tool_name]
        started_at = perf_counter()
        success = False
        output: BaseModel | None = None
        try:
            with span(f"tool.execute.{tool_name}"):
                raw_output = implementation(tool_input)
                output = schema.output_model.model_validate(raw_output)
                success = True
                return output
        finally:
            latency_ms = int((perf_counter() - started_at) * 1000)
            if self.connection is not None:
                self._record_audit(schema, tool_input, output, success, latency_ms)

    def _check_permission(self, schema: ToolDefinition, *, human_approved: bool) -> None:
        if schema.permission_level == "human_approved" and not human_approved:
            raise ToolPermissionError(f"{schema.name} requires human approval")

    def _record_audit(
        self,
        schema: ToolDefinition,
        tool_input: BaseModel,
        output: BaseModel | None,
        success: bool,
        latency_ms: int,
    ) -> None:
        input_values = tool_input.model_dump()
        output_values = output.model_dump() if output is not None else {}
        audit_fields = {
            field: input_values.get(field, output_values.get(field))
            for field in schema.audit_fields
            if field in input_values or field in output_values
        }
        run_id = str(input_values.get("run_id", "human-approved"))
        record_tool_audit_event(
            self.connection,
            ToolAuditEvent(
                run_id=run_id,
                tool_name=schema.name,
                version=schema.version,
                success=success,
                latency_ms=latency_ms,
                audit_fields=audit_fields,
            ),
        )
