from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from demand_mvp_radar.cli import main

FIXTURE = Path(__file__).parent / "fixtures" / "source_mix"


def test_import_sources_fixture_writes_evidence_and_manifest(tmp_path, capsys) -> None:
    data_dir = tmp_path / "data"
    report_dir = tmp_path / "reports"

    exit_code = main(
        [
            "import-sources",
            "--fixture",
            str(FIXTURE),
            "--data-dir",
            str(data_dir),
            "--report-dir",
            str(report_dir),
        ]
    )
    output = json.loads(capsys.readouterr().out)
    connection = _connect(data_dir / "radar.sqlite3")

    evidence_count = connection.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
    run = connection.execute(
        "SELECT status, source_counts FROM runs WHERE run_id = :run_id",
        {"run_id": "import-run-001"},
    ).fetchone()
    source_counts = json.loads(run["source_counts"])

    assert exit_code == 0
    assert output["status"] == "imported"
    assert output["evidence_count"] == 7
    assert evidence_count == 7
    assert run["status"] == "imported"
    assert source_counts["telegram_research_agent"] == 2
    assert source_counts["operator_notes"] == 1
    assert source_counts["github_repo"] == 4


def test_import_sources_updates_retrieval_without_report_generation(tmp_path, capsys) -> None:
    data_dir = tmp_path / "data"
    report_dir = tmp_path / "reports"

    main(
        [
            "import-sources",
            "--fixture",
            str(FIXTURE),
            "--data-dir",
            str(data_dir),
            "--report-dir",
            str(report_dir),
        ]
    )
    output = json.loads(capsys.readouterr().out)
    connection = _connect(data_dir / "radar.sqlite3")

    chunk_count = connection.execute("SELECT COUNT(*) FROM retrieval_chunks").fetchone()[0]
    run = connection.execute(
        "SELECT corpus_version FROM runs WHERE run_id = :run_id",
        {"run_id": "import-run-001"},
    ).fetchone()

    assert output["report_path"] is None
    assert output["corpus_version"] == "import-run-001-corpus"
    assert chunk_count == output["retrieval_chunk_count"]
    assert chunk_count > 0
    assert run["corpus_version"] == "import-run-001-corpus"
    assert not list(report_dir.glob("*.md"))


def test_import_sources_records_disabled_sources(tmp_path, capsys) -> None:
    data_dir = tmp_path / "data"

    main(
        [
            "import-sources",
            "--fixture",
            str(FIXTURE),
            "--data-dir",
            str(data_dir),
        ]
    )
    output = json.loads(capsys.readouterr().out)
    connection = _connect(data_dir / "radar.sqlite3")
    run = connection.execute(
        "SELECT source_counts FROM runs WHERE run_id = :run_id",
        {"run_id": "import-run-001"},
    ).fetchone()
    source_counts = json.loads(run["source_counts"])

    assert output["skipped_sources"] == ["serp"]
    assert source_counts["skipped_sources"] == ["serp"]


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection
