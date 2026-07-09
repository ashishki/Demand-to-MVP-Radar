from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from demand_mvp_radar.config import Settings
from demand_mvp_radar.credentials import CredentialRequirement
from demand_mvp_radar.models import OpportunityCandidate
from demand_mvp_radar.pipeline import collect_sources
from demand_mvp_radar.scoring import score_opportunity
from demand_mvp_radar.sources.live import LiveSourceConfig, RateLimitPolicy
from demand_mvp_radar.sources.reddit import RedditConnector

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "reddit"


def test_reddit_connector_maps_fixture_to_evidence() -> None:
    connector = RedditConnector(
        FIXTURE_DIR / "posts.json",
        allowed_subreddits=("SaaS",),
        queries=(),
    )

    result = connector.collect(_config(), run_id="reddit-001", cursor_state={})

    assert len(result.evidence) == 2
    post = result.evidence[0]
    comment = result.evidence[1]

    assert post.subreddit == "SaaS"
    assert post.source_url == (
        "https://www.reddit.com/r/SaaS/comments/reddit-post-001/csv_cleanup_automation/"
    )
    assert post.score == 37
    assert post.comment_count == 11
    assert post.search_query == "csv cleanup automation"
    assert post.created_at.isoformat() == "2026-05-20T10:00:00+00:00"
    assert post.captured_at.isoformat() == "2026-05-21T15:00:00+00:00"
    assert "delimiter detection" in post.normalized_text

    assert comment.comment_id == "reddit-comment-001"
    assert comment.author_hash is not None
    assert comment.search_query == "csv cleanup automation"
    assert "reddit-user-private-001" not in comment.model_dump_json()
    assert "brittle spreadsheet macro" in comment.normalized_text
    assert result.rate_limit_state.remaining == 42


def test_reddit_connector_enforces_allowlist() -> None:
    connector = RedditConnector(
        FIXTURE_DIR / "posts.json",
        allowed_subreddits=("SaaS",),
        queries=(),
    )

    result = connector.collect(_config(), run_id="reddit-001", cursor_state={})

    assert len(result.evidence) == 2
    assert len(result.quarantined) == 1
    assert "outside allowed subreddits" in result.quarantined[0].error_reason


def test_reddit_only_support_cannot_trigger_build() -> None:
    connector = RedditConnector(
        FIXTURE_DIR / "posts.json",
        allowed_subreddits=("SaaS",),
        queries=(),
    )
    result = connector.collect(_config(), run_id="reddit-001", cursor_state={})
    candidate = OpportunityCandidate(
        opportunity_id="reddit-csv-cleanup",
        normalized_pain="csv cleanup automation",
        target_audience="small SaaS operators",
        workflow="weekly client export cleanup",
        acquisition_channel="community",
        source_evidence_ids=tuple(record.source_id for record in result.evidence),
        candidate_title="CSV cleanup assistant",
    )

    score = score_opportunity(
        candidate,
        result.evidence,
        as_of=datetime(2026, 5, 21, tzinfo=UTC),
    )

    assert score.recommendation != "build"
    assert "low-trust sources require corroborating higher-trust source" in score.threshold_reasons


def test_reddit_cache_only_uses_fixture_without_credentials(tmp_path, monkeypatch) -> None:
    for env_var in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT"):
        monkeypatch.delenv(env_var, raising=False)
    fixture_payload = json.loads((FIXTURE_DIR / "posts.json").read_text(encoding="utf-8"))
    fixture_payload["posts"] = fixture_payload["posts"][:1]
    fixture_path = tmp_path / "reddit-cache.json"
    fixture_path.write_text(json.dumps(fixture_payload), encoding="utf-8")
    config_path = tmp_path / "sources.json"
    config_path.write_text(
        json.dumps(
            {
                "run_id": "reddit-cache-boundary",
                "sources": [
                    {
                        "source_name": "reddit_demand_cache",
                        "source_type": "reddit",
                        "trust_level": "medium",
                        "freshness_window_days": 14,
                        "enabled": True,
                        "cursor_support": True,
                        "raw_snapshot_policy": "metadata_only",
                        "approval_required": True,
                        "credential_env_vars": [
                            "REDDIT_CLIENT_ID",
                            "REDDIT_CLIENT_SECRET",
                            "REDDIT_USER_AGENT",
                        ],
                        "rate_limit_policy": {
                            "requests_per_minute": 4,
                            "burst_limit": 1,
                        },
                        "fixture_path": str(fixture_path.name),
                        "allowed_subreddits": ["SaaS"],
                        "queries": ["csv cleanup automation"],
                        "cache_only": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = collect_sources(
        config=config_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="reddit-cache-boundary",
    )

    assert result.evidence_count == 2
    assert result.source_counts["reddit_demand_cache"] == 2
    assert result.source_counts["source_modes"]["reddit_demand_cache"] == "cache_only"
    assert result.source_errors == {}


def test_reddit_dry_run_skips_live_collection_without_credentials(tmp_path, monkeypatch) -> None:
    for env_var in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT"):
        monkeypatch.delenv(env_var, raising=False)
    config_path = tmp_path / "sources.json"
    config_path.write_text(
        json.dumps(
            {
                "run_id": "reddit-dry-run-boundary",
                "sources": [
                    {
                        "source_name": "reddit_demand_dry_run",
                        "source_type": "reddit",
                        "trust_level": "medium",
                        "freshness_window_days": 14,
                        "enabled": True,
                        "cursor_support": True,
                        "raw_snapshot_policy": "metadata_only",
                        "approval_required": True,
                        "credential_env_vars": [
                            "REDDIT_CLIENT_ID",
                            "REDDIT_CLIENT_SECRET",
                            "REDDIT_USER_AGENT",
                        ],
                        "rate_limit_policy": {
                            "requests_per_minute": 4,
                            "burst_limit": 1,
                        },
                        "allowed_subreddits": ["SaaS"],
                        "queries": ["csv cleanup automation"],
                        "dry_run": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = collect_sources(
        config=config_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="reddit-dry-run-boundary",
    )

    assert result.evidence_count == 0
    assert result.source_counts["reddit_demand_dry_run"] == 0
    assert result.source_counts["source_modes"]["reddit_demand_dry_run"] == "dry_run"
    assert result.source_errors == {}


def _config() -> LiveSourceConfig:
    return LiveSourceConfig(
        source_name="reddit-live",
        source_type="reddit",
        trust_level="low",
        freshness_window_days=14,
        enabled=True,
        cursor_support=True,
        raw_snapshot_policy="metadata_only",
        rate_limit_policy=RateLimitPolicy(requests_per_minute=10),
        approval_required=False,
        credential_requirements=(
            CredentialRequirement(env_var_name="REDDIT_CLIENT_ID", required=False),
            CredentialRequirement(env_var_name="REDDIT_CLIENT_SECRET", required=False),
        ),
    )
