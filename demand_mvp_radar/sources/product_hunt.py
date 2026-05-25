"""Product Hunt fixture connector."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.sources.base import QuarantinedSourceRow
from demand_mvp_radar.sources.live import LiveConnectorResult, LiveSourceConfig, RateLimitState

MIN_BODY_LENGTH = 20


class ProductHuntConnector:
    connector_version = "product-hunt-v1"

    def __init__(
        self,
        fixture_path: Path | None,
        *,
        token: str | None = None,
        queries: tuple[str, ...] = (),
        per_run_limit: int = 25,
        timeout_seconds: int = 20,
    ) -> None:
        self.fixture_path = fixture_path
        self.token = token.strip() if token else None
        self.queries = tuple(query.lower() for query in queries if query.strip())
        self.per_run_limit = max(1, min(per_run_limit, 50))
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

        for index, launch in enumerate(payload.get("launches", ())):
            try:
                record = _launch_record(
                    launch,
                    config=config,
                    run_id=run_id,
                    connector_version=self.connector_version,
                )
                next_seen.add(record.source_fingerprint)
                if record.source_fingerprint not in seen_fingerprints:
                    evidence.append(record)
                for comment in _comments(launch):
                    comment_record = _comment_record(
                        comment,
                        launch=launch,
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
                        source_reference=f"product_hunt:launch-{index}",
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

    def _live_payload(self) -> dict[str, object]:
        if not self.token:
            raise ValueError("Product Hunt live collection requires token")
        query = """
        query RadarPosts($first: Int!) {
          posts(first: $first, order: NEWEST) {
            edges {
              node {
                id
                name
                tagline
                description
                url
                votesCount
                commentsCount
                createdAt
                topics { edges { node { name } } }
              }
            }
          }
        }
        """
        request = Request(
            "https://api.producthunt.com/v2/api/graphql",
            data=json.dumps(
                {"query": query, "variables": {"first": self.per_run_limit}}
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "User-Agent": "Demand-to-MVP-Radar/0.1",
            },
            method="POST",
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        launches = []
        for edge in payload.get("data", {}).get("posts", {}).get("edges", ()):
            node = edge.get("node") if isinstance(edge, dict) else None
            if isinstance(node, dict):
                launch = _live_post_to_fixture_row(node)
                if _matches_queries(launch, self.queries):
                    launches.append(launch)
        return {"launches": launches}


def _launch_record(
    row: object,
    *,
    config: LiveSourceConfig,
    run_id: str,
    connector_version: str,
) -> EvidenceRecord:
    if not isinstance(row, dict):
        raise TypeError("Product Hunt launch must be an object")
    product_id = _required_text(row, "product_id")
    name = _required_text(row, "name")
    product_url = _product_url(row)
    tagline = _normalize_text(_required_text(row, "tagline"))
    body = _normalize_text(_required_text(row, "body"))
    if len(body) < MIN_BODY_LENGTH:
        raise ValueError("Product Hunt launch body is too short")
    topics = _topics(row)
    launch_date = datetime.fromisoformat(_required_text(row, "launch_date"))
    captured_at = datetime.fromisoformat(_required_text(row, "captured_at"))
    vote_count = _non_negative_int(row, "votes_count")
    comment_count = _non_negative_int(row, "comments_count")
    normalized_text = (
        f"{name}\n\n{tagline}\n\n{body}\n\n"
        f"Topics: {', '.join(topics)}. Votes: {vote_count}. Comments: {comment_count}."
    )
    content_hash = _content_hash(config.source_type, product_id, tagline, body, str(vote_count))
    return EvidenceRecord(
        run_id=run_id,
        source_name=config.source_name,
        source_type=config.source_type,
        source_id=f"launch:{product_id}",
        source_url=product_url,
        captured_at=captured_at,
        title=name,
        snippet=tagline[:160],
        normalized_text=normalized_text,
        content_hash=content_hash,
        source_fingerprint=f"{config.source_type}:launch:{product_id}:{content_hash}",
        connector_version=connector_version,
        topics=topics,
        launch_date=launch_date,
        vote_count=vote_count,
        comment_count=comment_count,
    )


def _comment_record(
    row: object,
    *,
    launch: object,
    config: LiveSourceConfig,
    run_id: str,
    connector_version: str,
) -> EvidenceRecord:
    if not isinstance(launch, dict):
        raise TypeError("Product Hunt launch must be an object")
    if not isinstance(row, dict):
        raise TypeError("Product Hunt comment must be an object")
    product_id = _required_text(launch, "product_id")
    comment_id = _required_text(row, "comment_id")
    body = _normalize_text(_required_text(row, "body"))
    if len(body) < MIN_BODY_LENGTH:
        raise ValueError("Product Hunt comment body is too short")
    captured_at = datetime.fromisoformat(_required_text(row, "captured_at"))
    launch_date = datetime.fromisoformat(_required_text(launch, "launch_date"))
    topics = _topics(launch)
    content_hash = _content_hash(config.source_type, product_id, comment_id, body)
    return EvidenceRecord(
        run_id=run_id,
        source_name=config.source_name,
        source_type=config.source_type,
        source_id=f"comment:{product_id}:{comment_id}",
        source_url=f"{_product_url(launch)}#comment-{comment_id}",
        captured_at=captured_at,
        title=f"Comment on {_required_text(launch, 'name')}",
        snippet=body[:160],
        normalized_text=f"Product Hunt comment for {_required_text(launch, 'name')}\n\n{body}",
        content_hash=content_hash,
        source_fingerprint=f"{config.source_type}:comment:{product_id}:{comment_id}:{content_hash}",
        connector_version=connector_version,
        topics=topics,
        launch_date=launch_date,
    )


def _comments(launch: object) -> tuple[object, ...]:
    if not isinstance(launch, dict):
        raise TypeError("Product Hunt launch must be an object")
    comments = launch.get("comments", ())
    if not isinstance(comments, list):
        raise ValueError("Product Hunt comments must be a list")
    return tuple(comments)


def _product_url(row: dict[str, object]) -> str:
    product_url = _required_text(row, "url")
    parsed = urlparse(product_url)
    if parsed.scheme != "https" or parsed.netloc != "www.producthunt.com":
        raise ValueError("Product Hunt URL must be an absolute producthunt.com URL")
    return product_url


def _topics(row: dict[str, object]) -> tuple[str, ...]:
    topics = row.get("topics", ())
    if not isinstance(topics, list):
        raise ValueError("Product Hunt topics must be a list")
    return tuple(str(topic).strip() for topic in topics if str(topic).strip())


def _live_post_to_fixture_row(row: dict[str, object]) -> dict[str, object]:
    topics = []
    topic_edges = (
        row.get("topics", {}).get("edges", ())
        if isinstance(row.get("topics"), dict)
        else ()
    )
    for edge in topic_edges:
        node = edge.get("node") if isinstance(edge, dict) else None
        if isinstance(node, dict) and str(node.get("name", "")).strip():
            topics.append(str(node["name"]).strip())
    name = str(row.get("name") or "").strip()
    tagline = str(row.get("tagline") or "").strip()
    body = str(row.get("description") or tagline or name).strip()
    return {
        "product_id": str(row.get("id") or name).strip(),
        "name": name,
        "url": str(row.get("url") or "").strip(),
        "tagline": tagline or body,
        "body": body,
        "topics": topics,
        "launch_date": str(row.get("createdAt") or datetime.now(UTC).isoformat()).replace(
            "Z", "+00:00"
        ),
        "captured_at": datetime.now(UTC).isoformat(),
        "votes_count": int(row.get("votesCount") or 0),
        "comments_count": int(row.get("commentsCount") or 0),
        "comments": [],
    }


def _matches_queries(launch: dict[str, object], queries: tuple[str, ...]) -> bool:
    if not queries:
        return True
    text = " ".join(
        str(launch.get(field, ""))
        for field in ("name", "tagline", "body")
    ).lower()
    return any(query in text for query in queries)


def _non_negative_int(row: dict[str, object], field: str) -> int:
    value = row[field]
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _required_text(row: object, field: str) -> str:
    if not isinstance(row, dict):
        raise TypeError("Product Hunt row must be an object")
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


def _decode_seen_fingerprints(cursor_state: dict[str, str]) -> set[str]:
    raw_value = cursor_state.get("seen_fingerprints", "")
    return {value for value in raw_value.split("|") if value}


def _encode_seen_fingerprints(fingerprints: set[str]) -> str:
    return "|".join(sorted(fingerprints))
