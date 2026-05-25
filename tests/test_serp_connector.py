from __future__ import annotations

import json
from pathlib import Path

from demand_mvp_radar.cli import main
from demand_mvp_radar.credentials import CredentialRequirement
from demand_mvp_radar.sources.live import LiveSourceConfig, RateLimitPolicy
from demand_mvp_radar.sources.serp import SERPSearchConnector

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "serp"


def test_serp_connector_maps_fixture_to_evidence() -> None:
    connector = SERPSearchConnector(
        FIXTURE_DIR / "search_results.json",
        queries=("invoice reconciliation duplicate payment",),
        provider="serpapi",
        daily_budget_limit=10,
        per_run_budget_limit=2,
    )

    result = connector.collect(_config(), run_id="serp-001", cursor_state={})

    assert len(result.evidence) == 2
    first = result.evidence[0]
    assert first.source_type == "serp"
    assert first.search_query == "invoice reconciliation duplicate payment"
    assert first.result_rank == 1
    assert first.source_url == "https://example.com/invoice-reconciliation-alerts"
    assert "duplicate payments require manual cleanup" in first.normalized_text
    assert first.captured_at.isoformat() == "2026-05-21T12:00:00+00:00"
    assert first.provider == "serpapi"
    assert first.provider_metadata == {
        "engine": "google",
        "region": "us",
        "device": "desktop",
    }
    assert first.connector_version == "serp-v1"
    assert result.rate_limit_state.limited is False


def test_serp_connector_requires_credential_name(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
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

    assert exit_code == 0
    assert output["evidence_count"] == 0
    assert output["source_counts"]["serp-live"] == 0
    assert output["error_counts"]["serp-live"] == 1
    assert "serp-live" in output["source_errors"]
    assert "missing" in output["source_errors"]["serp-live"]
    assert "SERPAPI_API_KEY" in output["source_errors"]["serp-live"]


def test_serp_connector_enforces_budget_limits(tmp_path) -> None:
    missing_fixture = tmp_path / "would-fail-if-read.json"
    connector = SERPSearchConnector(
        missing_fixture,
        queries=("invoice reconciliation duplicate payment",),
        provider="serpapi",
        daily_budget_limit=3,
        per_run_budget_limit=2,
        daily_budget_used=3,
    )

    result = connector.collect(_config(), run_id="serp-budget-001", cursor_state={})

    assert result.evidence == ()
    assert result.quarantined == ()
    assert result.rate_limit_state.limited is True
    assert result.rate_limit_state.remaining == 0
    assert result.rate_limit_state.retry_after_seconds == 86400


def _write_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "live-sources.json"
    config_path.write_text(
        json.dumps(
            {
                "run_id": "serp-collect-001",
                "corpus_version": "serp-collect-001-corpus",
                "sources": [
                    {
                        "source_name": "serp-live",
                        "source_type": "serp",
                        "enabled": True,
                        "trust_level": "medium",
                        "freshness_window_days": 14,
                        "cursor_support": True,
                        "raw_snapshot_policy": "metadata_only",
                        "rate_limit_policy": {"requests_per_minute": 10},
                        "approval_required": False,
                        "credential_env_vars": ["SERPAPI_API_KEY"],
                        "fixture_path": str(FIXTURE_DIR / "search_results.json"),
                        "queries": ["invoice reconciliation duplicate payment"],
                        "provider": "serpapi",
                        "daily_budget_limit": 10,
                        "per_run_budget_limit": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return config_path


def _config() -> LiveSourceConfig:
    return LiveSourceConfig(
        source_name="serp-live",
        source_type="serp",
        trust_level="medium",
        freshness_window_days=14,
        enabled=True,
        cursor_support=True,
        raw_snapshot_policy="metadata_only",
        rate_limit_policy=RateLimitPolicy(requests_per_minute=10),
        approval_required=False,
        credential_requirements=(CredentialRequirement(env_var_name="SERPAPI_API_KEY"),),
    )
