"""Telegram export source adapter."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.sources.base import QuarantinedSourceRow, SourceImportResult


class TelegramExportAdapter:
    source_type = "telegram"

    def import_file(self, path: Path, *, run_id: str, quarantine_path: Path) -> SourceImportResult:
        rows = json.loads(path.read_text())
        evidence: list[EvidenceRecord] = []
        quarantined: list[QuarantinedSourceRow] = []

        for index, row in enumerate(rows):
            try:
                evidence.append(self._normalize_row(row, run_id=run_id))
            except (KeyError, TypeError, ValueError) as error:
                quarantined_row = QuarantinedSourceRow(
                    source_reference=str(row.get("id", f"row-{index}"))
                    if isinstance(row, dict)
                    else f"row-{index}",
                    error_reason=str(error),
                )
                quarantined.append(quarantined_row)

        if quarantined:
            self._write_quarantine(quarantine_path, quarantined)

        return SourceImportResult(evidence=tuple(evidence), quarantined=tuple(quarantined))

    def _normalize_row(self, row: dict[str, Any], *, run_id: str) -> EvidenceRecord:
        source_id = _required_text(row, "id")
        captured_at = datetime.fromisoformat(_required_text(row, "captured_at"))
        normalized_text = _normalize_text(_required_text(row, "text"))
        title = _title_from_text(normalized_text)
        snippet = normalized_text[:160]
        content_hash = _content_hash(
            self.source_type,
            source_id,
            captured_at.isoformat(),
            normalized_text,
        )
        return EvidenceRecord(
            run_id=run_id,
            source_type=self.source_type,
            source_id=source_id,
            source_url=row.get("url"),
            captured_at=captured_at,
            title=title,
            snippet=snippet,
            normalized_text=normalized_text,
            content_hash=content_hash,
            source_fingerprint=f"{self.source_type}:{source_id}:{content_hash}",
        )

    def _write_quarantine(
        self,
        quarantine_path: Path,
        quarantined: list[QuarantinedSourceRow],
    ) -> None:
        quarantine_path.parent.mkdir(parents=True, exist_ok=True)
        with quarantine_path.open("a") as file:
            for row in quarantined:
                file.write(row.model_dump_json())
                file.write("\n")


def _required_text(row: dict[str, Any], field: str) -> str:
    value = row[field]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


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
