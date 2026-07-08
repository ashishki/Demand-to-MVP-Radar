"""Bridge for sanitized telegram-research-agent exports."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.sources.base import QuarantinedSourceRow, SourceImportResult
from demand_mvp_radar.storage.repositories import EvidenceRepository


class TelegramResearchAgentBridge:
    source_type = "telegram_research_agent"
    metadata_fields = (
        "anti_complexity_note",
        "bucket",
        "channel_username",
        "demand_signal_type",
        "demand_surfaces",
        "evidence_strength",
        "knowledge_atom_types",
        "knowledge_thread_slug",
        "knowledge_thread_status",
        "knowledge_thread_title",
        "manual_tags",
        "mvp_shape",
        "pain_statement",
        "post_id",
        "project_names",
        "signal_score",
        "source_atom_ids",
        "source_kind",
        "source_urls",
        "target_user",
        "verification_needed",
    )

    def import_file(
        self,
        path: Path,
        *,
        run_id: str,
        repository: EvidenceRepository,
        quarantine_path: Path,
    ) -> SourceImportResult:
        rows = json.loads(path.read_text())
        evidence: list[EvidenceRecord] = []
        quarantined: list[QuarantinedSourceRow] = []

        for index, row in enumerate(rows):
            try:
                record = self._normalize_row(row, run_id=run_id)
                repository.write(record)
                evidence.append(record)
            except (KeyError, TypeError, ValueError) as error:
                quarantined.append(
                    QuarantinedSourceRow(
                        source_reference=_source_reference(row, index),
                        error_reason=str(error),
                    )
                )

        if quarantined:
            self._write_quarantine(quarantine_path, quarantined)

        return SourceImportResult(evidence=tuple(evidence), quarantined=tuple(quarantined))

    def _normalize_row(self, row: dict[str, Any], *, run_id: str) -> EvidenceRecord:
        if not isinstance(row, dict):
            raise TypeError("row must be an object")
        if row.get("private") is True or row.get("privacy") == "private":
            raise ValueError("private row is not importable")

        upstream_id = _required_text(row, "upstream_id")
        captured_at = datetime.fromisoformat(_required_text(row, "captured_at"))
        normalized_text = _normalize_text(_required_text(row, "text"))
        title = _optional_text(row, "title") or _title_from_text(normalized_text)
        snippet = _optional_text(row, "snippet") or normalized_text[:160]
        source_url = _optional_text(row, "source_url")
        content_hash = _content_hash(
            self.source_type,
            upstream_id,
            captured_at.isoformat(),
            normalized_text,
        )

        return EvidenceRecord(
            run_id=run_id,
            source_type=self.source_type,
            source_id=upstream_id,
            source_url=source_url,
            captured_at=captured_at,
            title=title,
            snippet=snippet,
            normalized_text=normalized_text,
            content_hash=content_hash,
            source_fingerprint=f"{self.source_type}:{upstream_id}:{content_hash}",
            provider_metadata=_provider_metadata(row, self.metadata_fields),
        )

    def _write_quarantine(
        self,
        quarantine_path: Path,
        quarantined: list[QuarantinedSourceRow],
    ) -> None:
        quarantine_path.parent.mkdir(parents=True, exist_ok=True)
        with quarantine_path.open("a", encoding="utf-8") as file:
            for row in quarantined:
                file.write(row.model_dump_json())
                file.write("\n")


def _required_text(row: dict[str, Any], field: str) -> str:
    value = row[field]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


def _optional_text(row: dict[str, Any], field: str) -> str | None:
    value = row.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be text")
    stripped = value.strip()
    return stripped or None


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _title_from_text(text: str) -> str:
    return text[:80]


def _content_hash(*parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _provider_metadata(row: dict[str, Any], fields: tuple[str, ...]) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for field in fields:
        if field not in row or row[field] is None:
            continue
        value = row[field]
        if isinstance(value, str):
            serialized = value.strip()
        elif isinstance(value, (bool, int, float)):
            serialized = str(value)
        elif isinstance(value, (list, tuple, dict)):
            serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
        else:
            raise ValueError(f"{field} must be metadata-serializable")
        if serialized:
            metadata[field] = serialized
    return metadata


def _source_reference(row: object, index: int) -> str:
    if not isinstance(row, dict):
        return f"row-{index}"
    for field in ("upstream_id", "source_id", "id"):
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"row-{index}"
