"""Entropy Core-compatible proof receipts for weekly reports."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from demand_mvp_radar.briefs import OpportunityBrief

PROOF_RECEIPT_SCHEMA_VERSION = "entropy_core.product_receipt.v1"
PRODUCT_ID = "demand-to-mvp-radar"
SHA256_HEX_LENGTH = 64


class ProofEvidenceRef(BaseModel):
    model_config = ConfigDict(frozen=True)

    evidence_id: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    supports: str = Field(min_length=1)
    captured_at: datetime | None = None
    checksum_sha256: str | None = Field(
        default=None, min_length=SHA256_HEX_LENGTH, max_length=SHA256_HEX_LENGTH
    )

    @field_validator("checksum_sha256")
    @classmethod
    def checksum_must_be_sha256(cls, value: str | None) -> str | None:
        if value is not None and any(char not in "0123456789abcdef" for char in value):
            raise ValueError("checksum_sha256 must be lowercase hexadecimal")
        return value


class WeeklyReportProofReceipt(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["weekly_report_receipt"] = "weekly_report_receipt"
    schema_version: Literal["entropy_core.product_receipt.v1"] = PROOF_RECEIPT_SCHEMA_VERSION
    product_id: Literal["demand-to-mvp-radar"] = PRODUCT_ID
    artifact_ref: str = Field(min_length=1)
    artifact_sha256: str = Field(min_length=SHA256_HEX_LENGTH, max_length=SHA256_HEX_LENGTH)
    generated_at: datetime
    evidence_refs: tuple[ProofEvidenceRef, ...] = Field(min_length=1)
    verifier_status: Literal["passed", "needs_review", "failed"]
    verifier_notes: tuple[str, ...] = ()
    entropy_core_level: Literal["receipt_compatible", "evidence_lookup_compatible"] = (
        "evidence_lookup_compatible"
    )

    @field_validator("artifact_sha256")
    @classmethod
    def artifact_hash_must_be_sha256(cls, value: str) -> str:
        if any(char not in "0123456789abcdef" for char in value):
            raise ValueError("artifact_sha256 must be lowercase hexadecimal")
        return value

    @model_validator(mode="after")
    def failed_or_review_status_requires_notes(self) -> WeeklyReportProofReceipt:
        if self.verifier_status != "passed" and not self.verifier_notes:
            raise ValueError("non-passed proof receipts require verifier_notes")
        return self

    def canonical_json(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    def receipt_sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def build_weekly_report_proof_receipt(
    *,
    report_markdown: str,
    report_path: Path | str,
    briefs: Sequence[OpportunityBrief],
    generated_at: datetime | None = None,
) -> WeeklyReportProofReceipt:
    evidence_refs = _collect_evidence_refs(briefs)
    verifier_status: Literal["passed", "needs_review", "failed"] = (
        "passed" if evidence_refs else "failed"
    )
    notes = () if evidence_refs else ("weekly report has no cited evidence packets",)
    return WeeklyReportProofReceipt(
        artifact_ref=str(report_path),
        artifact_sha256=hashlib.sha256(report_markdown.encode("utf-8")).hexdigest(),
        generated_at=generated_at or datetime.now(UTC),
        evidence_refs=evidence_refs,
        verifier_status=verifier_status,
        verifier_notes=notes,
    )


def _collect_evidence_refs(briefs: Sequence[OpportunityBrief]) -> tuple[ProofEvidenceRef, ...]:
    refs: list[ProofEvidenceRef] = []
    seen: set[str] = set()
    for brief in briefs:
        for packet in brief.evidence_packets:
            evidence_key = f"evidence:{packet.evidence_id}"
            if evidence_key in seen:
                continue
            seen.add(evidence_key)
            refs.append(
                ProofEvidenceRef(
                    evidence_id=evidence_key,
                    source_url=packet.source_url,
                    supports=brief.candidate.opportunity_id,
                    captured_at=packet.captured_at,
                    checksum_sha256=hashlib.sha256(packet.snippet.encode("utf-8")).hexdigest(),
                )
            )
    return tuple(refs)
