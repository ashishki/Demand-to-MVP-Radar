from __future__ import annotations

from datetime import UTC, datetime

from demand_mvp_radar.cli import build_health_payload
from demand_mvp_radar.config import Settings
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema

SERVICE = "deploy/demand-mvp-radar.service"
TIMER = "deploy/demand-mvp-radar.timer"


def test_scheduled_run_template_contains_required_command_and_env() -> None:
    service = _read(SERVICE)
    timer = _read(TIMER)

    assert "demand-mvp-radar run" in service
    assert '--fixture "$DMR_WEEKLY_FIXTURE"' in service
    assert '--data-dir "$DMR_DATA_DIR"' in service
    assert '--report-dir "$DMR_REPORT_DIR"' in service
    assert "Environment=DMR_DATA_DIR=" in service
    assert "Environment=DMR_REPORT_DIR=" in service
    assert "Environment=DMR_WEEKLY_FIXTURE=" in service
    assert "EnvironmentFile=-%h/.config/demand-mvp-radar/schedule.env" in service
    assert "OnCalendar=Mon *-*-* 09:00:00" in timer
    assert "Persistent=true" in timer


def test_scheduled_run_paths_are_local_and_secret_safe() -> None:
    service = _read(SERVICE)

    assert "$DMR_DATA_DIR/logs/scheduled-run.log" in service
    assert "$DMR_REPORT_DIR" in service
    assert "scheduled-$(date +%%Y-%%m-%%d)" in service
    for forbidden in ("TOKEN", "PASSWORD", "SECRET", "API_KEY", "COOKIE"):
        assert forbidden not in service


def test_health_reports_last_scheduled_run(tmp_path) -> None:
    data_dir = tmp_path / "data"
    connection = connect_database(data_dir / "radar.sqlite3")
    create_schema(connection)
    ended_at = datetime(2026, 5, 20, 9, 30, tzinfo=UTC).isoformat()
    connection.execute(
        """
        INSERT INTO runs (
            run_id,
            started_at,
            ended_at,
            status,
            corpus_version,
            max_weekly_llm_cost_usd
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "scheduled-2026-05-20",
            datetime(2026, 5, 20, 9, 0, tzinfo=UTC).isoformat(),
            ended_at,
            "completed",
            "scheduled-2026-05-20-corpus",
            "5.00",
        ),
    )
    connection.commit()

    payload = build_health_payload(Settings(data_dir=data_dir, report_dir=tmp_path / "reports"))

    assert payload["last_scheduled_run"] == {
        "run_id": "scheduled-2026-05-20",
        "status": "completed",
        "ended_at": ended_at,
    }


def _read(path: str) -> str:
    from pathlib import Path

    return Path(path).read_text(encoding="utf-8")
