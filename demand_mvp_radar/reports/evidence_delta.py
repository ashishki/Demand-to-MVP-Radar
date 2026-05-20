"""Evidence delta reports for source import review."""

from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, ConfigDict

from demand_mvp_radar.observability import span

SOURCE_NAME_TO_TYPE = {
    "operator_notes": "operator_note",
    "telegram_research_agent": "telegram_research_agent",
    "github_repo": "github_repo",
    "serp": "serp",
}
TOKEN_RE = re.compile(r"[a-z0-9]+")
PRIVATE_REF_RE = re.compile(r"(^/|[A-Za-z]:\\|token=|key=|secret=|private)", re.IGNORECASE)


class EvidenceDeltaCounts(BaseModel):
    model_config = ConfigDict(frozen=True)

    new_count: int = 0
    duplicate_count: int = 0
    stale_count: int = 0
    quarantined_count: int = 0
    skipped_count: int = 0


class EvidenceDeltaCluster(BaseModel):
    model_config = ConfigDict(frozen=True)

    cluster_label: str
    source_types: tuple[str, ...]
    source_refs: tuple[str, ...]
    change_types: tuple[str, ...]


class EvidenceDeltaReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    previous_run_id: str | None
    source_type_counts: dict[str, EvidenceDeltaCounts]
    changed_clusters: tuple[EvidenceDeltaCluster, ...]
    redaction_warnings: tuple[str, ...] = ()


def generate_evidence_delta_report(
    connection: sqlite3.Connection,
    *,
    run_id: str,
    previous_run_id: str | None = None,
    as_of: datetime | None = None,
    stale_after_days: int = 30,
) -> EvidenceDeltaReport:
    report_as_of = as_of or datetime.now(UTC)
    with span("reports.generate_evidence_delta"):
        current_run = _load_run(connection, run_id)
        effective_previous_run_id = previous_run_id or _find_previous_run_id(
            connection,
            run_id=run_id,
        )
        current_rows = _load_evidence(connection, run_id)
        previous_rows = (
            _load_evidence(connection, effective_previous_run_id)
            if effective_previous_run_id
            else ()
        )

    previous_hashes = {row["content_hash"] for row in previous_rows}
    previous_hash_by_source_id = {row["source_id"]: row["content_hash"] for row in previous_rows}
    count_accumulator: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "new_count": 0,
            "duplicate_count": 0,
            "stale_count": 0,
            "quarantined_count": 0,
            "skipped_count": 0,
        }
    )
    changed_rows: list[tuple[sqlite3.Row, str]] = []
    stale_cutoff = _to_utc(report_as_of) - timedelta(days=stale_after_days)

    for row in current_rows:
        source_type = str(row["source_type"])
        if row["content_hash"] in previous_hashes:
            count_accumulator[source_type]["duplicate_count"] += 1
        else:
            count_accumulator[source_type]["new_count"] += 1
            change_type = (
                "changed"
                if previous_hash_by_source_id.get(row["source_id"]) is not None
                else "new"
            )
            changed_rows.append((row, change_type))
        if _to_utc(datetime.fromisoformat(str(row["captured_at"]))) < stale_cutoff:
            count_accumulator[source_type]["stale_count"] += 1

    _apply_manifest_counts(current_run, count_accumulator)
    return EvidenceDeltaReport(
        run_id=run_id,
        previous_run_id=effective_previous_run_id,
        source_type_counts={
            source_type: EvidenceDeltaCounts(**counts)
            for source_type, counts in sorted(count_accumulator.items())
        },
        changed_clusters=_cluster_changed_rows(changed_rows),
        redaction_warnings=_redaction_warnings(changed_rows),
    )


def _load_run(connection: sqlite3.Connection, run_id: str) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT run_id, source_counts, error_counts
        FROM runs
        WHERE run_id = :run_id
        """,
        {"run_id": run_id},
    ).fetchone()
    if row is None:
        raise ValueError(f"run not found: {run_id}")
    return row


def _find_previous_run_id(connection: sqlite3.Connection, *, run_id: str) -> str | None:
    row = connection.execute(
        """
        SELECT run_id
        FROM runs
        WHERE run_id != :run_id
        ORDER BY COALESCE(ended_at, started_at) DESC
        LIMIT 1
        """,
        {"run_id": run_id},
    ).fetchone()
    return None if row is None else str(row["run_id"])


def _load_evidence(connection: sqlite3.Connection, run_id: str) -> tuple[sqlite3.Row, ...]:
    rows = connection.execute(
        """
        SELECT
            source_type,
            source_id,
            source_url,
            captured_at,
            title,
            content_hash
        FROM evidence
        WHERE run_id = :run_id
        ORDER BY id ASC
        """,
        {"run_id": run_id},
    ).fetchall()
    return tuple(rows)


def _apply_manifest_counts(
    run: sqlite3.Row,
    count_accumulator: dict[str, dict[str, int]],
) -> None:
    source_counts = json.loads(run["source_counts"])
    error_counts = json.loads(run["error_counts"])
    for source_name, count in error_counts.items():
        source_type = SOURCE_NAME_TO_TYPE.get(source_name, source_name)
        count_accumulator[source_type]["quarantined_count"] += int(count)
    for source_name in source_counts.get("skipped_sources", []):
        source_type = SOURCE_NAME_TO_TYPE.get(source_name, source_name)
        count_accumulator[source_type]["skipped_count"] += 1


def _cluster_changed_rows(
    changed_rows: list[tuple[sqlite3.Row, str]],
) -> tuple[EvidenceDeltaCluster, ...]:
    grouped: dict[str, list[tuple[sqlite3.Row, str]]] = defaultdict(list)
    for row, change_type in changed_rows:
        grouped[_cluster_label(str(row["title"]))].append((row, change_type))

    clusters = []
    for label, rows in sorted(grouped.items()):
        source_types = sorted({str(row["source_type"]) for row, _ in rows})
        source_refs = sorted({_redacted_source_ref(row) for row, _ in rows})
        change_types = sorted({change_type for _, change_type in rows})
        clusters.append(
            EvidenceDeltaCluster(
                cluster_label=label,
                source_types=tuple(source_types),
                source_refs=tuple(source_refs),
                change_types=tuple(change_types),
            )
        )
    return tuple(clusters)


def _cluster_label(title: str) -> str:
    tokens = TOKEN_RE.findall(title.lower())
    if not tokens:
        return "untitled evidence"
    return " ".join(tokens[:4])


def _redacted_source_ref(row: sqlite3.Row) -> str:
    source_type = str(row["source_type"])
    source_url = row["source_url"]
    if source_url is None or PRIVATE_REF_RE.search(str(source_url)):
        return f"{source_type}:redacted"
    return str(source_url)


def _redaction_warnings(
    changed_rows: list[tuple[sqlite3.Row, str]],
) -> tuple[str, ...]:
    redacted_types = {
        str(row["source_type"])
        for row, _ in changed_rows
        if row["source_url"] is None or PRIVATE_REF_RE.search(str(row["source_url"]))
    }
    return tuple(
        f"redacted private source reference for {source_type}"
        for source_type in sorted(redacted_types)
    )


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
