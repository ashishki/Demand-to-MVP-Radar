from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from demand_mvp_radar.cli import build_health_payload, main
from demand_mvp_radar.config import Settings


def test_collect_sources_imports_live_evidence_without_reports(tmp_path, capsys) -> None:
    data_dir = tmp_path / "data"
    report_dir = tmp_path / "reports"
    config_path = _write_collect_config(tmp_path)

    exit_code = main(
        [
            "collect-sources",
            "--config",
            str(config_path),
            "--data-dir",
            str(data_dir),
            "--report-dir",
            str(report_dir),
        ]
    )
    output = json.loads(capsys.readouterr().out)
    connection = _connect(data_dir / "radar.sqlite3")
    run = connection.execute(
        "SELECT status, source_counts, error_counts FROM runs WHERE run_id = ?",
        ("collect-run-001",),
    ).fetchone()

    assert exit_code == 0
    assert output["status"] == "collected"
    assert output["report_path"] is None
    assert output["evidence_count"] == 1
    assert output["retrieval_chunk_count"] > 0
    assert connection.execute("SELECT COUNT(*) FROM evidence").fetchone()[0] == 1
    assert connection.execute("SELECT COUNT(*) FROM retrieval_chunks").fetchone()[0] > 0
    assert run["status"] == "collected"
    assert json.loads(run["source_counts"])["fixture-hn"] == 1
    assert json.loads(run["error_counts"])["fixture-hn"] == 0
    assert not list(report_dir.glob("*.md"))


def test_collect_sources_isolates_source_failures(tmp_path, capsys) -> None:
    data_dir = tmp_path / "data"
    config_path = _write_collect_config(
        tmp_path,
        extra_sources=(
            {
                "source_name": "fixture-failing",
                "source_type": "fixture_live",
                "enabled": True,
                "trust_level": "medium",
                "freshness_window_days": 14,
                "cursor_support": True,
                "raw_snapshot_policy": "metadata_only",
                "rate_limit_policy": {"requests_per_minute": 60},
                "approval_required": False,
                "fail": True,
            },
        ),
    )

    exit_code = main(
        [
            "collect-sources",
            "--config",
            str(config_path),
            "--data-dir",
            str(data_dir),
        ]
    )
    output = json.loads(capsys.readouterr().out)
    connection = _connect(data_dir / "radar.sqlite3")
    run = connection.execute(
        "SELECT error_counts, source_errors FROM runs WHERE run_id = ?",
        ("collect-run-001",),
    ).fetchone()
    health = build_health_payload(Settings(data_dir=data_dir, report_dir=tmp_path / "reports"))

    assert exit_code == 0
    assert output["evidence_count"] == 1
    assert output["error_counts"]["fixture-failing"] == 1
    assert json.loads(run["error_counts"])["fixture-failing"] == 1
    assert "fixture failure requested" in json.loads(run["source_errors"])["fixture-failing"]
    assert (
        health["last_source_errors"]["fixture-failing"]
        == json.loads(run["source_errors"])["fixture-failing"]
    )


def test_collect_sources_is_idempotent_by_fingerprint(tmp_path, capsys) -> None:
    data_dir = tmp_path / "data"
    config_path = _write_collect_config(tmp_path)
    args = [
        "collect-sources",
        "--config",
        str(config_path),
        "--data-dir",
        str(data_dir),
    ]

    assert main(args) == 0
    first_output = json.loads(capsys.readouterr().out)
    connection = _connect(data_dir / "radar.sqlite3")
    first_chunk_count = connection.execute("SELECT COUNT(*) FROM retrieval_chunks").fetchone()[0]

    assert main(args) == 0
    second_output = json.loads(capsys.readouterr().out)
    second_chunk_count = connection.execute("SELECT COUNT(*) FROM retrieval_chunks").fetchone()[0]

    assert first_output["evidence_count"] == 1
    assert first_output["duplicate_count"] == 0
    assert second_output["evidence_count"] == 0
    assert second_output["duplicate_count"] == 1
    assert connection.execute("SELECT COUNT(*) FROM evidence").fetchone()[0] == 1
    assert second_chunk_count == first_chunk_count


def _write_collect_config(
    tmp_path: Path,
    *,
    extra_sources: tuple[dict[str, object], ...] = (),
) -> Path:
    config = {
        "run_id": "collect-run-001",
        "corpus_version": "collect-run-001-corpus",
        "sources": [
            {
                "source_name": "fixture-hn",
                "source_type": "fixture_live",
                "enabled": True,
                "trust_level": "medium",
                "freshness_window_days": 14,
                "cursor_support": True,
                "raw_snapshot_policy": "metadata_only",
                "rate_limit_policy": {"requests_per_minute": 60},
                "approval_required": False,
                "cursor_state": {"last_item_id": "423456"},
                "records": [
                    {
                        "source_id": "423456",
                        "source_url": "https://news.ycombinator.com/item?id=423456",
                        "captured_at": "2026-05-21T09:30:00+00:00",
                        "title": "Developers need cleaner changelog monitoring",
                        "snippet": "Teams manually scan changelogs for breaking changes.",
                        "normalized_text": (
                            "Teams manually scan changelogs for breaking changes and "
                            "miss important release notes."
                        ),
                        "content_hash": "b" * 64,
                        "source_fingerprint": "fixture_live:423456:" + ("b" * 64),
                        "connector_version": "fixture-live-v1",
                    }
                ],
            },
            *extra_sources,
        ],
    }
    config_path = tmp_path / "live-sources.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection
