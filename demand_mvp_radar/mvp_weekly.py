"""Weekly MVP selection from telegram-research-agent opportunity seeds."""

from __future__ import annotations

import copy
import json
import logging
import os
import re
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from demand_mvp_radar.briefs import OpportunityBrief, build_opportunity_brief
from demand_mvp_radar.config import Settings
from demand_mvp_radar.llm.adapter import LLMProvider, provider_from_env
from demand_mvp_radar.models import (
    EvidenceRecord,
    OpportunityCandidate,
    OpportunityExtraction,
    OpportunityScore,
    ScoreComponent,
)
from demand_mvp_radar.pipeline import CollectSourcesResult, collect_sources
from demand_mvp_radar.proof import (
    build_weekly_report_proof_receipt,
    proof_receipt_path_for_report,
    write_weekly_report_proof_receipt,
)
from demand_mvp_radar.reports.markdown import write_markdown_report
from demand_mvp_radar.retrieval.ingestion import build_corpus
from demand_mvp_radar.retrieval.query import EvidencePacket
from demand_mvp_radar.source_trust import build_source_trust_records
from demand_mvp_radar.sources.telegram_research_agent import TelegramResearchAgentBridge
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.storage.repositories import EvidenceRepository
from demand_mvp_radar.validation_evidence import (
    decision_grade_match_count,
    external_research_context,
    match_external_evidence,
    matched_external_fingerprints,
    matched_external_source_types,
    missing_evidence_by_kind,
)
from demand_mvp_radar.validation_queries import (
    build_validation_query_pack,
    validation_adapter_status,
)

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
EXTERNAL_DEMAND_SOURCE_TYPES = {
    "crawl4ai",
    "serp",
    "github_public",
    "stack_exchange",
    "reddit",
    "product_hunt",
    "youtube",
    "rss",
    "hacker_news",
    "store",
    "reviews",
    "forum",
    "news",
    "x",
}
OPERATOR_PROFILE_ENV = "DMR_OPERATOR_PROFILE_PATH"
PROFILE_FIT_KEYWORDS = (
    ("llm", "LLM orchestration"),
    ("agent", "agentic workflows"),
    ("workflow", "workflow automation"),
    ("automation", "workflow automation"),
    ("eval", "evaluation-first delivery"),
    ("guardrail", "guardrails and safety"),
    ("observability", "LLMOps observability"),
    ("telegram", "Telegram-native research"),
    ("obsidian", "knowledge memory"),
    ("knowledge", "knowledge memory"),
    ("research", "research tooling"),
    ("decision", "decision support"),
    ("training", "education and rollout"),
    ("rollout", "education and rollout"),
    ("document", "document/data pipeline"),
    ("pdf", "document/data pipeline"),
    ("fastapi", "Python backend fit"),
    ("python", "Python backend fit"),
    ("n8n", "workflow automation"),
)
PROFILE_MISMATCH_KEYWORDS = (
    ("java", "JVM-heavy implementation"),
    ("kotlin", "JVM/mobile-heavy implementation"),
    ("swift", "mobile-native implementation"),
    ("android", "mobile-native implementation"),
    ("ios", "mobile-native implementation"),
    ("wordpress", "CMS-specific implementation"),
    ("shopify", "platform-plugin implementation"),
    ("solidity", "smart-contract implementation"),
    ("trading bot", "live trading automation"),
    ("game engine", "game-engine domain mismatch"),
)
PROFILE_STACK_FIT_FLAGS = {
    "Python backend fit",
    "LLM orchestration",
    "evaluation-first delivery",
    "guardrails and safety",
    "knowledge memory",
    "research tooling",
    "document/data pipeline",
}
RECOMMENDATION_GATED = {"focused_experiment", "build"}
KIR_FRESHNESS_DAYS = 30
STALE_KIR_THREAD_STATUSES = {"stale", "superseded", "resolved", "hype_only"}
KIR_GATE_PASSING_STATUSES = {"passed", "not_required"}
LOGGER = logging.getLogger(__name__)


class MvpOfWeekResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    status: str
    database_path: Path
    report_path: Path
    json_path: Path
    proof_receipt_path: Path | None = None
    corpus_version: str
    evidence_count: int
    duplicate_count: int
    quarantined_count: int
    retrieval_chunk_count: int
    selected_title: str | None = None
    dossier_status: str | None = None
    recommendation: str | None = None
    score: int | None = None
    selected_source_mix: dict[str, object] | None = None
    validation_adapter_status: dict[str, object] = Field(default_factory=dict)
    matched_external_evidence: list[dict[str, object]] = Field(default_factory=list)
    missing_evidence_by_category: dict[str, object] = Field(default_factory=dict)
    decision_change_action: dict[str, object] | None = None
    source_counts: dict[str, object] = Field(default_factory=dict)
    source_errors: dict[str, str] = Field(default_factory=dict)
    llm_synthesis_status: str = "not_requested"
    synthesis_model: str | None = None


class LlmMvpSynthesis(BaseModel):
    model_config = ConfigDict(frozen=True)

    selected_title: str | None = None
    recommendation: str | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    markdown: str


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
    profile_fit_flags: set[str] = field(default_factory=set)
    profile_mismatch_flags: set[str] = field(default_factory=set)
    score: int = 0
    recommendation: str = "needs_more_evidence"


def run_mvp_of_week(
    *,
    telegram_export: Path,
    settings: Settings,
    run_id: str | None = None,
    top_evidence: int = 5,
    source_config: Path | None = None,
    live_intelligence_path: Path | None = None,
    llm_provider: LLMProvider | None = None,
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
    collect_result = _collect_configured_sources(
        source_config=source_config,
        settings=settings,
        run_id=effective_run_id,
    )
    after_count = _evidence_count(connection)
    duplicate_count = max(len(import_result.evidence) - max(after_count - before_count, 0), 0)

    evidence_records = _records_for_current_run(
        connection,
        run_id=effective_run_id,
        seed_records=import_result.evidence,
    )
    evidence_rows = _stored_evidence_rows(connection, evidence_records)
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

    context_only_records = _context_only_records(evidence_records)
    candidate_evidence_records = _candidate_evidence_records(evidence_records)
    candidates = _rank_candidates(candidate_evidence_records)
    selected = candidates[0] if candidates else None
    llm_provider = llm_provider if llm_provider is not None else provider_from_env()
    source_counts = _source_counts(candidate_evidence_records, collect_result=collect_result)
    if context_only_records:
        source_counts = {
            **source_counts,
            "context_only_record_count": len(context_only_records),
            "market_context": _market_context_summary(context_only_records),
        }
    live_intelligence = _load_live_intelligence_summary(live_intelligence_path)
    if live_intelligence is not None:
        source_counts = {**source_counts, "live_intelligence": live_intelligence}
    (
        synthesis_markdown,
        selected_title,
        recommendation,
        score,
        synthesis_status,
    ) = _synthesize_or_render(
        provider=llm_provider,
        run_id=effective_run_id,
        selected=selected,
        candidates=candidates[:5],
        evidence_records=candidate_evidence_records,
        evidence_count=len(candidate_evidence_records),
        quarantined_count=len(import_result.quarantined),
        top_evidence=top_evidence,
        source_counts=source_counts,
    )
    base_selected = _candidate_for_title(selected_title, candidates) or selected
    report_selected = _candidate_with_gated_result(
        base_selected,
        recommendation=recommendation,
        score=score,
    )
    report_candidates = _replace_candidate_in_list(
        candidates[:5],
        selected=base_selected,
        replacement=report_selected,
    )
    selected_source_mix = _selected_source_mix(report_selected, source_counts)
    if selected_source_mix is not None:
        source_counts = {
            **source_counts,
            "selected_candidate_source_mix": selected_source_mix,
        }
    matched_external_evidence = _matched_external_evidence(report_selected)
    validation_pack = _validation_query_pack(report_selected)
    missing_evidence_by_category = _missing_evidence_by_category_for_selected(
        report_selected,
        matched_evidence=matched_external_evidence,
        validation_queries=validation_pack,
    )
    adapter_status = validation_adapter_status(source_counts)
    decision_change_action = _decision_change_action(report_selected)
    markdown = (
        _render_report(
            run_id=effective_run_id,
            selected=report_selected,
            candidates=report_candidates,
            evidence_count=len(candidate_evidence_records),
            quarantined_count=len(import_result.quarantined),
            top_evidence=top_evidence,
            source_counts=source_counts,
        )
        if synthesis_markdown is None
        else synthesis_markdown
    )
    write_markdown_report(report_path, markdown)
    receipt_briefs = _receipt_briefs_for_candidates(report_candidates)
    proof_receipt_path = None
    if receipt_briefs:
        proof_receipt_path = proof_receipt_path_for_report(report_path)
        proof_receipt = build_weekly_report_proof_receipt(
            report_markdown=markdown,
            report_path=report_path,
            briefs=receipt_briefs,
        )
        write_weekly_report_proof_receipt(proof_receipt_path, proof_receipt)

    source_errors = collect_result.source_errors if collect_result is not None else {}
    result = MvpOfWeekResult(
        run_id=effective_run_id,
        status="selected" if selected is not None else "no_evidence",
        database_path=database_path,
        report_path=report_path,
        json_path=json_path,
        proof_receipt_path=proof_receipt_path,
        corpus_version=corpus_version,
        evidence_count=len(evidence_records),
        duplicate_count=duplicate_count + (collect_result.duplicate_count if collect_result else 0),
        quarantined_count=len(import_result.quarantined),
        retrieval_chunk_count=retrieval_chunk_count,
        selected_title=(report_selected.title if report_selected is not None else None),
        dossier_status=(_dossier_status(report_selected) if report_selected is not None else None),
        recommendation=(
            recommendation or report_selected.recommendation
            if report_selected is not None
            else None
        ),
        score=(
            score
            if score is not None
            else report_selected.score
            if report_selected is not None
            else None
        ),
        selected_source_mix=selected_source_mix,
        validation_adapter_status=adapter_status,
        matched_external_evidence=matched_external_evidence,
        missing_evidence_by_category=missing_evidence_by_category,
        decision_change_action=decision_change_action,
        source_counts=source_counts,
        source_errors=source_errors,
        llm_synthesis_status=synthesis_status,
        synthesis_model=_provider_model(llm_provider),
    )
    _write_json(
        json_path,
        selected=report_selected,
        candidates=report_candidates,
        result=result,
        source_counts=source_counts,
        source_config=source_config,
        live_intelligence_path=live_intelligence_path,
    )
    _record_mvp_run(
        connection,
        run_id=effective_run_id,
        corpus_version=corpus_version,
        source_counts=source_counts,
        source_errors=source_errors,
        evidence_count=len(evidence_records),
        duplicate_count=result.duplicate_count,
        quarantined_count=len(import_result.quarantined),
        selected_title=result.selected_title,
        score=result.score,
    )
    return result


def _rank_candidates(
    records: tuple[EvidenceRecord, ...],
    *,
    as_of: datetime | None = None,
) -> list[CandidateAggregate]:
    gate_as_of = as_of or datetime.now(UTC)
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
        candidate.profile_fit_flags.update(_profile_fit_flags(text))
        candidate.profile_mismatch_flags.update(_profile_mismatch_flags(text))

    for candidate in grouped.values():
        if _matched_external_count(candidate) == 0:
            candidate.missing_evidence.add("non-Telegram public evidence for the same pain")
        elif len(_matched_external_source_types(candidate)) < 2:
            candidate.missing_evidence.add("second independent external source type")
        if candidate.profile_mismatch_flags:
            candidate.missing_evidence.add("operator-fit wedge that avoids an unfamiliar stack")
        candidate.missing_evidence.update(_kir_gate_missing_evidence(candidate, as_of=gate_as_of))
        candidate.score = _score_candidate(candidate)
        if (
            candidate.score >= 70
            and not _has_blocking_gap(candidate)
            and _has_decision_grade_external_evidence(candidate)
            and _kir_gate_allows_candidate(candidate, as_of=gate_as_of)
            and not _has_profile_blocking_mismatch(candidate)
        ):
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


def _candidate_evidence_records(records: tuple[EvidenceRecord, ...]) -> tuple[EvidenceRecord, ...]:
    return tuple(record for record in records if not _is_context_only_record(record))


def _context_only_records(records: tuple[EvidenceRecord, ...]) -> tuple[EvidenceRecord, ...]:
    return tuple(record for record in records if _is_context_only_record(record))


def _is_context_only_record(record: EvidenceRecord) -> bool:
    metadata = record.provider_metadata
    return (
        _metadata_bool(metadata, "context_only")
        or _metadata_text(metadata, "radar_role") == "context_only"
        or _metadata_text(metadata, "source_kind") == "market_analyst_context"
    )


def _market_context_summary(records: tuple[EvidenceRecord, ...]) -> dict[str, object]:
    context_records = []
    for record in records[:3]:
        metadata = record.provider_metadata
        context_records.append(
            {
                "title": record.title,
                "source_id": record.source_id,
                "source_url": record.source_url,
                "source_kind": _metadata_text(metadata, "source_kind"),
                "radar_role": _metadata_text(metadata, "radar_role") or "context_only",
                "context_only": True,
                "build_ready_evidence": _metadata_bool(metadata, "build_ready_evidence"),
                "market_context_lens_kind": _metadata_text(metadata, "market_context_lens_kind"),
                "source_urls": _metadata_list(metadata, "source_urls")[:8],
                "text": _truncate(record.normalized_text, 3500),
            }
        )
    return {
        "status": "context_only",
        "record_count": len(records),
        "context_only": True,
        "build_ready_evidence": False,
        "source_gate_satisfied": False,
        "summary": (
            "Market/business context is ranking guidance only; it does not satisfy "
            "external evidence, KIR, or willingness-to-pay gates."
        ),
        "records": context_records,
    }


def _receipt_briefs_for_candidates(
    candidates: list[CandidateAggregate],
) -> tuple[OpportunityBrief, ...]:
    evidence_ids: dict[str, int] = {}
    briefs: list[OpportunityBrief] = []
    for candidate in candidates:
        packets = _receipt_evidence_packets(candidate, evidence_ids)
        if not packets:
            continue
        briefs.append(
            build_opportunity_brief(
                candidate=OpportunityCandidate(
                    opportunity_id=f"mvp:{candidate.key}",
                    normalized_pain=candidate.title.lower(),
                    target_audience="operators",
                    workflow=", ".join(sorted(candidate.surfaces)) or "weekly opportunity review",
                    acquisition_channel="public evidence review",
                    source_evidence_ids=tuple(record.source_id for record in candidate.evidence),
                    candidate_title=candidate.title,
                ),
                score=OpportunityScore(
                    opportunity_id=f"mvp:{candidate.key}",
                    recommendation=candidate.recommendation,
                    total_score=float(candidate.score),
                    confidence_band=_receipt_confidence_band(candidate),
                    components={
                        "signal_strength": ScoreComponent(
                            name="signal_strength",
                            value=float(candidate.score),
                            rationale="deterministic mvp-of-week candidate score",
                        ),
                        "evidence_count": ScoreComponent(
                            name="evidence_count",
                            value=float(min(len(candidate.evidence) * 20, 100)),
                            rationale=f"{len(candidate.evidence)} supporting evidence item(s)",
                        ),
                    },
                    threshold_reasons=tuple(sorted(candidate.missing_evidence)),
                ),
                extraction=OpportunityExtraction(
                    user_pain=candidate.title,
                    target_audience="operators",
                    current_workaround=_first_or_default(
                        candidate.anti_complexity_notes,
                        "Manual weekly review of scattered demand signals.",
                    ),
                    competitor_shape="Needs public competitor corroboration.",
                    mvp_function=_first_or_default(
                        candidate.mvp_scopes,
                        f"Validate one narrow workflow around {candidate.title}.",
                    ),
                    acquisition_angle="Public source corroboration before build-worthy framing.",
                    risk_flags=tuple(sorted(candidate.risk_flags)),
                    confidence_note="Receipt adapter for the mvp-of-week product loop.",
                ),
                evidence_packets=packets,
            )
        )
    return tuple(briefs)


def _receipt_evidence_packets(
    candidate: CandidateAggregate,
    evidence_ids: dict[str, int],
) -> tuple[EvidencePacket, ...]:
    packets: list[EvidencePacket] = []
    for record in candidate.evidence:
        if not record.source_url:
            continue
        evidence_key = record.source_fingerprint or f"{record.source_type}:{record.source_id}"
        if evidence_key not in evidence_ids:
            evidence_ids[evidence_key] = len(evidence_ids) + 1
        packets.append(
            EvidencePacket(
                evidence_id=evidence_ids[evidence_key],
                source_url=record.source_url,
                captured_at=record.captured_at,
                snippet=record.snippet or record.normalized_text[:240],
                relevance_score=1.0,
                citation_number=len(packets) + 1,
            )
        )
    return tuple(packets)


def _receipt_confidence_band(candidate: CandidateAggregate) -> str:
    if candidate.recommendation == "focused_experiment":
        return "medium"
    if candidate.score >= 50:
        return "low"
    return "insufficient"


def _collect_configured_sources(
    *,
    source_config: Path | None,
    settings: Settings,
    run_id: str,
) -> CollectSourcesResult | None:
    if source_config is None:
        return None
    if not source_config.exists():
        raise FileNotFoundError(f"MVP source config not found: {source_config}")
    return collect_sources(config=source_config, settings=settings, run_id=run_id)


def _records_for_current_run(
    connection,
    *,
    run_id: str,
    seed_records: tuple[EvidenceRecord, ...],
) -> tuple[EvidenceRecord, ...]:
    by_fingerprint = {
        record.source_fingerprint: record for record in _stored_records_for_run(connection, run_id)
    }
    for record in seed_records:
        by_fingerprint[record.source_fingerprint] = record
    return tuple(by_fingerprint.values())


def _stored_records_for_run(connection, run_id: str) -> tuple[EvidenceRecord, ...]:
    rows = connection.execute(
        """
        SELECT
            run_id,
            source_name,
            source_type,
            source_id,
            source_url,
            captured_at,
            title,
            snippet,
            normalized_text,
            content_hash,
            source_fingerprint,
            connector_version,
            search_query,
            result_rank,
            provider,
            provider_metadata,
            source_created_at,
            author_hash,
            subreddit,
            comment_id,
            score,
            comment_count
        FROM evidence
        WHERE run_id = :run_id
        ORDER BY id ASC
        """,
        {"run_id": run_id},
    ).fetchall()
    records: list[EvidenceRecord] = []
    for row in rows:
        records.append(
            EvidenceRecord(
                run_id=str(row["run_id"]),
                source_name=row["source_name"],
                source_type=str(row["source_type"]),
                source_id=str(row["source_id"]),
                source_url=row["source_url"],
                captured_at=datetime.fromisoformat(str(row["captured_at"])),
                title=str(row["title"]),
                snippet=str(row["snippet"]),
                normalized_text=str(row["normalized_text"]),
                content_hash=str(row["content_hash"]),
                source_fingerprint=str(row["source_fingerprint"]),
                connector_version=row["connector_version"],
                search_query=row["search_query"],
                result_rank=row["result_rank"],
                provider=row["provider"],
                provider_metadata=_provider_metadata_from_row(row["provider_metadata"]),
                created_at=_optional_datetime(row["source_created_at"]),
                author_hash=row["author_hash"],
                subreddit=row["subreddit"],
                comment_id=row["comment_id"],
                score=row["score"],
                comment_count=row["comment_count"],
            )
        )
    return tuple(records)


def _optional_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _provider_metadata_from_row(value: object) -> dict[str, str]:
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    if not isinstance(decoded, dict):
        return {}
    return {str(key): str(item) for key, item in decoded.items()}


def _source_counts(
    records: tuple[EvidenceRecord, ...],
    *,
    collect_result: CollectSourcesResult | None,
) -> dict[str, object]:
    counts: dict[str, object] = {}
    for record in records:
        counts[record.source_type] = int(counts.get(record.source_type, 0)) + 1
    counts["external_evidence_count"] = _external_evidence_count(records)
    counts["external_source_types"] = tuple(sorted(_external_source_types(records)))
    counts["telegram_seed_evidence_count"] = sum(
        1 for record in records if record.source_type == "telegram_research_agent"
    )
    counts["kir_thread_seed_count"] = sum(
        1
        for record in records
        if record.source_type == "telegram_research_agent"
        and _kir_source_kind(record) == "knowledge_thread"
    )
    counts["kir_fresh_thread_seed_count"] = sum(
        1
        for record in records
        if record.source_type == "telegram_research_agent" and _kir_record_has_fresh_thread(record)
    )
    counts["source_trust_records"] = tuple(
        record.as_dict() for record in build_source_trust_records(records)
    )
    if collect_result is not None:
        counts["configured_sources"] = collect_result.source_counts
        counts["skipped_sources"] = collect_result.skipped_sources
        if collect_result.source_errors:
            counts["source_errors"] = collect_result.source_errors
    return counts


def _load_live_intelligence_summary(path: Path | None) -> dict[str, object] | None:
    if path is None:
        return None
    if not path.exists():
        raise FileNotFoundError(f"Live intelligence snapshot not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Live intelligence snapshot must be a JSON object")
    if payload.get("schema_version") != "live_source_intelligence.v1":
        raise ValueError("Unsupported live intelligence schema_version")
    radar_context = (
        payload.get("radar_context") if isinstance(payload.get("radar_context"), dict) else {}
    )
    return {
        "schema_version": payload.get("schema_version"),
        "generated_at": payload.get("generated_at"),
        "generation_mode": payload.get("generation_mode"),
        "events_scanned": _safe_int(payload.get("events_scanned"), default=0),
        "window": _object_dict(payload.get("window")),
        "pathway": _object_dict(payload.get("pathway")),
        "top_channels": _top_values(payload.get("channels"), key="channel_username", limit=5),
        "top_demand_surfaces": _top_values(payload.get("demand_surfaces"), key="surface", limit=5),
        "repeated_claim_count": len(_object_list(payload.get("repeated_claim_candidates"))),
        "radar_summary": str(radar_context.get("summary") or ""),
        "context_only": True,
    }


def _synthesize_or_render(
    *,
    provider: LLMProvider | None,
    run_id: str,
    selected: CandidateAggregate | None,
    candidates: list[CandidateAggregate],
    evidence_records: tuple[EvidenceRecord, ...],
    evidence_count: int,
    quarantined_count: int,
    top_evidence: int,
    source_counts: dict[str, object],
) -> tuple[str | None, str | None, str | None, int | None, str]:
    if provider is None or selected is None:
        return None, None, None, None, "no_provider" if provider is None else "no_candidate"

    prompt = _build_synthesis_prompt(
        run_id=run_id,
        candidates=candidates,
        evidence_records=evidence_records,
        evidence_count=evidence_count,
        quarantined_count=quarantined_count,
        top_evidence=top_evidence,
        source_counts=source_counts,
    )
    try:
        raw_response = provider.complete_json(prompt=prompt, evidence_packets=())
        payload = _json_from_llm_response(raw_response)
        synthesis = LlmMvpSynthesis.model_validate(payload)
    except Exception:
        LOGGER.warning(
            "MVP weekly LLM synthesis failed; falling back to deterministic report",
            exc_info=True,
        )
        return None, None, None, None, "fallback_deterministic"

    llm_selected_title = _optional_non_empty(synthesis.selected_title)
    recommendation = _optional_non_empty(synthesis.recommendation)
    score = synthesis.score
    gate_candidate = _candidate_for_title(llm_selected_title, candidates)
    if gate_candidate is None:
        if llm_selected_title:
            LOGGER.warning(
                "MVP weekly LLM selected title not found in shortlist; "
                "using deterministic candidate title=%r",
                llm_selected_title,
            )
        gate_candidate = selected
    selected_title = gate_candidate.title
    recommendation, score, gate_notes = _apply_synthesis_gates(
        candidate=gate_candidate,
        recommendation=recommendation,
        score=score,
        source_counts=source_counts,
    )
    display_candidate = _candidate_with_gated_result(
        gate_candidate,
        recommendation=recommendation,
        score=score,
    )
    display_candidates = _replace_candidate_in_list(
        candidates,
        selected=gate_candidate,
        replacement=display_candidate,
    )

    markdown = synthesis.markdown.strip()
    if not markdown.startswith("#"):
        markdown = f"# MVP of the Week: {selected_title}\n\n{markdown}"
    markdown = _canonicalize_synthesis_markdown(
        markdown,
        selected=display_candidate,
        candidates=display_candidates,
        source_counts=source_counts,
        top_evidence=top_evidence,
    )
    if gate_notes:
        markdown = _append_gate_notes(markdown, gate_notes)
    markdown = _append_report_quality_sections(
        markdown,
        source_counts=source_counts,
        selected=display_candidate,
        candidates=display_candidates,
    )
    markdown = _remove_failed_gate_build_claims(markdown, selected=display_candidate)
    return (
        markdown.rstrip() + "\n",
        selected_title,
        recommendation,
        score,
        "llm_synthesized",
    )


def _build_synthesis_prompt(
    *,
    run_id: str,
    candidates: list[CandidateAggregate],
    evidence_records: tuple[EvidenceRecord, ...],
    evidence_count: int,
    quarantined_count: int,
    top_evidence: int,
    source_counts: dict[str, object],
) -> str:
    candidate_lines = []
    for index, candidate in enumerate(candidates, start=1):
        external_types = ", ".join(_matched_external_source_types(candidate)) or "none"
        kir_state = _kir_gate_state(candidate)
        candidate_lines.append(
            f"{index}. {candidate.title} | score={candidate.score} | "
            f"recommendation={candidate.recommendation} | "
            f"surfaces={', '.join(sorted(candidate.surfaces)) or 'unknown'} | "
            f"evidence_count={len(candidate.evidence)} | "
            f"external_source_types={external_types} | "
            f"kir_gate={kir_state.get('kir_gate_status')} | "
            f"kir_thread={kir_state.get('kir_thread_slug') or 'none'} | "
            f"profile_fit={', '.join(sorted(candidate.profile_fit_flags)) or 'weak'} | "
            f"profile_mismatch={', '.join(sorted(candidate.profile_mismatch_flags)) or 'none'} | "
            f"risks={', '.join(sorted(candidate.risk_flags)) or 'none'}"
        )
    evidence_lines = []
    for index, record in enumerate(_rank_evidence_for_prompt(evidence_records)[:24], start=1):
        citation = f"E{index}"
        date = record.captured_at.date().isoformat()
        title = _truncate(record.title, 120)
        snippet = _truncate(record.snippet or record.normalized_text, 420)
        metadata = _compact_metadata(record.provider_metadata)
        evidence_lines.append(
            f"[{citation}] source={record.source_type}; date={date}; "
            f"title={title}; snippet={snippet}; "
            f"url={record.source_url or 'none'}; metadata={metadata}"
        )

    prompt_lines = [
        "You are writing Demand-to-MVP Radar's weekly Candidate Dossier.",
        "",
        ("This artifact is NOT a technical implementation-ideas brief for existing repositories."),
        (
            "Its job is to choose one candidate and say whether it is build-ready, "
            "a focused experiment, an investigation, or a rejection."
        ),
        (
            "Telegram Research Agent evidence is only a seed layer. Treat public "
            "source, competitor, workaround, repeated-question, store/category, "
            "and search-intent evidence as stronger validation."
        ),
        (
            "A focused_experiment recommendation requires at least two non-Telegram "
            "evidence packets from at least two independent external source types "
            "for the selected MVP. If that gate is not met, use "
            "revisit_with_evidence_gap or needs_more_evidence."
        ),
        (
            "If the selected candidate includes Telegram Research Agent seed evidence, "
            "build or focused_experiment also requires fresh Knowledge Thread "
            "provenance with source_atom_ids and source_urls. If the KIR gate is not "
            "passed, use revisit_with_evidence_gap or needs_more_evidence."
        ),
        (
            "If evidence is thin, choose revisit_with_evidence_gap instead of "
            "pretending build confidence."
        ),
        (
            "The idea must fit the operator: Python/FastAPI/Telegram/LLM workflows, "
            "evaluation, guardrails, knowledge systems, decision support, education "
            "and rollout are strong fits. Java/JVM, mobile-native, CMS-plugin, or "
            "unfamiliar domain-heavy ideas should be downgraded unless the MVP can "
            "be tested as a thin Python/API workflow."
        ),
        (
            "Do not recommend building a broad platform. Keep the MVP to one "
            "function that can be tested in 7 days."
        ),
        (
            "Do not make revenue, investment, trading, legal, medical, or "
            "platform-terms claims unless the evidence explicitly supports them."
        ),
        "",
        f"Run ID: {run_id}",
        f"Evidence count: {evidence_count}",
        f"Quarantined seed rows: {quarantined_count}",
        f"Source counts: {json.dumps(source_counts, ensure_ascii=False, sort_keys=True)}",
        "",
        "Context-only market lens:",
        *_market_context_prompt_lines(source_counts),
        "",
        "Operator fit profile:",
        _load_operator_profile(),
        "",
        "Deterministic candidate shortlist:",
        *(candidate_lines or ["No deterministic candidates."]),
        "",
        f"Evidence packets for synthesis, cite as [E1]..[E{min(24, len(evidence_records))}]:",
        *(evidence_lines or ["No evidence packets."]),
        "",
        "Return strict JSON with this shape:",
        "{",
        '  "selected_title": "short product title or null",',
        (
            '  "recommendation": "focused_experiment | revisit_with_evidence_gap | '
            'needs_more_evidence | reject",'
        ),
        '  "score": 0,',
        '  "markdown": "# Candidate Dossier: ...\\n\\n## Why This Candidate\\n...\\n"',
        "}",
        "",
        "Markdown requirements:",
        (
            "- Include sections: Why This Candidate, Source Mix, Decision Gate, "
            "Market Context Lens, KIR Evidence, Live Source Intelligence, Source Trust "
            "And Repeated Signals, Build-Worthy Recommendations, Interesting Signals, "
            "Validation Query Pack, Matched External Evidence, Operator Fit, "
            "One-Function MVP, Evidence, Missing Evidence, Risks, Next Experiment, "
            "Kill Criteria, Anti-Complexity Guardrail."
        ),
        "- Evidence section must cite only provided evidence IDs like [E1].",
        "- Market Context Lens is context only and must not be cited as validation evidence.",
        (
            "- Source Mix must explicitly say whether the selected idea is supported "
            "by Telegram only or by external sources such as SERP, Reddit, GitHub, "
            "HN/RSS, Product Hunt, YouTube, stores, or forums."
        ),
        (
            "- Operator Fit must say why this MVP matches or mismatches the "
            "operator's stack and professional identity."
        ),
        f"- Show at most {top_evidence} primary evidence bullets.",
        ("- Explain why the selected MVP is separate from existing repo implementation upgrades."),
        "- Use Russian language.",
    ]
    return "\n".join(prompt_lines)


def _rank_evidence_for_prompt(records: tuple[EvidenceRecord, ...]) -> list[EvidenceRecord]:
    priority = {
        "serp": 0,
        "github_public": 1,
        "stack_exchange": 2,
        "reddit": 3,
        "product_hunt": 4,
        "youtube": 5,
        "rss": 6,
        "telegram_research_agent": 7,
        "github_repo": 8,
    }
    return sorted(
        records,
        key=lambda record: (
            priority.get(record.source_type, 9),
            -_metadata_score(record),
            record.captured_at,
        ),
    )


def _metadata_score(record: EvidenceRecord) -> int:
    score = 0
    bucket = _metadata_text(record.provider_metadata, "bucket") or ""
    score += BUCKET_WEIGHTS.get(bucket, 0)
    score += len(_metadata_list(record.provider_metadata, "demand_surfaces")) * 3
    if record.source_url:
        score += 2
    return score


def _json_from_llm_response(raw_response: str) -> dict[str, Any]:
    text = raw_response.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    decoded = json.loads(text)
    if not isinstance(decoded, dict):
        raise ValueError("MVP synthesis response must be a JSON object")
    return decoded


def _provider_model(provider: LLMProvider | None) -> str | None:
    model = getattr(provider, "model", None)
    return str(model) if model else None


def _optional_non_empty(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _candidate_for_title(
    title: str | None,
    candidates: list[CandidateAggregate],
) -> CandidateAggregate | None:
    if not title:
        return None
    normalized = _normalize_key(title)
    for candidate in candidates:
        if candidate.key == normalized or _normalize_key(candidate.title) == normalized:
            return candidate
    return None


def _candidate_with_gated_result(
    candidate: CandidateAggregate | None,
    *,
    recommendation: str | None,
    score: int | None,
) -> CandidateAggregate | None:
    if candidate is None:
        return None
    cloned = replace(
        candidate,
        evidence=list(candidate.evidence),
        surfaces=set(candidate.surfaces),
        channels=set(candidate.channels),
        missing_evidence=set(candidate.missing_evidence),
        risk_flags=set(candidate.risk_flags),
        mvp_scopes=list(candidate.mvp_scopes),
        anti_complexity_notes=list(candidate.anti_complexity_notes),
        profile_fit_flags=set(candidate.profile_fit_flags),
        profile_mismatch_flags=set(candidate.profile_mismatch_flags),
    )
    if recommendation:
        cloned.recommendation = recommendation
    if score is not None:
        cloned.score = score
    return cloned


def _replace_candidate_in_list(
    candidates: list[CandidateAggregate],
    *,
    selected: CandidateAggregate | None,
    replacement: CandidateAggregate | None,
) -> list[CandidateAggregate]:
    if selected is None or replacement is None:
        return list(candidates)
    return [
        replacement if candidate.key == selected.key else copy.copy(candidate)
        for candidate in candidates
    ]


def _canonicalize_synthesis_markdown(
    markdown: str,
    *,
    selected: CandidateAggregate,
    candidates: list[CandidateAggregate],
    source_counts: dict[str, object],
    top_evidence: int,
) -> str:
    markdown = _replace_top_recommendation_block(markdown, selected=selected)
    markdown = _replace_or_append_markdown_section(
        markdown,
        "Why This Candidate",
        [_why_this_week(selected)],
    )
    markdown = _replace_or_append_markdown_section(
        markdown,
        "Source Mix",
        [_source_mix_summary(source_counts, selected=selected)],
    )
    markdown = _replace_or_append_markdown_section(
        markdown,
        "Validation Query Pack",
        _validation_query_pack_lines(selected),
    )
    markdown = _replace_or_append_markdown_section(
        markdown,
        "Matched External Evidence",
        _matched_external_evidence_lines(selected),
    )
    markdown = _replace_or_append_markdown_section(
        markdown,
        "What Would Change The Decision",
        _decision_change_action_lines(selected),
    )
    markdown = _replace_or_append_markdown_section(
        markdown,
        "Market Context Lens",
        _market_context_lines(source_counts),
    )
    markdown = _replace_or_append_markdown_section(
        markdown,
        "KIR Evidence",
        _kir_evidence_lines(selected),
    )
    markdown = _replace_or_append_markdown_section(
        markdown,
        "Live Source Intelligence",
        _live_intelligence_lines(source_counts),
    )
    markdown = _replace_or_append_markdown_section(
        markdown,
        "Decision Gate",
        _decision_gate_summary(source_counts, selected=selected).splitlines(),
    )
    markdown = _replace_or_append_markdown_section(
        markdown,
        "Evidence",
        _evidence_lines(selected, top_evidence=top_evidence),
    )
    markdown = _replace_or_append_markdown_section(
        markdown,
        "Missing Evidence",
        _prefixed_lines(
            sorted(selected.missing_evidence)
            or ["pricing or willingness-to-pay signal", "competitor comparison"],
        ),
    )
    markdown = _replace_or_append_markdown_section(
        markdown,
        "Next Experiment",
        _next_experiment_lines(selected),
    )
    markdown = _replace_or_append_markdown_section(
        markdown,
        "Kill Criteria",
        _kill_criteria_lines(selected),
    )
    markdown = _replace_or_append_markdown_section(
        markdown,
        "Operator Fit",
        [_operator_fit_summary(selected)],
    )
    markdown = _replace_or_append_markdown_section(
        markdown,
        "Anti-Complexity Guardrail",
        [_anti_complexity_guardrail(selected)],
    )
    markdown = _replace_or_append_markdown_section(
        markdown,
        "Build-Worthy Recommendations",
        _build_worthy_lines(candidates),
    )
    return markdown


def _replace_top_recommendation_block(markdown: str, *, selected: CandidateAggregate) -> str:
    lines = markdown.rstrip().splitlines()
    if not lines:
        return markdown
    title = f"# Candidate Dossier: {selected.title}"
    body: list[str] = []
    index = 1
    while index < len(lines) and not lines[index].startswith("## "):
        line = lines[index]
        if re.match(
            r"^\s*(status|decision|confidence|next action|recommendation|score)\s*:",
            line,
            flags=re.IGNORECASE,
        ):
            index += 1
            continue
        if line.strip() or body:
            body.append(line)
        index += 1

    top_block = [
        title,
        "",
        f"Status: {_dossier_status(selected)}",
        f"Decision: {_dossier_decision(selected)}",
        f"Confidence: {_dossier_confidence(selected)}",
        f"Next action: {_dossier_next_action(selected)}",
        f"Recommendation: **{selected.recommendation}**",
        f"Score: {selected.score}/100",
    ]
    if body:
        top_block.extend(["", *body])
    if index < len(lines):
        top_block.extend(["", *lines[index:]])
    return "\n".join(top_block).strip() + "\n"


def _replace_or_append_markdown_section(
    markdown: str,
    heading: str,
    body_lines: list[str],
) -> str:
    heading_line = f"## {heading}"
    lines = markdown.rstrip().splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line.strip().lower() == heading_line.lower()),
        None,
    )
    replacement = [heading_line, "", *body_lines]
    if start is None:
        return "\n".join([*lines, "", *replacement]).strip() + "\n"
    end = next(
        (index for index in range(start + 1, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    return "\n".join([*lines[:start], *replacement, "", *lines[end:]]).strip() + "\n"


def _apply_synthesis_gates(
    *,
    candidate: CandidateAggregate,
    recommendation: str | None,
    score: int | None,
    source_counts: dict[str, object],
) -> tuple[str | None, int | None, list[str]]:
    notes: list[str] = []
    normalized_recommendation = (recommendation or "").strip().lower()
    gated_recommendation = recommendation
    gated_score = score

    if normalized_recommendation in RECOMMENDATION_GATED:
        kir_state = _kir_gate_state(candidate)
        if str(kir_state.get("kir_gate_status")) not in KIR_GATE_PASSING_STATUSES:
            gated_recommendation = "revisit_with_evidence_gap"
            gated_score = min(gated_score if gated_score is not None else candidate.score, 64)
            reasons = _string_list(kir_state.get("kir_gate_reasons"))
            notes.append(
                "Downgraded from focused_experiment because the selected Telegram-seeded "
                "candidate failed the KIR gate: "
                f"{_join_or_none(reasons)}."
            )
        if not _has_decision_grade_external_evidence(candidate):
            gated_recommendation = "revisit_with_evidence_gap"
            gated_score = min(gated_score if gated_score is not None else candidate.score, 64)
            notes.append(
                "Downgraded from focused_experiment because the selected candidate "
                "does not yet have two independent non-Telegram evidence sources."
            )
        if _has_blocking_gap(candidate):
            gated_recommendation = "needs_more_evidence"
            gated_score = min(gated_score if gated_score is not None else candidate.score, 49)
            notes.append(
                "Downgraded because the selected candidate has blocking risk flags "
                "that must be resolved before a build or focused experiment."
            )
        if _has_profile_blocking_mismatch(candidate):
            gated_recommendation = "needs_more_evidence"
            gated_score = min(gated_score if gated_score is not None else candidate.score, 49)
            notes.append(
                "Downgraded because the selected candidate currently mismatches the "
                "operator profile and needs a closer Python/LLM workflow wedge."
            )

    if not _source_mix_has_any_external(source_counts):
        notes.append(
            "Run-level source mix warning: this report is dominated by Telegram "
            "seeds; SERP/Reddit/GitHub/store evidence was not available in this run."
        )
    return gated_recommendation, gated_score, notes


def _append_gate_notes(markdown: str, gate_notes: list[str]) -> str:
    lines = [markdown.rstrip(), "", "## Source Mix Gate", ""]
    lines.extend(f"- {note}" for note in gate_notes)
    return "\n".join(lines)


def _append_report_quality_sections(
    markdown: str,
    *,
    source_counts: dict[str, object],
    selected: CandidateAggregate,
    candidates: list[CandidateAggregate],
) -> str:
    existing = markdown.lower()
    lines = [markdown.rstrip()]
    if "## decision gate" not in existing:
        lines.extend(
            [
                "",
                "## Decision Gate",
                "",
                _decision_gate_summary(source_counts, selected=selected),
            ]
        )
    if "## source trust and repeated signals" not in existing:
        lines.extend(
            [
                "",
                "## Source Trust And Repeated Signals",
                "",
                *_source_trust_lines(source_counts),
            ]
        )
    if "## validation query pack" not in existing:
        lines.extend(
            [
                "",
                "## Validation Query Pack",
                "",
                *_validation_query_pack_lines(selected),
            ]
        )
    if "## matched external evidence" not in existing:
        lines.extend(
            [
                "",
                "## Matched External Evidence",
                "",
                *_matched_external_evidence_lines(selected),
            ]
        )
    if "## kir evidence" not in existing:
        lines.extend(["", "## KIR Evidence", "", *_kir_evidence_lines(selected)])
    if "## build-worthy recommendations" not in existing:
        lines.extend(
            [
                "",
                "## Build-Worthy Recommendations",
                "",
                *_build_worthy_lines(candidates),
            ]
        )
    if "## interesting signals" not in existing:
        lines.extend(["", "## Interesting Signals", "", *_interesting_signal_lines(candidates)])
    return "\n".join(lines)


def _remove_failed_gate_build_claims(markdown: str, *, selected: CandidateAggregate) -> str:
    if selected.recommendation in RECOMMENDATION_GATED:
        return markdown
    forbidden_phrases = (
        "ready to build now",
        "build now",
        "gate passed",
        "decision gate passed",
        "recommendation allowed: yes",
        "reason: focused_experiment",
        "status: build",
        "recommendation: **focused_experiment**",
    )
    lines: list[str] = []
    removed = False
    for line in markdown.splitlines():
        normalized = line.lower()
        if any(phrase in normalized for phrase in forbidden_phrases):
            removed = True
            continue
        lines.append(line)
    if removed and "## Gate Notes" not in markdown:
        lines.extend(
            [
                "",
                "## Gate Notes",
                "",
                "- Removed contradictory build-ready claim because source gates failed.",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def _source_mix_has_any_external(source_counts: dict[str, object]) -> bool:
    count = source_counts.get("external_evidence_count")
    try:
        return int(count) > 0
    except (TypeError, ValueError):
        return False


def _load_operator_profile() -> str:
    env_path = os.environ.get(OPERATOR_PROFILE_ENV, "").strip()
    profile_path = (
        Path(env_path) if env_path else _repo_root() / "config" / "operator_fit_profile.md"
    )
    if not profile_path.is_absolute():
        profile_path = Path.cwd() / profile_path
    if not profile_path.exists():
        return (
            "No operator profile file found. Prefer Python/LLM workflow, research, "
            "evaluation, guardrail, knowledge, automation, and education-adoption MVPs."
        )
    return profile_path.read_text(encoding="utf-8").strip()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _truncate(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def _compact_metadata(metadata: dict[str, str]) -> str:
    keys = (
        "channel_username",
        "bucket",
        "demand_signal_type",
        "demand_surfaces",
        "knowledge_thread_slug",
        "knowledge_thread_status",
        "source_atom_ids",
        "source_kind",
        "source_urls",
        "mvp_shape",
        "verification_needed",
    )
    compact = {key: value for key, value in metadata.items() if key in keys and value}
    return json.dumps(compact, ensure_ascii=False, sort_keys=True)


def _score_candidate(candidate: CandidateAggregate) -> int:
    score = 18
    score += min(len(candidate.evidence) * 8, 24)
    score += min(len(candidate.channels) * 4, 12)
    score += min(sum(SURFACE_WEIGHTS.get(surface, 6) for surface in candidate.surfaces), 28)
    score += min(_bucket_bonus(candidate.evidence), 18)
    score += min(_matched_external_count(candidate) * 6, 18)
    score += min(len(_matched_external_source_types(candidate)) * 6, 18)
    score += min(len(candidate.profile_fit_flags) * 5, 15)
    if candidate.mvp_scopes:
        score += 8
    if any(record.source_url for record in candidate.evidence):
        score += 6
    score -= min(len(candidate.risk_flags) * 8, 24)
    score -= min(len(candidate.profile_mismatch_flags) * 12, 36)
    if _matched_external_count(candidate) == 0:
        score -= 14
    if _has_blocking_gap(candidate):
        score -= 12
    if _has_profile_blocking_mismatch(candidate):
        score -= 16
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


def _has_decision_grade_external_evidence(candidate: CandidateAggregate) -> bool:
    return (
        _matched_external_count(candidate) >= 2
        and len(_matched_external_source_types(candidate)) >= 2
    )


def _kir_gate_allows_candidate(
    candidate: CandidateAggregate,
    *,
    as_of: datetime | None = None,
) -> bool:
    state = _kir_gate_state(candidate, as_of=as_of)
    return str(state.get("kir_gate_status")) in KIR_GATE_PASSING_STATUSES


def _kir_gate_missing_evidence(
    candidate: CandidateAggregate,
    *,
    as_of: datetime | None = None,
) -> tuple[str, ...]:
    state = _kir_gate_state(candidate, as_of=as_of)
    if str(state.get("kir_gate_status")) in KIR_GATE_PASSING_STATUSES:
        return ()
    reasons = state.get("kir_gate_reasons")
    if isinstance(reasons, tuple | list):
        return tuple(str(reason) for reason in reasons if str(reason).strip())
    if isinstance(reasons, str) and reasons.strip():
        return (reasons.strip(),)
    return ("fresh KIR Knowledge Thread evidence with source atoms and source URLs",)


def _kir_gate_state(
    candidate: CandidateAggregate,
    *,
    as_of: datetime | None = None,
) -> dict[str, object]:
    telegram_records = [
        record for record in candidate.evidence if record.source_type == "telegram_research_agent"
    ]
    kir_required = bool(telegram_records)
    kir_records = [
        record for record in telegram_records if _kir_source_kind(record) == "knowledge_thread"
    ]
    selected_record = kir_records[0] if kir_records else None
    atom_ids = _kir_source_atom_ids(kir_records)
    source_urls = _kir_source_urls(kir_records)
    has_fresh_thread = any(
        _kir_record_has_fresh_thread(record, as_of=as_of) for record in kir_records
    )
    blockers: list[tuple[str, str]] = []

    if kir_required:
        if not kir_records:
            blockers.append(("missing_kir_thread", "fresh KIR Knowledge Thread evidence"))
        elif not has_fresh_thread:
            blockers.append(("stale_kir_thread", "fresh KIR Knowledge Thread evidence"))
        if kir_records and not atom_ids:
            blockers.append(("missing_source_atoms", "KIR source atom IDs"))
        if kir_records and not source_urls:
            blockers.append(("missing_source_urls", "KIR source URLs"))
        if not _has_decision_grade_external_evidence(candidate):
            blockers.append(
                (
                    "missing_decision_grade_external_evidence",
                    "two independent non-Telegram evidence sources",
                )
            )
        if _has_blocking_gap(candidate):
            blockers.append(("blocking_risk", "no blocking risk flags"))
        if _has_profile_blocking_mismatch(candidate):
            blockers.append(("profile_mismatch", "operator-fit wedge without profile mismatch"))
        elif not _has_operator_fit(candidate):
            blockers.append(("missing_operator_fit", "positive operator fit signal"))

    status = "not_required"
    if kir_required:
        status = blockers[0][0] if blockers else "passed"

    return {
        "kir_required": kir_required,
        "kir_source_kind": _kir_source_kind(selected_record) if selected_record else None,
        "kir_thread_slug": (
            _metadata_text(selected_record.provider_metadata, "knowledge_thread_slug")
            if selected_record
            else None
        ),
        "kir_thread_title": (
            _metadata_text(selected_record.provider_metadata, "knowledge_thread_title")
            if selected_record
            else None
        ),
        "kir_thread_status": _metadata_text(
            selected_record.provider_metadata,
            "knowledge_thread_status",
        )
        if selected_record
        else None,
        "kir_source_atom_count": len(atom_ids),
        "kir_source_url_count": len(source_urls),
        "kir_has_fresh_thread": has_fresh_thread,
        "kir_gate_status": status,
        "kir_gate_reasons": tuple(reason for _status, reason in blockers),
    }


def _kir_source_kind(record: EvidenceRecord | None) -> str | None:
    if record is None:
        return None
    return _metadata_text(record.provider_metadata, "source_kind")


def _kir_source_atom_ids(records: list[EvidenceRecord]) -> tuple[str, ...]:
    atom_ids: list[str] = []
    for record in records:
        for atom_id in _metadata_list(record.provider_metadata, "source_atom_ids"):
            if atom_id not in atom_ids:
                atom_ids.append(atom_id)
    return tuple(atom_ids)


def _kir_source_urls(records: list[EvidenceRecord]) -> tuple[str, ...]:
    urls: list[str] = []
    for record in records:
        for url in _metadata_list(record.provider_metadata, "source_urls"):
            if url not in urls:
                urls.append(url)
        if record.source_url and record.source_url not in urls:
            urls.append(record.source_url)
    return tuple(urls)


def _kir_record_has_fresh_thread(
    record: EvidenceRecord,
    *,
    as_of: datetime | None = None,
) -> bool:
    if _kir_source_kind(record) != "knowledge_thread":
        return False
    status = (_metadata_text(record.provider_metadata, "knowledge_thread_status") or "").lower()
    if not status or status in STALE_KIR_THREAD_STATUSES:
        return False
    current = as_of or datetime.now(UTC)
    age_days = max((_to_utc(current) - _to_utc(record.captured_at)).days, 0)
    return age_days <= KIR_FRESHNESS_DAYS


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _has_operator_fit(candidate: CandidateAggregate) -> bool:
    return bool(candidate.profile_fit_flags) and not _has_profile_blocking_mismatch(candidate)


def _has_profile_blocking_mismatch(candidate: CandidateAggregate) -> bool:
    return bool(candidate.profile_mismatch_flags) and not (
        candidate.profile_fit_flags & PROFILE_STACK_FIT_FLAGS
    )


def _external_evidence_count(records: tuple[EvidenceRecord, ...] | list[EvidenceRecord]) -> int:
    return sum(1 for record in records if record.source_type in EXTERNAL_DEMAND_SOURCE_TYPES)


def _external_source_types(
    records: tuple[EvidenceRecord, ...] | list[EvidenceRecord],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                record.source_type
                for record in records
                if record.source_type in EXTERNAL_DEMAND_SOURCE_TYPES
            }
        )
    )


def _profile_fit_flags(text: str) -> set[str]:
    return {label for keyword, label in PROFILE_FIT_KEYWORDS if keyword in text}


def _profile_mismatch_flags(text: str) -> set[str]:
    return {label for keyword, label in PROFILE_MISMATCH_KEYWORDS if keyword in text}


def _is_existing_project(title: str) -> bool:
    return title.strip().lower() in EXISTING_PROJECT_TITLES


def _is_generic_candidate(title: str) -> bool:
    normalized = title.strip().lower()
    return normalized in GENERIC_CANDIDATE_TITLES or normalized.startswith("opportunity probe:")


def _dossier_status(candidate: CandidateAggregate) -> str:
    recommendation = candidate.recommendation
    if recommendation == "build":
        return "build"
    if recommendation == "focused_experiment":
        return "focused_experiment"
    if recommendation in {
        "revisit_with_evidence_gap",
        "needs_more_specific_scope",
        "existing_project_context",
    }:
        return "investigate"
    if recommendation == "needs_more_evidence":
        if candidate.score < 40 or _has_blocking_gap(candidate):
            return "reject"
        return "investigate"
    if recommendation == "reject":
        return "reject"
    return "investigate"


def _dossier_confidence(candidate: CandidateAggregate) -> str:
    status = _dossier_status(candidate)
    if status == "build":
        return "high"
    if status == "focused_experiment":
        return "medium"
    if status == "investigate":
        return "low"
    return "insufficient"


def _dossier_decision(candidate: CandidateAggregate) -> str:
    status = _dossier_status(candidate)
    if candidate.recommendation == "existing_project_context":
        return "Apply this to an existing project/backlog; do not frame it as a standalone new MVP."
    if status == "build":
        return "Evidence is strong enough to build the narrow MVP."
    if status == "focused_experiment":
        return "Run a focused one-week experiment before committing to a build."
    if status == "investigate":
        return "Investigate missing evidence before treating this as build-ready."
    return "Reject or park this candidate until evidence changes."


def _dossier_next_action(candidate: CandidateAggregate) -> str:
    if candidate.recommendation == "existing_project_context":
        return "Open the related existing repo/backlog and attach the evidence as project context."
    status = _dossier_status(candidate)
    if status in {"build", "focused_experiment"}:
        return (
            "Run the next experiment below and record build/revisit/reject at the end of the week."
        )
    if status == "investigate":
        return "Collect the missing source evidence listed below before building."
    return "Do not build; revisit only if a new independent source appears."


def _evidence_lines(candidate: CandidateAggregate, *, top_evidence: int) -> list[str]:
    if not candidate.evidence:
        return ["- No evidence rows available for this candidate."]
    return [
        _render_evidence_line(index, record)
        for index, record in enumerate(candidate.evidence[:top_evidence], start=1)
    ]


def _next_experiment_lines(candidate: CandidateAggregate) -> list[str]:
    return [f"{index}. {step}" for index, step in enumerate(_next_experiment(candidate), start=1)]


def _next_experiment(candidate: CandidateAggregate) -> list[str]:
    if candidate.recommendation == "existing_project_context":
        return [
            "Attach this evidence to the existing project as context.",
            "Identify one current backlog item that becomes clearer because of the signal.",
            "Decide whether to update, defer, or reject that backlog item.",
        ]
    if _dossier_status(candidate) == "reject":
        return [
            "Do not start an experiment this week.",
            "Watch for an independent public source that changes the evidence state.",
        ]
    return [
        "Pick 3-5 public examples that match the evidence pattern.",
        "Produce one static artifact or concierge workflow, not a platform.",
        "Show before/after value in a copyable report.",
        "Ask 5 relevant operators or creators whether they would use or pay for it.",
        "End with build/revisit/reject and write the decision back to memory.",
    ]


def _kill_criteria_lines(candidate: CandidateAggregate) -> list[str]:
    return [f"- {criterion}" for criterion in _kill_criteria(candidate)]


def _kill_criteria(candidate: CandidateAggregate) -> list[str]:
    criteria = [
        "No second independent non-Telegram source supports the same pain.",
        "Users describe curiosity but no repeated workaround, budget, or urgency.",
        "The only plausible implementation expands into a broad platform.",
    ]
    if candidate.recommendation == "existing_project_context":
        criteria.append("The signal cannot be tied to a concrete existing-project backlog change.")
    if candidate.risk_flags:
        criteria.append(
            "Risk flags remain unresolved: " + ", ".join(sorted(candidate.risk_flags)) + "."
        )
    return criteria


def _anti_complexity_guardrail(candidate: CandidateAggregate) -> str:
    return _first_or_default(
        candidate.anti_complexity_notes,
        "Do not build a platform. Build one proof artifact and one operator-facing report.",
    )


def _render_report(
    *,
    run_id: str,
    selected: CandidateAggregate | None,
    candidates: list[CandidateAggregate],
    evidence_count: int,
    quarantined_count: int,
    top_evidence: int,
    source_counts: dict[str, object],
) -> str:
    generated_at = datetime.now(UTC).isoformat()
    if selected is None:
        return (
            "\n".join(
                [
                    "# Candidate Dossier",
                    "",
                    "Status: reject",
                    "Decision: No usable opportunity seeds were available this week.",
                    "Confidence: insufficient",
                    (
                        "Next action: Check ingestion and source collection "
                        "before considering candidates."
                    ),
                    "",
                    f"Generated: {generated_at}",
                    f"Run ID: {run_id}",
                    "",
                    f"Imported evidence: {evidence_count}; quarantined rows: {quarantined_count}.",
                    "",
                    "## Source Mix",
                    "",
                    _source_mix_summary(source_counts),
                    "",
                    "## Validation Query Pack",
                    "",
                    *_validation_query_pack_lines(None),
                    "",
                    "## Matched External Evidence",
                    "",
                    *_matched_external_evidence_lines(None),
                    "",
                    "## What Would Change The Decision",
                    "",
                    *_decision_change_action_lines(None),
                    "",
                    "## Market Context Lens",
                    "",
                    *_market_context_lines(source_counts),
                    "",
                    "## KIR Evidence",
                    "",
                    "- KIR gate: not_required",
                    "",
                    "## Live Source Intelligence",
                    "",
                    *_live_intelligence_lines(source_counts),
                ]
            )
            + "\n"
        )

    lines = [
        f"# Candidate Dossier: {selected.title}",
        "",
        f"Status: {_dossier_status(selected)}",
        f"Decision: {_dossier_decision(selected)}",
        f"Confidence: {_dossier_confidence(selected)}",
        f"Next action: {_dossier_next_action(selected)}",
        f"Recommendation: **{selected.recommendation}**",
        f"Score: {selected.score}/100",
        "",
        f"Generated: {generated_at}",
        f"Run ID: {run_id}",
        f"Imported evidence: {evidence_count}; quarantined rows: {quarantined_count}.",
        "",
        "## Why This Candidate",
        "",
        _why_this_week(selected),
        "",
        "## Source Mix",
        "",
        _source_mix_summary(source_counts, selected=selected),
        "",
        "## Validation Query Pack",
        "",
        *_validation_query_pack_lines(selected),
        "",
        "## Matched External Evidence",
        "",
        *_matched_external_evidence_lines(selected),
        "",
        "## What Would Change The Decision",
        "",
        *_decision_change_action_lines(selected),
        "",
        "## Market Context Lens",
        "",
        *_market_context_lines(source_counts),
        "",
        "## KIR Evidence",
        "",
        *_kir_evidence_lines(selected),
        "",
        "## Live Source Intelligence",
        "",
        *_live_intelligence_lines(source_counts),
        "",
        "## Decision Gate",
        "",
        _decision_gate_summary(source_counts, selected=selected),
        "",
        "## Source Trust And Repeated Signals",
        "",
        *_source_trust_lines(source_counts),
        "",
        "## Evidence",
        "",
        *_evidence_lines(selected, top_evidence=top_evidence),
        "",
        "## Missing Evidence",
        "",
        *_prefixed_lines(
            sorted(selected.missing_evidence)
            or ["pricing or willingness-to-pay signal", "competitor comparison"],
        ),
        "",
        "## Next Experiment",
        "",
        *_next_experiment_lines(selected),
        "",
        "## Kill Criteria",
        "",
        *_kill_criteria_lines(selected),
        "",
        "## Operator Fit",
        "",
        _operator_fit_summary(selected),
        "",
        "## One-Function MVP",
        "",
        _first_or_default(
            selected.mvp_scopes,
            f"Build the smallest artifact that proves demand for {selected.title}.",
        ),
        "",
        "## Anti-Complexity Guardrail",
        "",
        _anti_complexity_guardrail(selected),
        "",
        "## Build-Worthy Recommendations",
        "",
        *_build_worthy_lines(candidates),
        "",
        "## Interesting Signals",
        "",
        *_interesting_signal_lines(candidates),
        "",
    ]

    lines.extend(
        [
            "## Risk Flags",
            "",
            *_prefixed_lines(
                sorted(selected.risk_flags) or ["No explicit risk flags in the seeds."]
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


def _source_mix_summary(
    source_counts: dict[str, object],
    *,
    selected: CandidateAggregate | None = None,
) -> str:
    return "\n".join(_source_mix_card_lines(source_counts, selected=selected))


def _validation_query_pack(selected: CandidateAggregate | None) -> dict[str, object] | None:
    if selected is None:
        return None
    return build_validation_query_pack(
        candidate_title=selected.title,
        surfaces=selected.surfaces,
        missing_evidence=selected.missing_evidence,
    )


def _matched_external_evidence(selected: CandidateAggregate | None) -> list[dict[str, object]]:
    if selected is None:
        return []
    return match_external_evidence(
        candidate_title=selected.title,
        records=selected.evidence,
        external_source_types=EXTERNAL_DEMAND_SOURCE_TYPES,
    )


def _matched_external_count(selected: CandidateAggregate) -> int:
    return decision_grade_match_count(_matched_external_evidence(selected))


def _matched_external_source_types(selected: CandidateAggregate) -> tuple[str, ...]:
    return matched_external_source_types(_matched_external_evidence(selected))


def _matched_external_records(selected: CandidateAggregate) -> list[EvidenceRecord]:
    fingerprints = matched_external_fingerprints(_matched_external_evidence(selected))
    return [record for record in selected.evidence if record.source_fingerprint in fingerprints]


def _validation_query_pack_lines(selected: CandidateAggregate | None) -> list[str]:
    pack = _validation_query_pack(selected)
    if pack is None:
        return [
            "- Planner: deterministic_rve_query_planner",
            "- Live API calls: false",
            "- Status: no selected candidate, so no candidate-specific queries.",
        ]
    lines = [
        "- Planner: deterministic_rve_query_planner",
        "- Live API calls: false",
        (
            "- Gate rule: planned queries do not satisfy gates until matched "
            "external evidence is attached to this candidate."
        ),
    ]
    next_query = _object_dict(pack.get("next_query"))
    if next_query:
        lines.append(f"- Next query: {next_query.get('query')} ({next_query.get('intent')})")
    queries_by_intent = pack.get("queries_by_intent")
    if not isinstance(queries_by_intent, dict):
        return lines
    intent_order = (
        "search_demand",
        "manual_workarounds",
        "competitors",
        "wtp_signals",
        "reddit_forum_complaints",
        "github_discussions",
        "x_discussions",
    )
    for intent in intent_order:
        records = queries_by_intent.get(intent) or []
        if not isinstance(records, list) or not records:
            continue
        first = records[0]
        if not isinstance(first, dict):
            continue
        sources = _string_list(first.get("source_types"))
        lines.append(
            "- "
            f"{intent}: {first.get('query')} | "
            f"kind={first.get('expected_evidence_kind')} | "
            f"sources={_join_or_none(sources)} | "
            f"priority={first.get('priority')}"
        )
    return lines


def _matched_external_evidence_lines(selected: CandidateAggregate | None) -> list[str]:
    matches = _matched_external_evidence(selected)
    if not matches:
        return [
            "- No matched external validation evidence for the selected candidate.",
            "- Gate rule: unmatched external results remain decision context only.",
        ]
    lines = ["- Gate rule: only matched decision-grade external evidence can satisfy source gates."]
    for match in matches[:8]:
        decision_grade = "yes" if bool(match.get("decision_grade")) else "no"
        supports_gate = "yes" if bool(match.get("supports_gate")) else "no"
        url = match.get("source_url") or "no url"
        query = match.get("query") or "no query"
        source_label = str(match.get("source_type") or "unknown")
        subreddit = match.get("subreddit")
        if isinstance(subreddit, str) and subreddit.strip():
            source_label = f"{source_label}/r/{subreddit.strip()}"
        page_kind = match.get("page_kind")
        if isinstance(page_kind, str) and page_kind.strip():
            source_label = f"{source_label}/{page_kind.strip()}"
        discussion_kind = match.get("discussion_kind")
        if isinstance(discussion_kind, str) and discussion_kind.strip():
            source_label = f"{source_label}/{discussion_kind.strip()}"
        lines.append(
            "- "
            f"{match.get('evidence_kind')}: {source_label} | "
            f"query={query} | "
            f"decision_grade={decision_grade} | supports_gate={supports_gate} | "
            f"basis={match.get('match_basis')} | {url}"
        )
    return lines


def _missing_evidence_by_category_for_selected(
    selected: CandidateAggregate | None,
    *,
    matched_evidence: list[dict[str, object]] | None = None,
    validation_queries: dict[str, object] | None = None,
) -> dict[str, dict[str, object]]:
    if selected is None:
        return {}
    effective_matches = (
        matched_evidence if matched_evidence is not None else _matched_external_evidence(selected)
    )
    effective_queries = (
        validation_queries if validation_queries is not None else _validation_query_pack(selected)
    )
    return missing_evidence_by_kind(
        matched_evidence=effective_matches,
        validation_queries=effective_queries,
        current_missing=selected.missing_evidence,
    )


def _decision_change_action(selected: CandidateAggregate | None) -> dict[str, object] | None:
    if selected is None:
        return {
            "current_gate": "reject",
            "next_validation_action": (
                "Collect usable opportunity seeds, then run the candidate-specific "
                "validation query pack."
            ),
            "required_gate_change": (
                "select a candidate before build/focused decisions are considered"
            ),
            "market_context_role": "context_only_not_proof",
            "context_only_results_rule": "context-only records do not satisfy source gates",
        }
    matched_evidence = _matched_external_evidence(selected)
    validation_pack = _validation_query_pack(selected)
    missing = _missing_evidence_by_category_for_selected(
        selected,
        matched_evidence=matched_evidence,
        validation_queries=validation_pack,
    )
    next_query = _next_validation_query(validation_pack, missing)
    matched_types = list(_matched_external_source_types(selected))
    matched_count = decision_grade_match_count(matched_evidence)
    missing_category = str(next_query.get("category") or "")
    query = str(next_query.get("query") or "").strip()
    intent = str(next_query.get("intent") or "").strip()
    if query:
        action = (
            f"Run `{query}` for {intent or missing_category or 'external validation'} "
            "and attach only records that explicitly match the candidate and ICP."
        )
    else:
        action = (
            "Run the candidate-specific validation query pack and attach only records "
            "that explicitly match the candidate and ICP."
        )
    return {
        "current_gate": _dossier_status(selected),
        "matched_external_evidence_count": matched_count,
        "matched_external_source_types": matched_types,
        "next_query": query or None,
        "next_intent": intent or None,
        "missing_category": missing_category or None,
        "next_validation_action": action,
        "required_gate_change": (
            "two independent matched decision-grade external source types, including "
            "manual-workaround or willingness-to-pay evidence, before build/focused status"
        ),
        "market_context_role": "context_only_not_proof",
        "context_only_results_rule": (
            "unmatched external research and market lens records remain context only"
        ),
    }


def _decision_change_action_lines(selected: CandidateAggregate | None) -> list[str]:
    action = _decision_change_action(selected) or {}
    lines = [
        f"- Current gate: {action.get('current_gate') or 'unknown'}",
        f"- Next validation action: {action.get('next_validation_action')}",
        f"- Required gate change: {action.get('required_gate_change')}",
        "- Market context: context only, not proof.",
        f"- Context-only rule: {action.get('context_only_results_rule')}",
    ]
    matched_count = action.get("matched_external_evidence_count")
    if matched_count is not None:
        matched_types = _string_list(action.get("matched_external_source_types"))
        lines.insert(
            1,
            (
                f"- Matched decision-grade external evidence: {matched_count} "
                f"(types: {', '.join(matched_types) or 'none'})"
            ),
        )
    return lines


def _next_validation_query(
    validation_queries: dict[str, object] | None,
    missing_by_category: dict[str, dict[str, object]],
) -> dict[str, object]:
    for category, entry in missing_by_category.items():
        if not isinstance(entry, dict):
            continue
        query = str(entry.get("next_query") or "").strip()
        if query:
            return {
                "category": category,
                "intent": str(entry.get("next_intent") or ""),
                "query": query,
            }
    if not isinstance(validation_queries, dict):
        return {}
    next_query = validation_queries.get("next_query")
    if isinstance(next_query, dict):
        return {
            "category": None,
            "intent": str(next_query.get("intent") or ""),
            "query": str(next_query.get("query") or "").strip(),
        }
    queries_by_intent = validation_queries.get("queries_by_intent")
    if isinstance(queries_by_intent, dict):
        for intent in ("search_demand", "manual_workarounds", "reddit_forum_complaints"):
            records = queries_by_intent.get(intent)
            if not isinstance(records, list) or not records:
                continue
            first = records[0]
            if isinstance(first, dict) and str(first.get("query") or "").strip():
                return {
                    "category": None,
                    "intent": intent,
                    "query": str(first.get("query") or "").strip(),
                }
    return {}


def _market_context_prompt_lines(source_counts: dict[str, object]) -> list[str]:
    context = _object_dict(source_counts.get("market_context"))
    if not context:
        return ["- No context-only market lens supplied."]
    lines = [
        f"- Status: {context.get('status') or 'context_only'}",
        f"- Record count: {context.get('record_count') or 0}",
        "- Evidence use: ranking and critique context only; do not cite as proof.",
        "- Source gate: not satisfied by market context.",
    ]
    for record in _object_list(context.get("records"))[:2]:
        if not isinstance(record, dict):
            continue
        title = str(record.get("title") or "Market context")
        text = _truncate(str(record.get("text") or ""), 1800)
        lines.append(f"- {title}: {text}")
    return lines


def _market_context_lines(source_counts: dict[str, object]) -> list[str]:
    context = _object_dict(source_counts.get("market_context"))
    if not context:
        return ["- Market context: not supplied."]
    lines = [
        f"- Context-only records: {context.get('record_count') or 0}",
        "- Evidence role: ranking guidance and critique only.",
        "- Source gate: not satisfied by market context.",
        "- Build-ready evidence: false.",
        f"- Summary: {context.get('summary') or 'context only'}",
    ]
    for record in _object_list(context.get("records"))[:2]:
        if not isinstance(record, dict):
            continue
        title = str(record.get("title") or "Market context")
        lens_kind = str(record.get("market_context_lens_kind") or "unknown")
        text = _truncate(str(record.get("text") or ""), 700)
        lines.extend(
            [
                f"- Context row: {title} ({lens_kind})",
                f"  - Excerpt: {text}",
            ]
        )
    return lines


def _kir_evidence_lines(selected: CandidateAggregate | None) -> list[str]:
    if selected is None:
        return ["- KIR gate: not_required"]
    state = _kir_gate_state(selected)
    required = "yes" if bool(state.get("kir_required")) else "no"
    fresh = "yes" if bool(state.get("kir_has_fresh_thread")) else "no"
    reasons = _string_list(state.get("kir_gate_reasons"))
    thread_slug = state.get("kir_thread_slug") or "none"
    thread_status = state.get("kir_thread_status") or "none"
    source_kind = state.get("kir_source_kind") or "none"
    return [
        f"- KIR required: {required}",
        f"- KIR gate: {state.get('kir_gate_status')}",
        (
            f"- Knowledge Thread: {thread_slug} "
            f"(source_kind={source_kind}, status={thread_status}, fresh={fresh})"
        ),
        f"- Source atoms: {state.get('kir_source_atom_count', 0)}",
        f"- Source URLs: {state.get('kir_source_url_count', 0)}",
        f"- KIR blockers: {_join_or_none(reasons)}",
    ]


def _source_mix_card_lines(
    source_counts: dict[str, object],
    *,
    selected: CandidateAggregate | None = None,
) -> list[str]:
    selected_mix = _selected_source_mix(selected, source_counts)
    if selected_mix is None:
        run_external_types = _object_list(source_counts.get("external_source_types"))
        run_external_count = _safe_int(source_counts.get("external_evidence_count"), default=0)
        telegram_count = _safe_int(source_counts.get("telegram_seed_evidence_count"), default=0)
        return [
            "- Readiness: telegram_only",
            f"- Run Telegram seed evidence: {telegram_count}",
            (
                "- Run external evidence: "
                f"{run_external_count} (types: {_join_or_none(run_external_types)})"
            ),
            "- Selected external evidence: 0 (types: none)",
            "- Missing credentials/source errors: none",
            "- Reddit API: not_used",
            "- GitHub evidence: none",
            "- Gate: external evidence gap remains",
        ]

    missing_credentials = _string_list(selected_mix.get("missing_credentials"))
    source_errors = _string_list(selected_mix.get("source_error_sources"))
    issue_sources = missing_credentials or source_errors
    missing_text = _join_or_none(issue_sources)
    if missing_credentials:
        env_vars = selected_mix.get("missing_credential_env_vars")
        env_text = _join_or_none(_string_list(env_vars))
        missing_text = f"{missing_text} ({env_text})"

    selected_external_types = _string_list(selected_mix.get("selected_external_source_types"))
    run_external_types = _string_list(selected_mix.get("run_external_source_types"))
    kir_gate_status = str(selected_mix.get("kir_gate_status") or "not_required")
    gate = (
        "decision-grade external evidence present"
        if bool(selected_mix.get("decision_grade_external"))
        and kir_gate_status in KIR_GATE_PASSING_STATUSES
        else "KIR evidence gap remains"
        if bool(selected_mix.get("decision_grade_external"))
        else "external evidence gap remains"
    )
    return [
        f"- Readiness: {selected_mix.get('readiness', 'telegram_only')}",
        (
            "- Selected Telegram seed evidence: "
            f"{selected_mix.get('selected_telegram_seed_evidence_count', 0)}"
        ),
        (
            "- Selected external evidence: "
            f"{selected_mix.get('selected_external_evidence_count', 0)} "
            f"(types: {_join_or_none(selected_external_types)})"
        ),
        (
            "- Run external evidence: "
            f"{selected_mix.get('run_external_evidence_count', 0)} "
            f"(types: {_join_or_none(run_external_types)})"
        ),
        f"- Missing credentials/source errors: {missing_text}",
        f"- Reddit API: {selected_mix.get('reddit_api_status', 'not_used')}",
        f"- GitHub evidence: {selected_mix.get('github_evidence_role', 'none')}",
        f"- KIR gate: {kir_gate_status}",
        f"- Gate: {gate}",
    ]


def _selected_source_mix(
    selected: CandidateAggregate | None,
    source_counts: dict[str, object],
) -> dict[str, object] | None:
    if selected is None:
        return None
    source_errors = _source_error_map(source_counts.get("source_errors"))
    missing_credentials = _missing_credential_sources(source_errors)
    selected_external_matches = _matched_external_evidence(selected)
    selected_external_records = _matched_external_records(selected)
    selected_external_types = list(matched_external_source_types(selected_external_matches))
    selected_external_count = decision_grade_match_count(selected_external_matches)
    selected_telegram_count = sum(
        1 for record in selected.evidence if record.source_type == "telegram_research_agent"
    )
    kir_state = _kir_gate_state(selected)
    run_external_types = _object_list(source_counts.get("external_source_types"))
    readiness = _source_mix_readiness(
        selected_external_count=selected_external_count,
        missing_credentials=missing_credentials,
    )
    return {
        "readiness": readiness,
        "selected_telegram_seed_evidence_count": selected_telegram_count,
        "selected_external_evidence_count": selected_external_count,
        "selected_external_source_types": selected_external_types,
        "run_external_evidence_count": _safe_int(
            source_counts.get("external_evidence_count"),
            default=0,
        ),
        "run_external_source_types": run_external_types,
        "decision_grade_external": _has_decision_grade_external_evidence(selected),
        "source_error_sources": sorted(source_errors),
        "missing_credentials": sorted(missing_credentials),
        "missing_credential_env_vars": _missing_credential_env_vars(source_errors),
        "reddit_api_status": _reddit_api_status(
            selected_external_records=selected_external_records,
            source_counts=source_counts,
            missing_credentials=missing_credentials,
        ),
        "github_evidence_role": _github_evidence_role(selected_external_records),
        **kir_state,
    }


def _source_mix_readiness(
    *,
    selected_external_count: int,
    missing_credentials: set[str],
) -> str:
    if missing_credentials:
        return "credential_limited"
    if selected_external_count <= 0:
        return "telegram_only"
    return "externally_corroborated"


def _reddit_api_status(
    *,
    selected_external_records: list[EvidenceRecord],
    source_counts: dict[str, object],
    missing_credentials: set[str],
) -> str:
    configured_sources = _object_dict(source_counts.get("configured_sources"))
    reddit_run_count = _safe_int(source_counts.get("reddit"), default=0)
    reddit_config_count = sum(
        _safe_int(value, default=0)
        for key, value in configured_sources.items()
        if "reddit" in str(key).lower()
    )
    if any(record.source_type == "reddit" for record in selected_external_records):
        return "used"
    if _has_serp_indexed_reddit(selected_external_records):
        return "serp_indexed_only"
    if any("reddit" in source.lower() for source in missing_credentials):
        return "missing_credentials"
    if reddit_run_count > 0 or reddit_config_count > 0:
        return "run_only_unmatched"
    return "not_used"


def _has_serp_indexed_reddit(records: list[EvidenceRecord]) -> bool:
    for record in records:
        if record.source_type != "serp":
            continue
        text = " ".join(
            value
            for value in (
                record.source_url or "",
                record.source_id,
                record.title,
                record.snippet,
                record.normalized_text,
            )
            if value
        ).lower()
        if "reddit" in text:
            return True
    return False


def _github_evidence_role(selected_external_records: list[EvidenceRecord]) -> str:
    github_records = [
        record for record in selected_external_records if record.source_type == "github_public"
    ]
    if not github_records:
        return "none"
    signal_counts: dict[str, int] = {}
    for record in github_records:
        key = _source_signal_key(record)
        signal_counts[key] = signal_counts.get(key, 0) + 1
    repeated_count = sum(count - 1 for count in signal_counts.values() if count > 1)
    if repeated_count and len(signal_counts) <= 1:
        return "repeated_variants_only"
    if repeated_count:
        return "mixed_primary_and_variants"
    return "primary_evidence"


def _source_signal_key(record: EvidenceRecord) -> str:
    value = (
        _metadata_text(record.provider_metadata, "mvp_shape")
        or _metadata_text(record.provider_metadata, "demand_signal_type")
        or ",".join(_metadata_list(record.provider_metadata, "demand_surfaces"))
        or record.title
        or record.normalized_text[:80]
    )
    return " ".join(value.lower().split())


def _source_error_map(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items()}


def _missing_credential_sources(source_errors: dict[str, str]) -> set[str]:
    return {
        source
        for source, message in source_errors.items()
        if "status=missing" in message or "missing required credential" in message
    }


def _missing_credential_env_vars(source_errors: dict[str, str]) -> list[str]:
    env_vars: set[str] = set()
    for source in _missing_credential_sources(source_errors):
        message = source_errors[source]
        match = re.search(r"env_vars=([^;]+)", message)
        if not match:
            continue
        env_vars.update(value.strip() for value in match.group(1).split(",") if value.strip())
    return sorted(env_vars)


def _object_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item)]
    return [str(value)]


def _string_list(value: object) -> list[str]:
    return _object_list(value)


def _object_dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


def _top_values(value: object, *, key: str, limit: int) -> list[str]:
    items = value if isinstance(value, list) else []
    results: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        rendered = str(item.get(key) or "").strip()
        if rendered:
            results.append(rendered)
        if len(results) >= max(1, int(limit or 1)):
            break
    return results


def _join_or_none(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


def _safe_int(value: object, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _decision_gate_summary(
    source_counts: dict[str, object],
    *,
    selected: CandidateAggregate,
) -> str:
    telegram_count = source_counts.get("telegram_seed_evidence_count", "missing")
    external_count = source_counts.get("external_evidence_count", "missing")
    external_types = source_counts.get("external_source_types", "missing")
    if not isinstance(external_types, str):
        external_types = ", ".join(str(value) for value in external_types) or "none"
    matched_count = _matched_external_count(selected)
    matched_types = ", ".join(_matched_external_source_types(selected)) or "none"
    repeated_signal_count = _selected_repeated_signal_count(source_counts, selected=selected)
    missing_evidence = ", ".join(sorted(selected.missing_evidence)) or "none"
    kir_state = _kir_gate_state(selected)
    allowed = "yes" if selected.recommendation in RECOMMENDATION_GATED else "no"
    reason = _decision_gate_reason(selected, external_count=external_count)
    return "\n".join(
        [
            f"- Telegram seed evidence: {telegram_count}",
            f"- Run external evidence: {external_count}",
            f"- External source types: {external_types}",
            f"- Matched external evidence: {matched_count}",
            f"- Matched external source types: {matched_types}",
            f"- Repeated signal count: {repeated_signal_count}",
            f"- KIR gate: {kir_state.get('kir_gate_status')}",
            f"- Missing evidence: {missing_evidence}",
            f"- Recommendation allowed: {allowed}",
            f"- Reason: {reason}",
        ]
    )


def _selected_repeated_signal_count(
    source_counts: dict[str, object],
    *,
    selected: CandidateAggregate,
) -> int:
    selected_source_types = {record.source_type for record in selected.evidence}
    trust_records = source_counts.get("source_trust_records") or ()
    if not isinstance(trust_records, tuple | list):
        return 0
    total = 0
    for record in trust_records:
        if not isinstance(record, dict) or record.get("source_type") not in selected_source_types:
            continue
        try:
            total += int(record.get("repeated_signal_count", 0))
        except (TypeError, ValueError):
            continue
    return total


def _decision_gate_reason(
    selected: CandidateAggregate,
    *,
    external_count: object,
) -> str:
    if selected.recommendation in RECOMMENDATION_GATED:
        return selected.recommendation
    if selected.missing_evidence:
        if selected.missing_evidence & {
            "non-Telegram public evidence for the same pain",
            "second independent external source type",
        }:
            return "source_mix_gate"
        if not _kir_gate_allows_candidate(selected):
            return "kir_gate"
        return "insufficient_evidence"
    if _has_profile_blocking_mismatch(selected):
        return "operator_fit_gate"
    try:
        if int(external_count) <= 0:
            return "source_mix_gate"
    except (TypeError, ValueError):
        return "missing_gate_fields"
    if not _kir_gate_allows_candidate(selected):
        return "kir_gate"
    return "insufficient_evidence"


def _source_trust_lines(source_counts: dict[str, object]) -> list[str]:
    records = source_counts.get("source_trust_records") or ()
    if not isinstance(records, tuple | list) or not records:
        return ["- No source trust records available."]
    lines = []
    for record in records:
        if not isinstance(record, dict):
            continue
        reasons = record.get("rejection_reasons") or ()
        if isinstance(reasons, str):
            reason_text = reasons
        else:
            reason_text = ", ".join(str(reason) for reason in reasons) or "none"
        lines.append(
            "- "
            f"{record.get('source_name', record.get('source_type', 'unknown'))}: "
            f"evidence={record.get('evidence_count', 0)}, "
            f"unique_signals={record.get('unique_signal_count', 0)}, "
            f"repeated_signals={record.get('repeated_signal_count', 0)}, "
            f"evidence_density={record.get('evidence_density', 0)}; "
            f"rejection_reasons={reason_text}"
        )
    return lines or ["- No source trust records available."]


def _live_intelligence_lines(source_counts: dict[str, object]) -> list[str]:
    live = _object_dict(source_counts.get("live_intelligence"))
    if not live:
        return ["- No live source intelligence snapshot supplied."]
    window = _object_dict(live.get("window"))
    pathway = _object_dict(live.get("pathway"))
    top_channels = _string_list(live.get("top_channels"))
    top_surfaces = _string_list(live.get("top_demand_surfaces"))
    return [
        "- Context only: this snapshot does not satisfy external evidence gates.",
        f"- Generated: {live.get('generated_at') or 'unknown'}",
        f"- Window: {window.get('days', 'unknown')} day(s)",
        f"- Events scanned: {live.get('events_scanned', 0)}",
        f"- Top channels: {_join_or_none(top_channels)}",
        f"- Top demand surfaces: {_join_or_none(top_surfaces)}",
        f"- Repeated claim candidates: {live.get('repeated_claim_count', 0)}",
        f"- Pathway runtime: {pathway.get('status', 'unknown')}",
        f"- Summary: {live.get('radar_summary') or 'none'}",
    ]


def _build_worthy_lines(candidates: list[CandidateAggregate]) -> list[str]:
    build_worthy = [
        candidate for candidate in candidates if candidate.recommendation in RECOMMENDATION_GATED
    ]
    if not build_worthy:
        return ["- No build-worthy recommendations passed the Decision Gate."]
    return [
        f"- {candidate.title}: {candidate.score}/100, {len(candidate.evidence)} evidence item(s)"
        for candidate in build_worthy
    ]


def _interesting_signal_lines(candidates: list[CandidateAggregate]) -> list[str]:
    interesting = [
        candidate for candidate in candidates if candidate.recommendation != "focused_experiment"
    ]
    if not interesting:
        return ["- No downgraded interesting signals this week."]
    lines = []
    for candidate in interesting:
        missing = ", ".join(sorted(candidate.missing_evidence)) or "none"
        lines.append(
            f"- {candidate.title}: {candidate.score}/100, {candidate.recommendation}; "
            f"missing={missing}"
        )
    return lines


def _operator_fit_summary(candidate: CandidateAggregate) -> str:
    fit = ", ".join(sorted(candidate.profile_fit_flags)) or "weak explicit fit signal"
    mismatch = ", ".join(sorted(candidate.profile_mismatch_flags)) or "none"
    if _has_profile_blocking_mismatch(candidate):
        verdict = (
            "This should not be a build candidate until it is reframed as a "
            "Python/LLM workflow close to the operator profile."
        )
    else:
        verdict = "The candidate is acceptable only if the MVP stays narrow and close to this fit."
    return f"Fit signals: {fit}. Mismatch signals: {mismatch}. {verdict}"


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


def _metadata_bool(metadata: dict[str, str], field_name: str) -> bool:
    value = metadata.get(field_name)
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


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
    source_counts: dict[str, object],
    source_config: Path | None,
    live_intelligence_path: Path | None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    validation_pack = _validation_query_pack(selected)
    matched_evidence = _matched_external_evidence(selected)
    matched_fingerprints = matched_external_fingerprints(matched_evidence)
    missing_evidence_by_category = missing_evidence_by_kind(
        matched_evidence=matched_evidence,
        validation_queries=validation_pack,
        current_missing=selected.missing_evidence if selected is not None else (),
    )
    external_context = external_research_context(
        candidate_title=selected.title if selected is not None else None,
        records=tuple(record for candidate in candidates for record in candidate.evidence),
        matched_fingerprints=matched_fingerprints,
        external_source_types=EXTERNAL_DEMAND_SOURCE_TYPES,
    )
    payload = {
        "schema_version": "demand_mvp_radar.mvp_of_week.v1",
        "result": result.model_dump(mode="json"),
        "selected": _candidate_json(selected, source_counts=source_counts)
        if selected is not None
        else None,
        "candidates": [
            _candidate_json(candidate, source_counts=source_counts) for candidate in candidates
        ],
        "source_config": str(source_config) if source_config is not None else None,
        "live_intelligence_path": str(live_intelligence_path)
        if live_intelligence_path is not None
        else None,
        "live_intelligence": source_counts.get("live_intelligence"),
        "validation_queries": validation_pack,
        "matched_external_evidence": matched_evidence,
        "missing_evidence_by_category": missing_evidence_by_category,
        "validation_adapter_status": validation_adapter_status(source_counts),
        "decision_change_action": _decision_change_action(selected),
        "decision_context": {
            "market_context": source_counts.get("market_context"),
            "external_research_context": external_context,
            "context_only_record_count": source_counts.get("context_only_record_count", 0),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _candidate_json(
    candidate: CandidateAggregate,
    *,
    source_counts: dict[str, object],
) -> dict[str, object]:
    return {
        "candidate_id": f"candidate:{candidate.key}",
        "title": candidate.title,
        "score": candidate.score,
        "dossier_status": _dossier_status(candidate),
        "confidence": _dossier_confidence(candidate),
        "recommendation": candidate.recommendation,
        "decision_reason": _decision_gate_reason(
            candidate,
            external_count=source_counts.get("external_evidence_count", "missing"),
        ),
        "source_mix": _selected_source_mix(candidate, source_counts),
        "validation_queries": _validation_query_pack(candidate),
        "matched_external_evidence": _matched_external_evidence(candidate),
        "missing_evidence_by_category": _missing_evidence_by_category_for_selected(candidate),
        "decision_change_action": _decision_change_action(candidate),
        "next_experiment": _next_experiment(candidate),
        "kill_criteria": _kill_criteria(candidate),
        "evidence_count": len(candidate.evidence),
        "surfaces": sorted(candidate.surfaces),
        "channels": sorted(candidate.channels),
        "external_source_types": list(_matched_external_source_types(candidate)),
        "profile_fit_flags": sorted(candidate.profile_fit_flags),
        "profile_mismatch_flags": sorted(candidate.profile_mismatch_flags),
        "missing_evidence": sorted(candidate.missing_evidence),
        "risk_flags": sorted(candidate.risk_flags),
    }


def _record_mvp_run(
    connection,
    *,
    run_id: str,
    corpus_version: str,
    source_counts: dict[str, object],
    source_errors: dict[str, str],
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
                    **source_counts,
                    "total_evidence": evidence_count,
                    "selected_title": selected_title or "",
                    "score": score or 0,
                },
                sort_keys=True,
            ),
            "error_counts": json.dumps(
                {"telegram_research_agent_quarantined": quarantined_count},
                sort_keys=True,
            ),
            "source_errors": json.dumps(source_errors, sort_keys=True),
            "source_health": "{}",
            "duplicate_count": duplicate_count,
            "corpus_version": corpus_version,
            "max_weekly_llm_cost_usd": "0",
        },
    )
    connection.commit()
