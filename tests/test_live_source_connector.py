from datetime import UTC, datetime

import pytest
from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.sources.base import QuarantinedSourceRow
from demand_mvp_radar.sources.live import (
    LiveConnectorResult,
    LiveSourceConfig,
    RateLimitPolicy,
    RateLimitState,
)
from pydantic import ValidationError


def test_live_source_config_validates_required_fields() -> None:
    config = LiveSourceConfig(
        source_name="hacker-news-front-page",
        source_type="hacker_news",
        trust_level="medium",
        freshness_window_days=14,
        enabled=True,
        cursor_support=True,
        raw_snapshot_policy="metadata_only",
        rate_limit_policy=RateLimitPolicy(requests_per_minute=60, burst_limit=10),
        approval_required=False,
    )

    assert config.source_name == "hacker-news-front-page"
    assert config.source_type == "hacker_news"
    assert config.cursor_support is True
    assert config.raw_snapshot_policy == "metadata_only"
    assert config.rate_limit_policy.requests_per_minute == 60

    with pytest.raises(ValidationError):
        LiveSourceConfig(
            source_name="",
            source_type="hacker_news",
            trust_level="medium",
            freshness_window_days=14,
            enabled=True,
            cursor_support=True,
            raw_snapshot_policy="metadata_only",
            rate_limit_policy=RateLimitPolicy(requests_per_minute=60),
            approval_required=False,
        )

    with pytest.raises(ValidationError):
        LiveSourceConfig(
            source_name="serp-live",
            source_type="serp",
            trust_level="unknown",
            freshness_window_days=14,
            enabled=True,
            cursor_support=True,
            raw_snapshot_policy="full",
            rate_limit_policy=RateLimitPolicy(requests_per_minute=60),
            approval_required=True,
        )


def test_connector_result_preserves_collection_metadata() -> None:
    captured_at = datetime(2026, 5, 21, 9, 30, tzinfo=UTC)
    evidence = _live_evidence(captured_at=captured_at)
    result = LiveConnectorResult(
        evidence=(evidence,),
        quarantined=(
            QuarantinedSourceRow(
                source_reference="hn:item:bad-row",
                error_reason="missing text",
            ),
        ),
        source_counts={"hacker-news-front-page": 1},
        error_counts={"hacker-news-front-page": 1},
        cursor_state={"last_item_id": "423456"},
        rate_limit_state=RateLimitState(
            limited=False,
            remaining=42,
            reset_at=captured_at,
        ),
        last_success_at=captured_at,
    )

    assert result.evidence == (evidence,)
    assert result.quarantined[0].source_reference == "hn:item:bad-row"
    assert result.source_counts == {"hacker-news-front-page": 1}
    assert result.error_counts == {"hacker-news-front-page": 1}
    assert result.cursor_state == {"last_item_id": "423456"}
    assert result.rate_limit_state.remaining == 42
    assert result.last_success_at == captured_at


def test_live_evidence_preserves_required_provenance() -> None:
    evidence = _live_evidence(captured_at=datetime(2026, 5, 21, 9, 30, tzinfo=UTC))
    result = LiveConnectorResult(
        evidence=(evidence,),
        source_counts={"hacker-news-front-page": 1},
        error_counts={},
        cursor_state={},
        rate_limit_state=RateLimitState(limited=False),
        last_success_at=evidence.captured_at,
    )

    live_evidence = result.evidence[0]
    assert live_evidence.source_name == "hacker-news-front-page"
    assert live_evidence.source_type == "hacker_news"
    assert live_evidence.source_url == "https://news.ycombinator.com/item?id=423456"
    assert live_evidence.captured_at == evidence.captured_at
    assert live_evidence.content_hash == "a" * 64
    assert live_evidence.source_fingerprint == "hacker_news:423456:" + ("a" * 64)
    assert live_evidence.connector_version == "hacker-news-v1"
    assert live_evidence.run_id == "run-live-001"

    with pytest.raises(ValidationError):
        LiveConnectorResult(
            evidence=(evidence.model_copy(update={"connector_version": None}),),
            source_counts={"hacker-news-front-page": 1},
            error_counts={},
            cursor_state={},
            rate_limit_state=RateLimitState(limited=False),
            last_success_at=evidence.captured_at,
        )


def _live_evidence(*, captured_at: datetime) -> EvidenceRecord:
    content_hash = "a" * 64
    return EvidenceRecord(
        run_id="run-live-001",
        source_name="hacker-news-front-page",
        source_type="hacker_news",
        source_id="423456",
        source_url="https://news.ycombinator.com/item?id=423456",
        captured_at=captured_at,
        title="Developers need cleaner changelog monitoring",
        snippet="Teams are manually scanning changelogs for breaking changes.",
        normalized_text="Teams are manually scanning changelogs for breaking changes.",
        content_hash=content_hash,
        source_fingerprint=f"hacker_news:423456:{content_hash}",
        connector_version="hacker-news-v1",
    )
