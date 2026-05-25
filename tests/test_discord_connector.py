from __future__ import annotations

import json
from pathlib import Path

from demand_mvp_radar.cli import build_health_payload, main
from demand_mvp_radar.config import Settings
from demand_mvp_radar.credentials import CredentialRequirement
from demand_mvp_radar.sources.discord import DiscordConnector
from demand_mvp_radar.sources.live import LiveSourceConfig, RateLimitPolicy

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "discord"


def test_discord_connector_maps_fixture_to_evidence() -> None:
    connector = DiscordConnector(
        FIXTURE_DIR / "messages.json",
        approved_channels=(_approved_channel(),),
    )

    result = connector.collect(_config(), run_id="discord-001", cursor_state={})

    assert len(result.evidence) == 1
    message = result.evidence[0]
    assert message.source_url.startswith("discord://message/")
    assert message.message_locator == message.source_url
    assert message.channel_locator_hash is not None
    assert message.author_hash is not None
    assert message.created_at.isoformat() == "2026-05-20T18:00:00+00:00"
    assert message.captured_at.isoformat() == "2026-05-21T16:00:00+00:00"
    assert "webhook replay debugging" in message.normalized_text
    assert "guild-private-001" not in message.model_dump_json()
    assert "channel-private-001" not in message.model_dump_json()
    assert "discord-author-private-001" not in message.model_dump_json()


def test_discord_connector_requires_approved_allowlist() -> None:
    connector = DiscordConnector(
        FIXTURE_DIR / "messages.json",
        approved_channels=(_approved_channel(),),
    )

    result = connector.collect(_config(), run_id="discord-001", cursor_state={})

    assert len(result.evidence) == 1
    assert len(result.quarantined) == 1
    assert "not approved" in result.quarantined[0].error_reason


def test_discord_connector_redacts_private_values(tmp_path, monkeypatch, capsys) -> None:
    secret_value = "test-discord-bot-token-secret"
    monkeypatch.setenv("DISCORD_BOT_TOKEN", secret_value)
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
    health = build_health_payload(
        Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports", source_catalog=())
    )
    serialized = json.dumps({"output": output, "health": health}, sort_keys=True)

    assert exit_code == 0
    assert output["evidence_count"] == 1
    assert secret_value not in serialized
    assert "DISCORD_BOT_TOKEN" not in serialized
    assert "founder-secret-backlog" not in serialized
    assert "guild-private-001" not in serialized
    assert "channel-private-001" not in serialized


def _write_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "live-sources.json"
    config_path.write_text(
        json.dumps(
            {
                "run_id": "discord-collect-001",
                "corpus_version": "discord-collect-001-corpus",
                "sources": [
                    {
                        "source_name": "discord-live",
                        "source_type": "discord",
                        "enabled": True,
                        "trust_level": "low",
                        "freshness_window_days": 14,
                        "cursor_support": True,
                        "raw_snapshot_policy": "metadata_only",
                        "rate_limit_policy": {"requests_per_minute": 10},
                        "approval_required": False,
                        "credential_env_vars": ["DISCORD_BOT_TOKEN"],
                        "fixture_path": str(FIXTURE_DIR / "messages.json"),
                        "approved_channels": [_approved_channel()],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return config_path


def _approved_channel() -> dict[str, object]:
    return {
        "guild_id": "guild-private-001",
        "channel_id": "channel-private-001",
        "approved": True,
    }


def _config() -> LiveSourceConfig:
    return LiveSourceConfig(
        source_name="discord-live",
        source_type="discord",
        trust_level="low",
        freshness_window_days=14,
        enabled=True,
        cursor_support=True,
        raw_snapshot_policy="metadata_only",
        rate_limit_policy=RateLimitPolicy(requests_per_minute=10),
        approval_required=False,
        credential_requirements=(CredentialRequirement(env_var_name="DISCORD_BOT_TOKEN"),),
    )
