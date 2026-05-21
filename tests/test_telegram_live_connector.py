from __future__ import annotations

from pathlib import Path

from demand_mvp_radar.credentials import CredentialRequirement
from demand_mvp_radar.sources.live import LiveSourceConfig, RateLimitPolicy
from demand_mvp_radar.sources.telegram_live import TelegramLiveConnector

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "telegram_live"


def test_telegram_live_connector_maps_fixture_to_evidence() -> None:
    connector = TelegramLiveConnector(
        FIXTURE_DIR / "messages.json",
        approved_channels=(_approved_channel(),),
    )

    result = connector.collect(_config(), run_id="telegram-live-001", cursor_state={})

    assert len(result.evidence) == 1
    message = result.evidence[0]
    assert message.source_url.startswith("telegram://message/")
    assert message.message_locator == message.source_url
    assert message.channel_locator_hash is not None
    assert message.created_at.isoformat() == "2026-05-20T19:00:00+00:00"
    assert message.captured_at.isoformat() == "2026-05-21T17:00:00+00:00"
    assert "invoice reconciliation alerts" in message.normalized_text
    assert "telegram-channel-approved-001" not in message.model_dump_json()
    assert "approved_public_channel" not in message.model_dump_json()
    assert "telegram-author-private-001" not in message.model_dump_json()


def test_telegram_live_connector_rejects_private_chats() -> None:
    connector = TelegramLiveConnector(
        FIXTURE_DIR / "messages.json",
        approved_channels=(_approved_channel(),),
    )

    result = connector.collect(_config(), run_id="telegram-live-001", cursor_state={})

    assert len(result.evidence) == 1
    assert len(result.quarantined) == 1
    assert "not approved or supported" in result.quarantined[0].error_reason


def test_telegram_live_connector_matches_export_redaction_contract() -> None:
    connector = TelegramLiveConnector(
        FIXTURE_DIR / "messages.json",
        approved_channels=(_approved_channel(),),
    )

    first = connector.collect(_config(), run_id="telegram-live-001", cursor_state={})
    second = connector.collect(
        _config(),
        run_id="telegram-live-001",
        cursor_state=first.cursor_state,
    )
    serialized = " ".join(record.model_dump_json() for record in first.evidence)
    quarantined = " ".join(row.model_dump_json() for row in first.quarantined)

    assert second.evidence == ()
    assert "private_chat_name" not in serialized
    assert "telegram-private-chat-001" not in serialized
    assert "telegram-private-chat-001" not in quarantined


def _approved_channel() -> dict[str, object]:
    return {
        "channel_id": "telegram-channel-approved-001",
        "approved": True,
    }


def _config() -> LiveSourceConfig:
    return LiveSourceConfig(
        source_name="telegram-live",
        source_type="telegram_live",
        trust_level="medium",
        freshness_window_days=14,
        enabled=True,
        cursor_support=True,
        raw_snapshot_policy="metadata_only",
        rate_limit_policy=RateLimitPolicy(requests_per_minute=10),
        approval_required=False,
        credential_requirements=(
            CredentialRequirement(env_var_name="TELEGRAM_BOT_TOKEN", required=False),
        ),
    )
