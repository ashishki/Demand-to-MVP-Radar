from __future__ import annotations

import json
from pathlib import Path

from demand_mvp_radar.config import Settings
from demand_mvp_radar.pipeline import collect_sources
from demand_mvp_radar.sources.live import LiveSourceConfig, RateLimitPolicy
from demand_mvp_radar.sources.x_discussions import XDiscussionConnector


def test_x_discussion_connector_maps_fixture_to_lower_confidence_evidence(tmp_path) -> None:
    fixture_path = _write_fixture(tmp_path)
    connector = XDiscussionConnector(
        fixture_path,
        queries=("csv cleanup automation",),
        max_results_per_run=3,
    )

    result = connector.collect(_config(), run_id="x-discussions-001", cursor_state={})
    pain = result.evidence[0]
    trend = result.evidence[1]

    assert len(result.evidence) == 2
    assert pain.source_type == "x"
    assert pain.source_url == "https://x.com/example/status/1001"
    assert pain.search_query == "csv cleanup automation"
    assert pain.provider == "x-research"
    assert pain.provider_metadata["discussion_kind"] == "pain"
    assert pain.provider_metadata["evidence_kind"] == "repeated_complaint"
    assert pain.provider_metadata["lower_confidence"] == "true"
    assert pain.provider_metadata["corroboration_required"] == "true"
    assert pain.author_hash is not None
    assert "x-user-private-001" not in pain.model_dump_json()
    assert trend.provider_metadata["discussion_kind"] == "trend_chatter"
    assert trend.provider_metadata["evidence_kind"] == "negative_signal"
    assert result.rate_limit_state.remaining == 12


def test_x_discussion_cache_only_uses_fixture_without_credentials(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    fixture_path = _write_fixture(tmp_path)
    config_path = _write_source_config(
        tmp_path,
        fixture_path=fixture_path,
        cache_only=True,
        dry_run=False,
    )

    result = collect_sources(
        config=config_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="x-cache-boundary",
    )

    assert result.evidence_count == 2
    assert result.source_counts["x_discussions_cache"] == 2
    assert result.source_counts["source_modes"]["x_discussions_cache"] == "cache_only"
    assert result.source_errors == {}


def test_x_discussion_dry_run_skips_live_without_credentials(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    config_path = _write_source_config(
        tmp_path,
        fixture_path=None,
        cache_only=False,
        dry_run=True,
    )

    result = collect_sources(
        config=config_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="x-dry-run-boundary",
    )

    assert result.evidence_count == 0
    assert result.source_counts["x_discussions_cache"] == 0
    assert result.source_counts["source_modes"]["x_discussions_cache"] == "dry_run"
    assert result.source_errors == {}


def _write_fixture(tmp_path: Path) -> Path:
    fixture_path = tmp_path / "x-discussions.json"
    fixture_path.write_text(
        json.dumps(
            {
                "rate_limit": {
                    "limited": False,
                    "remaining": 12,
                },
                "discussions": [
                    {
                        "query": "csv cleanup automation",
                        "discussion_id": "1001",
                        "url": "https://x.com/example/status/1001",
                        "author_id": "x-user-private-001",
                        "title": "X discussion about CSV cleanup",
                        "text": (
                            "CSV cleanup automation for client exports keeps coming up; "
                            "people still fix broken headers and delimiters manually."
                        ),
                        "discussion_kind": "pain",
                        "target_candidate": "CSV cleanup automation for client exports",
                        "like_count": 21,
                        "reply_count": 4,
                        "created_at": "2026-05-20T10:00:00+00:00",
                        "captured_at": "2026-05-21T15:00:00+00:00",
                    },
                    {
                        "query": "csv cleanup automation",
                        "discussion_id": "1002",
                        "url": "https://x.com/example/status/1002",
                        "author_id": "x-user-private-002",
                        "title": "Generic AI automation trend",
                        "text": (
                            "Everyone is posting broad AI automation takes without "
                            "a concrete CSV cleanup pain, workaround, or buying signal."
                        ),
                        "discussion_kind": "trend_chatter",
                        "target_candidate": "CSV cleanup automation for client exports",
                        "like_count": 3,
                        "reply_count": 0,
                        "created_at": "2026-05-20T11:00:00+00:00",
                        "captured_at": "2026-05-21T15:05:00+00:00",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return fixture_path


def _write_source_config(
    tmp_path: Path,
    *,
    fixture_path: Path | None,
    cache_only: bool,
    dry_run: bool,
) -> Path:
    source = {
        "source_name": "x_discussions_cache",
        "source_type": "x",
        "trust_level": "low",
        "freshness_window_days": 7,
        "enabled": True,
        "cursor_support": True,
        "raw_snapshot_policy": "metadata_only",
        "approval_required": True,
        "credential_env_vars": ["XAI_API_KEY"],
        "rate_limit_policy": {
            "requests_per_minute": 1,
            "burst_limit": 1,
        },
        "queries": ["csv cleanup automation"],
        "max_results_per_run": 3,
        "cache_only": cache_only,
        "dry_run": dry_run,
    }
    if fixture_path is not None:
        source["fixture_path"] = str(fixture_path.name)
    config_path = tmp_path / "x-source-config.json"
    config_path.write_text(
        json.dumps(
            {
                "run_id": "x-cache-boundary",
                "sources": [source],
            }
        ),
        encoding="utf-8",
    )
    return config_path


def _config() -> LiveSourceConfig:
    return LiveSourceConfig(
        source_name="x_discussions_fixture",
        source_type="x",
        trust_level="low",
        freshness_window_days=7,
        enabled=True,
        cursor_support=True,
        raw_snapshot_policy="metadata_only",
        rate_limit_policy=RateLimitPolicy(requests_per_minute=1),
        approval_required=True,
        credential_requirements=(),
    )
