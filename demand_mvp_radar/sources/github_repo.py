"""Local GitHub repository snapshot importer."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.sources.base import QuarantinedSourceRow, SourceImportResult
from demand_mvp_radar.tools.schemas import (
    ReadGithubRepoSnapshotInput,
    ReadGithubRepoSnapshotOutput,
)

EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", "reports", "data"}
EXCLUDED_SUFFIXES = {".sqlite", ".sqlite3", ".db", ".env", ".pem", ".key"}


class GitHubRepoSnapshotImporter:
    source_type = "github_repo"

    def import_repository(
        self,
        repository_path: Path,
        *,
        run_id: str,
        repository_identifier: str,
    ) -> SourceImportResult:
        repo_hash = repository_identifier_hash(repository_identifier)
        evidence: list[EvidenceRecord] = []
        quarantined: list[QuarantinedSourceRow] = []

        for item in self._selected_items(repository_path):
            try:
                evidence.append(
                    self._evidence_from_item(
                        item,
                        run_id=run_id,
                        repository_path=repository_path,
                        repository_id_hash=repo_hash,
                    )
                )
            except (OSError, ValueError, json.JSONDecodeError) as error:
                quarantined.append(
                    QuarantinedSourceRow(
                        source_reference=f"github_repo:{repo_hash}",
                        error_reason=str(error),
                    )
                )

        return SourceImportResult(evidence=tuple(evidence), quarantined=tuple(quarantined))

    def _selected_items(self, repository_path: Path) -> tuple[Path, ...]:
        issue_dir = repository_path / "issues"
        issue_files = tuple(issue_dir.glob("*.json")) if issue_dir.exists() else ()
        candidates = (
            repository_path / "README.md",
            repository_path / "TODO.md",
            *issue_files,
            repository_path / "recent_changes.json",
        )
        return tuple(path for path in candidates if path.exists() and _is_allowed_path(path))

    def _evidence_from_item(
        self,
        path: Path,
        *,
        run_id: str,
        repository_path: Path,
        repository_id_hash: str,
    ) -> EvidenceRecord:
        relative_path = path.relative_to(repository_path)
        kind, title, normalized_text, captured_at = _parse_selected_file(path)
        content_hash = _content_hash(
            self.source_type,
            repository_id_hash,
            str(relative_path),
            normalized_text,
        )
        source_id = f"{repository_id_hash}:{kind}:{content_hash[:12]}"
        source_reference = f"github_repo:{repository_id_hash}:{kind}"

        return EvidenceRecord(
            run_id=run_id,
            source_type=self.source_type,
            source_id=source_id,
            source_url=source_reference,
            captured_at=captured_at,
            title=title,
            snippet=normalized_text[:160],
            normalized_text=normalized_text,
            content_hash=content_hash,
            source_fingerprint=f"{self.source_type}:{source_id}:{content_hash}",
        )


def read_github_repo_snapshot(
    tool_input: ReadGithubRepoSnapshotInput,
) -> ReadGithubRepoSnapshotOutput:
    result = GitHubRepoSnapshotImporter().import_repository(
        Path(tool_input.repository_path),
        run_id=tool_input.run_id,
        repository_identifier=tool_input.repository_identifier,
    )
    return ReadGithubRepoSnapshotOutput(
        repository_id_hash=repository_identifier_hash(tool_input.repository_identifier),
        source_count=len(result.evidence),
        error_count=len(result.quarantined),
    )


def repository_identifier_hash(repository_identifier: str) -> str:
    return hashlib.sha256(repository_identifier.encode("utf-8")).hexdigest()


def _parse_selected_file(path: Path) -> tuple[str, str, str, datetime]:
    if path.name == "README.md":
        raw_text = path.read_text(encoding="utf-8")
        text = _normalize_text(raw_text)
        return "readme", _title_from_markdown(raw_text), text, _default_captured_at()
    if path.name == "TODO.md":
        text = _normalize_text(path.read_text(encoding="utf-8"))
        return "todo", "Repository TODOs", text, _default_captured_at()
    if path.name == "recent_changes.json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        text = _normalize_text(" ".join(item["summary"] for item in payload["changes"]))
        captured_at = datetime.fromisoformat(payload["captured_at"])
        return "recent_changes", "Recent repository changes", text, captured_at

    payload = json.loads(path.read_text(encoding="utf-8"))
    text = _normalize_text(f"{payload['title']} {payload['body']}")
    captured_at = datetime.fromisoformat(payload["captured_at"])
    return "issue", payload["title"], text, captured_at


def _is_allowed_path(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDED_DIRS:
        return False
    if path.name.startswith(".env"):
        return False
    return not any(str(path).endswith(suffix) for suffix in EXCLUDED_SUFFIXES)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _title_from_markdown(text: str) -> str:
    first_line = text.strip().splitlines()[0].strip()
    if first_line.startswith("# "):
        return first_line.removeprefix("# ").strip()[:80]
    return _normalize_text(text)[:80]


def _default_captured_at() -> datetime:
    return datetime(2026, 5, 20, tzinfo=UTC)


def _content_hash(*parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()
