"""GitHub public search connector."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.sources.base import QuarantinedSourceRow
from demand_mvp_radar.sources.live import LiveConnectorResult, LiveSourceConfig, RateLimitState

MIN_BODY_LENGTH = 20


class GitHubPublicSearchConnector:
    connector_version = "github-public-v1"

    def __init__(
        self,
        fixture_path: Path | None,
        *,
        queries: tuple[str, ...],
        api_token: str | None = None,
        per_query_limit: int = 10,
        timeout_seconds: int = 20,
    ) -> None:
        if not queries:
            raise ValueError("GitHub public connector requires at least one query")
        self.fixture_path = fixture_path
        self.queries = queries
        self.api_token = api_token.strip() if api_token else None
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

        for index, row in enumerate(payload.get("items", ())):
            try:
                record = _record_from_item(
                    row,
                    config=config,
                    run_id=run_id,
                    connector_version=self.connector_version,
                )
                next_seen.add(record.source_fingerprint)
                if record.source_fingerprint in seen_fingerprints:
                    continue
                evidence.append(record)
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
            cursor_state={"seen_fingerprints": _encode_seen_fingerprints(next_seen)},
            rate_limit_state=RateLimitState(limited=False),
            last_success_at=datetime.now(UTC),
        )

    def _live_payload(self) -> dict[str, object]:
        items: list[dict[str, object]] = []
        for query in self.queries:
            url = (
                "https://api.github.com/search/issues"
                f"?q={quote(query)}&sort=updated&order=desc&per_page={self.per_query_limit}"
            )
            headers = {
                "Accept": "application/vnd.github+json",
                "User-Agent": "Demand-to-MVP-Radar/0.1",
            }
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            request = Request(url, headers=headers)
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            for item in payload.get("items", ()):
                if isinstance(item, dict):
                    items.append(_live_item_to_fixture_row(item, query=query))
        return {"items": items}


def _live_item_to_fixture_row(item: dict[str, object], *, query: str) -> dict[str, object]:
    html_url = _live_required_text(item, "html_url")
    repository_url = _live_required_text(item, "repository_url")
    repository = repository_url.rsplit("/repos/", 1)[-1]
    title = _live_required_text(item, "title")
    body = str(item.get("body") or "").strip()
    if len(body) < MIN_BODY_LENGTH:
        body = f"{title}\n\nGitHub search match for query: {query}"
    return {
        "repository": repository,
        "kind": "pull_request" if isinstance(item.get("pull_request"), dict) else "issue",
        "number": int(item["number"]),
        "url": html_url,
        "title": title,
        "body": body,
        "labels": [
            str(label.get("name", "")).strip()
            for label in item.get("labels", ())
            if isinstance(label, dict) and str(label.get("name", "")).strip()
        ],
        "created_at": _live_required_text(item, "created_at"),
        "updated_at": _live_required_text(item, "updated_at"),
        "captured_at": datetime.now(UTC).isoformat(),
    }


def _live_required_text(row: dict[str, object], field: str) -> str:
    value = row[field]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"GitHub live field {field} is required")
    return value.strip()


def _record_from_item(
    row: object,
    *,
    config: LiveSourceConfig,
    run_id: str,
    connector_version: str,
) -> EvidenceRecord:
    if not isinstance(row, dict):
        raise TypeError("GitHub search item must be an object")
    repository = _required_text(row, "repository")
    kind = _required_text(row, "kind")
    number = _positive_int(row, "number")
    source_url = _public_github_url(row)
    title = _required_text(row, "title")
    body = _normalize_text(_required_text(row, "body"))
    if len(body) < MIN_BODY_LENGTH:
        raise ValueError("GitHub search item body is too short")

    labels = _labels(row)
    created_at = datetime.fromisoformat(_required_text(row, "created_at"))
    updated_at = datetime.fromisoformat(_required_text(row, "updated_at"))
    captured_at = datetime.fromisoformat(_required_text(row, "captured_at"))
    content_hash = _content_hash(config.source_type, repository, kind, str(number), body)

    return EvidenceRecord(
        run_id=run_id,
        source_name=config.source_name,
        source_type=config.source_type,
        source_id=f"{repository}:{kind}:{number}",
        source_url=source_url,
        captured_at=captured_at,
        title=title,
        snippet=body[:160],
        normalized_text=f"{title}\n\n{body}",
        content_hash=content_hash,
        source_fingerprint=f"{config.source_type}:{repository}:{kind}:{number}:{content_hash}",
        connector_version=connector_version,
        repository_locator=repository,
        labels=labels,
        created_at=created_at,
        updated_at=updated_at,
    )


def _public_github_url(row: dict[str, object]) -> str:
    source_url = _required_text(row, "url")
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or parsed.netloc != "github.com":
        if source_url.startswith("/") or source_url.startswith("file:"):
            raise ValueError("local path is not importable")
        raise ValueError("GitHub public connector only accepts https://github.com URLs")
    repository = _required_text(row, "repository")
    if repository.startswith("private/"):
        raise ValueError(f"private repository is not importable: {repository}")
    expected_prefix = f"/{repository}/"
    if not parsed.path.startswith(expected_prefix):
        raise ValueError("GitHub URL does not match repository locator")
    return source_url


def _labels(row: dict[str, object]) -> tuple[str, ...]:
    value = row.get("labels", ())
    if not isinstance(value, list):
        raise ValueError("GitHub labels must be a list")
    return tuple(str(label).strip() for label in value if str(label).strip())


def _positive_int(row: dict[str, object], field: str) -> int:
    value = row[field]
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _required_text(row: dict[str, object], field: str) -> str:
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


def _source_reference(row: object, index: int) -> str:
    if isinstance(row, dict):
        repository = row.get("repository")
        number = row.get("number")
        if isinstance(repository, str) and isinstance(number, int):
            return f"github_public:{repository}:{number}"
    return f"github_public:row-{index}"
