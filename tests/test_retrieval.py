from __future__ import annotations

import ast
import json
from datetime import UTC, datetime
from pathlib import Path

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.retrieval.chunking import INDEX_SCHEMA_VERSION, chunk_evidence
from demand_mvp_radar.retrieval.ingestion import build_corpus
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.storage.repositories import EvidenceRepository


def make_evidence(source_id: str) -> EvidenceRecord:
    return EvidenceRecord(
        run_id="run-001",
        source_type="telegram",
        source_id=source_id,
        source_url=f"https://example.com/{source_id}",
        captured_at=datetime(2026, 5, 18, 10, 0, tzinfo=UTC),
        title="Spreadsheet formula pain",
        snippet="Operators ask for spreadsheet formula helpers.",
        normalized_text=(
            "Operators ask for spreadsheet formula helpers that explain broken formulas."
        ),
        content_hash=f"hash-{source_id}",
        source_fingerprint=f"telegram:{source_id}:hash-{source_id}",
    )


def test_chunks_preserve_source_metadata() -> None:
    evidence = make_evidence("msg-001")

    chunks = chunk_evidence(42, evidence, corpus_version="corpus-test")

    assert chunks[0].evidence_id == 42
    assert chunks[0].source_type == "telegram"
    assert chunks[0].source_url == "https://example.com/msg-001"
    assert chunks[0].captured_at == evidence.captured_at
    assert chunks[0].content_hash == evidence.content_hash
    assert chunks[0].corpus_version == "corpus-test"
    assert chunks[0].index_schema_version == INDEX_SCHEMA_VERSION


def test_corpus_build_records_version_and_schema(tmp_path) -> None:
    connection = connect_database(tmp_path / "radar.sqlite3")
    create_schema(connection)
    repository = EvidenceRepository(connection)
    rows = []
    for index in range(3):
        evidence = make_evidence(f"msg-00{index}")
        rows.append((repository.write(evidence), evidence))

    result = build_corpus(connection, rows, corpus_version="corpus-test")
    stored_chunks = connection.execute(
        """
        SELECT corpus_version, metadata
        FROM retrieval_chunks
        """
    ).fetchall()
    manifest = connection.execute(
        """
        SELECT corpus_version, index_schema_version
        FROM runs
        WHERE run_id = :run_id
        """,
        {"run_id": "run-001"},
    ).fetchone()
    metadata = [json.loads(row["metadata"]) for row in stored_chunks]

    assert result["corpus_version"] == "corpus-test"
    assert result["index_schema_version"] == INDEX_SCHEMA_VERSION
    assert manifest["corpus_version"] == "corpus-test"
    assert manifest["index_schema_version"] == INDEX_SCHEMA_VERSION
    assert result["chunk_count"] == 3
    assert {row["corpus_version"] for row in stored_chunks} == {"corpus-test"}
    assert {item["index_schema_version"] for item in metadata} == {INDEX_SCHEMA_VERSION}


def test_ingestion_module_does_not_import_query_module() -> None:
    source = Path("demand_mvp_radar/retrieval/ingestion.py").read_text()
    tree = ast.parse(source)

    imports = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ]
    from_imports = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    ]

    assert "demand_mvp_radar.retrieval.query" not in imports
    assert "demand_mvp_radar.retrieval.query" not in from_imports
