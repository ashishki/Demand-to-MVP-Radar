"""Retrieval ingestion pipeline."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.observability import span
from demand_mvp_radar.retrieval.chunking import INDEX_SCHEMA_VERSION, RetrievalChunk, chunk_evidence
from demand_mvp_radar.retrieval.embeddings import HashEmbeddingClient
from demand_mvp_radar.retrieval.index import write_retrieval_chunks


def build_corpus(
    connection: sqlite3.Connection,
    evidence_rows: list[tuple[int, EvidenceRecord]],
    *,
    corpus_version: str,
    embedding_client: HashEmbeddingClient | None = None,
) -> dict[str, object]:
    client = embedding_client or HashEmbeddingClient()
    chunks: list[RetrievalChunk] = []
    for evidence_id, evidence in evidence_rows:
        chunks.extend(chunk_evidence(evidence_id, evidence, corpus_version=corpus_version))

    with span("retrieval.embed_chunks"):
        embeddings = client.embed_texts([chunk.chunk_text for chunk in chunks])

    chunk_count = write_retrieval_chunks(connection, tuple(chunks), embeddings)
    _record_run_manifest(
        connection,
        run_id=evidence_rows[0][1].run_id if evidence_rows else f"{corpus_version}-empty",
        corpus_version=corpus_version,
    )
    return {
        "corpus_version": corpus_version,
        "index_schema_version": INDEX_SCHEMA_VERSION,
        "chunk_count": chunk_count,
        "embedding_provider": client.model_info.provider,
        "embedding_model": client.model_info.model,
        "embedding_dimensions": client.model_info.dimensions,
    }


def _record_run_manifest(
    connection: sqlite3.Connection,
    *,
    run_id: str,
    corpus_version: str,
) -> None:
    now = datetime.now(UTC).isoformat()
    with span("sqlite.record_retrieval_manifest"):
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
                duplicate_count,
                corpus_version,
                index_schema_version,
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
                :duplicate_count,
                :corpus_version,
                :index_schema_version,
                :max_weekly_llm_cost_usd
            )
            ON CONFLICT(run_id) DO UPDATE SET
                ended_at = excluded.ended_at,
                status = excluded.status,
                corpus_version = excluded.corpus_version,
                index_schema_version = excluded.index_schema_version
            """,
            {
                "run_id": run_id,
                "started_at": now,
                "ended_at": now,
                "status": "retrieval_ingested",
                "source_counts": "{}",
                "error_counts": "{}",
                "source_errors": "{}",
                "duplicate_count": 0,
                "corpus_version": corpus_version,
                "index_schema_version": INDEX_SCHEMA_VERSION,
                "max_weekly_llm_cost_usd": "0",
            },
        )
        connection.commit()
