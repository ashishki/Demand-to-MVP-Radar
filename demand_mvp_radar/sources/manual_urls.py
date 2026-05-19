"""Manual URL snapshot source tool."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict

from demand_mvp_radar.observability import span


class HttpResponse(Protocol):
    status_code: int
    text: str


class HttpClient(Protocol):
    def get(self, url: str, *, timeout: int) -> HttpResponse:
        """Fetch a URL with a bounded timeout."""


class UrlSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    url: str
    status_code: int
    fetched_at: datetime
    content_hash: str
    normalized_text: str


def fetch_url_snapshot(
    url: str,
    *,
    client: HttpClient,
    timeout_seconds: int,
    fetched_at: datetime | None = None,
    max_attempts: int = 2,
) -> UrlSnapshot:
    last_error: Exception | None = None
    for _attempt in range(max_attempts):
        try:
            with span("http.fetch_url_snapshot"):
                response = client.get(url, timeout=timeout_seconds)
            normalized_text = _normalize_text(response.text)
            timestamp = fetched_at or datetime.now(UTC)
            return UrlSnapshot(
                url=url,
                status_code=response.status_code,
                fetched_at=timestamp,
                content_hash=_content_hash(url, str(response.status_code), normalized_text),
                normalized_text=normalized_text,
            )
        except TimeoutError as error:
            last_error = error
    raise TimeoutError(f"fetch_url_snapshot timed out for {url}") from last_error


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _content_hash(*parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()
