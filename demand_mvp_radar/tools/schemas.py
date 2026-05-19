"""Versioned tool schema catalog."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    name: str
    version: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    side_effect_class: str
    idempotency_key_fields: tuple[str, ...]
    permission_level: str
    retry_policy: str
    audit_fields: tuple[str, ...]


class ReadTelegramEvidenceInput(BaseModel):
    run_id: str
    source_id: str
    path: str


class ReadTelegramEvidenceOutput(BaseModel):
    row_count: int = Field(ge=0)
    error_count: int = Field(ge=0)


class FetchUrlSnapshotInput(BaseModel):
    run_id: str
    url: str


class FetchUrlSnapshotOutput(BaseModel):
    status_code: int
    content_hash: str
    fetched_at: datetime
    normalized_text: str


class ReadSerpSnapshotInput(BaseModel):
    run_id: str
    query: str
    provider: str
    snapshot_id: str


class ReadSerpSnapshotOutput(BaseModel):
    result_count: int = Field(ge=0)


class ReadStoreMetadataInput(BaseModel):
    run_id: str
    store: str
    listing_id: str


class ReadStoreMetadataOutput(BaseModel):
    status: str


class RetrieveEvidenceInput(BaseModel):
    run_id: str
    corpus_version: str
    query_hash: str
    top_k: int = Field(gt=0)


class RetrieveEvidenceOutput(BaseModel):
    hit_count: int = Field(ge=0)


class WriteReportInput(BaseModel):
    run_id: str
    report_path: str
    content_hash: str


class WriteReportOutput(BaseModel):
    report_path: str
    content_hash: str


class RecordOperatorDecisionInput(BaseModel):
    opportunity_id: int
    decision: Literal["build", "reject", "revisit"]
    actor: str
    timestamp: datetime


class RecordOperatorDecisionOutput(BaseModel):
    decision_id: int


TOOL_CATALOG = {
    "read_telegram_evidence": ToolDefinition(
        name="read_telegram_evidence",
        version="1.0",
        input_model=ReadTelegramEvidenceInput,
        output_model=ReadTelegramEvidenceOutput,
        side_effect_class="read",
        idempotency_key_fields=("source_id", "path"),
        permission_level="local_operator",
        retry_policy="retry_local_read_once",
        audit_fields=("run_id", "source_id", "path", "row_count", "error_count"),
    ),
    "fetch_url_snapshot": ToolDefinition(
        name="fetch_url_snapshot",
        version="1.0",
        input_model=FetchUrlSnapshotInput,
        output_model=FetchUrlSnapshotOutput,
        side_effect_class="read_with_local_snapshot_write",
        idempotency_key_fields=("url",),
        permission_level="local_operator",
        retry_policy="bounded_retries_with_backoff",
        audit_fields=("run_id", "url", "status_code", "content_hash", "fetched_at"),
    ),
    "read_serp_snapshot": ToolDefinition(
        name="read_serp_snapshot",
        version="1.0",
        input_model=ReadSerpSnapshotInput,
        output_model=ReadSerpSnapshotOutput,
        side_effect_class="read",
        idempotency_key_fields=("query", "provider", "snapshot_id"),
        permission_level="local_operator",
        retry_policy="no_retry_for_saved_snapshots",
        audit_fields=("run_id", "query", "provider", "snapshot_id"),
    ),
    "read_store_metadata": ToolDefinition(
        name="read_store_metadata",
        version="1.0",
        input_model=ReadStoreMetadataInput,
        output_model=ReadStoreMetadataOutput,
        side_effect_class="read",
        idempotency_key_fields=("store", "listing_id"),
        permission_level="local_operator",
        retry_policy="bounded_retries_rate_limit_aware",
        audit_fields=("run_id", "store", "listing_id", "status"),
    ),
    "retrieve_evidence": ToolDefinition(
        name="retrieve_evidence",
        version="1.0",
        input_model=RetrieveEvidenceInput,
        output_model=RetrieveEvidenceOutput,
        side_effect_class="read",
        idempotency_key_fields=("corpus_version", "query_hash", "top_k"),
        permission_level="internal_pipeline",
        retry_policy="retry_transient_index_read_failure_only",
        audit_fields=("run_id", "corpus_version", "query_hash", "top_k", "hit_count"),
    ),
    "write_report": ToolDefinition(
        name="write_report",
        version="1.0",
        input_model=WriteReportInput,
        output_model=WriteReportOutput,
        side_effect_class="local_write",
        idempotency_key_fields=("run_id", "report_path"),
        permission_level="local_operator",
        retry_policy="atomic_temp_file_then_rename",
        audit_fields=("run_id", "report_path", "content_hash"),
    ),
    "record_operator_decision": ToolDefinition(
        name="record_operator_decision",
        version="1.0",
        input_model=RecordOperatorDecisionInput,
        output_model=RecordOperatorDecisionOutput,
        side_effect_class="local_write",
        idempotency_key_fields=("opportunity_id", "timestamp"),
        permission_level="human_approved",
        retry_policy="no_retry_after_validation_failure",
        audit_fields=("opportunity_id", "decision", "actor", "timestamp"),
    ),
}
