from __future__ import annotations

import json
from pathlib import Path

from demand_mvp_radar.sources.telegram_research_agent import TelegramResearchAgentBridge
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.storage.repositories import EvidenceRepository

FIXTURE = Path(__file__).parent / "fixtures" / "telegram_research_agent_export.json"


def _repository(tmp_path) -> tuple[EvidenceRepository, object]:
    connection = connect_database(tmp_path / "radar.sqlite3")
    create_schema(connection)
    return EvidenceRepository(connection), connection


def test_bridge_imports_sanitized_export_as_evidence(tmp_path) -> None:
    repository, connection = _repository(tmp_path)

    result = TelegramResearchAgentBridge().import_file(
        FIXTURE,
        run_id="run-tra-001",
        repository=repository,
        quarantine_path=tmp_path / "quarantine.jsonl",
    )

    assert len(result.evidence) == 2
    first = result.evidence[0]
    assert first.run_id == "run-tra-001"
    assert first.source_type == "telegram_research_agent"
    assert first.source_id == "tra-2026-05-001"
    assert first.captured_at.isoformat() == "2026-05-18T10:00:00+00:00"
    assert first.normalized_text == (
        "Several builders asked for a lightweight way to compare prompt changes "
        "before shipping automations."
    )
    assert first.content_hash
    assert first.source_fingerprint.startswith("telegram_research_agent:tra-2026-05-001:")

    stored_count = connection.execute(
        """
        SELECT COUNT(*) AS evidence_count
        FROM evidence
        WHERE source_type = :source_type
        """,
        {"source_type": "telegram_research_agent"},
    ).fetchone()["evidence_count"]
    assert stored_count == 2


def test_bridge_preserves_optional_opportunity_metadata(tmp_path) -> None:
    repository, _connection = _repository(tmp_path)
    export_path = tmp_path / "export.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "tra-meta-001",
                    "captured_at": "2026-05-18T10:00:00+00:00",
                    "text": "Owners of Telegram channels need searchable SEO mirrors.",
                    "demand_surfaces": ["creator_content_gap", "search_intent"],
                    "mvp_shape": "Telegram Channel SEO Site Generator",
                    "bucket": "watch",
                    "signal_score": 0.67,
                }
            ]
        ),
        encoding="utf-8",
    )

    result = TelegramResearchAgentBridge().import_file(
        export_path,
        run_id="run-tra-meta",
        repository=repository,
        quarantine_path=tmp_path / "quarantine.jsonl",
    )

    metadata = result.evidence[0].provider_metadata
    assert metadata["mvp_shape"] == "Telegram Channel SEO Site Generator"
    assert json.loads(metadata["demand_surfaces"]) == ["creator_content_gap", "search_intent"]
    assert metadata["bucket"] == "watch"
    assert metadata["signal_score"] == "0.67"


def test_bridge_preserves_knowledge_thread_provenance_metadata(tmp_path) -> None:
    repository, _connection = _repository(tmp_path)
    export_path = tmp_path / "knowledge-thread-export.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "knowledge-thread:lead-response-sla-monitors",
                    "captured_at": "2026-07-06T08:00:00+00:00",
                    "title": "Lead Response SLA Monitor",
                    "text": "Lead response SLA monitors are recurring operator demand.",
                    "source_url": "https://t.me/market_ai/501",
                    "source_kind": "knowledge_thread",
                    "source_urls": [
                        "https://t.me/market_ai/501",
                        "https://t.me/operators/502",
                    ],
                    "knowledge_thread_slug": "lead-response-sla-monitors",
                    "knowledge_thread_title": "Lead Response SLA Monitors",
                    "knowledge_thread_status": "active",
                    "knowledge_atom_types": ["market_signal", "workflow_pattern"],
                    "source_atom_ids": [501, 502],
                }
            ]
        ),
        encoding="utf-8",
    )

    result = TelegramResearchAgentBridge().import_file(
        export_path,
        run_id="run-tra-kir",
        repository=repository,
        quarantine_path=tmp_path / "quarantine.jsonl",
    )

    metadata = result.evidence[0].provider_metadata
    assert metadata["source_kind"] == "knowledge_thread"
    assert metadata["knowledge_thread_slug"] == "lead-response-sla-monitors"
    assert metadata["knowledge_thread_title"] == "Lead Response SLA Monitors"
    assert metadata["knowledge_thread_status"] == "active"
    assert json.loads(metadata["knowledge_atom_types"]) == ["market_signal", "workflow_pattern"]
    assert json.loads(metadata["source_atom_ids"]) == [501, 502]
    assert json.loads(metadata["source_urls"]) == [
        "https://t.me/market_ai/501",
        "https://t.me/operators/502",
    ]


def test_bridge_import_is_idempotent(tmp_path) -> None:
    repository, connection = _repository(tmp_path)
    bridge = TelegramResearchAgentBridge()

    first = bridge.import_file(
        FIXTURE,
        run_id="run-tra-001",
        repository=repository,
        quarantine_path=tmp_path / "first-quarantine.jsonl",
    )
    second = bridge.import_file(
        FIXTURE,
        run_id="run-tra-002",
        repository=repository,
        quarantine_path=tmp_path / "second-quarantine.jsonl",
    )

    stored_count = connection.execute(
        """
        SELECT COUNT(*) AS evidence_count
        FROM evidence
        WHERE source_type = :source_type
        """,
        {"source_type": "telegram_research_agent"},
    ).fetchone()["evidence_count"]

    assert [item.source_fingerprint for item in first.evidence] == [
        item.source_fingerprint for item in second.evidence
    ]
    assert stored_count == 2


def test_bridge_quarantines_invalid_rows(tmp_path) -> None:
    repository, _connection = _repository(tmp_path)
    quarantine_path = tmp_path / "quarantine.jsonl"

    result = TelegramResearchAgentBridge().import_file(
        FIXTURE,
        run_id="run-tra-001",
        repository=repository,
        quarantine_path=quarantine_path,
    )
    quarantined_rows = [json.loads(line) for line in quarantine_path.read_text().splitlines()]

    assert len(result.evidence) == 2
    assert len(result.quarantined) == 2
    assert quarantined_rows == [
        {
            "source_reference": "tra-private-003",
            "error_reason": "private row is not importable",
        },
        {
            "source_reference": "tra-bad-004",
            "error_reason": "'text'",
        },
    ]
