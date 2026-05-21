from __future__ import annotations

import json
from pathlib import Path

from demand_mvp_radar.cli import main
from demand_mvp_radar.sources.hacker_news import HackerNewsLiveConnector, author_hash
from demand_mvp_radar.sources.live import LiveSourceConfig, RateLimitPolicy

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "hacker_news"


def test_hacker_news_connector_maps_fixture_to_evidence() -> None:
    connector = HackerNewsLiveConnector(FIXTURE_DIR / "items.json")
    result = connector.collect(
        _config(),
        run_id="hn-run-001",
        cursor_state={},
    )

    assert len(result.evidence) == 2
    story = result.evidence[0]
    comment = result.evidence[1]

    assert story.title == "Developers need cleaner changelog monitoring"
    assert "Teams are manually scanning changelogs" in story.normalized_text
    assert story.source_url == "https://example.com/changelog-monitoring"
    assert story.author_hash == author_hash("founder123")
    assert story.captured_at.isoformat() == "2026-05-21T09:30:00+00:00"
    assert story.source_id == "423456"
    assert story.source_fingerprint.startswith("hacker_news:423456:")
    assert story.connector_version == "hacker-news-v1"

    assert comment.title == "HN comment 423457"
    assert comment.source_url == "https://news.ycombinator.com/item?id=423457"
    assert comment.author_hash == author_hash("ops_builder")
    assert "vendor changelog emails miss" in comment.normalized_text


def test_hacker_news_connector_persists_cursor_state() -> None:
    connector = HackerNewsLiveConnector(FIXTURE_DIR / "items.json")

    first = connector.collect(_config(), run_id="hn-run-001", cursor_state={})
    second = connector.collect(
        _config(),
        run_id="hn-run-002",
        cursor_state=first.cursor_state,
    )

    assert first.cursor_state == {"max_item_id": "423457"}
    assert len(first.evidence) == 2
    assert second.evidence == ()
    assert second.cursor_state == {"max_item_id": "423457"}


def test_hacker_news_connector_quarantines_malformed_rows() -> None:
    connector = HackerNewsLiveConnector(FIXTURE_DIR / "mixed_items.json")

    result = connector.collect(_config(), run_id="hn-run-001", cursor_state={})

    assert len(result.evidence) == 1
    assert len(result.quarantined) == 2
    assert result.source_counts == {"hacker-news": 1}
    assert result.error_counts == {"hacker-news": 2}
    assert {row.source_reference for row in result.quarantined} == {
        "hn:423458",
        "hn:row-2",
    }


def test_collect_sources_runs_hacker_news_fixture_connector(tmp_path, capsys) -> None:
    config_path = tmp_path / "live-sources.json"
    config_path.write_text(
        json.dumps(
            {
                "run_id": "hn-collect-001",
                "corpus_version": "hn-collect-001-corpus",
                "sources": [
                    {
                        "source_name": "hacker-news",
                        "source_type": "hacker_news",
                        "enabled": True,
                        "trust_level": "medium",
                        "freshness_window_days": 14,
                        "cursor_support": True,
                        "raw_snapshot_policy": "metadata_only",
                        "rate_limit_policy": {"requests_per_minute": 60},
                        "approval_required": False,
                        "fixture_path": str(FIXTURE_DIR / "items.json"),
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
    assert output["source_counts"]["hacker-news"] == 2
    assert output["error_counts"]["hacker-news"] == 0


def _config() -> LiveSourceConfig:
    return LiveSourceConfig(
        source_name="hacker-news",
        source_type="hacker_news",
        trust_level="medium",
        freshness_window_days=14,
        enabled=True,
        cursor_support=True,
        raw_snapshot_policy="metadata_only",
        rate_limit_policy=RateLimitPolicy(requests_per_minute=60),
        approval_required=False,
    )
