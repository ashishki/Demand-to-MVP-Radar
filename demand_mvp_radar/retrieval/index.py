"""SQLite-backed local retrieval index writes."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from demand_mvp_radar.observability import span
from demand_mvp_radar.retrieval.chunking import RetrievalChunk


class IndexedChunk:
    def __init__(
        self,
        *,
        row_id: int,
        evidence_id: int,
        corpus_version: str,
        chunk_text: str,
        chunk_index: int,
        content_hash: str,
        source_type: str,
        source_url: str | None,
        captured_at: datetime,
        index_schema_version: str,
    ) -> None:
        self.row_id = row_id
        self.evidence_id = evidence_id
        self.corpus_version = corpus_version
        self.chunk_text = chunk_text
        self.chunk_index = chunk_index
        self.content_hash = content_hash
        self.source_type = source_type
        self.source_url = source_url
        self.captured_at = captured_at
        self.index_schema_version = index_schema_version


def write_retrieval_chunks(
    connection: sqlite3.Connection,
    chunks: tuple[RetrievalChunk, ...],
    embeddings: list[list[float]],
) -> int:
    if len(chunks) != len(embeddings):
        raise ValueError("chunks and embeddings must have the same length")

    with span("sqlite.write_retrieval_chunks"):
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            connection.execute(
                """
                INSERT INTO retrieval_chunks (
                    evidence_id,
                    corpus_version,
                    chunk_text,
                    chunk_index,
                    content_hash,
                    metadata
                )
                VALUES (
                    :evidence_id,
                    :corpus_version,
                    :chunk_text,
                    :chunk_index,
                    :content_hash,
                    :metadata
                )
                """,
                {
                    "evidence_id": chunk.evidence_id,
                    "corpus_version": chunk.corpus_version,
                    "chunk_text": chunk.chunk_text,
                    "chunk_index": chunk.chunk_index,
                    "content_hash": chunk.content_hash,
                    "metadata": json.dumps(
                        {
                            "source_type": chunk.source_type,
                            "source_url": chunk.source_url,
                            "captured_at": chunk.captured_at.isoformat(),
                            "content_hash": chunk.content_hash,
                            "corpus_version": chunk.corpus_version,
                            "index_schema_version": chunk.index_schema_version,
                            "embedding": embedding,
                        },
                        sort_keys=True,
                    ),
                },
            )
        connection.commit()
    return len(chunks)


def load_indexed_chunks(
    connection: sqlite3.Connection,
    *,
    corpus_version: str,
) -> tuple[IndexedChunk, ...]:
    with span("sqlite.load_retrieval_chunks"):
        rows = connection.execute(
            """
            SELECT
                id,
                evidence_id,
                corpus_version,
                chunk_text,
                chunk_index,
                content_hash,
                metadata
            FROM retrieval_chunks
            WHERE corpus_version = :corpus_version
            ORDER BY id ASC
            """,
            {"corpus_version": corpus_version},
        ).fetchall()

    chunks: list[IndexedChunk] = []
    for row in rows:
        metadata = json.loads(row["metadata"])
        chunks.append(
            IndexedChunk(
                row_id=int(row["id"]),
                evidence_id=int(row["evidence_id"]),
                corpus_version=str(row["corpus_version"]),
                chunk_text=str(row["chunk_text"]),
                chunk_index=int(row["chunk_index"]),
                content_hash=str(row["content_hash"]),
                source_type=str(metadata["source_type"]),
                source_url=metadata.get("source_url"),
                captured_at=datetime.fromisoformat(str(metadata["captured_at"])),
                index_schema_version=str(metadata["index_schema_version"]),
            )
        )
    return tuple(chunks)
