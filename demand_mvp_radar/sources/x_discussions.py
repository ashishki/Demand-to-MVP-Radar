"""Cache-first X/Twitter corroboration connector."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.sources.base import QuarantinedSourceRow
from demand_mvp_radar.sources.live import LiveConnectorResult, LiveSourceConfig, RateLimitState

MIN_TEXT_LENGTH = 20
DISCUSSION_KINDS = {"pain", "workaround", "wtp", "trend_chatter"}


class XDiscussionConnector:
    connector_version = "x-discussions-v1"

    def __init__(
        self,
        fixture_path: Path | None,
        *,
        queries: tuple[str, ...] = (),
        max_results_per_run: int = 10,
    ) -> None:
        if fixture_path is None:
            raise ValueError("X discussion connector requires a cache fixture")
        self.fixture_path = fixture_path
        self.queries = tuple(query for query in queries if query.strip())
        self.max_results_per_run = max(1, min(max_results_per_run, 25))

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

        for index, row in enumerate(_discussions(payload)):
            try:
                if len(evidence) >= self.max_results_per_run:
                    raise ValueError("X discussion result limit exceeded")
                record = _discussion_record(
                    row,
                    config=config,
                    run_id=run_id,
                    connector_version=self.connector_version,
                    allowed_queries=self.queries,
                )
                next_seen.add(record.source_fingerprint)
                if record.source_fingerprint not in seen_fingerprints:
                    evidence.append(record)
            except (KeyError, TypeError, ValueError) as error:
                quarantined.append(
                    QuarantinedSourceRow(
                        source_reference=f"x:discussion-{index}",
                        error_reason=str(error),
                    )
                )

        rate_limit = dict(payload.get("rate_limit", {}))
        return LiveConnectorResult(
            evidence=tuple(evidence),
            quarantined=tuple(quarantined),
            source_counts={config.source_name: len(evidence)},
            error_counts={config.source_name: len(quarantined)},
            cursor_state={"seen_fingerprints": _encode_seen_fingerprints(next_seen)},
            rate_limit_state=RateLimitState(
                limited=bool(rate_limit.get("limited", False)),
                remaining=rate_limit.get("remaining"),
                retry_after_seconds=rate_limit.get("retry_after_seconds"),
            ),
            last_success_at=datetime.now(UTC),
        )


def _discussion_record(
    row: object,
    *,
    config: LiveSourceConfig,
    run_id: str,
    connector_version: str,
    allowed_queries: tuple[str, ...],
) -> EvidenceRecord:
    if not isinstance(row, dict):
        raise TypeError("X discussion row must be an object")
    query = _optional_text(row.get("query"))
    if allowed_queries and query not in allowed_queries:
        raise ValueError("X discussion query is outside configured query list")
    discussion_id = _required_text(row, "discussion_id")
    source_url = _x_url(row)
    title = _required_text(row, "title")
    text = _normalize_text(_required_text(row, "text"))
    if len(text) < MIN_TEXT_LENGTH:
        raise ValueError("X discussion text is too short")
    discussion_kind = _discussion_kind(row)
    created_at = datetime.fromisoformat(_required_text(row, "created_at"))
    captured_at = datetime.fromisoformat(_required_text(row, "captured_at"))
    like_count = _non_negative_int(row, "like_count")
    reply_count = _non_negative_int(row, "reply_count")
    target_candidate = _optional_text(row.get("target_candidate"))
    content_hash = _content_hash(
        config.source_type,
        discussion_id,
        source_url,
        text,
        discussion_kind,
    )
    metadata = {
        "discussion_kind": discussion_kind,
        "evidence_kind": _evidence_kind_for_discussion(discussion_kind),
        "lower_confidence": "true",
        "corroboration_required": "true",
    }
    if target_candidate:
        metadata["target_candidate"] = target_candidate
        metadata["mvp_shape"] = target_candidate
    return EvidenceRecord(
        run_id=run_id,
        source_name=config.source_name,
        source_type=config.source_type,
        source_id=f"discussion:{discussion_id}",
        source_url=source_url,
        captured_at=captured_at,
        title=title,
        snippet=text[:160],
        normalized_text=_normalized_discussion_text(
            title=title,
            text=text,
            discussion_kind=discussion_kind,
            like_count=like_count,
            reply_count=reply_count,
        ),
        content_hash=content_hash,
        source_fingerprint=f"{config.source_type}:discussion:{discussion_id}:{content_hash}",
        connector_version=connector_version,
        author_hash=_author_hash(_required_text(row, "author_id")),
        search_query=query,
        provider="x-research",
        provider_metadata=metadata,
        score=like_count,
        comment_count=reply_count,
        created_at=created_at,
    )


def _normalized_discussion_text(
    *,
    title: str,
    text: str,
    discussion_kind: str,
    like_count: int,
    reply_count: int,
) -> str:
    return "\n\n".join(
        (
            title,
            text,
            f"Discussion kind: {discussion_kind}.",
            "Confidence: lower; X/Twitter is corroboration only.",
            f"Likes: {like_count}. Replies: {reply_count}.",
        )
    )


def _discussions(payload: object) -> tuple[object, ...]:
    if not isinstance(payload, dict):
        raise TypeError("X discussion payload must be an object")
    discussions = payload.get("discussions", ())
    if not isinstance(discussions, list):
        raise ValueError("X discussions must be a list")
    return tuple(discussions)


def _x_url(row: dict[str, object]) -> str:
    source_url = _required_text(row, "url")
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or parsed.hostname not in {"x.com", "twitter.com"}:
        raise ValueError("X discussion URL must be an absolute x.com/twitter.com URL")
    return source_url


def _discussion_kind(row: dict[str, object]) -> str:
    discussion_kind = _required_text(row, "discussion_kind").lower()
    if discussion_kind not in DISCUSSION_KINDS:
        raise ValueError("X discussion_kind must be one of: " + ", ".join(sorted(DISCUSSION_KINDS)))
    return discussion_kind


def _evidence_kind_for_discussion(discussion_kind: str) -> str:
    if discussion_kind == "workaround":
        return "manual_workaround"
    if discussion_kind == "wtp":
        return "wtp_signal"
    if discussion_kind == "trend_chatter":
        return "negative_signal"
    return "repeated_complaint"


def _required_text(row: object, field: str) -> str:
    if not isinstance(row, dict):
        raise TypeError("X discussion row must be an object")
    value = row[field]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _non_negative_int(row: dict[str, object], field: str) -> int:
    value = row[field]
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _author_hash(author_id: str) -> str:
    return hashlib.sha256(author_id.encode("utf-8")).hexdigest()


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


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
