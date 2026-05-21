"""Stack Exchange live connector."""

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

MIN_BODY_LENGTH = 30


class StackExchangeLiveConnector:
    connector_version = "stack-exchange-v1"

    def __init__(
        self,
        fixture_path: Path,
        *,
        sites: tuple[str, ...],
        tags: tuple[str, ...],
    ) -> None:
        if not sites:
            raise ValueError("Stack Exchange connector requires at least one site")
        if not tags:
            raise ValueError("Stack Exchange connector requires at least one tag")
        self.fixture_path = fixture_path
        self.sites = sites
        self.tags = tags

    def collect(
        self,
        config: LiveSourceConfig,
        *,
        run_id: str,
        cursor_state: dict[str, str],
    ) -> LiveConnectorResult:
        payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        if "backoff_seconds" in payload:
            retry_after_seconds = int(payload["backoff_seconds"])
            return LiveConnectorResult(
                evidence=(),
                quarantined=(
                    QuarantinedSourceRow(
                        source_reference=f"stack_exchange:{','.join(self.sites)}",
                        error_reason=f"Stack Exchange backoff requested: {retry_after_seconds}s",
                    ),
                ),
                source_counts={config.source_name: 0},
                error_counts={config.source_name: 1},
                cursor_state=cursor_state,
                rate_limit_state=RateLimitState(
                    limited=True,
                    retry_after_seconds=retry_after_seconds,
                ),
                last_success_at=None,
            )

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
                if not _matches_config(row, sites=self.sites, tags=self.tags):
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


def _evidence_from_item(
    row: object,
    *,
    config: LiveSourceConfig,
    run_id: str,
    connector_version: str,
) -> EvidenceRecord:
    if not isinstance(row, dict):
        raise TypeError("Stack Exchange item must be an object")
    item_type = _required_text(row, "type")
    item_id = _item_id(row)
    body = _normalize_text(_required_text(row, "body"))
    if len(body) < MIN_BODY_LENGTH:
        raise ValueError("Stack Exchange item body is too short")

    title = _title(row, item_type=item_type, item_id=item_id)
    site = _required_text(row, "site")
    tags = _tags(row)
    score = _score(row)
    accepted_answer = _accepted_answer(row, item_type=item_type)
    source_url = _required_text(row, "link")
    captured_at = datetime.fromisoformat(_required_text(row, "captured_at"))
    content_hash = _content_hash(config.source_type, site, str(item_id), body)

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
        source_fingerprint=f"{config.source_type}:{site}:{item_id}:{content_hash}",
        connector_version=connector_version,
        source_site=site,
        tags=tags,
        score=score,
        accepted_answer=accepted_answer,
    )


def _matches_config(row: object, *, sites: tuple[str, ...], tags: tuple[str, ...]) -> bool:
    if not isinstance(row, dict):
        raise TypeError("Stack Exchange item must be an object")
    return _required_text(row, "site") in sites and bool(set(_tags(row)) & set(tags))


def _item_id(row: object) -> int:
    if not isinstance(row, dict):
        raise TypeError("Stack Exchange item must be an object")
    if row.get("type") == "answer":
        value = row["answer_id"]
    else:
        value = row["question_id"]
    if not isinstance(value, int) or value <= 0:
        raise ValueError("Stack Exchange item id must be a positive integer")
    return value


def _title(row: dict[str, Any], *, item_type: str, item_id: int) -> str:
    if item_type == "question":
        return _required_text(row, "title")
    if item_type == "answer":
        return f"Stack Exchange answer {item_id}"
    raise ValueError(f"unsupported Stack Exchange item type: {item_type}")


def _tags(row: dict[str, Any]) -> tuple[str, ...]:
    value = row["tags"]
    if not isinstance(value, list) or not value:
        raise ValueError("Stack Exchange item tags are required")
    tags = tuple(str(tag).strip() for tag in value if str(tag).strip())
    if not tags:
        raise ValueError("Stack Exchange item tags are required")
    return tags


def _score(row: dict[str, Any]) -> int:
    value = row["score"]
    if not isinstance(value, int):
        raise ValueError("Stack Exchange item score must be an integer")
    return value


def _accepted_answer(row: dict[str, Any], *, item_type: str) -> bool:
    if item_type == "question":
        return bool(row.get("accepted_answer_id"))
    return bool(row.get("is_accepted", False))


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
    if isinstance(row, dict):
        for field in ("answer_id", "question_id"):
            if isinstance(row.get(field), int):
                return f"stack_exchange:{row[field]}"
    return f"stack_exchange:row-{index}"
