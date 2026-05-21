"""Telegram approved-channel live fixture connector."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.sources.base import QuarantinedSourceRow
from demand_mvp_radar.sources.live import LiveConnectorResult, LiveSourceConfig, RateLimitState

SUPPORTED_CHANNEL_TYPES = {"public", "operator_owned"}


class TelegramLiveConnector:
    connector_version = "telegram-live-v1"

    def __init__(
        self,
        fixture_path: Path,
        *,
        approved_channels: tuple[dict[str, object], ...],
    ) -> None:
        self.fixture_path = fixture_path
        self.approved_channel_keys = {
            _channel_key(str(channel["channel_id"]))
            for channel in approved_channels
            if bool(channel.get("approved", False))
        }
        if not self.approved_channel_keys:
            raise ValueError("Telegram live connector requires approved channels")

    def collect(
        self,
        config: LiveSourceConfig,
        *,
        run_id: str,
        cursor_state: dict[str, str],
    ) -> LiveConnectorResult:
        payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        seen_fingerprints = _decode_seen_fingerprints(cursor_state)
        next_seen = set(seen_fingerprints)
        evidence: list[EvidenceRecord] = []
        quarantined: list[QuarantinedSourceRow] = []

        for index, row in enumerate(payload.get("messages", ())):
            try:
                if not self._is_collectable(row):
                    raise ValueError("Telegram channel is not approved or supported")
                record = _message_record(
                    row,
                    config=config,
                    run_id=run_id,
                    connector_version=self.connector_version,
                )
                next_seen.add(record.source_fingerprint)
                if record.source_fingerprint not in seen_fingerprints:
                    evidence.append(record)
            except (KeyError, TypeError, ValueError) as error:
                quarantined.append(
                    QuarantinedSourceRow(
                        source_reference=f"telegram_live:message-{index}",
                        error_reason=str(error),
                    )
                )

        return LiveConnectorResult(
            evidence=tuple(evidence),
            quarantined=tuple(quarantined),
            source_counts={config.source_name: len(evidence)},
            error_counts={config.source_name: len(quarantined)},
            cursor_state={"seen_fingerprints": _encode_seen_fingerprints(next_seen)},
            rate_limit_state=RateLimitState(limited=False),
            last_success_at=datetime.now(UTC),
        )

    def _is_collectable(self, row: object) -> bool:
        if not isinstance(row, dict):
            raise TypeError("Telegram message must be an object")
        channel_type = _required_text(row, "channel_type")
        if channel_type not in SUPPORTED_CHANNEL_TYPES:
            return False
        return _channel_key(_required_text(row, "channel_id")) in self.approved_channel_keys


def _message_record(
    row: object,
    *,
    config: LiveSourceConfig,
    run_id: str,
    connector_version: str,
) -> EvidenceRecord:
    if not isinstance(row, dict):
        raise TypeError("Telegram message must be an object")
    channel_id = _required_text(row, "channel_id")
    message_id = _required_text(row, "message_id")
    text = _normalize_text(_required_text(row, "text"))
    channel_hash = _hash_text(_channel_key(channel_id))
    message_locator = f"telegram://message/{channel_hash}/{quote(message_id, safe='')}"
    captured_at = datetime.fromisoformat(_required_text(row, "captured_at"))
    created_at = datetime.fromisoformat(_required_text(row, "created_at"))
    content_hash = _content_hash(config.source_type, channel_hash, message_id, text)
    return EvidenceRecord(
        run_id=run_id,
        source_name=config.source_name,
        source_type=config.source_type,
        source_id=f"message:{channel_hash}:{message_id}",
        source_url=message_locator,
        captured_at=captured_at,
        title=text[:80],
        snippet=text[:160],
        normalized_text=text,
        content_hash=content_hash,
        source_fingerprint=f"{config.source_type}:message:{channel_hash}:{message_id}:{content_hash}",
        connector_version=connector_version,
        channel_locator_hash=channel_hash,
        message_locator=message_locator,
        author_hash=_hash_text(_required_text(row, "author_id")),
        created_at=created_at,
    )


def _channel_key(channel_id: str) -> str:
    return channel_id


def _required_text(row: object, field: str) -> str:
    if not isinstance(row, dict):
        raise TypeError("Telegram row must be an object")
    value = row[field]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _content_hash(*parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _decode_seen_fingerprints(cursor_state: dict[str, str]) -> set[str]:
    raw_value = cursor_state.get("seen_fingerprints", "")
    return {value for value in raw_value.split("|") if value}


def _encode_seen_fingerprints(fingerprints: set[str]) -> str:
    return "|".join(sorted(fingerprints))
