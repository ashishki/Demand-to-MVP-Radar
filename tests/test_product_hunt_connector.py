from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from demand_mvp_radar.cli import build_health_payload, main
from demand_mvp_radar.config import Settings
from demand_mvp_radar.credentials import CredentialRequirement
from demand_mvp_radar.models import OpportunityCandidate
from demand_mvp_radar.scoring import score_opportunity
from demand_mvp_radar.sources.live import LiveSourceConfig, RateLimitPolicy
from demand_mvp_radar.sources.product_hunt import ProductHuntConnector

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "product_hunt"


def test_product_hunt_connector_maps_fixture_to_evidence() -> None:
    connector = ProductHuntConnector(FIXTURE_DIR / "launches.json")

    result = connector.collect(_config(), run_id="product-hunt-001", cursor_state={})

    assert len(result.evidence) == 2
    launch = result.evidence[0]
    comment = result.evidence[1]

    assert launch.source_url == "https://www.producthunt.com/products/ledgerpulse"
    assert launch.title == "LedgerPulse"
    assert launch.topics == ("Fintech", "Productivity", "Finance")
    assert launch.launch_date.isoformat() == "2026-05-20T00:00:00+00:00"
    assert launch.vote_count == 412
    assert launch.comment_count == 18
    assert launch.captured_at.isoformat() == "2026-05-21T14:00:00+00:00"
    assert "duplicate payment detection" in launch.normalized_text

    assert comment.source_url.endswith("#comment-ph-comment-001")
    assert comment.topics == ("Fintech", "Productivity", "Finance")
    assert "invoice reconciliation alternatives" in comment.normalized_text


def test_product_hunt_connector_reports_access_mode(tmp_path, monkeypatch) -> None:
    secret_value = "test-product-hunt-token-secret"
    monkeypatch.setenv("PRODUCT_HUNT_TOKEN", secret_value)
    config_path = _write_access_mode_config(tmp_path)

    assert main(["collect-sources", "--config", str(config_path), "--data-dir", str(tmp_path)]) == 0

    payload = build_health_payload(
        Settings(data_dir=tmp_path, report_dir=tmp_path / "reports", source_catalog=())
    )
    public_source = payload["live_sources"]["product-hunt-public"]
    credentialed_source = payload["live_sources"]["product-hunt-credentialed"]
    serialized = json.dumps(payload, sort_keys=True)

    assert public_source["access_mode"] == "public"
    assert public_source["credential_required"] is False
    assert credentialed_source["access_mode"] == "credentialed"
    assert credentialed_source["credential_required"] is True
    assert secret_value not in serialized


def test_product_hunt_only_evidence_cannot_trigger_build() -> None:
    connector = ProductHuntConnector(FIXTURE_DIR / "launches.json")
    result = connector.collect(_config(), run_id="product-hunt-001", cursor_state={})
    candidate = OpportunityCandidate(
        opportunity_id="ph-ledgerpulse",
        normalized_pain="invoice reconciliation duplicate payment cleanup",
        target_audience="small finance teams",
        workflow="invoice matching",
        acquisition_channel="marketplace",
        source_evidence_ids=tuple(record.source_id for record in result.evidence),
        candidate_title="LedgerPulse competitor watcher",
    )

    score = score_opportunity(
        candidate,
        result.evidence,
        as_of=datetime(2026, 5, 21, tzinfo=UTC),
    )

    assert score.recommendation != "build"
    assert "low-trust sources require corroborating higher-trust source" in score.threshold_reasons


def _write_access_mode_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "live-sources.json"
    source = {
        "source_type": "product_hunt",
        "enabled": True,
        "trust_level": "medium",
        "freshness_window_days": 30,
        "cursor_support": True,
        "raw_snapshot_policy": "metadata_only",
        "rate_limit_policy": {"requests_per_minute": 10},
        "approval_required": False,
        "fixture_path": str(FIXTURE_DIR / "launches.json"),
    }
    config_path.write_text(
        json.dumps(
            {
                "run_id": "product-hunt-collect-001",
                "corpus_version": "product-hunt-collect-001-corpus",
                "sources": [
                    {
                        **source,
                        "source_name": "product-hunt-public",
                    },
                    {
                        **source,
                        "source_name": "product-hunt-credentialed",
                        "credential_env_vars": ["PRODUCT_HUNT_TOKEN"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return config_path


def _config() -> LiveSourceConfig:
    return LiveSourceConfig(
        source_name="product-hunt-live",
        source_type="product_hunt",
        trust_level="medium",
        freshness_window_days=30,
        enabled=True,
        cursor_support=True,
        raw_snapshot_policy="metadata_only",
        rate_limit_policy=RateLimitPolicy(requests_per_minute=10),
        approval_required=False,
        credential_requirements=(
            CredentialRequirement(env_var_name="PRODUCT_HUNT_TOKEN", required=False),
        ),
    )
