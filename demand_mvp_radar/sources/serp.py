"""Credentialed SERP fixture connector."""

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

MIN_SNIPPET_LENGTH = 20


class SERPSearchConnector:
    connector_version = "serp-v1"

    def __init__(
        self,
        fixture_path: Path,
        *,
        queries: tuple[str, ...],
        provider: str,
        daily_budget_limit: int,
        per_run_budget_limit: int,
        daily_budget_used: int = 0,
    ) -> None:
        if not queries:
            raise ValueError("SERP connector requires at least one query")
        if daily_budget_limit < 0 or per_run_budget_limit < 0 or daily_budget_used < 0:
            raise ValueError("SERP budget values must be non-negative")
        self.fixture_path = fixture_path
        self.queries = queries
        self.provider = provider
        self.daily_budget_limit = daily_budget_limit
        self.per_run_budget_limit = per_run_budget_limit
        self.daily_budget_used = daily_budget_used

    def collect(
        self,
        config: LiveSourceConfig,
        *,
        run_id: str,
        cursor_state: dict[str, str],
    ) -> LiveConnectorResult:
        remaining_budget = min(
            self.per_run_budget_limit,
            max(self.daily_budget_limit - self.daily_budget_used, 0),
        )
        if remaining_budget <= 0:
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

        payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        provider = str(payload.get("provider", self.provider)).strip() or self.provider
        seen_fingerprints = _decode_seen_fingerprints(cursor_state)
        next_seen = set(seen_fingerprints)
        evidence: list[EvidenceRecord] = []
        quarantined: list[QuarantinedSourceRow] = []
        consumed_queries = 0

        for search_index, search in enumerate(payload.get("searches", ())):
            try:
                search_query = _required_text(search, "query")
                if search_query not in self.queries:
                    continue
                if consumed_queries >= remaining_budget:
                    break
                consumed_queries += 1
                captured_at = datetime.fromisoformat(
                    str(search.get("captured_at", payload["captured_at"]))
                )
                provider_metadata = _string_metadata(search.get("provider_metadata", {}))
                for result in _results(search):
                    try:
                        record = _record_from_result(
                            result,
                            config=config,
                            run_id=run_id,
                            connector_version=self.connector_version,
                            provider=provider,
                            provider_metadata=provider_metadata,
                            query=search_query,
                            captured_at=captured_at,
                        )
                        next_seen.add(record.source_fingerprint)
                        if record.source_fingerprint in seen_fingerprints:
                            continue
                        evidence.append(record)
                    except (KeyError, TypeError, ValueError) as error:
                        quarantined.append(
                            QuarantinedSourceRow(
                                source_reference=f"serp:{search_query}:result",
                                error_reason=str(error),
                            )
                        )
            except (KeyError, TypeError, ValueError) as error:
                quarantined.append(
                    QuarantinedSourceRow(
                        source_reference=f"serp:search-{search_index}",
                        error_reason=str(error),
                    )
                )

        return LiveConnectorResult(
            evidence=tuple(evidence),
            quarantined=tuple(quarantined),
            source_counts={config.source_name: len(evidence)},
            error_counts={config.source_name: len(quarantined)},
            cursor_state={"seen_fingerprints": _encode_seen_fingerprints(next_seen)},
            rate_limit_state=RateLimitState(
                limited=False,
                remaining=max(remaining_budget - consumed_queries, 0),
            ),
            last_success_at=datetime.now(UTC),
        )


def _record_from_result(
    row: object,
    *,
    config: LiveSourceConfig,
    run_id: str,
    connector_version: str,
    provider: str,
    provider_metadata: dict[str, str],
    query: str,
    captured_at: datetime,
) -> EvidenceRecord:
    if not isinstance(row, dict):
        raise TypeError("SERP result must be an object")
    rank = _positive_int(row, "rank")
    result_url = _public_result_url(row)
    title = _required_text(row, "title")
    snippet = _normalize_text(_required_text(row, "snippet"))
    if len(snippet) < MIN_SNIPPET_LENGTH:
        raise ValueError("SERP result snippet is too short")
    content_hash = _content_hash(
        config.source_type,
        provider,
        query,
        str(rank),
        result_url,
        snippet,
    )

    return EvidenceRecord(
        run_id=run_id,
        source_name=config.source_name,
        source_type=config.source_type,
        source_id=f"{provider}:{query}:{rank}",
        source_url=result_url,
        captured_at=captured_at,
        title=title,
        snippet=snippet[:160],
        normalized_text=f"{title}\n\n{snippet}",
        content_hash=content_hash,
        source_fingerprint=f"{config.source_type}:{provider}:{query}:{rank}:{content_hash}",
        connector_version=connector_version,
        search_query=query,
        result_rank=rank,
        provider=provider,
        provider_metadata=provider_metadata,
    )


def _results(search: object) -> tuple[object, ...]:
    if not isinstance(search, dict):
        raise TypeError("SERP search must be an object")
    results = search.get("results", ())
    if not isinstance(results, list):
        raise ValueError("SERP search results must be a list")
    return tuple(results)


def _public_result_url(row: dict[str, object]) -> str:
    result_url = _required_text(row, "url")
    parsed = urlparse(result_url)
    if parsed.scheme != "https" or not parsed.netloc:
        if result_url.startswith("/") or result_url.startswith("file:"):
            raise ValueError("local path is not importable")
        raise ValueError("SERP result URL must be an absolute https URL")
    return result_url


def _string_metadata(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError("SERP provider metadata must be an object")
    return {str(key): str(metadata_value) for key, metadata_value in value.items()}


def _positive_int(row: dict[str, object], field: str) -> int:
    value = row[field]
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _required_text(row: object, field: str) -> str:
    if not isinstance(row, dict):
        raise TypeError("SERP row must be an object")
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
