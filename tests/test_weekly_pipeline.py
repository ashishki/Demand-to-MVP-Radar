from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from demand_mvp_radar.cli import main

FIXTURE = Path("tests/fixtures/weekly_run")


def test_weekly_run_writes_expected_artifacts(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "run",
            "--fixture",
            str(FIXTURE),
            "--data-dir",
            str(tmp_path / "data"),
            "--report-dir",
            str(tmp_path / "reports"),
        ]
    )
    output = json.loads(capsys.readouterr().out)
    database_path = tmp_path / "data" / "radar.sqlite3"
    report_path = tmp_path / "reports" / "weekly-run-001.md"

    assert exit_code == 0
    assert output["status"] == "completed"
    assert output["corpus_version"] == "corpus-weekly-001"
    assert database_path.exists()
    assert report_path.exists()
    assert "Recommendation:" in report_path.read_text()

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    run = connection.execute("SELECT * FROM runs WHERE run_id = ?", ("weekly-run-001",)).fetchone()
    evidence_count = connection.execute("SELECT COUNT(*) AS count FROM evidence").fetchone()[
        "count"
    ]
    chunk_count = connection.execute("SELECT COUNT(*) AS count FROM retrieval_chunks").fetchone()[
        "count"
    ]

    assert run["status"] == "completed"
    assert run["corpus_version"] == "corpus-weekly-001"
    assert evidence_count == 2
    assert chunk_count == 2


def test_weekly_run_enforces_llm_budget_ceiling(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "run",
            "--fixture",
            str(FIXTURE),
            "--data-dir",
            str(tmp_path / "data"),
            "--report-dir",
            str(tmp_path / "reports"),
            "--max-weekly-llm-cost-usd",
            "0.10",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["status"] == "budget_exceeded"
    assert output["estimated_llm_cost_usd"] == "1.25"
    assert not (tmp_path / "reports" / "weekly-run-001.md").exists()


def test_weekly_run_is_idempotent_for_same_fixture(tmp_path, capsys) -> None:
    args = [
        "run",
        "--fixture",
        str(FIXTURE),
        "--data-dir",
        str(tmp_path / "data"),
        "--report-dir",
        str(tmp_path / "reports"),
    ]

    first = main(args)
    capsys.readouterr()
    second = main(args)
    capsys.readouterr()

    connection = sqlite3.connect(tmp_path / "data" / "radar.sqlite3")
    evidence_count = connection.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
    decision_count = connection.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]

    assert first == 0
    assert second == 0
    assert evidence_count == 2
    assert decision_count == 0
