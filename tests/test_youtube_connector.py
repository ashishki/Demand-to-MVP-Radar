from __future__ import annotations

import json
from pathlib import Path

from demand_mvp_radar.cli import main
from demand_mvp_radar.credentials import CredentialRequirement
from demand_mvp_radar.sources.live import LiveSourceConfig, RateLimitPolicy
from demand_mvp_radar.sources.youtube import YouTubeConnector

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "youtube"


def test_youtube_connector_maps_fixture_to_evidence() -> None:
    connector = YouTubeConnector(
        FIXTURE_DIR / "search_results.json",
        queries=("spreadsheet cleanup automation tutorial",),
        quota_limit=1000,
        per_run_quota_limit=200,
    )

    result = connector.collect(_config(), run_id="youtube-001", cursor_state={})

    assert len(result.evidence) == 2
    video = result.evidence[0]
    comment = result.evidence[1]

    assert video.source_url == "https://www.youtube.com/watch?v=vid-spreadsheet-cleanup-001"
    assert video.video_id == "vid-spreadsheet-cleanup-001"
    assert video.comment_id is None
    assert video.search_query == "spreadsheet cleanup automation tutorial"
    assert video.published_at.isoformat() == "2026-05-20T08:00:00+00:00"
    assert video.captured_at.isoformat() == "2026-05-21T13:00:00+00:00"
    assert "spreadsheet cleanup automation" in video.normalized_text
    assert video.channel_hash is not None
    assert "UC-private-channel-001" not in video.model_dump_json()

    assert comment.source_url.endswith("&lc=comment-cleanup-001")
    assert comment.comment_id == "comment-cleanup-001"
    assert comment.video_id == "vid-spreadsheet-cleanup-001"
    assert "client CSV exports every Friday" in comment.normalized_text
    assert "UC-comment-author-001" not in comment.model_dump_json()


def test_youtube_connector_records_quota_and_page_state() -> None:
    connector = YouTubeConnector(
        FIXTURE_DIR / "search_results.json",
        queries=("spreadsheet cleanup automation tutorial",),
        quota_limit=1000,
        per_run_quota_limit=200,
        quota_used=50,
    )

    first = connector.collect(_config(), run_id="youtube-001", cursor_state={})
    second = connector.collect(
        _config(),
        run_id="youtube-001",
        cursor_state=first.cursor_state,
    )

    assert first.cursor_state["next_page_token"] == "yt-page-2"
    assert first.cursor_state["quota_used"] == "151"
    assert first.rate_limit_state.remaining == 99
    assert second.evidence == ()
    assert second.cursor_state["seen_fingerprints"] == first.cursor_state["seen_fingerprints"]


def test_youtube_connector_redacts_api_key(tmp_path, monkeypatch, capsys) -> None:
    secret_value = "test-youtube-api-key-secret"
    monkeypatch.setenv("YOUTUBE_API_KEY", secret_value)
    config_path = _write_config(tmp_path)

    exit_code = main(
        [
            "collect-sources",
            "--config",
            str(config_path),
            "--data-dir",
            str(tmp_path / "data"),
        ]
    )
    output = json.loads(capsys.readouterr().out)
    serialized = json.dumps(output, sort_keys=True)

    assert exit_code == 0
    assert output["evidence_count"] == 2
    assert output["source_counts"]["youtube-live"] == 2
    assert secret_value not in serialized
    assert "YOUTUBE_API_KEY" not in serialized


def _write_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "live-sources.json"
    config_path.write_text(
        json.dumps(
            {
                "run_id": "youtube-collect-001",
                "corpus_version": "youtube-collect-001-corpus",
                "sources": [
                    {
                        "source_name": "youtube-live",
                        "source_type": "youtube",
                        "enabled": True,
                        "trust_level": "medium",
                        "freshness_window_days": 14,
                        "cursor_support": True,
                        "raw_snapshot_policy": "metadata_only",
                        "rate_limit_policy": {"requests_per_minute": 10},
                        "approval_required": False,
                        "credential_env_vars": ["YOUTUBE_API_KEY"],
                        "fixture_path": str(FIXTURE_DIR / "search_results.json"),
                        "queries": ["spreadsheet cleanup automation tutorial"],
                        "quota_limit": 1000,
                        "per_run_quota_limit": 200,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return config_path


def _config() -> LiveSourceConfig:
    return LiveSourceConfig(
        source_name="youtube-live",
        source_type="youtube",
        trust_level="medium",
        freshness_window_days=14,
        enabled=True,
        cursor_support=True,
        raw_snapshot_policy="metadata_only",
        rate_limit_policy=RateLimitPolicy(requests_per_minute=10),
        approval_required=False,
        credential_requirements=(CredentialRequirement(env_var_name="YOUTUBE_API_KEY"),),
    )
