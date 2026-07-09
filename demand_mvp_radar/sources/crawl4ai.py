"""Bounded competitor/workaround crawler source connector."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.sources.base import QuarantinedSourceRow
from demand_mvp_radar.sources.live import LiveConnectorResult, LiveSourceConfig, RateLimitState

MIN_TEXT_LENGTH = 20
PAGE_KINDS = {"competitor", "workaround", "integration", "irrelevant"}


class Crawl4AIConnector:
    connector_version = "crawl4ai-v1"

    def __init__(
        self,
        fixture_path: Path | None,
        *,
        urls: tuple[str, ...] = (),
        queries: tuple[str, ...] = (),
        allowed_domains: tuple[str, ...] = (),
        max_pages_per_run: int = 5,
        max_pages_per_domain: int = 2,
        timeout_seconds: int = 20,
    ) -> None:
        if fixture_path is None and not urls:
            raise ValueError("Crawl4AI connector requires fixture_path or explicit URLs")
        self.fixture_path = fixture_path
        self.urls = tuple(url for url in urls if url.strip())
        self.queries = tuple(query for query in queries if query.strip())
        self.allowed_domains = tuple(_normalize_domain(domain) for domain in allowed_domains)
        self.max_pages_per_run = max(1, min(max_pages_per_run, 25))
        self.max_pages_per_domain = max(1, min(max_pages_per_domain, 10))
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
        domain_counts: defaultdict[str, int] = defaultdict(int)

        for index, page in enumerate(_pages(payload)):
            try:
                if len(evidence) >= self.max_pages_per_run:
                    raise ValueError("crawler page limit exceeded")
                domain = _domain_for_page(page, allowed_domains=self.allowed_domains)
                if domain_counts[domain] >= self.max_pages_per_domain:
                    raise ValueError(f"crawler domain page limit exceeded: {domain}")
                record = _page_record(
                    page,
                    config=config,
                    run_id=run_id,
                    connector_version=self.connector_version,
                    allowed_domains=self.allowed_domains,
                )
                domain_counts[domain] += 1
                next_seen.add(record.source_fingerprint)
                if record.source_fingerprint not in seen_fingerprints:
                    evidence.append(record)
            except (KeyError, TypeError, ValueError) as error:
                quarantined.append(
                    QuarantinedSourceRow(
                        source_reference=f"crawl4ai:page-{index}",
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
        pages = []
        domain_counts: defaultdict[str, int] = defaultdict(int)
        for url in self.urls:
            if len(pages) >= self.max_pages_per_run:
                break
            parsed = _public_url(url, allowed_domains=self.allowed_domains)
            domain = _domain_key(parsed.hostname or "")
            if domain_counts[domain] >= self.max_pages_per_domain:
                continue
            request = Request(url, headers={"User-Agent": "Demand-to-MVP-Radar/0.1"})
            with urlopen(request, timeout=self.timeout_seconds) as response:
                html = response.read().decode("utf-8", errors="replace")
            extracted = _extract_html(html)
            page_text = _normalize_text(
                f"{extracted.title} {extracted.description} {extracted.text}"
            )
            query = self.queries[0] if self.queries else None
            pages.append(
                {
                    "url": url,
                    "title": extracted.title or parsed.netloc,
                    "positioning": extracted.description or page_text[:180],
                    "body": page_text,
                    "page_kind": _infer_page_kind(url, page_text),
                    "pricing_hint": _pricing_hint(page_text),
                    "query": query,
                    "captured_at": datetime.now(UTC).isoformat(),
                }
            )
            domain_counts[domain] += 1
        return {"pages": pages}


def _page_record(
    row: object,
    *,
    config: LiveSourceConfig,
    run_id: str,
    connector_version: str,
    allowed_domains: tuple[str, ...],
) -> EvidenceRecord:
    if not isinstance(row, dict):
        raise TypeError("crawler page must be an object")
    parsed = _public_url(_required_text(row, "url"), allowed_domains=allowed_domains)
    title = _required_text(row, "title")
    positioning = _normalize_text(_required_text(row, "positioning"))
    body = _normalize_text(_required_text(row, "body"))
    if len(body) < MIN_TEXT_LENGTH:
        raise ValueError("crawler page body is too short")
    page_kind = _page_kind(row)
    captured_at = datetime.fromisoformat(_required_text(row, "captured_at"))
    pricing_hint = _optional_text(row.get("pricing_hint"))
    target_candidate = _optional_text(row.get("target_candidate"))
    target_icp = _optional_text(row.get("target_icp"))
    query = _optional_text(row.get("query"))
    normalized_text = _normalized_page_text(
        title=title,
        positioning=positioning,
        body=body,
        page_kind=page_kind,
        pricing_hint=pricing_hint,
        target_icp=target_icp,
    )
    content_hash = _content_hash(
        config.source_type,
        parsed.geturl(),
        title,
        positioning,
        body,
        page_kind,
    )
    metadata = {
        "evidence_kind": _evidence_kind_for_page(page_kind),
        "page_kind": page_kind,
        "positioning": positioning,
        "landing_url": parsed.geturl(),
    }
    if pricing_hint:
        metadata["pricing_hint"] = pricing_hint
    if target_candidate:
        metadata["target_candidate"] = target_candidate
        metadata["mvp_shape"] = target_candidate
    if target_icp:
        metadata["target_icp"] = target_icp
    return EvidenceRecord(
        run_id=run_id,
        source_name=config.source_name,
        source_type=config.source_type,
        source_id=f"page:{_stable_id(parsed.geturl())}",
        source_url=parsed.geturl(),
        captured_at=captured_at,
        title=title,
        snippet=positioning[:160],
        normalized_text=normalized_text,
        content_hash=content_hash,
        source_fingerprint=f"{config.source_type}:page:{_stable_id(parsed.geturl())}:{content_hash}",
        connector_version=connector_version,
        search_query=query,
        provider="crawl4ai",
        provider_metadata=metadata,
        source_site=parsed.netloc.lower(),
    )


def _normalized_page_text(
    *,
    title: str,
    positioning: str,
    body: str,
    page_kind: str,
    pricing_hint: str | None,
    target_icp: str | None,
) -> str:
    parts = [
        title,
        positioning,
        body,
        f"Page kind: {page_kind}.",
    ]
    if pricing_hint:
        parts.append(f"Pricing/WTP hint: {pricing_hint}.")
    if target_icp:
        parts.append(f"Target ICP: {target_icp}.")
    return "\n\n".join(parts)


def _pages(payload: object) -> tuple[object, ...]:
    if not isinstance(payload, dict):
        raise TypeError("crawler payload must be an object")
    pages = payload.get("pages", ())
    if not isinstance(pages, list):
        raise ValueError("crawler pages must be a list")
    return tuple(pages)


def _domain_for_page(row: object, *, allowed_domains: tuple[str, ...]) -> str:
    if not isinstance(row, dict):
        raise TypeError("crawler page must be an object")
    parsed = _public_url(_required_text(row, "url"), allowed_domains=allowed_domains)
    return _domain_key(parsed.hostname or "")


def _public_url(url: str, *, allowed_domains: tuple[str, ...]):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("crawler URL must be an absolute https URL")
    hostname = parsed.hostname or ""
    if allowed_domains and not any(_domain_matches(hostname, domain) for domain in allowed_domains):
        raise ValueError(f"crawler URL is outside allowed domains: {hostname}")
    return parsed


def _domain_matches(hostname: str, domain: str) -> bool:
    normalized_hostname = _domain_key(hostname)
    normalized_domain = _domain_key(domain)
    return normalized_hostname == normalized_domain or normalized_hostname.endswith(
        f".{normalized_domain}"
    )


def _domain_key(value: str) -> str:
    return _normalize_domain(value)


def _page_kind(row: dict[str, object]) -> str:
    page_kind = _required_text(row, "page_kind").lower()
    if page_kind not in PAGE_KINDS:
        raise ValueError(f"crawler page_kind must be one of: {', '.join(sorted(PAGE_KINDS))}")
    return page_kind


def _evidence_kind_for_page(page_kind: str) -> str:
    if page_kind == "workaround":
        return "manual_workaround"
    if page_kind == "irrelevant":
        return "negative_signal"
    return "competitor_traction"


def _required_text(row: object, field: str) -> str:
    if not isinstance(row, dict):
        raise TypeError("crawler row must be an object")
    value = row[field]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _normalize_domain(value: str) -> str:
    return value.strip().lower().removeprefix("www.")


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


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


def _infer_page_kind(url: str, text: str) -> str:
    normalized = f"{url} {text}".lower()
    if any(token in normalized for token in ("workaround", "manual", "guide", "how to")):
        return "workaround"
    if "integration" in normalized:
        return "integration"
    if any(token in normalized for token in ("pricing", "alternative", "competitor")):
        return "competitor"
    return "irrelevant"


def _pricing_hint(text: str) -> str | None:
    match = re.search(r"(\$\s?\d+(?:[.,]\d+)?\s?(?:/mo|/month|per month)?)", text, re.I)
    if match:
        return match.group(1).strip()
    if "pricing" in text.lower() or "paid" in text.lower():
        return "pricing mentioned"
    return None


class _HtmlExtraction:
    def __init__(self, *, title: str, description: str, text: str) -> None:
        self.title = title
        self.description = description
        self.text = text


class _HtmlTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self._skip_depth = 0
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.description = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.lower()
        if normalized == "title":
            self._in_title = True
        if normalized in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if normalized == "meta":
            attr_map = {name.lower(): value or "" for name, value in attrs}
            if attr_map.get("name", "").lower() == "description":
                self.description = attr_map.get("content", "").strip()

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.lower()
        if normalized == "title":
            self._in_title = False
        if normalized in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text or self._skip_depth:
            return
        if self._in_title:
            self.title_parts.append(text)
            return
        self.text_parts.append(text)


def _extract_html(html: str) -> _HtmlExtraction:
    parser = _HtmlTextParser()
    parser.feed(html)
    title = _normalize_text(" ".join(parser.title_parts))
    description = _normalize_text(parser.description)
    text = _normalize_text(" ".join(parser.text_parts))
    return _HtmlExtraction(title=title, description=description, text=text)
