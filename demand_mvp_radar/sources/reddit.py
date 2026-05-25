"""Reddit source connector."""

from __future__ import annotations

import hashlib
import json
import re
from base64 import b64encode
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.sources.base import QuarantinedSourceRow
from demand_mvp_radar.sources.live import LiveConnectorResult, LiveSourceConfig, RateLimitState

MIN_TEXT_LENGTH = 20


class RedditConnector:
    connector_version = "reddit-v1"

    def __init__(
        self,
        fixture_path: Path | None,
        *,
        allowed_subreddits: tuple[str, ...],
        queries: tuple[str, ...],
        client_id: str | None = None,
        client_secret: str | None = None,
        user_agent: str | None = None,
        per_query_limit: int = 10,
        timeout_seconds: int = 20,
    ) -> None:
        if not allowed_subreddits and not queries:
            raise ValueError("Reddit connector requires allowlisted subreddits or queries")
        self.fixture_path = fixture_path
        self.allowed_subreddits = {subreddit.lower() for subreddit in allowed_subreddits}
        self.queries = tuple(queries)
        self.client_id = client_id.strip() if client_id else None
        self.client_secret = client_secret.strip() if client_secret else None
        self.user_agent = user_agent.strip() if user_agent else None
        self.per_query_limit = max(1, min(per_query_limit, 50))
        self.timeout_seconds = timeout_seconds

    def collect(
        self,
        config: LiveSourceConfig,
        *,
        run_id: str,
        cursor_state: dict[str, str],
    ) -> LiveConnectorResult:
        payload = (
            json.loads(self.fixture_path.read_text(encoding="utf-8"))
            if self.fixture_path is not None
            else self._live_payload()
        )
        seen_fingerprints = _decode_seen_fingerprints(cursor_state)
        next_seen = set(seen_fingerprints)
        evidence: list[EvidenceRecord] = []
        quarantined: list[QuarantinedSourceRow] = []

        for index, post in enumerate(payload.get("posts", ())):
            try:
                if not self._is_allowed(post):
                    raise ValueError("Reddit post is outside allowed subreddits and queries")
                record = _post_record(
                    post,
                    config=config,
                    run_id=run_id,
                    connector_version=self.connector_version,
                )
                next_seen.add(record.source_fingerprint)
                if record.source_fingerprint not in seen_fingerprints:
                    evidence.append(record)
                for comment in _comments(post):
                    comment_record = _comment_record(
                        comment,
                        post=post,
                        config=config,
                        run_id=run_id,
                        connector_version=self.connector_version,
                    )
                    next_seen.add(comment_record.source_fingerprint)
                    if comment_record.source_fingerprint not in seen_fingerprints:
                        evidence.append(comment_record)
            except (KeyError, TypeError, ValueError) as error:
                quarantined.append(
                    QuarantinedSourceRow(
                        source_reference=f"reddit:post-{index}",
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

    def _is_allowed(self, post: object) -> bool:
        if not isinstance(post, dict):
            raise TypeError("Reddit post must be an object")
        subreddit = _required_text(post, "subreddit").lower()
        query = str(post.get("query", ""))
        return subreddit in self.allowed_subreddits or query in self.queries

    def _live_payload(self) -> dict[str, object]:
        if not self.client_id or not self.client_secret or not self.user_agent:
            raise ValueError("Reddit live collection requires client id, secret, and user agent")
        token = self._access_token()
        posts: list[dict[str, object]] = []
        subreddits = tuple(sorted(self.allowed_subreddits)) or ("all",)
        for subreddit in subreddits:
            for query in self.queries:
                params = urlencode(
                    {
                        "q": query,
                        "restrict_sr": "1" if subreddit != "all" else "0",
                        "sort": "new",
                        "limit": str(self.per_query_limit),
                        "raw_json": "1",
                    }
                )
                endpoint = (
                    f"https://oauth.reddit.com/r/{quote(subreddit)}/search?{params}"
                    if subreddit != "all"
                    else f"https://oauth.reddit.com/search?{params}"
                )
                request = Request(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "User-Agent": self.user_agent,
                    },
                )
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                for child in payload.get("data", {}).get("children", ()):
                    if isinstance(child, dict) and isinstance(child.get("data"), dict):
                        posts.append(_live_post_to_fixture_row(child["data"], query=query))
        return {"rate_limit": {"limited": False}, "posts": posts}

    def _access_token(self) -> str:
        assert self.client_id is not None
        assert self.client_secret is not None
        assert self.user_agent is not None
        auth = b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode("ascii")
        data = urlencode({"grant_type": "client_credentials"}).encode("utf-8")
        request = Request(
            "https://www.reddit.com/api/v1/access_token",
            data=data,
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": self.user_agent,
            },
            method="POST",
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        token = str(payload.get("access_token", "")).strip()
        if not token:
            raise ValueError("Reddit access_token missing from OAuth response")
        return token


def _live_post_to_fixture_row(row: dict[str, object], *, query: str) -> dict[str, object]:
    title = _required_text(row, "title")
    body = str(row.get("selftext") or "").strip()
    if len(body) < MIN_TEXT_LENGTH:
        body = f"{title}\n\nReddit search match for query: {query}"
    permalink = _required_text(row, "permalink")
    created_at = datetime.fromtimestamp(float(row["created_utc"]), tz=UTC).isoformat()
    return {
        "query": query,
        "subreddit": _required_text(row, "subreddit"),
        "post_id": _required_text(row, "id"),
        "url": f"https://www.reddit.com{permalink}",
        "title": title,
        "body": body,
        "score": int(row.get("score", 0)),
        "comment_count": int(row.get("num_comments", 0)),
        "created_at": created_at,
        "captured_at": datetime.now(UTC).isoformat(),
        "comments": [],
    }


def _post_record(
    row: object,
    *,
    config: LiveSourceConfig,
    run_id: str,
    connector_version: str,
) -> EvidenceRecord:
    if not isinstance(row, dict):
        raise TypeError("Reddit post must be an object")
    post_id = _required_text(row, "post_id")
    subreddit = _required_text(row, "subreddit")
    title = _required_text(row, "title")
    body = _normalize_text(_required_text(row, "body"))
    if len(body) < MIN_TEXT_LENGTH:
        raise ValueError("Reddit post body is too short")
    source_url = _reddit_url(row)
    captured_at = datetime.fromisoformat(_required_text(row, "captured_at"))
    created_at = datetime.fromisoformat(_required_text(row, "created_at"))
    score = _int(row, "score")
    comment_count = _non_negative_int(row, "comment_count")
    content_hash = _content_hash(config.source_type, subreddit, post_id, title, body)
    return EvidenceRecord(
        run_id=run_id,
        source_name=config.source_name,
        source_type=config.source_type,
        source_id=f"post:{post_id}",
        source_url=source_url,
        captured_at=captured_at,
        title=title,
        snippet=body[:160],
        normalized_text=f"{title}\n\n{body}",
        content_hash=content_hash,
        source_fingerprint=f"{config.source_type}:post:{post_id}:{content_hash}",
        connector_version=connector_version,
        subreddit=subreddit,
        score=score,
        comment_count=comment_count,
        created_at=created_at,
    )


def _comment_record(
    row: object,
    *,
    post: object,
    config: LiveSourceConfig,
    run_id: str,
    connector_version: str,
) -> EvidenceRecord:
    if not isinstance(post, dict):
        raise TypeError("Reddit post must be an object")
    if not isinstance(row, dict):
        raise TypeError("Reddit comment must be an object")
    post_id = _required_text(post, "post_id")
    comment_id = _required_text(row, "comment_id")
    body = _normalize_text(_required_text(row, "body"))
    if len(body) < MIN_TEXT_LENGTH:
        raise ValueError("Reddit comment body is too short")
    subreddit = _required_text(post, "subreddit")
    source_url = f"{_reddit_url(post)}{quote(comment_id, safe='')}/"
    captured_at = datetime.fromisoformat(_required_text(row, "captured_at"))
    created_at = datetime.fromisoformat(_required_text(row, "created_at"))
    content_hash = _content_hash(config.source_type, subreddit, post_id, comment_id, body)
    return EvidenceRecord(
        run_id=run_id,
        source_name=config.source_name,
        source_type=config.source_type,
        source_id=f"comment:{post_id}:{comment_id}",
        source_url=source_url,
        captured_at=captured_at,
        title=f"Comment on {_required_text(post, 'title')}",
        snippet=body[:160],
        normalized_text=f"Reddit comment in r/{subreddit}\n\n{body}",
        content_hash=content_hash,
        source_fingerprint=f"{config.source_type}:comment:{post_id}:{comment_id}:{content_hash}",
        connector_version=connector_version,
        subreddit=subreddit,
        score=_int(row, "score"),
        comment_id=comment_id,
        author_hash=_author_hash(_required_text(row, "author_id")),
        created_at=created_at,
    )


def _comments(post: object) -> tuple[object, ...]:
    if not isinstance(post, dict):
        raise TypeError("Reddit post must be an object")
    comments = post.get("comments", ())
    if not isinstance(comments, list):
        raise ValueError("Reddit comments must be a list")
    return tuple(comments)


def _reddit_url(row: dict[str, object]) -> str:
    source_url = _required_text(row, "url")
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or parsed.netloc != "www.reddit.com":
        raise ValueError("Reddit URL must be an absolute reddit.com URL")
    if "/r/" not in parsed.path:
        raise ValueError("Reddit URL must include subreddit path")
    return source_url


def _int(row: dict[str, object], field: str) -> int:
    value = row[field]
    if not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    return value


def _non_negative_int(row: dict[str, object], field: str) -> int:
    value = _int(row, field)
    if value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value


def _required_text(row: object, field: str) -> str:
    if not isinstance(row, dict):
        raise TypeError("Reddit row must be an object")
    value = row[field]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


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
