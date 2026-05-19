from __future__ import annotations

from demand_mvp_radar.cli import build_health_payload
from demand_mvp_radar.config import Settings
from demand_mvp_radar.pipeline import run_weekly_pipeline


def test_health_json_reports_runtime_status(tmp_path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        report_dir=tmp_path / "reports",
    )
    run_weekly_pipeline(
        fixture=tmp_path_fixture(),
        settings=settings,
    )

    payload = build_health_payload(settings)

    assert payload["database"]["status"] == "ok"
    assert payload["report_dir"]["status"] == "writable"
    assert payload["corpus_version"] == "corpus-weekly-001"
    assert isinstance(payload["index_age_days"], int)
    assert payload["max_index_age_days"] == settings.max_index_age_days
    assert payload["configured_sources"] == 0


def tmp_path_fixture():
    from pathlib import Path

    return Path("tests/fixtures/weekly_run")
