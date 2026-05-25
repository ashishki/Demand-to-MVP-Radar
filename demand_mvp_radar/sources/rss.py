"""RSS and Atom live connector."""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.sources.base import QuarantinedSourceRow
from demand_mvp_radar.sources.live import LiveConnectorResult, LiveSourceConfig, RateLimitState

ATOM_NS = "{http://www.w3.org/2005/Atom}"


class RSSFeedConnector:
    connector_version = "rss-v1"

    def __init__(
        self,
        feed_paths: tuple[Path | str, ...],
        *,
        captured_at: datetime | None = None,
        timeout_seconds: int = 20,
    ) -> None:
        self.feed_paths = feed_paths
        self.captured_at = captured_at
        self.timeout_seconds = timeout_seconds

    def collect(
        self,
        config: LiveSourceConfig,
        *,
        run_id: str,
        cursor_state: dict[str, str],
    ) -> LiveConnectorResult:
        seen_fingerprints = _decode_seen_fingerprints(cursor_state)
        next_seen = set(seen_fingerprints)
        evidence: list[EvidenceRecord] = []
        quarantined: list[QuarantinedSourceRow] = []

        for feed_path in self.feed_paths:
            try:
                for entry in _parse_feed(feed_path, timeout_seconds=self.timeout_seconds):
                    record = _record_from_entry(
                        entry,
                        config=config,
                        run_id=run_id,
                        connector_version=self.connector_version,
                        captured_at=self.captured_at or datetime.now(UTC),
                    )
                    next_seen.add(record.source_fingerprint)
                    if record.source_fingerprint in seen_fingerprints:
                        continue
                    evidence.append(record)
            except (ET.ParseError, KeyError, OSError, TypeError, ValueError) as error:
                quarantined.append(
                    QuarantinedSourceRow(
                        source_reference=str(feed_path),
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


class FeedEntry:
    def __init__(
        self,
        *,
        source_id: str,
        feed_url: str,
        entry_url: str,
        title: str,
        body: str,
        published_at: datetime,
    ) -> None:
        self.source_id = source_id
        self.feed_url = feed_url
        self.entry_url = entry_url
        self.title = title
        self.body = body
        self.published_at = published_at


def _parse_feed(feed_path: Path | str, *, timeout_seconds: int) -> tuple[FeedEntry, ...]:
    root = _load_feed_root(feed_path, timeout_seconds=timeout_seconds)
    if root.tag == "rss":
        return _parse_rss(root)
    if root.tag == f"{ATOM_NS}feed":
        return _parse_atom(root)
    raise ValueError(f"unsupported feed root: {root.tag}")


def _load_feed_root(feed_path: Path | str, *, timeout_seconds: int) -> ET.Element:
    location = str(feed_path)
    parsed = urlparse(location)
    if parsed.scheme in {"http", "https"}:
        request = Request(location, headers={"User-Agent": "demand-mvp-radar"})
        with urlopen(request, timeout=timeout_seconds) as response:
            return ET.fromstring(response.read())
    return ET.parse(Path(location)).getroot()


def _parse_rss(root: ET.Element) -> tuple[FeedEntry, ...]:
    channel = root.find("channel")
    if channel is None:
        raise ValueError("RSS feed missing channel")
    feed_url = _required_child_text(channel, "link")
    entries: list[FeedEntry] = []
    for item in channel.findall("item"):
        entry_url = _required_child_text(item, "link")
        body = _normalize_text(_required_child_text(item, "description"))
        entries.append(
            FeedEntry(
                source_id=_optional_child_text(item, "guid") or entry_url,
                feed_url=feed_url,
                entry_url=entry_url,
                title=_required_child_text(item, "title"),
                body=body,
                published_at=_parse_datetime(_required_child_text(item, "pubDate")),
            )
        )
    return tuple(entries)


def _parse_atom(root: ET.Element) -> tuple[FeedEntry, ...]:
    feed_url = _atom_link(root) or _required_child_text(root, f"{ATOM_NS}id")
    entries: list[FeedEntry] = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        entry_url = _atom_link(entry) or _required_child_text(entry, f"{ATOM_NS}id")
        body = _normalize_text(
            _optional_child_text(entry, f"{ATOM_NS}summary")
            or _required_child_text(entry, f"{ATOM_NS}content")
        )
        entries.append(
            FeedEntry(
                source_id=_required_child_text(entry, f"{ATOM_NS}id"),
                feed_url=feed_url,
                entry_url=entry_url,
                title=_required_child_text(entry, f"{ATOM_NS}title"),
                body=body,
                published_at=_parse_datetime(_required_child_text(entry, f"{ATOM_NS}updated")),
            )
        )
    return tuple(entries)


def _record_from_entry(
    entry: FeedEntry,
    *,
    config: LiveSourceConfig,
    run_id: str,
    connector_version: str,
    captured_at: datetime,
) -> EvidenceRecord:
    content_hash = _content_hash(
        config.source_type,
        entry.feed_url,
        entry.source_id,
        entry.title,
        entry.body,
    )
    return EvidenceRecord(
        run_id=run_id,
        source_name=config.source_name,
        source_type=config.source_type,
        source_id=entry.source_id,
        source_url=entry.entry_url,
        captured_at=captured_at,
        title=entry.title,
        snippet=entry.body[:160],
        normalized_text=f"{entry.title}\n\n{entry.body}",
        content_hash=content_hash,
        source_fingerprint=f"{config.source_type}:{entry.source_id}:{content_hash}",
        connector_version=connector_version,
        feed_url=entry.feed_url,
        published_at=entry.published_at,
    )


def _required_child_text(element: ET.Element, tag: str) -> str:
    value = _optional_child_text(element, tag)
    if value is None:
        raise ValueError(f"missing required feed field: {tag}")
    return value


def _optional_child_text(element: ET.Element, tag: str) -> str | None:
    child = element.find(tag)
    if child is None or child.text is None or not child.text.strip():
        return None
    return child.text.strip()


def _atom_link(element: ET.Element) -> str | None:
    for child in element.findall(f"{ATOM_NS}link"):
        href = child.attrib.get("href")
        if href:
            return href.strip()
    return None


def _parse_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        parsed = parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


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
