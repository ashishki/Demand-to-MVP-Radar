from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from demand_mvp_radar.cli import main
from demand_mvp_radar.sources.live import LiveSourceConfig, RateLimitPolicy
from demand_mvp_radar.sources.rss import RSSFeedConnector

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "rss"


def test_rss_connector_maps_feeds_to_evidence() -> None:
    captured_at = datetime(2026, 5, 21, 12, 0, tzinfo=UTC)
    connector = RSSFeedConnector(
        (FIXTURE_DIR / "feed.xml", FIXTURE_DIR / "atom.xml"),
        captured_at=captured_at,
    )

    result = connector.collect(_config(), run_id="rss-run-001", cursor_state={})

    assert len(result.evidence) == 2
    rss_item = result.evidence[0]
    atom_item = result.evidence[1]

    assert rss_item.title == "Breaking auth changes for API clients"
    assert rss_item.source_url == "https://vendor.example.com/changelog/breaking-auth"
    assert rss_item.feed_url == "https://vendor.example.com/changelog.xml"
    assert rss_item.published_at.isoformat() == "2026-05-21T10:00:00+00:00"
    assert rss_item.captured_at == captured_at
    assert "OAuth token refresh behavior changed" in rss_item.normalized_text

    assert atom_item.title == "Release notes now require manual triage"
    assert atom_item.source_url == "https://example.com/releases/17"
    assert atom_item.feed_url == "https://example.com/atom"
    assert atom_item.published_at.isoformat() == "2026-05-21T11:00:00+00:00"
    assert "classify release notes" in atom_item.normalized_text


def test_rss_connector_dedupes_repeated_entries() -> None:
    connector = RSSFeedConnector((FIXTURE_DIR / "feed.xml",))

    first = connector.collect(_config(), run_id="rss-run-001", cursor_state={})
    second = connector.collect(
        _config(),
        run_id="rss-run-002",
        cursor_state=first.cursor_state,
    )

    assert len(first.evidence) == 1
    assert first.cursor_state["seen_fingerprints"]
    assert second.evidence == ()
    assert second.cursor_state == first.cursor_state


def test_rss_connector_records_feed_parse_errors() -> None:
    connector = RSSFeedConnector((FIXTURE_DIR / "feed.xml", FIXTURE_DIR / "malformed.xml"))

    result = connector.collect(_config(), run_id="rss-run-001", cursor_state={})

    assert len(result.evidence) == 1
    assert len(result.quarantined) == 1
    assert result.error_counts == {"rss-feeds": 1}
    assert "malformed.xml" in result.quarantined[0].source_reference
    assert "line" in result.quarantined[0].error_reason


def test_collect_sources_runs_rss_fixture_connector(tmp_path, capsys) -> None:
    config_path = tmp_path / "live-sources.json"
    config_path.write_text(
        json.dumps(
            {
                "run_id": "rss-collect-001",
                "corpus_version": "rss-collect-001-corpus",
                "sources": [
                    {
                        "source_name": "rss-feeds",
                        "source_type": "rss",
                        "enabled": True,
                        "trust_level": "medium",
                        "freshness_window_days": 14,
                        "cursor_support": True,
                        "raw_snapshot_policy": "metadata_only",
                        "rate_limit_policy": {"requests_per_minute": 60},
                        "approval_required": False,
                        "fixture_paths": [
                            str(FIXTURE_DIR / "feed.xml"),
                            str(FIXTURE_DIR / "atom.xml"),
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

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

    assert exit_code == 0
    assert output["status"] == "collected"
    assert output["evidence_count"] == 2
    assert output["source_counts"]["rss-feeds"] == 2


def _config() -> LiveSourceConfig:
    return LiveSourceConfig(
        source_name="rss-feeds",
        source_type="rss",
        trust_level="medium",
        freshness_window_days=14,
        enabled=True,
        cursor_support=True,
        raw_snapshot_policy="metadata_only",
        rate_limit_policy=RateLimitPolicy(requests_per_minute=60),
        approval_required=False,
    )
