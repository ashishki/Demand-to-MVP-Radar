from __future__ import annotations

import ast
import json
from datetime import datetime
from pathlib import Path

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.retrieval.ingestion import build_corpus
from demand_mvp_radar.retrieval.query import query_evidence
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.storage.repositories import EvidenceRepository

FIXTURE = Path("tests/fixtures/retrieval_queries.json")


def test_query_returns_cited_evidence_packets(tmp_path) -> None:
    connection, corpus_version, as_of = _build_fixture_corpus(tmp_path)

    response = query_evidence(
        connection,
        "Excel formula helper demand",
        corpus_version=corpus_version,
        min_independent_sources=2,
        top_k=3,
        as_of=as_of,
    )

    assert response.status == "ok"
    assert response.missing_evidence_reasons == ()
    assert len(response.evidence_packets) >= 2
    assert {packet.source_url for packet in response.evidence_packets[:2]} == {
        "https://t.me/operators/101",
        "https://example.com/excel-formula-helper",
    }
    assert [packet.citation_number for packet in response.evidence_packets] == [1, 2]
    for packet in response.evidence_packets:
        assert packet.evidence_id > 0
        assert packet.source_url.startswith("https://")
        assert packet.captured_at.tzinfo is not None
        assert packet.snippet
        assert packet.relevance_score > 0


def test_query_returns_insufficient_evidence_when_support_is_low(tmp_path) -> None:
    connection, corpus_version, as_of = _build_fixture_corpus(tmp_path)

    response = query_evidence(
        connection,
        "prerender SEO rendering pain",
        corpus_version=corpus_version,
        min_independent_sources=2,
        top_k=3,
        as_of=as_of,
    )

    assert response.status == "insufficient_evidence"
    assert len(response.evidence_packets) == 1
    assert response.evidence_packets[0].source_url == "https://example.com/prerender-seo"
    assert response.missing_evidence_reasons == (
        "minimum independent source count: required 2, found 1",
    )


def test_query_module_does_not_import_ingestion_module() -> None:
    source = Path("demand_mvp_radar/retrieval/query.py").read_text()
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

    assert "demand_mvp_radar.retrieval.ingestion" not in imports
    assert "demand_mvp_radar.retrieval.ingestion" not in from_imports


def _build_fixture_corpus(tmp_path):
    payload = json.loads(FIXTURE.read_text())
    connection = connect_database(tmp_path / "radar.sqlite3")
    create_schema(connection)
    repository = EvidenceRepository(connection)
    rows = []
    for item in payload["evidence"]:
        evidence = EvidenceRecord(
            run_id=payload["run_id"],
            source_type=item["source_type"],
            source_id=item["source_id"],
            source_url=item["source_url"],
            captured_at=datetime.fromisoformat(item["captured_at"]),
            title=item["title"],
            snippet=item["snippet"],
            normalized_text=item["normalized_text"],
            content_hash=item["content_hash"],
            source_fingerprint=item["source_fingerprint"],
        )
        rows.append((repository.write(evidence), evidence))

    corpus_version = payload["corpus_version"]
    build_corpus(connection, rows, corpus_version=corpus_version)
    return connection, corpus_version, datetime.fromisoformat(payload["as_of"])
