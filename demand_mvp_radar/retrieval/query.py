"""Query-time retrieval and insufficient-evidence gating."""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field

from demand_mvp_radar.observability import span
from demand_mvp_radar.retrieval.index import IndexedChunk, load_indexed_chunks

TOKEN_RE = re.compile(r"[a-z0-9]+")
DEFAULT_SOURCE_TRUST_WEIGHTS = {
    "operator_note": 0.35,
    "manual_note": 0.35,
    "news": 0.5,
    "rss": 0.5,
    "reddit": 0.5,
    "product_hunt": 0.6,
    "serp": 0.7,
    "telegram_research_agent": 0.75,
    "github": 0.8,
    "github_repo": 0.8,
    "reviews": 0.9,
}


class EvidencePacket(BaseModel):
    model_config = ConfigDict(frozen=True)

    evidence_id: int
    source_url: str
    captured_at: datetime
    snippet: str
    relevance_score: float = Field(ge=0, le=1)
    citation_number: int = Field(ge=1)


class RetrievalResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str
    corpus_version: str
    evidence_packets: tuple[EvidencePacket, ...] = ()
    missing_evidence_reasons: tuple[str, ...] = ()


def query_evidence(
    connection: sqlite3.Connection,
    query: str,
    *,
    corpus_version: str,
    min_independent_sources: int = 2,
    top_k: int = 3,
    max_age_days: int = 365,
    min_relevance_score: float = 0.5,
    source_freshness_windows: Mapping[str, int] | None = None,
    source_trust_weights: Mapping[str, float] | None = None,
    as_of: datetime | None = None,
) -> RetrievalResponse:
    query_tokens = _tokenize(query)
    if not query_tokens:
        return _insufficient(
            corpus_version,
            "non-empty query",
            "minimum independent source count",
        )

    with span("retrieval.query"):
        chunks = load_indexed_chunks(connection, corpus_version=corpus_version)
        query_as_of = as_of or datetime.now(UTC)
        scored = _score_chunks(
            chunks,
            query_tokens=query_tokens,
            max_age_days=max_age_days,
            min_relevance_score=min_relevance_score,
            source_freshness_windows=source_freshness_windows,
            source_trust_weights=source_trust_weights,
            as_of=query_as_of,
        )
        packets = _assemble_packets(scored, top_k=top_k)

    independent_sources = {packet.source_url for packet in packets}
    if len(independent_sources) < min_independent_sources:
        missing = [
            (
                "minimum independent source count: "
                f"required {min_independent_sources}, found {len(independent_sources)}"
            )
        ]
        if _has_relevant_unlinked_chunk(chunks, query_tokens=query_tokens):
            missing.append("fresh source link")
        if (
            chunks
            and not scored
            and _has_relevant_stale_chunk(
                chunks,
                query_tokens=query_tokens,
                max_age_days=max_age_days,
                source_freshness_windows=source_freshness_windows,
                as_of=query_as_of,
            )
        ):
            missing.append("fresh relevant evidence")
        return RetrievalResponse(
            status="insufficient_evidence",
            corpus_version=corpus_version,
            evidence_packets=packets,
            missing_evidence_reasons=tuple(missing),
        )

    return RetrievalResponse(
        status="ok",
        corpus_version=corpus_version,
        evidence_packets=packets,
        missing_evidence_reasons=(),
    )


def _score_chunks(
    chunks: tuple[IndexedChunk, ...],
    *,
    query_tokens: set[str],
    max_age_days: int,
    min_relevance_score: float,
    source_freshness_windows: Mapping[str, int] | None,
    source_trust_weights: Mapping[str, float] | None,
    as_of: datetime,
) -> list[tuple[IndexedChunk, float]]:
    scored: list[tuple[IndexedChunk, float]] = []
    for chunk in chunks:
        if chunk.source_url is None:
            continue
        min_captured_at = as_of - timedelta(
            days=_source_freshness_window(
                chunk.source_type,
                source_freshness_windows=source_freshness_windows,
                default_days=max_age_days,
            )
        )
        if _to_utc(chunk.captured_at) < min_captured_at:
            continue

        chunk_tokens = _tokenize(chunk.chunk_text)
        overlap = query_tokens & chunk_tokens
        if not overlap:
            continue

        base_score = len(overlap) / len(query_tokens)
        score = base_score * _source_trust_weight(
            chunk.source_type,
            source_trust_weights=source_trust_weights,
        )
        if base_score < min_relevance_score:
            continue
        scored.append((chunk, round(score, 6)))

    scored.sort(key=lambda item: (-item[1], item[0].row_id))
    return _dedupe_by_source(scored)


def _assemble_packets(
    scored: list[tuple[IndexedChunk, float]],
    *,
    top_k: int,
) -> tuple[EvidencePacket, ...]:
    packets = [
        EvidencePacket(
            evidence_id=chunk.evidence_id,
            source_url=chunk.source_url or "",
            captured_at=chunk.captured_at,
            snippet=_snippet(chunk.chunk_text),
            relevance_score=score,
            citation_number=index,
        )
        for index, (chunk, score) in enumerate(scored[:top_k], start=1)
    ]
    return tuple(packets)


def _dedupe_by_source(scored: list[tuple[IndexedChunk, float]]) -> list[tuple[IndexedChunk, float]]:
    seen: set[str] = set()
    deduped: list[tuple[IndexedChunk, float]] = []
    for chunk, score in scored:
        if chunk.source_url is None or chunk.source_url in seen:
            continue
        seen.add(chunk.source_url)
        deduped.append((chunk, score))
    return deduped


def _tokenize(text: str) -> set[str]:
    return {match.group(0) for match in TOKEN_RE.finditer(text.lower())}


def _has_relevant_unlinked_chunk(
    chunks: tuple[IndexedChunk, ...],
    *,
    query_tokens: set[str],
) -> bool:
    return any(
        chunk.source_url is None and query_tokens & _tokenize(chunk.chunk_text) for chunk in chunks
    )


def _has_relevant_stale_chunk(
    chunks: tuple[IndexedChunk, ...],
    *,
    query_tokens: set[str],
    max_age_days: int,
    source_freshness_windows: Mapping[str, int] | None,
    as_of: datetime,
) -> bool:
    for chunk in chunks:
        min_captured_at = as_of - timedelta(
            days=_source_freshness_window(
                chunk.source_type,
                source_freshness_windows=source_freshness_windows,
                default_days=max_age_days,
            )
        )
        if (
            chunk.source_url is not None
            and _to_utc(chunk.captured_at) < min_captured_at
            and query_tokens & _tokenize(chunk.chunk_text)
        ):
            return True
    return False


def _source_freshness_window(
    source_type: str,
    *,
    source_freshness_windows: Mapping[str, int] | None,
    default_days: int,
) -> int:
    if not source_freshness_windows:
        return default_days
    window_days = source_freshness_windows.get(source_type, default_days)
    return max(int(window_days), 1)


def _source_trust_weight(
    source_type: str,
    *,
    source_trust_weights: Mapping[str, float] | None,
) -> float:
    weights = source_trust_weights or DEFAULT_SOURCE_TRUST_WEIGHTS
    weight = float(weights.get(source_type, 1.0))
    return min(max(weight, 0.0), 1.0)


def _snippet(text: str, *, max_chars: int = 220) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized
    return f"{normalized[: max_chars - 3].rstrip()}..."


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _insufficient(corpus_version: str, *reasons: str) -> RetrievalResponse:
    return RetrievalResponse(
        status="insufficient_evidence",
        corpus_version=corpus_version,
        missing_evidence_reasons=tuple(reasons),
    )
