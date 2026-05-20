"""Local operator note importer."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.sources.base import QuarantinedSourceRow, SourceImportResult

REDACTED_NOTE_REFERENCE = "operator_note:redacted"


class OperatorNotesAdapter:
    source_type = "operator_note"

    def import_file(
        self,
        path: Path,
        *,
        run_id: str,
        quarantine_path: Path | None = None,
    ) -> SourceImportResult:
        try:
            record = self._normalize_markdown(path, run_id=run_id)
        except (KeyError, ValueError) as error:
            quarantined = (
                QuarantinedSourceRow(
                    source_reference=REDACTED_NOTE_REFERENCE,
                    error_reason=str(error),
                ),
            )
            if quarantine_path is not None:
                self._write_quarantine(quarantine_path, quarantined)
            return SourceImportResult(evidence=(), quarantined=quarantined)

        return SourceImportResult(evidence=(record,))

    def _normalize_markdown(self, path: Path, *, run_id: str) -> EvidenceRecord:
        metadata, body = _split_frontmatter(path.read_text(encoding="utf-8"))
        captured_at = datetime.fromisoformat(_required_metadata(metadata, "captured_at"))
        normalized_text = _normalize_text(body)
        if not normalized_text:
            raise ValueError("note body is required")

        title = metadata.get("title") or _title_from_text(normalized_text)
        content_hash = _content_hash(
            self.source_type,
            captured_at.isoformat(),
            normalized_text,
        )
        source_id = metadata.get("source_id") or f"note-{content_hash[:12]}"

        return EvidenceRecord(
            run_id=run_id,
            source_type=self.source_type,
            source_id=source_id,
            source_url=REDACTED_NOTE_REFERENCE,
            captured_at=captured_at,
            title=title,
            snippet=normalized_text[:160],
            normalized_text=normalized_text,
            content_hash=content_hash,
            source_fingerprint=f"{self.source_type}:{source_id}:{content_hash}",
        )

    def _write_quarantine(
        self,
        quarantine_path: Path,
        quarantined: tuple[QuarantinedSourceRow, ...],
    ) -> None:
        quarantine_path.parent.mkdir(parents=True, exist_ok=True)
        with quarantine_path.open("a", encoding="utf-8") as file:
            for row in quarantined:
                file.write(row.model_dump_json())
                file.write("\n")


def _split_frontmatter(content: str) -> tuple[dict[str, str], str]:
    if not content.startswith("---\n"):
        raise ValueError("frontmatter is required")
    try:
        _opening, raw_metadata, body = content.split("---", 2)
    except ValueError as error:
        raise ValueError("frontmatter closing marker is required") from error
    metadata = _parse_frontmatter(raw_metadata)
    return metadata, body


def _parse_frontmatter(raw_metadata: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in raw_metadata.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        key, separator, value = stripped.partition(":")
        if not separator:
            raise ValueError(f"invalid frontmatter line: {key}")
        metadata[key.strip()] = value.strip().strip('"')
    return metadata


def _required_metadata(metadata: dict[str, str], field: str) -> str:
    value = metadata[field]
    if not value:
        raise ValueError(f"{field} is required")
    return value


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
