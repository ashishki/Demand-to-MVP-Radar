from __future__ import annotations

import json
from pathlib import Path

from demand_mvp_radar.cli import main
from demand_mvp_radar.credentials import CredentialRequirement, resolve_credentials
from demand_mvp_radar.sources.github_public import GitHubPublicSearchConnector
from demand_mvp_radar.sources.live import LiveSourceConfig, RateLimitPolicy

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "github_public"


def test_github_public_connector_maps_search_results() -> None:
    connector = GitHubPublicSearchConnector(
        FIXTURE_DIR / "search_results.json",
        queries=("breaking changelog",),
    )

    result = connector.collect(_config(), run_id="github-public-001", cursor_state={})

    assert len(result.evidence) == 2
    issue = result.evidence[0]
    discussion = result.evidence[1]

    assert issue.title == "Need alerts for breaking API changelog entries"
    assert issue.repository_locator == "octo/api-client"
    assert issue.source_url == "https://github.com/octo/api-client/issues/17"
    assert issue.labels == ("api", "changelog", "monitoring")
    assert issue.created_at.isoformat() == "2026-05-20T09:00:00+00:00"
    assert issue.updated_at.isoformat() == "2026-05-21T09:00:00+00:00"
    assert issue.captured_at.isoformat() == "2026-05-21T12:00:00+00:00"
    assert issue.source_fingerprint.startswith("github_public:octo/api-client:issue:17:")

    assert discussion.repository_locator == "octo/platform"
    assert discussion.source_url == "https://github.com/octo/platform/discussions/42"
    assert discussion.labels == ("release-notes", "ops")


def test_github_public_connector_supports_optional_token(tmp_path, capsys) -> None:
    token_value = "test-gh-token-secret"
    credential = CredentialRequirement(env_var_name="GITHUB_TOKEN", required=False)
    resolution = resolve_credentials(
        source_name="github-public",
        requirements=(credential,),
        env={"GITHUB_TOKEN": token_value},
    )
    assert resolution.status == "available"
    assert token_value not in resolution.model_dump_json()

    config_path = tmp_path / "live-sources.json"
    config_path.write_text(
        json.dumps(
            {
                "run_id": "github-public-collect-001",
                "corpus_version": "github-public-collect-001-corpus",
                "sources": [
                    {
                        "source_name": "github-public",
                        "source_type": "github_public",
                        "enabled": True,
                        "trust_level": "medium",
                        "freshness_window_days": 14,
                        "cursor_support": True,
                        "raw_snapshot_policy": "metadata_only",
                        "rate_limit_policy": {"requests_per_minute": 30},
                        "approval_required": False,
                        "credential_env_vars": ["GITHUB_TOKEN"],
                        "fixture_path": str(FIXTURE_DIR / "search_results.json"),
                        "queries": ["breaking changelog"],
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
    assert output["evidence_count"] == 2
    assert output["source_counts"]["github-public"] == 2
    assert token_value not in json.dumps(output, sort_keys=True)


def test_github_public_connector_redacts_private_values() -> None:
    connector = GitHubPublicSearchConnector(
        FIXTURE_DIR / "private_results.json",
        queries=("breaking changelog",),
    )

    result = connector.collect(_config(), run_id="github-public-001", cursor_state={})
    serialized = " ".join(record.model_dump_json() for record in result.evidence)
    quarantined = " ".join(row.model_dump_json() for row in result.quarantined)

    assert len(result.evidence) == 1
    assert len(result.quarantined) == 2
    assert "https://github.com/private/repo" not in serialized
    assert "/home/ashishki" not in serialized
    assert "private/repo" in quarantined
    assert "local path" in quarantined


def _config() -> LiveSourceConfig:
    return LiveSourceConfig(
        source_name="github-public",
        source_type="github_public",
        trust_level="medium",
        freshness_window_days=14,
        enabled=True,
        cursor_support=True,
        raw_snapshot_policy="metadata_only",
        rate_limit_policy=RateLimitPolicy(requests_per_minute=30),
        approval_required=False,
        credential_requirements=(
            CredentialRequirement(env_var_name="GITHUB_TOKEN", required=False),
        ),
    )
