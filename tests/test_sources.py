from __future__ import annotations

import json
from pathlib import Path

from demand_mvp_radar.sources.telegram_export import TelegramExportAdapter

FIXTURE = Path(__file__).parent / "fixtures" / "telegram_export.json"


def test_telegram_export_imports_two_evidence_records(tmp_path) -> None:
    result = TelegramExportAdapter().import_file(
        FIXTURE,
        run_id="run-001",
        quarantine_path=tmp_path / "quarantine.jsonl",
    )

    assert len(result.evidence) == 2
    first = result.evidence[0]
    assert first.source_type == "telegram"
    assert first.source_id == "msg-001"
    assert first.captured_at.isoformat() == "2026-05-18T10:00:00+00:00"
    assert first.title
    assert first.snippet
    assert first.normalized_text
    assert first.content_hash


def test_malformed_telegram_row_is_quarantined(tmp_path) -> None:
    quarantine_path = tmp_path / "quarantine.jsonl"

    result = TelegramExportAdapter().import_file(
        FIXTURE,
        run_id="run-001",
        quarantine_path=quarantine_path,
    )
    quarantined_rows = [json.loads(line) for line in quarantine_path.read_text().splitlines()]

    assert len(result.evidence) == 2
    assert len(result.quarantined) == 1
    assert quarantined_rows == [
        {
            "source_reference": "bad-003",
            "error_reason": "'text'",
        }
    ]


def test_telegram_content_hash_is_stable(tmp_path) -> None:
    adapter = TelegramExportAdapter()

    first = adapter.import_file(
        FIXTURE,
        run_id="run-001",
        quarantine_path=tmp_path / "first.jsonl",
    )
    second = adapter.import_file(
        FIXTURE,
        run_id="run-002",
        quarantine_path=tmp_path / "second.jsonl",
    )

    assert [item.content_hash for item in first.evidence] == [
        item.content_hash for item in second.evidence
    ]
