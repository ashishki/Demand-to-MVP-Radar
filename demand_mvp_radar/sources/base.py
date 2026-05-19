"""Source adapter contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict

from demand_mvp_radar.models import EvidenceRecord


class QuarantinedSourceRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_reference: str
    error_reason: str


class SourceImportResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    evidence: tuple[EvidenceRecord, ...]
    quarantined: tuple[QuarantinedSourceRow, ...] = ()


class SourceAdapter(Protocol):
    def import_file(self, path: Path, *, run_id: str, quarantine_path: Path) -> SourceImportResult:
        """Import local source data into normalized evidence records."""
