"""Hacker News live connector."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.sources.base import QuarantinedSourceRow
from demand_mvp_radar.sources.live import LiveConnectorResult, LiveSourceConfig, RateLimitState

MIN_TEXT_LENGTH = 20


class HackerNewsLiveConnector:
    connector_version = "hacker-news-v1"

    def __init__(self, fixture_path: Path) -> None:
        self.fixture_path = fixture_path

    def collect(
        self,
        config: LiveSourceConfig,
        *,
        run_id: str,
        cursor_state: dict[str, str],
    ) -> LiveConnectorResult:
        payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        previous_max_item_id = int(cursor_state.get("max_item_id", "0"))
        max_item_id = previous_max_item_id
        evidence: list[EvidenceRecord] = []
        quarantined: list[QuarantinedSourceRow] = []

        for index, row in enumerate(payload.get("items", ())):
            try:
                item_id = _item_id(row)
                max_item_id = max(max_item_id, item_id)
                if item_id <= previous_max_item_id:
                    continue
                evidence.append(
                    _evidence_from_item(
                        row,
                        config=config,
                        run_id=run_id,
                        connector_version=self.connector_version,
                    )
                )
            except (KeyError, TypeError, ValueError) as error:
                quarantined.append(
                    QuarantinedSourceRow(
                        source_reference=_source_reference(row, index),
                        error_reason=str(error),
                    )
                )

        return LiveConnectorResult(
            evidence=tuple(evidence),
            quarantined=tuple(quarantined),
            source_counts={config.source_name: len(evidence)},
            error_counts={config.source_name: len(quarantined)},
            cursor_state={"max_item_id": str(max_item_id)},
            rate_limit_state=RateLimitState(limited=False),
            last_success_at=datetime.now(UTC),
        )


def author_hash(author: str) -> str:
    return hashlib.sha256(author.encode("utf-8")).hexdigest()


def _evidence_from_item(
    row: object,
    *,
    config: LiveSourceConfig,
    run_id: str,
    connector_version: str,
) -> EvidenceRecord:
    if not isinstance(row, dict):
        raise TypeError("Hacker News item must be an object")
    item_id = _item_id(row)
    item_type = _required_text(row, "type")
    body = _normalize_text(_required_text(row, "text"))
    if len(body) < MIN_TEXT_LENGTH:
        raise ValueError("Hacker News item text is too short")

    title = _title(row, item_type=item_type, item_id=item_id)
    source_url = _source_url(row, item_id=item_id)
    captured_at = _captured_at(row)
    author = _required_text(row, "by")
    content_hash = _content_hash(config.source_type, str(item_id), title, body)

    return EvidenceRecord(
        run_id=run_id,
        source_name=config.source_name,
        source_type=config.source_type,
        source_id=str(item_id),
        source_url=source_url,
        captured_at=captured_at,
        title=title,
        snippet=body[:160],
        normalized_text=f"{title}\n\n{body}",
        content_hash=content_hash,
        source_fingerprint=f"{config.source_type}:{item_id}:{content_hash}",
        connector_version=connector_version,
        author_hash=author_hash(author),
    )


def _item_id(row: object) -> int:
    if not isinstance(row, dict):
        raise TypeError("Hacker News item must be an object")
    value = row["id"]
    if not isinstance(value, int) or value <= 0:
        raise ValueError("Hacker News item id must be a positive integer")
    return value


def _title(row: dict[str, Any], *, item_type: str, item_id: int) -> str:
    if item_type == "story":
        return _required_text(row, "title")
    if item_type == "comment":
        return f"HN comment {item_id}"
    raise ValueError(f"unsupported Hacker News item type: {item_type}")


def _source_url(row: dict[str, Any], *, item_id: int) -> str:
    value = row.get("url")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return f"https://news.ycombinator.com/item?id={item_id}"


def _captured_at(row: dict[str, Any]) -> datetime:
    if "captured_at" in row:
        return datetime.fromisoformat(_required_text(row, "captured_at"))
    timestamp = row["time"]
    if not isinstance(timestamp, int):
        raise ValueError("Hacker News item time must be a unix timestamp")
    return datetime.fromtimestamp(timestamp, tz=UTC)


def _required_text(row: dict[str, Any], field: str) -> str:
    value = row[field]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _content_hash(*parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _source_reference(row: object, index: int) -> str:
    if isinstance(row, dict) and isinstance(row.get("id"), int):
        return f"hn:{row['id']}"
    return f"hn:row-{index}"
