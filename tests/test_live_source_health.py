from __future__ import annotations

import json
from pathlib import Path

from demand_mvp_radar.cli import build_health_payload, main
from demand_mvp_radar.config import Settings
from demand_mvp_radar.models import SourceCatalogEntry


def test_health_reports_live_source_status(tmp_path) -> None:
    data_dir = tmp_path / "data"
    config_path = _write_live_config(tmp_path)

    assert main(["collect-sources", "--config", str(config_path), "--data-dir", str(data_dir)]) == 0

    payload = build_health_payload(
        Settings(data_dir=data_dir, report_dir=tmp_path / "reports")
    )
    source = payload["live_sources"]["fixture-live"]

    assert source["enabled"] is True
    assert source["last_success_at"] is not None
    assert source["last_error_class"] is None
    assert source["cursor_age_days"] == 0
    assert source["freshness_status"] == "current"
    assert source["credential_status"] == "not_required"
    assert source["rate_limit_state"]["limited"] is False


def test_health_redacts_live_source_credentials(tmp_path) -> None:
    secret_value = "test-gh-token-secret"
    settings = Settings(
        data_dir=tmp_path / "data",
        report_dir=tmp_path / "reports",
        source_catalog=(
            SourceCatalogEntry(
                source_type="github_public",
                priority="P1",
                trust_level="medium",
                freshness_window_days=14,
                access_method="public_api",
                enabled=True,
                credential_env_vars=("GITHUB_TOKEN",),
            ),
        ),
    )

    payload = build_health_payload(settings, env={"GITHUB_TOKEN": secret_value})
    serialized = json.dumps(payload, sort_keys=True)

    assert secret_value not in serialized
    assert payload["live_sources"]["github_public"]["credential_status"] == "available"
    assert payload["live_sources"]["github_public"]["credential_required"] is True
    assert "GITHUB_TOKEN" not in json.dumps(payload["live_sources"], sort_keys=True)


def test_health_distinguishes_source_failures_from_system_failure(tmp_path) -> None:
    data_dir = tmp_path / "data"
    config_path = _write_live_config(
        tmp_path,
        include_failure=True,
        run_id="collect-with-failure",
    )

    assert main(["collect-sources", "--config", str(config_path), "--data-dir", str(data_dir)]) == 0

    payload = build_health_payload(
        Settings(data_dir=data_dir, report_dir=tmp_path / "reports")
    )

    assert payload["status"] == "ok"
    assert payload["database"]["status"] == "ok"
    assert payload["live_sources"]["fixture-live"]["freshness_status"] == "current"
    failed = payload["live_sources"]["fixture-failing"]
    assert failed["last_error_class"] == "source_error"
    assert failed["freshness_status"] == "failing"
    assert "fixture-failing" in payload["source_warnings"]


def _write_live_config(
    tmp_path: Path,
    *,
    include_failure: bool = False,
    run_id: str = "collect-health-001",
) -> Path:
    sources: list[dict[str, object]] = [
        {
            "source_name": "fixture-live",
            "source_type": "fixture_live",
            "enabled": True,
            "trust_level": "medium",
            "freshness_window_days": 14,
            "cursor_support": True,
            "raw_snapshot_policy": "metadata_only",
            "rate_limit_policy": {"requests_per_minute": 60},
            "approval_required": False,
            "cursor_state": {"page": "1"},
            "records": [
                {
                    "source_id": "health-1",
                    "source_url": "https://example.com/health-1",
                    "captured_at": "2026-05-21T09:30:00+00:00",
                    "title": "Health fixture source",
                    "snippet": "Teams need visible live source health.",
                    "normalized_text": "Teams need visible live source health.",
                    "content_hash": "c" * 64,
                    "source_fingerprint": "fixture_live:health-1:" + ("c" * 64),
                    "connector_version": "fixture-live-v1",
                }
            ],
        }
    ]
    if include_failure:
        sources.append(
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
            }
        )
    config_path = tmp_path / "live-sources.json"
    config_path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "corpus_version": f"{run_id}-corpus",
                "sources": sources,
            }
        ),
        encoding="utf-8",
    )
    return config_path
