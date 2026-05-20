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
