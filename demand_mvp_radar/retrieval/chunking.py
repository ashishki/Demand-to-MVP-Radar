"""Source-aware text chunking for retrieval ingestion."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from demand_mvp_radar.models import EvidenceRecord

INDEX_SCHEMA_VERSION = "retrieval-index-v1"


class RetrievalChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    evidence_id: int
    source_type: str
    source_url: str | None
    captured_at: datetime
    content_hash: str
    corpus_version: str
    index_schema_version: str = INDEX_SCHEMA_VERSION
    chunk_index: int
    chunk_text: str


def chunk_evidence(
    evidence_id: int,
    evidence: EvidenceRecord,
    *,
    corpus_version: str,
    max_chars: int = 400,
) -> tuple[RetrievalChunk, ...]:
    parts = _split_text(evidence.normalized_text, max_chars=max_chars)
    return tuple(
        RetrievalChunk(
            evidence_id=evidence_id,
            source_type=evidence.source_type,
            source_url=evidence.source_url,
            captured_at=evidence.captured_at,
            content_hash=evidence.content_hash,
            corpus_version=corpus_version,
            chunk_index=index,
            chunk_text=part,
        )
        for index, part in enumerate(parts)
    )


def _split_text(text: str, *, max_chars: int) -> tuple[str, ...]:
    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return (normalized,)

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in normalized.split(" "):
        extra = len(word) + (1 if current else 0)
        if current and current_len + extra > max_chars:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += extra
    if current:
        chunks.append(" ".join(current))
    return tuple(chunks)
