"""Weekly pipeline orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from demand_mvp_radar.briefs import OpportunityBrief, build_opportunity_brief
from demand_mvp_radar.clustering import cluster_evidence
from demand_mvp_radar.config import Settings
from demand_mvp_radar.models import EvidenceRecord, OpportunityExtraction
from demand_mvp_radar.reports.markdown import render_markdown_report, write_markdown_report
from demand_mvp_radar.retrieval.ingestion import build_corpus
from demand_mvp_radar.retrieval.query import EvidencePacket
from demand_mvp_radar.scoring import score_opportunity
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.storage.repositories import EvidenceRepository


class WeeklyRunResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    status: str
    database_path: Path
    report_path: Path | None = None
    corpus_version: str | None = None
    evidence_count: int = 0
    opportunity_count: int = 0
    estimated_llm_cost_usd: Decimal
    error_reason: str | None = None


def run_weekly_pipeline(
    *,
    fixture: Path,
    settings: Settings,
    run_id: str | None = None,
) -> WeeklyRunResult:
    payload = json.loads((fixture / "weekly_run.json").read_text())
    effective_run_id = run_id or str(payload["run_id"])
    estimated_cost = Decimal(str(payload.get("estimated_llm_cost_usd", "0")))
    database_path = settings.data_dir / "radar.sqlite3"
    report_path = settings.report_dir / f"{effective_run_id}.md"
    corpus_version = str(payload.get("corpus_version", f"{effective_run_id}-corpus"))

    if estimated_cost > settings.max_weekly_llm_cost_usd:
        return WeeklyRunResult(
            run_id=effective_run_id,
            status="budget_exceeded",
            database_path=database_path,
            corpus_version=corpus_version,
            estimated_llm_cost_usd=estimated_cost,
            error_reason="estimated LLM cost exceeds configured budget ceiling",
        )

    connection = connect_database(database_path)
    create_schema(connection)
    repository = EvidenceRepository(connection)
    evidence_rows = []
    evidence_records = []
    for item in payload["evidence"]:
        evidence = _evidence_from_fixture(item, run_id=effective_run_id)
        evidence_id = repository.write(evidence)
        evidence_rows.append((evidence_id, evidence))
        evidence_records.append(evidence)

    corpus_metadata = build_corpus(connection, evidence_rows, corpus_version=corpus_version)
    candidates = cluster_evidence(evidence_records)
    extraction = _extraction_from_fixture(payload["extraction"])
    briefs = [
        _brief_for_candidate(candidate, evidence_records, extraction) for candidate in candidates
    ]
    report = render_markdown_report(
        briefs,
        top_n=int(payload.get("top_n", 5)),
        generated_at=datetime.now(UTC),
    )
    write_markdown_report(report_path, report)
    _record_completed_run(
        connection,
        run_id=effective_run_id,
        corpus_version=corpus_version,
        estimated_cost=estimated_cost,
    )

    return WeeklyRunResult(
        run_id=effective_run_id,
        status="completed",
        database_path=database_path,
        report_path=report_path,
        corpus_version=str(corpus_metadata["corpus_version"]),
        evidence_count=len(evidence_records),
        opportunity_count=len(candidates),
        estimated_llm_cost_usd=estimated_cost,
    )


def _evidence_from_fixture(item: dict[str, object], *, run_id: str) -> EvidenceRecord:
    return EvidenceRecord(
        run_id=run_id,
        source_type=str(item["source_type"]),
        source_id=str(item["source_id"]),
        source_url=item.get("source_url"),
        captured_at=datetime.fromisoformat(str(item["captured_at"])),
        title=str(item["title"]),
        snippet=str(item["snippet"]),
        normalized_text=str(item["normalized_text"]),
        content_hash=str(item["content_hash"]),
        source_fingerprint=str(item["source_fingerprint"]),
    )


def _extraction_from_fixture(item: dict[str, object]) -> OpportunityExtraction:
    return OpportunityExtraction.model_validate(item)


def _brief_for_candidate(
    candidate,
    evidence_records: list[EvidenceRecord],
    extraction: OpportunityExtraction,
) -> OpportunityBrief:
    score = score_opportunity(candidate, evidence_records)
    selected = [
        record for record in evidence_records if record.source_id in candidate.source_evidence_ids
    ]
    packets = tuple(
        EvidencePacket(
            evidence_id=index,
            source_url=record.source_url or "",
            captured_at=record.captured_at,
            snippet=record.snippet,
            relevance_score=1.0,
            citation_number=index,
        )
        for index, record in enumerate(selected, start=1)
        if record.source_url is not None
    )
    return build_opportunity_brief(
        candidate=candidate,
        score=score,
        extraction=extraction,
        evidence_packets=packets,
    )


def _record_completed_run(
    connection,
    *,
    run_id: str,
    corpus_version: str,
    estimated_cost: Decimal,
) -> None:
    now = datetime.now(UTC).isoformat()
    connection.execute(
        """
        UPDATE runs
        SET status = :status,
            ended_at = :ended_at,
            corpus_version = :corpus_version,
            max_weekly_llm_cost_usd = :estimated_cost
        WHERE run_id = :run_id
        """,
        {
            "run_id": run_id,
            "status": "completed",
            "ended_at": now,
            "corpus_version": corpus_version,
            "estimated_cost": str(estimated_cost),
        },
    )
    connection.commit()
