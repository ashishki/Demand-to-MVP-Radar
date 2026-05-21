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
from demand_mvp_radar.credentials import (
    CredentialRequirement,
    resolve_live_source_credentials,
)
from demand_mvp_radar.models import EvidenceRecord, OpportunityExtraction
from demand_mvp_radar.reports.evidence_delta import (
    EvidenceDeltaReport,
    generate_evidence_delta_report,
)
from demand_mvp_radar.reports.markdown import render_markdown_report, write_markdown_report
from demand_mvp_radar.retrieval.ingestion import build_corpus
from demand_mvp_radar.retrieval.query import EvidencePacket
from demand_mvp_radar.scoring import score_opportunity
from demand_mvp_radar.sources.base import SourceImportResult
from demand_mvp_radar.sources.github_public import GitHubPublicSearchConnector
from demand_mvp_radar.sources.github_repo import GitHubRepoSnapshotImporter
from demand_mvp_radar.sources.hacker_news import HackerNewsLiveConnector
from demand_mvp_radar.sources.live import (
    LiveConnectorResult,
    LiveSourceConfig,
    RateLimitPolicy,
    RateLimitState,
)
from demand_mvp_radar.sources.operator_notes import OperatorNotesAdapter
from demand_mvp_radar.sources.rss import RSSFeedConnector
from demand_mvp_radar.sources.serp import SERPSearchConnector
from demand_mvp_radar.sources.stack_exchange import StackExchangeLiveConnector
from demand_mvp_radar.sources.telegram_research_agent import TelegramResearchAgentBridge
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


class ImportSourcesResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    status: str
    database_path: Path
    report_path: Path | None = None
    corpus_version: str
    evidence_count: int
    retrieval_chunk_count: int
    source_counts: dict[str, object]
    error_counts: dict[str, int]
    skipped_sources: tuple[str, ...]
    evidence_delta_report: EvidenceDeltaReport | None = None


class CollectSourcesResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    status: str
    database_path: Path
    report_path: Path | None = None
    corpus_version: str
    evidence_count: int
    duplicate_count: int
    retrieval_chunk_count: int
    source_counts: dict[str, object]
    error_counts: dict[str, int]
    source_errors: dict[str, str]
    skipped_sources: tuple[str, ...]


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


def import_sources(
    *,
    fixture: Path,
    settings: Settings,
    run_id: str | None = None,
) -> ImportSourcesResult:
    payload = json.loads((fixture / "sources.json").read_text())
    effective_run_id = run_id or str(payload["run_id"])
    corpus_version = str(payload.get("corpus_version", f"{effective_run_id}-corpus"))
    database_path = settings.data_dir / "radar.sqlite3"

    connection = connect_database(database_path)
    create_schema(connection)
    repository = EvidenceRepository(connection)

    evidence_rows: list[tuple[int, EvidenceRecord]] = []
    source_counts: dict[str, object] = {}
    error_counts: dict[str, int] = {}
    skipped_sources: list[str] = []

    for source_name, source_config in payload["sources"].items():
        if not bool(source_config.get("enabled", False)):
            skipped_sources.append(source_name)
            continue

        result_records = _import_configured_source(
            source_name,
            source_config,
            fixture=fixture,
            run_id=effective_run_id,
            repository=repository,
            quarantine_dir=settings.data_dir / "quarantine",
        )
        for evidence in result_records.evidence:
            evidence_id = repository.write(evidence)
            evidence_rows.append((evidence_id, evidence))
        source_counts[source_name] = len(result_records.evidence)
        error_counts[source_name] = len(result_records.quarantined)

    source_counts["skipped_sources"] = tuple(skipped_sources)
    corpus_metadata = build_corpus(connection, evidence_rows, corpus_version=corpus_version)
    _record_import_run(
        connection,
        run_id=effective_run_id,
        corpus_version=corpus_version,
        source_counts=source_counts,
        error_counts=error_counts,
    )
    evidence_delta_report = generate_evidence_delta_report(
        connection,
        run_id=effective_run_id,
    )

    return ImportSourcesResult(
        run_id=effective_run_id,
        status="imported",
        database_path=database_path,
        corpus_version=str(corpus_metadata["corpus_version"]),
        evidence_count=len(evidence_rows),
        retrieval_chunk_count=int(corpus_metadata["chunk_count"]),
        source_counts=source_counts,
        error_counts=error_counts,
        skipped_sources=tuple(skipped_sources),
        evidence_delta_report=evidence_delta_report,
    )


def collect_sources(
    *,
    config: Path,
    settings: Settings,
    run_id: str | None = None,
) -> CollectSourcesResult:
    payload = json.loads(config.read_text(encoding="utf-8"))
    config_dir = config.parent
    effective_run_id = run_id or str(payload["run_id"])
    corpus_version = str(payload.get("corpus_version", f"{effective_run_id}-corpus"))
    database_path = settings.data_dir / "radar.sqlite3"

    connection = connect_database(database_path)
    create_schema(connection)
    repository = EvidenceRepository(connection)

    evidence_rows: list[tuple[int, EvidenceRecord]] = []
    source_counts: dict[str, object] = {}
    error_counts: dict[str, int] = {}
    source_errors: dict[str, str] = {}
    source_health: dict[str, dict[str, object]] = {}
    skipped_sources: list[str] = []
    duplicate_count = 0

    for raw_source in payload.get("sources", []):
        source_config = dict(raw_source)
        live_config = _live_config_from_payload(source_config)
        if not live_config.enabled:
            skipped_sources.append(live_config.source_name)
            continue

        credential_state = resolve_live_source_credentials((live_config,))[0]
        if credential_state.source_error is not None:
            source_counts[live_config.source_name] = 0
            error_counts[live_config.source_name] = 1
            source_errors[live_config.source_name] = (
                credential_state.source_error.to_manifest_value()
            )
            source_health[live_config.source_name] = _source_health_from_error(
                live_config,
                credential_state.source_error.status,
            )
            continue

        try:
            result_records = _collect_configured_live_source(
                live_config,
                source_config,
                run_id=effective_run_id,
                config_dir=config_dir,
            )
        except (KeyError, TypeError, ValueError) as error:
            source_counts[live_config.source_name] = 0
            error_counts[live_config.source_name] = 1
            source_errors[live_config.source_name] = f"{live_config.source_name}: {error}"
            source_health[live_config.source_name] = _source_health_from_error(
                live_config,
                "source_error",
            )
            continue

        source_counts[live_config.source_name] = len(result_records.evidence)
        error_counts[live_config.source_name] = len(result_records.quarantined)
        if result_records.quarantined:
            source_errors[live_config.source_name] = "; ".join(
                row.error_reason for row in result_records.quarantined
            )
        source_health[live_config.source_name] = _source_health_from_result(
            live_config,
            result_records,
            collected_at=datetime.now(UTC),
        )

        for evidence in result_records.evidence:
            evidence_id, inserted = repository.write_with_status(evidence)
            if inserted:
                evidence_rows.append((evidence_id, evidence))
            else:
                duplicate_count += 1

    source_counts["skipped_sources"] = tuple(skipped_sources)
    if evidence_rows:
        corpus_metadata = build_corpus(connection, evidence_rows, corpus_version=corpus_version)
        retrieval_chunk_count = int(corpus_metadata["chunk_count"])
    else:
        retrieval_chunk_count = 0
    _record_collect_run(
        connection,
        run_id=effective_run_id,
        corpus_version=corpus_version,
        source_counts=source_counts,
        error_counts=error_counts,
        source_errors=source_errors,
        source_health=source_health,
        duplicate_count=duplicate_count,
    )

    return CollectSourcesResult(
        run_id=effective_run_id,
        status="collected",
        database_path=database_path,
        corpus_version=corpus_version,
        evidence_count=len(evidence_rows),
        duplicate_count=duplicate_count,
        retrieval_chunk_count=retrieval_chunk_count,
        source_counts=source_counts,
        error_counts=error_counts,
        source_errors=source_errors,
        skipped_sources=tuple(skipped_sources),
    )


def _import_configured_source(
    source_name: str,
    source_config: dict[str, object],
    *,
    fixture: Path,
    run_id: str,
    repository: EvidenceRepository,
    quarantine_dir: Path,
) -> SourceImportResult:
    if source_name == "telegram_research_agent":
        return TelegramResearchAgentBridge().import_file(
            fixture / str(source_config["path"]),
            run_id=run_id,
            repository=repository,
            quarantine_path=quarantine_dir / f"{source_name}.jsonl",
        )
    if source_name == "operator_notes":
        adapter = OperatorNotesAdapter()
        evidence = []
        quarantined = []
        for relative_path in source_config["paths"]:
            result = adapter.import_file(
                fixture / str(relative_path),
                run_id=run_id,
                quarantine_path=quarantine_dir / f"{source_name}.jsonl",
            )
            evidence.extend(result.evidence)
            quarantined.extend(result.quarantined)
        return SourceImportResult(evidence=tuple(evidence), quarantined=tuple(quarantined))
    if source_name == "github_repo":
        return GitHubRepoSnapshotImporter().import_repository(
            fixture / str(source_config["path"]),
            run_id=run_id,
            repository_identifier=str(source_config["repository_identifier"]),
        )
    raise ValueError(f"unsupported source: {source_name}")


def _live_config_from_payload(source_config: dict[str, object]) -> LiveSourceConfig:
    rate_limit_config = dict(source_config.get("rate_limit_policy", {}))
    credential_env_vars = tuple(str(name) for name in source_config.get("credential_env_vars", ()))
    return LiveSourceConfig(
        source_name=str(source_config["source_name"]),
        source_type=str(source_config["source_type"]),
        trust_level=source_config["trust_level"],
        freshness_window_days=int(source_config["freshness_window_days"]),
        enabled=bool(source_config.get("enabled", False)),
        cursor_support=bool(source_config["cursor_support"]),
        raw_snapshot_policy=source_config["raw_snapshot_policy"],
        rate_limit_policy=RateLimitPolicy(**rate_limit_config),
        approval_required=bool(source_config.get("approval_required", False)),
        credential_requirements=tuple(
            CredentialRequirement(
                env_var_name=env_var_name,
                required=str(source_config["source_type"]) != "github_public",
            )
            for env_var_name in credential_env_vars
        ),
    )


def _source_health_from_result(
    live_config: LiveSourceConfig,
    result: LiveConnectorResult,
    *,
    collected_at: datetime,
) -> dict[str, object]:
    return {
        "enabled": live_config.enabled,
        "freshness_window_days": live_config.freshness_window_days,
        "credential_status": "not_required"
        if not live_config.credential_requirements
        else "available",
        "last_success_at": result.last_success_at.isoformat()
        if result.last_success_at
        else None,
        "last_collected_at": collected_at.isoformat(),
        "last_error_class": "source_error" if result.quarantined else None,
        "cursor_state": result.cursor_state,
        "rate_limit_state": result.rate_limit_state.model_dump(mode="json"),
    }


def _source_health_from_error(
    live_config: LiveSourceConfig,
    error_class: str,
) -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    return {
        "enabled": live_config.enabled,
        "freshness_window_days": live_config.freshness_window_days,
        "credential_status": error_class if error_class in {"missing", "invalid"} else "unknown",
        "last_success_at": None,
        "last_collected_at": now,
        "last_error_class": error_class,
        "cursor_state": {},
        "rate_limit_state": {"limited": False},
    }


def _collect_configured_live_source(
    live_config: LiveSourceConfig,
    source_config: dict[str, object],
    *,
    run_id: str,
    config_dir: Path,
) -> LiveConnectorResult:
    if bool(source_config.get("fail", False)):
        raise ValueError("fixture failure requested")
    if live_config.source_type == "hacker_news":
        fixture_path = Path(str(source_config["fixture_path"]))
        if not fixture_path.is_absolute():
            fixture_path = config_dir / fixture_path
        return HackerNewsLiveConnector(fixture_path).collect(
            live_config,
            run_id=run_id,
            cursor_state={
                str(key): str(value)
                for key, value in dict(source_config.get("cursor_state", {})).items()
            },
        )
    if live_config.source_type == "stack_exchange":
        fixture_path = Path(str(source_config["fixture_path"]))
        if not fixture_path.is_absolute():
            fixture_path = config_dir / fixture_path
        return StackExchangeLiveConnector(
            fixture_path,
            sites=tuple(str(site) for site in source_config.get("sites", ())),
            tags=tuple(str(tag) for tag in source_config.get("tags", ())),
        ).collect(
            live_config,
            run_id=run_id,
            cursor_state={
                str(key): str(value)
                for key, value in dict(source_config.get("cursor_state", {})).items()
            },
        )
    if live_config.source_type == "rss":
        fixture_paths = tuple(
            _resolve_fixture_path(config_dir, path)
            for path in source_config.get("fixture_paths", ())
        )
        return RSSFeedConnector(fixture_paths).collect(
            live_config,
            run_id=run_id,
            cursor_state={
                str(key): str(value)
                for key, value in dict(source_config.get("cursor_state", {})).items()
            },
        )
    if live_config.source_type == "github_public":
        fixture_path = _resolve_fixture_path(config_dir, source_config["fixture_path"])
        return GitHubPublicSearchConnector(
            fixture_path,
            queries=tuple(str(query) for query in source_config.get("queries", ())),
        ).collect(
            live_config,
            run_id=run_id,
            cursor_state={
                str(key): str(value)
                for key, value in dict(source_config.get("cursor_state", {})).items()
            },
        )
    if live_config.source_type == "serp":
        fixture_path = _resolve_fixture_path(config_dir, source_config["fixture_path"])
        return SERPSearchConnector(
            fixture_path,
            queries=tuple(str(query) for query in source_config.get("queries", ())),
            provider=str(source_config.get("provider", "serpapi")),
            daily_budget_limit=int(source_config["daily_budget_limit"]),
            per_run_budget_limit=int(source_config["per_run_budget_limit"]),
            daily_budget_used=int(source_config.get("daily_budget_used", 0)),
        ).collect(
            live_config,
            run_id=run_id,
            cursor_state={
                str(key): str(value)
                for key, value in dict(source_config.get("cursor_state", {})).items()
            },
        )
    if live_config.source_type != "fixture_live":
        raise ValueError(f"unsupported live source: {live_config.source_type}")

    evidence = tuple(
        _live_evidence_from_fixture_row(row, live_config=live_config, run_id=run_id)
        for row in source_config.get("records", ())
    )
    return LiveConnectorResult(
        evidence=evidence,
        source_counts={live_config.source_name: len(evidence)},
        error_counts={live_config.source_name: 0},
        cursor_state={
            str(key): str(value)
            for key, value in dict(source_config.get("cursor_state", {})).items()
        },
        rate_limit_state=RateLimitState(limited=False),
        last_success_at=datetime.now(UTC),
    )


def _resolve_fixture_path(config_dir: Path, raw_path: object) -> Path:
    fixture_path = Path(str(raw_path))
    if not fixture_path.is_absolute():
        return config_dir / fixture_path
    return fixture_path


def _live_evidence_from_fixture_row(
    row: object,
    *,
    live_config: LiveSourceConfig,
    run_id: str,
) -> EvidenceRecord:
    if not isinstance(row, dict):
        raise TypeError("live fixture row must be an object")
    return EvidenceRecord(
        run_id=run_id,
        source_name=live_config.source_name,
        source_type=live_config.source_type,
        source_id=str(row["source_id"]),
        source_url=str(row["source_url"]),
        captured_at=datetime.fromisoformat(str(row["captured_at"])),
        title=str(row["title"]),
        snippet=str(row["snippet"]),
        normalized_text=str(row["normalized_text"]),
        content_hash=str(row["content_hash"]),
        source_fingerprint=str(row["source_fingerprint"]),
        connector_version=str(row.get("connector_version", "fixture-live-v1")),
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


def _record_import_run(
    connection,
    *,
    run_id: str,
    corpus_version: str,
    source_counts: dict[str, object],
    error_counts: dict[str, int],
) -> None:
    now = datetime.now(UTC).isoformat()
    connection.execute(
        """
        UPDATE runs
        SET status = :status,
            ended_at = :ended_at,
            corpus_version = :corpus_version,
            source_counts = :source_counts,
            error_counts = :error_counts,
            max_weekly_llm_cost_usd = :max_weekly_llm_cost_usd
        WHERE run_id = :run_id
        """,
        {
            "run_id": run_id,
            "status": "imported",
            "ended_at": now,
            "corpus_version": corpus_version,
            "source_counts": json.dumps(source_counts, sort_keys=True),
            "error_counts": json.dumps(error_counts, sort_keys=True),
            "max_weekly_llm_cost_usd": "0",
        },
    )
    connection.commit()


def _record_collect_run(
    connection,
    *,
    run_id: str,
    corpus_version: str,
    source_counts: dict[str, object],
    error_counts: dict[str, int],
    source_errors: dict[str, str],
    source_health: dict[str, dict[str, object]],
    duplicate_count: int,
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
            source_errors = excluded.source_errors,
            source_health = excluded.source_health,
            duplicate_count = excluded.duplicate_count,
            corpus_version = excluded.corpus_version,
            max_weekly_llm_cost_usd = excluded.max_weekly_llm_cost_usd
        """,
        {
            "run_id": run_id,
            "started_at": now,
            "ended_at": now,
            "status": "collected",
            "source_counts": json.dumps(source_counts, sort_keys=True),
            "error_counts": json.dumps(error_counts, sort_keys=True),
            "source_errors": json.dumps(source_errors, sort_keys=True),
            "source_health": json.dumps(source_health, sort_keys=True),
            "duplicate_count": duplicate_count,
            "corpus_version": corpus_version,
            "max_weekly_llm_cost_usd": "0",
        },
    )
    connection.commit()
