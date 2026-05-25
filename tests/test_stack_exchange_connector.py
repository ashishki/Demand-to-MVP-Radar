from __future__ import annotations

import json
from pathlib import Path

import pytest
from demand_mvp_radar.cli import main
from demand_mvp_radar.sources.live import LiveSourceConfig, RateLimitPolicy
from demand_mvp_radar.sources.stack_exchange import StackExchangeLiveConnector

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "stack_exchange"


def test_stack_exchange_connector_maps_fixture_to_evidence() -> None:
    connector = StackExchangeLiveConnector(
        FIXTURE_DIR / "items.json",
        sites=("stackoverflow",),
        tags=("api", "changelog"),
    )

    result = connector.collect(_config(), run_id="se-run-001", cursor_state={})

    assert len(result.evidence) == 2
    question = result.evidence[0]
    answer = result.evidence[1]

    assert question.title == "How do teams monitor vendor API changelog breaking changes?"
    assert "missing breaking changes" in question.normalized_text
    assert (
        question.source_url
        == "https://stackoverflow.com/questions/101/vendor-api-changelog-monitoring"
    )
    assert question.source_site == "stackoverflow"
    assert question.tags == ("api", "changelog", "monitoring")
    assert question.score == 18
    assert question.accepted_answer is True
    assert question.captured_at.isoformat() == "2026-05-21T10:00:00+00:00"

    assert answer.title == "Stack Exchange answer 202"
    assert answer.source_url == "https://stackoverflow.com/a/202"
    assert answer.accepted_answer is True
    assert answer.score == 11
    assert "watches vendor changelog feeds" in answer.normalized_text


def test_stack_exchange_connector_validates_sites_and_tags(tmp_path, capsys) -> None:
    with pytest.raises(ValueError, match="at least one site"):
        StackExchangeLiveConnector(FIXTURE_DIR / "items.json", sites=(), tags=("api",))
    with pytest.raises(ValueError, match="at least one tag"):
        StackExchangeLiveConnector(FIXTURE_DIR / "items.json", sites=("stackoverflow",), tags=())

    config_path = tmp_path / "live-sources.json"
    config_path.write_text(
        json.dumps(
            {
                "run_id": "se-collect-001",
                "corpus_version": "se-collect-001-corpus",
                "sources": [
                    {
                        "source_name": "stack-exchange",
                        "source_type": "stack_exchange",
                        "enabled": True,
                        "trust_level": "medium",
                        "freshness_window_days": 30,
                        "cursor_support": True,
                        "raw_snapshot_policy": "metadata_only",
                        "rate_limit_policy": {"requests_per_minute": 30},
                        "approval_required": False,
                        "fixture_path": str(FIXTURE_DIR / "items.json"),
                        "sites": ["stackoverflow"],
                        "tags": ["api", "changelog"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert (
        main(
            [
                "collect-sources",
                "--config",
                str(config_path),
                "--data-dir",
                str(tmp_path / "data"),
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["evidence_count"] == 2
    assert output["source_counts"]["stack-exchange"] == 2


def test_stack_exchange_connector_records_rate_limit_state() -> None:
    connector = StackExchangeLiveConnector(
        FIXTURE_DIR / "rate_limited.json",
        sites=("stackoverflow",),
        tags=("api",),
    )
    cursor_state = {"max_item_id": "101"}

    result = connector.collect(_config(), run_id="se-run-001", cursor_state=cursor_state)

    assert result.evidence == ()
    assert result.cursor_state == cursor_state
    assert result.rate_limit_state.limited is True
    assert result.rate_limit_state.retry_after_seconds == 45
    assert result.error_counts == {"stack-exchange": 1}
    assert result.quarantined[0].source_reference == "stack_exchange:stackoverflow"


def _config() -> LiveSourceConfig:
    return LiveSourceConfig(
        source_name="stack-exchange",
        source_type="stack_exchange",
        trust_level="medium",
        freshness_window_days=30,
        enabled=True,
        cursor_support=True,
        raw_snapshot_policy="metadata_only",
        rate_limit_policy=RateLimitPolicy(requests_per_minute=30),
        approval_required=False,
    )
