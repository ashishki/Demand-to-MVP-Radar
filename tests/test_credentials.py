from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

from demand_mvp_radar.cli import build_health_payload
from demand_mvp_radar.config import Settings
from demand_mvp_radar.credentials import (
    CredentialRequirement,
    resolve_credentials,
    resolve_live_source_credentials,
)
from demand_mvp_radar.models import RunManifest, SourceCatalogEntry
from demand_mvp_radar.sources.live import LiveSourceConfig, RateLimitPolicy


def test_credentials_resolve_from_environment_names_only() -> None:
    secret_value = "test-key-serp-secret"
    requirement = CredentialRequirement(env_var_name="SERPAPI_API_KEY")
    resolution = resolve_credentials(
        source_name="serp",
        requirements=(requirement,),
        env={"SERPAPI_API_KEY": secret_value},
    )

    assert resolution.status == "available"
    assert resolution.env_var_names == ("SERPAPI_API_KEY",)
    assert resolution.secret_value("SERPAPI_API_KEY") == secret_value

    serialized = resolution.model_dump_json()
    assert "SERPAPI_API_KEY" in serialized
    assert secret_value not in serialized

    config = LiveSourceConfig(
        source_name="serp-live",
        source_type="serp",
        trust_level="medium",
        freshness_window_days=14,
        enabled=True,
        cursor_support=True,
        raw_snapshot_policy="metadata_only",
        rate_limit_policy=RateLimitPolicy(requests_per_minute=10),
        approval_required=True,
        credential_requirements=(requirement,),
    )
    assert config.credential_requirements[0].env_var_name == "SERPAPI_API_KEY"
    assert secret_value not in config.model_dump_json()


def test_missing_credentials_are_source_scoped_errors() -> None:
    missing_source = _live_config(
        source_name="serp-live",
        source_type="serp",
        credential_env_var="SERPAPI_API_KEY",
    )
    open_source = _live_config(source_name="hacker-news", source_type="hacker_news")

    states = resolve_live_source_credentials(
        (missing_source, open_source),
        env={},
    )
    states_by_name = {state.source_name: state for state in states}

    assert states_by_name["serp-live"].credential_status == "missing"
    assert states_by_name["serp-live"].effective_enabled is False
    assert states_by_name["serp-live"].source_error is not None
    assert states_by_name["serp-live"].source_error.status == "missing"

    assert states_by_name["hacker-news"].credential_status == "not_required"
    assert states_by_name["hacker-news"].effective_enabled is True
    assert states_by_name["hacker-news"].source_error is None


def test_secret_values_are_redacted_from_outputs(tmp_path) -> None:
    secret_value = "test-key-youtube-secret"
    requirement = CredentialRequirement(env_var_name="YOUTUBE_API_KEY")
    resolution = resolve_credentials(
        source_name="youtube",
        requirements=(requirement,),
        env={"YOUTUBE_API_KEY": secret_value},
    )
    source_error = resolve_credentials(
        source_name="product_hunt",
        requirements=(CredentialRequirement(env_var_name="PRODUCT_HUNT_TOKEN"),),
        env={},
    ).to_source_error()
    assert source_error is not None

    manifest = RunManifest(
        run_id="run-credential-redaction",
        started_at=datetime(2026, 5, 21, 12, 0, tzinfo=UTC),
        ended_at=datetime(2026, 5, 21, 12, 1, tzinfo=UTC),
        status="completed",
        source_counts={"youtube": 1},
        error_counts={"product_hunt": 1},
        source_errors={"product_hunt": source_error.to_manifest_value()},
        duplicate_count=0,
        corpus_version="corpus-credentials",
        max_weekly_llm_cost_usd=Decimal("5.00"),
    )
    health_payload = build_health_payload(
        Settings(
            data_dir=tmp_path / "data",
            report_dir=tmp_path / "reports",
            source_catalog=(
                SourceCatalogEntry(
                    source_type="youtube",
                    priority="P2",
                    trust_level="medium",
                    freshness_window_days=30,
                    access_method="credentialed_api",
                    approval_required=True,
                    credential_env_vars=("YOUTUBE_API_KEY",),
                ),
            ),
        ),
        env={"YOUTUBE_API_KEY": secret_value},
    )

    outputs = (
        resolution.model_dump_json(),
        source_error.model_dump_json(),
        str(source_error),
        source_error.log_message(),
        manifest.model_dump_json(),
        json.dumps(health_payload, sort_keys=True),
    )
    for output in outputs:
        assert secret_value not in output

    assert "YOUTUBE_API_KEY" in json.dumps(health_payload, sort_keys=True)
    assert health_payload["credentials"]["youtube"]["status"] == "available"


def _live_config(
    *,
    source_name: str,
    source_type: str,
    credential_env_var: str | None = None,
) -> LiveSourceConfig:
    requirements = (
        (CredentialRequirement(env_var_name=credential_env_var),) if credential_env_var else ()
    )
    return LiveSourceConfig(
        source_name=source_name,
        source_type=source_type,
        trust_level="medium",
        freshness_window_days=14,
        enabled=True,
        cursor_support=True,
        raw_snapshot_policy="metadata_only",
        rate_limit_policy=RateLimitPolicy(requests_per_minute=60),
        approval_required=credential_env_var is not None,
        credential_requirements=requirements,
    )
