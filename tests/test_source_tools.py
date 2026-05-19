from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from demand_mvp_radar.sources.manual_urls import fetch_url_snapshot
from demand_mvp_radar.sources.serp_snapshot import read_serp_snapshot
from demand_mvp_radar.sources.store_metadata import read_store_metadata
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.tools.executor import ToolExecutor

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    status_code = 200
    text = "  A page about Telegram lead follow-up reminders.  "


class FakeHttpClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def get(self, url: str, *, timeout: int) -> FakeResponse:
        self.calls.append((url, timeout))
        return FakeResponse()


class FlakyHttpClient:
    def __init__(self) -> None:
        self.calls = 0

    def get(self, _url: str, *, timeout: int) -> FakeResponse:
        self.calls += 1
        if self.calls == 1:
            raise TimeoutError(f"timeout after {timeout}")
        return FakeResponse()


def test_fetch_url_snapshot_records_provenance() -> None:
    client = FakeHttpClient()
    fetched_at = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)

    snapshot = fetch_url_snapshot(
        "https://example.com/telegram-crm",
        client=client,
        timeout_seconds=7,
        fetched_at=fetched_at,
    )

    assert client.calls == [("https://example.com/telegram-crm", 7)]
    assert snapshot.url == "https://example.com/telegram-crm"
    assert snapshot.status_code == 200
    assert snapshot.fetched_at == fetched_at
    assert snapshot.content_hash
    assert snapshot.normalized_text == "A page about Telegram lead follow-up reminders."


def test_fetch_url_snapshot_retries_timeout_once() -> None:
    client = FlakyHttpClient()

    snapshot = fetch_url_snapshot(
        "https://example.com/telegram-crm",
        client=client,
        timeout_seconds=7,
        fetched_at=datetime(2026, 5, 19, 12, 0, tzinfo=UTC),
    )

    assert client.calls == 2
    assert snapshot.status_code == 200


def test_fetch_url_snapshot_records_tool_audit_fields(tmp_path) -> None:
    connection = connect_database(tmp_path / "radar.sqlite3")
    create_schema(connection)
    client = FakeHttpClient()

    def implementation(tool_input):
        snapshot = fetch_url_snapshot(
            tool_input.url,
            client=client,
            timeout_seconds=7,
            fetched_at=datetime(2026, 5, 19, 12, 0, tzinfo=UTC),
        )
        return snapshot.model_dump()

    executor = ToolExecutor({"fetch_url_snapshot": implementation}, connection=connection)
    executor.execute("fetch_url_snapshot", {"run_id": "run-001", "url": "https://example.com"})

    row = connection.execute(
        """
        SELECT audit_fields
        FROM tool_audit_events
        WHERE tool_name = :tool_name
        """,
        {"tool_name": "fetch_url_snapshot"},
    ).fetchone()

    assert '"url": "https://example.com"' in row["audit_fields"]
    assert '"status_code": 200' in row["audit_fields"]


def test_read_serp_snapshot_imports_fixture_results() -> None:
    results = read_serp_snapshot(FIXTURES / "serp_snapshot.json")

    assert len(results) == 2
    assert results[0].query == "telegram lead follow up reminders"
    assert results[0].provider == "saved-serp"
    assert results[0].rank == 1
    assert results[0].title == "Telegram CRM follow up workflow"
    assert results[0].url == "https://example.com/telegram-crm"
    assert results[0].snippet
    assert results[0].captured_at.isoformat() == "2026-05-18T10:00:00+00:00"


def test_read_store_metadata_imports_listing_fixture() -> None:
    listing = read_store_metadata(FIXTURES / "store_listing.json")

    assert listing.listing_id == "app-001"
    assert listing.store == "gpt-store"
    assert listing.title == "Review Miner"
    assert listing.description == "Summarizes app reviews into product gaps."
    assert listing.rating == 4.6
    assert listing.review_count == 128
    assert listing.captured_at.isoformat() == "2026-05-18T12:00:00+00:00"
