"""YouTube fixture connector."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.sources.base import QuarantinedSourceRow
from demand_mvp_radar.sources.live import LiveConnectorResult, LiveSourceConfig, RateLimitState

MIN_TEXT_LENGTH = 20


class YouTubeConnector:
    connector_version = "youtube-v1"

    def __init__(
        self,
        fixture_path: Path | None,
        *,
        queries: tuple[str, ...],
        quota_limit: int,
        per_run_quota_limit: int,
        quota_used: int = 0,
        api_key: str | None = None,
        results_per_query: int = 10,
        timeout_seconds: int = 20,
    ) -> None:
        if not queries:
            raise ValueError("YouTube connector requires at least one query")
        if quota_limit < 0 or per_run_quota_limit < 0 or quota_used < 0:
            raise ValueError("YouTube quota values must be non-negative")
        self.fixture_path = fixture_path
        self.queries = queries
        self.quota_limit = quota_limit
        self.per_run_quota_limit = per_run_quota_limit
        self.quota_used = quota_used
        self.api_key = api_key.strip() if api_key else None
        self.results_per_query = max(1, min(results_per_query, 25))
        self.timeout_seconds = timeout_seconds

    def collect(
        self,
        config: LiveSourceConfig,
        *,
        run_id: str,
        cursor_state: dict[str, str],
    ) -> LiveConnectorResult:
        remaining_quota = min(
            self.per_run_quota_limit,
            max(self.quota_limit - self.quota_used, 0),
        )
        if remaining_quota <= 0:
            return LiveConnectorResult(
                evidence=(),
                quarantined=(),
                source_counts={config.source_name: 0},
                error_counts={config.source_name: 0},
                cursor_state=cursor_state,
                rate_limit_state=RateLimitState(
                    limited=True,
                    remaining=0,
                    retry_after_seconds=86400,
                ),
                last_success_at=None,
            )

        payload = (
            json.loads(self.fixture_path.read_text(encoding="utf-8"))
            if self.fixture_path is not None
            else self._live_payload(max_quota=remaining_quota)
        )
        seen_fingerprints = _decode_seen_fingerprints(cursor_state)
        next_seen = set(seen_fingerprints)
        evidence: list[EvidenceRecord] = []
        quarantined: list[QuarantinedSourceRow] = []
        consumed_quota = 0
        next_page_token = ""

        for search_index, search in enumerate(payload.get("searches", ())):
            try:
                query = _required_text(search, "query")
                if query not in self.queries:
                    continue
                quota_cost = _non_negative_int(search, "quota_cost")
                if consumed_quota + quota_cost > remaining_quota:
                    break
                consumed_quota += quota_cost
                next_page_token = str(search.get("next_page_token", ""))
                captured_at = datetime.fromisoformat(
                    str(search.get("captured_at", payload["captured_at"]))
                )
                for video in _videos(search):
                    try:
                        video_record = _video_record(
                            video,
                            config=config,
                            run_id=run_id,
                            connector_version=self.connector_version,
                            query=query,
                            captured_at=captured_at,
                        )
                        next_seen.add(video_record.source_fingerprint)
                        if video_record.source_fingerprint not in seen_fingerprints:
                            evidence.append(video_record)
                        for comment in _comments(video):
                            comment_record = _comment_record(
                                comment,
                                video=video,
                                config=config,
                                run_id=run_id,
                                connector_version=self.connector_version,
                                query=query,
                                captured_at=captured_at,
                            )
                            next_seen.add(comment_record.source_fingerprint)
                            if comment_record.source_fingerprint not in seen_fingerprints:
                                evidence.append(comment_record)
                    except (KeyError, TypeError, ValueError) as error:
                        quarantined.append(
                            QuarantinedSourceRow(
                                source_reference=f"youtube:{query}:video",
                                error_reason=str(error),
                            )
                        )
            except (KeyError, TypeError, ValueError) as error:
                quarantined.append(
                    QuarantinedSourceRow(
                        source_reference=f"youtube:search-{search_index}",
                        error_reason=str(error),
                    )
                )

        return LiveConnectorResult(
            evidence=tuple(evidence),
            quarantined=tuple(quarantined),
            source_counts={config.source_name: len(evidence)},
            error_counts={config.source_name: len(quarantined)},
            cursor_state={
                "next_page_token": next_page_token,
                "quota_used": str(self.quota_used + consumed_quota),
                "seen_fingerprints": _encode_seen_fingerprints(next_seen),
            },
            rate_limit_state=RateLimitState(
                limited=False,
                remaining=max(remaining_quota - consumed_quota, 0),
            ),
            last_success_at=datetime.now(UTC),
        )

    def _live_payload(self, *, max_quota: int) -> dict[str, object]:
        if not self.api_key:
            raise ValueError("YouTube live collection requires api_key")
        searches: list[dict[str, object]] = []
        consumed = 0
        for query in self.queries:
            quota_cost = 100
            if consumed + quota_cost > max_quota:
                break
            consumed += quota_cost
            params = urlencode(
                {
                    "part": "snippet",
                    "type": "video",
                    "order": "relevance",
                    "maxResults": str(self.results_per_query),
                    "q": query,
                    "key": self.api_key,
                }
            )
            request = Request(
                f"https://www.googleapis.com/youtube/v3/search?{params}",
                headers={"User-Agent": "Demand-to-MVP-Radar/0.1"},
            )
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            videos = []
            for item in payload.get("items", ()):
                if not isinstance(item, dict):
                    continue
                video_id = (
                    item.get("id", {}).get("videoId") if isinstance(item.get("id"), dict) else None
                )
                snippet = item.get("snippet", {}) if isinstance(item.get("snippet"), dict) else {}
                title = str(snippet.get("title") or "").strip()
                description = str(snippet.get("description") or title).strip()
                channel_id = str(snippet.get("channelId") or "unknown-channel").strip()
                published_at = str(snippet.get("publishedAt") or datetime.now(UTC).isoformat())
                if video_id and title:
                    videos.append(
                        {
                            "video_id": str(video_id),
                            "title": title,
                            "description": description,
                            "channel_id": channel_id,
                            "published_at": published_at.replace("Z", "+00:00"),
                            "comments": [],
                        }
                    )
            searches.append(
                {
                    "query": query,
                    "quota_cost": quota_cost,
                    "captured_at": datetime.now(UTC).isoformat(),
                    "next_page_token": str(payload.get("nextPageToken", "")),
                    "videos": videos,
                }
            )
        return {"captured_at": datetime.now(UTC).isoformat(), "searches": searches}


def _video_record(
    row: object,
    *,
    config: LiveSourceConfig,
    run_id: str,
    connector_version: str,
    query: str,
    captured_at: datetime,
) -> EvidenceRecord:
    if not isinstance(row, dict):
        raise TypeError("YouTube video must be an object")
    video_id = _required_text(row, "video_id")
    title = _required_text(row, "title")
    description = _normalize_text(_required_text(row, "description"))
    if len(description) < MIN_TEXT_LENGTH:
        raise ValueError("YouTube video description is too short")
    channel_hash = _channel_hash(_required_text(row, "channel_id"))
    published_at = datetime.fromisoformat(_required_text(row, "published_at"))
    source_url = _video_url(video_id)
    content_hash = _content_hash(config.source_type, query, video_id, title, description)
    return EvidenceRecord(
        run_id=run_id,
        source_name=config.source_name,
        source_type=config.source_type,
        source_id=f"video:{video_id}",
        source_url=source_url,
        captured_at=captured_at,
        title=title,
        snippet=description[:160],
        normalized_text=f"{title}\n\n{description}",
        content_hash=content_hash,
        source_fingerprint=f"{config.source_type}:video:{video_id}:{content_hash}",
        connector_version=connector_version,
        search_query=query,
        channel_hash=channel_hash,
        video_id=video_id,
        published_at=published_at,
    )


def _comment_record(
    row: object,
    *,
    video: object,
    config: LiveSourceConfig,
    run_id: str,
    connector_version: str,
    query: str,
    captured_at: datetime,
) -> EvidenceRecord:
    if not isinstance(video, dict):
        raise TypeError("YouTube video must be an object")
    if not isinstance(row, dict):
        raise TypeError("YouTube comment must be an object")
    video_id = _required_text(video, "video_id")
    comment_id = _required_text(row, "comment_id")
    text = _normalize_text(_required_text(row, "text"))
    if len(text) < MIN_TEXT_LENGTH:
        raise ValueError("YouTube comment text is too short")
    channel_hash = _channel_hash(_required_text(row, "author_channel_id"))
    published_at = datetime.fromisoformat(_required_text(row, "published_at"))
    source_url = f"{_video_url(video_id)}&lc={quote(comment_id, safe='')}"
    title = f"Comment on {_required_text(video, 'title')}"
    content_hash = _content_hash(config.source_type, query, video_id, comment_id, text)
    return EvidenceRecord(
        run_id=run_id,
        source_name=config.source_name,
        source_type=config.source_type,
        source_id=f"comment:{video_id}:{comment_id}",
        source_url=source_url,
        captured_at=captured_at,
        title=title,
        snippet=text[:160],
        normalized_text=f"{title}\n\n{text}",
        content_hash=content_hash,
        source_fingerprint=f"{config.source_type}:comment:{video_id}:{comment_id}:{content_hash}",
        connector_version=connector_version,
        search_query=query,
        channel_hash=channel_hash,
        video_id=video_id,
        comment_id=comment_id,
        published_at=published_at,
    )


def _videos(search: object) -> tuple[object, ...]:
    if not isinstance(search, dict):
        raise TypeError("YouTube search must be an object")
    videos = search.get("videos", ())
    if not isinstance(videos, list):
        raise ValueError("YouTube videos must be a list")
    return tuple(videos)


def _comments(video: object) -> tuple[object, ...]:
    if not isinstance(video, dict):
        raise TypeError("YouTube video must be an object")
    comments = video.get("comments", ())
    if not isinstance(comments, list):
        raise ValueError("YouTube comments must be a list")
    return tuple(comments)


def _non_negative_int(row: object, field: str) -> int:
    if not isinstance(row, dict):
        raise TypeError("YouTube row must be an object")
    value = row[field]
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _required_text(row: object, field: str) -> str:
    if not isinstance(row, dict):
        raise TypeError("YouTube row must be an object")
    value = row[field]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


def _video_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={quote(video_id, safe='')}"


def _channel_hash(channel_id: str) -> str:
    return hashlib.sha256(channel_id.encode("utf-8")).hexdigest()


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
