"""Weekly MVP selection from telegram-research-agent opportunity seeds."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from demand_mvp_radar.config import Settings
from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.reports.markdown import write_markdown_report
from demand_mvp_radar.retrieval.ingestion import build_corpus
from demand_mvp_radar.sources.telegram_research_agent import TelegramResearchAgentBridge
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.storage.repositories import EvidenceRepository

SURFACE_WEIGHTS = {
    "manual_workaround": 24,
    "search_intent": 22,
    "competitor_traction": 20,
    "repeated_questions": 18,
    "creator_content_gap": 18,
    "workflow_automation": 17,
    "store_category_demand": 16,
    "platform_timing_event": 14,
    "education_rollout": 12,
}
BUCKET_WEIGHTS = {
    "strong": 18,
    "watch": 12,
    "cultural": 4,
    "noise": 0,
}
RISK_TERMS = (
    "copyright",
    "private data",
    "terms",
    "tos",
    "scraping",
    "investment",
    "trading",
)
EXISTING_PROJECT_TITLES = {
    "ai rollout training os",
    "workflow-to-agent studio",
    "lead response sla monitor",
    "document-to-structured-data validator",
    "manual workflow automation probe",
}
GENERIC_CANDIDATE_TITLES = {
    "creator content discovery gap report",
}


class MvpOfWeekResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    status: str
    database_path: Path
    report_path: Path
    json_path: Path
    corpus_version: str
    evidence_count: int
    duplicate_count: int
    quarantined_count: int
    retrieval_chunk_count: int
    selected_title: str | None = None
    recommendation: str | None = None
    score: int | None = None


@dataclass
class CandidateAggregate:
    key: str
    title: str
    evidence: list[EvidenceRecord] = field(default_factory=list)
    surfaces: set[str] = field(default_factory=set)
    channels: set[str] = field(default_factory=set)
    missing_evidence: set[str] = field(default_factory=set)
    risk_flags: set[str] = field(default_factory=set)
    mvp_scopes: list[str] = field(default_factory=list)
    anti_complexity_notes: list[str] = field(default_factory=list)
    score: int = 0
    recommendation: str = "needs_more_evidence"


def run_mvp_of_week(
    *,
    telegram_export: Path,
    settings: Settings,
    run_id: str | None = None,
    top_evidence: int = 5,
) -> MvpOfWeekResult:
    effective_run_id = run_id or f"mvp-weekly-{datetime.now(UTC).strftime('%Y-W%V')}"
    corpus_version = f"{effective_run_id}-corpus"
    database_path = settings.data_dir / "radar.sqlite3"
    report_path = settings.report_dir / "mvp_of_week" / f"{effective_run_id}.md"
    json_path = settings.report_dir / "mvp_of_week" / f"{effective_run_id}.json"

    connection = connect_database(database_path)
    create_schema(connection)
    repository = EvidenceRepository(connection)

    before_count = _evidence_count(connection)
    import_result = TelegramResearchAgentBridge().import_file(
        telegram_export,
        run_id=effective_run_id,
        repository=repository,
        quarantine_path=settings.data_dir / "quarantine" / f"{effective_run_id}.jsonl",
    )
    after_count = _evidence_count(connection)
    duplicate_count = max(len(import_result.evidence) - max(after_count - before_count, 0), 0)

    evidence_rows = _stored_evidence_rows(connection, import_result.evidence)
    retrieval_chunk_count = 0
    if evidence_rows:
        connection.execute(
            "DELETE FROM retrieval_chunks WHERE corpus_version = :corpus_version",
            {"corpus_version": corpus_version},
        )
        connection.commit()
        corpus_metadata = build_corpus(
            connection,
            evidence_rows,
            corpus_version=corpus_version,
        )
        retrieval_chunk_count = int(corpus_metadata["chunk_count"])

    candidates = _rank_candidates(import_result.evidence)
    selected = candidates[0] if candidates else None
    markdown = _render_report(
        run_id=effective_run_id,
        selected=selected,
        candidates=candidates[:5],
        evidence_count=len(import_result.evidence),
        quarantined_count=len(import_result.quarantined),
        top_evidence=top_evidence,
    )
    write_markdown_report(report_path, markdown)

    result = MvpOfWeekResult(
        run_id=effective_run_id,
        status="selected" if selected is not None else "no_evidence",
        database_path=database_path,
        report_path=report_path,
        json_path=json_path,
        corpus_version=corpus_version,
        evidence_count=len(import_result.evidence),
        duplicate_count=duplicate_count,
        quarantined_count=len(import_result.quarantined),
        retrieval_chunk_count=retrieval_chunk_count,
        selected_title=selected.title if selected is not None else None,
        recommendation=selected.recommendation if selected is not None else None,
        score=selected.score if selected is not None else None,
    )
    _write_json(json_path, selected=selected, candidates=candidates[:5], result=result)
    _record_mvp_run(
        connection,
        run_id=effective_run_id,
        corpus_version=corpus_version,
        evidence_count=len(import_result.evidence),
        duplicate_count=duplicate_count,
        quarantined_count=len(import_result.quarantined),
        selected_title=result.selected_title,
        score=result.score,
    )
    return result


def _rank_candidates(records: tuple[EvidenceRecord, ...]) -> list[CandidateAggregate]:
    grouped: dict[str, CandidateAggregate] = {}
    for record in records:
        metadata = record.provider_metadata
        title = _metadata_text(metadata, "mvp_shape") or record.title
        key = _normalize_key(title)
        candidate = grouped.setdefault(key, CandidateAggregate(key=key, title=title))
        candidate.evidence.append(record)
        candidate.surfaces.update(_metadata_list(metadata, "demand_surfaces"))
        if not candidate.surfaces:
            surface = _metadata_text(metadata, "demand_signal_type")
            if surface:
                candidate.surfaces.add(surface)
        channel = _metadata_text(metadata, "channel_username")
        if channel:
            candidate.channels.add(channel)
        for value in _metadata_list(metadata, "verification_needed"):
            candidate.missing_evidence.add(value)
        mvp_scope = _metadata_text(metadata, "mvp_shape")
        if mvp_scope:
            candidate.mvp_scopes.append(mvp_scope)
        anti_complexity_note = _metadata_text(metadata, "anti_complexity_note")
        if anti_complexity_note:
            candidate.anti_complexity_notes.append(anti_complexity_note)
        text = f"{record.title} {record.snippet} {record.normalized_text}".lower()
        for term in RISK_TERMS:
            if term in text:
                candidate.risk_flags.add(term)

    for candidate in grouped.values():
        candidate.score = _score_candidate(candidate)
        if candidate.score >= 70 and not _has_blocking_gap(candidate):
            candidate.recommendation = "focused_experiment"
        elif candidate.score >= 50:
            candidate.recommendation = "revisit_with_evidence_gap"
        else:
            candidate.recommendation = "needs_more_evidence"
        if _is_existing_project(candidate.title):
            candidate.score = max(candidate.score - 35, 0)
            candidate.recommendation = "existing_project_context"
        if _is_generic_candidate(candidate.title):
            candidate.score = max(candidate.score - 25, 0)
            if candidate.recommendation == "focused_experiment":
                candidate.recommendation = "needs_more_specific_scope"

    return sorted(grouped.values(), key=lambda item: item.score, reverse=True)


def _score_candidate(candidate: CandidateAggregate) -> int:
    score = 18
    score += min(len(candidate.evidence) * 8, 24)
    score += min(len(candidate.channels) * 4, 12)
    score += min(sum(SURFACE_WEIGHTS.get(surface, 6) for surface in candidate.surfaces), 28)
    score += min(_bucket_bonus(candidate.evidence), 18)
    if candidate.mvp_scopes:
        score += 8
    if any(record.source_url for record in candidate.evidence):
        score += 6
    score -= min(len(candidate.risk_flags) * 8, 24)
    if _has_blocking_gap(candidate):
        score -= 12
    return max(min(score, 100), 0)


def _bucket_bonus(records: list[EvidenceRecord]) -> int:
    total = 0
    for record in records:
        bucket = _metadata_text(record.provider_metadata, "bucket") or ""
        total += BUCKET_WEIGHTS.get(bucket, 0)
        tags = set(_metadata_list(record.provider_metadata, "manual_tags"))
        if tags & {"strong", "try_in_project"}:
            total += 10
        elif tags & {"interesting", "read_later"}:
            total += 5
    return total


def _has_blocking_gap(candidate: CandidateAggregate) -> bool:
    joined = " ".join(candidate.risk_flags).lower()
    return "copyright" in joined or "private data" in joined or "terms" in joined


def _is_existing_project(title: str) -> bool:
    return title.strip().lower() in EXISTING_PROJECT_TITLES


def _is_generic_candidate(title: str) -> bool:
    normalized = title.strip().lower()
    return normalized in GENERIC_CANDIDATE_TITLES or normalized.startswith("opportunity probe:")


def _render_report(
    *,
    run_id: str,
    selected: CandidateAggregate | None,
    candidates: list[CandidateAggregate],
    evidence_count: int,
    quarantined_count: int,
    top_evidence: int,
) -> str:
    generated_at = datetime.now(UTC).isoformat()
    if selected is None:
        return "\n".join(
            [
                "# MVP of the Week",
                "",
                f"Generated: {generated_at}",
                f"Run ID: {run_id}",
                "",
                "No usable opportunity seeds were available this week.",
                f"Imported evidence: {evidence_count}; quarantined rows: {quarantined_count}.",
            ]
        ) + "\n"

    lines = [
        f"# MVP of the Week: {selected.title}",
        "",
        f"Generated: {generated_at}",
        f"Run ID: {run_id}",
        f"Recommendation: **{selected.recommendation}**",
        f"Score: {selected.score}/100",
        f"Imported evidence: {evidence_count}; quarantined rows: {quarantined_count}.",
        "",
        "## Why This Week",
        "",
        _why_this_week(selected),
        "",
        "## One-Function MVP",
        "",
        _first_or_default(
            selected.mvp_scopes,
            f"Build the smallest artifact that proves demand for {selected.title}.",
        ),
        "",
        "## This Week's Experiment",
        "",
        "1. Pick 3-5 public examples that match the evidence pattern.",
        "2. Produce one static artifact or concierge workflow, not a platform.",
        "3. Show before/after value in a copyable report.",
        "4. Ask 5 relevant operators or creators whether they would use or pay for it.",
        "5. End with build/revisit/reject and write the decision back to memory.",
        "",
        "## Evidence",
        "",
    ]
    for index, record in enumerate(selected.evidence[:top_evidence], start=1):
        lines.append(_render_evidence_line(index, record))

    lines.extend(
        [
            "",
            "## Missing Evidence",
            "",
            *_prefixed_lines(
                sorted(selected.missing_evidence)
                or ["pricing or willingness-to-pay signal", "competitor comparison"],
            ),
            "",
            "## Risk Flags",
            "",
            *_prefixed_lines(
                sorted(selected.risk_flags) or ["No explicit risk flags in the seeds."]
            ),
            "",
            "## Anti-Complexity Guardrail",
            "",
            _first_or_default(
                selected.anti_complexity_notes,
                "Do not build a platform. Build one proof artifact and one operator-facing report.",
            ),
            "",
            "## Other Candidates",
            "",
        ]
    )
    for candidate in candidates[1:]:
        lines.append(
            f"- {candidate.title}: {candidate.score}/100, {candidate.recommendation}, "
            f"{len(candidate.evidence)} evidence item(s)"
        )
    if len(candidates) <= 1:
        lines.append("- No other ranked candidates this week.")
    return "\n".join(lines).rstrip() + "\n"


def _why_this_week(candidate: CandidateAggregate) -> str:
    surfaces = ", ".join(sorted(candidate.surfaces)) or "unclassified demand"
    channels = ", ".join(sorted(candidate.channels)) or "Telegram sources"
    return (
        f"The strongest cluster combines {len(candidate.evidence)} evidence item(s) "
        f"from {channels}. Demand surfaces: {surfaces}. The scope is small enough "
        "to validate through a one-week public-data experiment."
    )


def _render_evidence_line(index: int, record: EvidenceRecord) -> str:
    channel = _metadata_text(record.provider_metadata, "channel_username") or record.source_id
    url = f" - {record.source_url}" if record.source_url else ""
    snippet = record.snippet.strip() or record.normalized_text[:180]
    return f"[{index}] {channel} | {record.captured_at.date().isoformat()}: {snippet}{url}"


def _prefixed_lines(values: list[str]) -> list[str]:
    return [f"- {value}" for value in values if value]


def _first_or_default(values: list[str], default: str) -> str:
    for value in values:
        if value.strip():
            return value.strip()
    return default


def _metadata_text(metadata: dict[str, str], field_name: str) -> str | None:
    value = metadata.get(field_name)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _metadata_list(metadata: dict[str, str], field_name: str) -> list[str]:
    value = metadata.get(field_name)
    if not value:
        return []
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        decoded = value
    if isinstance(decoded, list):
        return [str(item).strip() for item in decoded if str(item).strip()]
    if isinstance(decoded, str):
        return [item.strip() for item in re.split(r"[,;]", decoded) if item.strip()]
    return []


def _normalize_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9а-яё]+", "-", value.lower()).strip("-")
    return normalized or "untitled"


def _evidence_count(connection) -> int:
    return int(connection.execute("SELECT COUNT(*) FROM evidence").fetchone()[0])


def _stored_evidence_rows(
    connection,
    records: tuple[EvidenceRecord, ...],
) -> list[tuple[int, EvidenceRecord]]:
    evidence_rows: list[tuple[int, EvidenceRecord]] = []
    seen_ids: set[int] = set()
    for record in records:
        row = connection.execute(
            """
            SELECT id
            FROM evidence
            WHERE source_fingerprint = :source_fingerprint
            """,
            {"source_fingerprint": record.source_fingerprint},
        ).fetchone()
        if row is None:
            continue
        evidence_id = int(row["id"])
        if evidence_id in seen_ids:
            continue
        seen_ids.add(evidence_id)
        evidence_rows.append((evidence_id, record))
    return evidence_rows


def _write_json(
    path: Path,
    *,
    selected: CandidateAggregate | None,
    candidates: list[CandidateAggregate],
    result: MvpOfWeekResult,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "result": result.model_dump(mode="json"),
        "selected": _candidate_json(selected) if selected is not None else None,
        "candidates": [_candidate_json(candidate) for candidate in candidates],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _candidate_json(candidate: CandidateAggregate) -> dict[str, object]:
    return {
        "title": candidate.title,
        "score": candidate.score,
        "recommendation": candidate.recommendation,
        "evidence_count": len(candidate.evidence),
        "surfaces": sorted(candidate.surfaces),
        "channels": sorted(candidate.channels),
        "missing_evidence": sorted(candidate.missing_evidence),
        "risk_flags": sorted(candidate.risk_flags),
    }


def _record_mvp_run(
    connection,
    *,
    run_id: str,
    corpus_version: str,
    evidence_count: int,
    duplicate_count: int,
    quarantined_count: int,
    selected_title: str | None,
    score: int | None,
) -> None:
    now = datetime.now(UTC).isoformat()
    connection.execute(
        """
        INSERT INTO runs (
            run_id,
            started_at,
            ended_at,
            status,
            source_counts,
            error_counts,
            source_errors,
            source_health,
            duplicate_count,
            corpus_version,
            max_weekly_llm_cost_usd
        )
        VALUES (
            :run_id,
            :started_at,
            :ended_at,
            :status,
            :source_counts,
            :error_counts,
            :source_errors,
            :source_health,
            :duplicate_count,
            :corpus_version,
            :max_weekly_llm_cost_usd
        )
        ON CONFLICT(run_id) DO UPDATE SET
            ended_at = excluded.ended_at,
            status = excluded.status,
            source_counts = excluded.source_counts,
            error_counts = excluded.error_counts,
            duplicate_count = excluded.duplicate_count,
            corpus_version = excluded.corpus_version,
            max_weekly_llm_cost_usd = excluded.max_weekly_llm_cost_usd
        """,
        {
            "run_id": run_id,
            "started_at": now,
            "ended_at": now,
            "status": "mvp_of_week",
            "source_counts": json.dumps(
                {
                    "telegram_research_agent": evidence_count,
                    "selected_title": selected_title or "",
                    "score": score or 0,
                },
                sort_keys=True,
            ),
            "error_counts": json.dumps(
                {"telegram_research_agent_quarantined": quarantined_count},
                sort_keys=True,
            ),
            "source_errors": "{}",
            "source_health": "{}",
            "duplicate_count": duplicate_count,
            "corpus_version": corpus_version,
            "max_weekly_llm_cost_usd": "0",
        },
    )
    connection.commit()
