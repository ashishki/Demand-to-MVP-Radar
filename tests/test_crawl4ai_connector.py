from __future__ import annotations

import json
from pathlib import Path

from demand_mvp_radar.config import Settings
from demand_mvp_radar.pipeline import collect_sources
from demand_mvp_radar.sources.crawl4ai import Crawl4AIConnector
from demand_mvp_radar.sources.live import LiveSourceConfig, RateLimitPolicy


def test_crawl4ai_connector_maps_fixture_pages_to_evidence(tmp_path) -> None:
    fixture_path = _write_fixture(tmp_path)
    connector = Crawl4AIConnector(
        fixture_path,
        allowed_domains=("cleansheet.example", "docs.example"),
        max_pages_per_run=3,
        max_pages_per_domain=2,
    )

    result = connector.collect(_config(), run_id="crawl4ai-001", cursor_state={})
    competitor = result.evidence[0]
    workaround = result.evidence[1]
    negative = result.evidence[2]

    assert len(result.evidence) == 3
    assert competitor.source_type == "crawl4ai"
    assert competitor.source_url == "https://cleansheet.example/csv-cleanup"
    assert competitor.search_query == "csv cleanup automation alternative"
    assert competitor.provider == "crawl4ai"
    assert competitor.provider_metadata["page_kind"] == "competitor"
    assert competitor.provider_metadata["evidence_kind"] == "competitor_traction"
    assert competitor.provider_metadata["pricing_hint"] == "$29/mo"
    assert competitor.provider_metadata["target_icp"] == "small SaaS operators"
    assert "CSV cleanup automation for client exports" in competitor.normalized_text

    assert workaround.provider_metadata["page_kind"] == "workaround"
    assert workaround.provider_metadata["evidence_kind"] == "manual_workaround"
    assert negative.provider_metadata["page_kind"] == "irrelevant"
    assert negative.provider_metadata["evidence_kind"] == "negative_signal"


def test_crawl4ai_connector_enforces_domain_allowlist_and_domain_limits(tmp_path) -> None:
    fixture_path = _write_fixture(tmp_path)
    connector = Crawl4AIConnector(
        fixture_path,
        allowed_domains=("cleansheet.example",),
        max_pages_per_run=5,
        max_pages_per_domain=1,
    )

    result = connector.collect(_config(), run_id="crawl4ai-001", cursor_state={})

    assert len(result.evidence) == 1
    assert len(result.quarantined) == 2
    assert "crawler domain page limit exceeded" in result.quarantined[0].error_reason
    assert "outside allowed domains" in result.quarantined[1].error_reason


def test_crawl4ai_connector_enforces_run_page_limit(tmp_path) -> None:
    fixture_path = _write_fixture(tmp_path)
    connector = Crawl4AIConnector(
        fixture_path,
        allowed_domains=("cleansheet.example", "docs.example"),
        max_pages_per_run=1,
        max_pages_per_domain=2,
    )

    result = connector.collect(_config(), run_id="crawl4ai-001", cursor_state={})

    assert len(result.evidence) == 1
    assert len(result.quarantined) == 2
    assert all("crawler page limit exceeded" in row.error_reason for row in result.quarantined)


def test_crawl4ai_cache_only_uses_fixture_without_live_fetch(tmp_path) -> None:
    fixture_path = _write_fixture(tmp_path)
    config_path = _write_source_config(
        tmp_path,
        fixture_path=fixture_path,
        cache_only=True,
        dry_run=False,
    )

    result = collect_sources(
        config=config_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="crawl4ai-cache-boundary",
    )

    assert result.evidence_count == 3
    assert result.source_counts["crawl4ai_competitor_cache"] == 3
    assert result.source_counts["source_modes"]["crawl4ai_competitor_cache"] == "cache_only"
    assert result.source_errors == {}


def test_crawl4ai_dry_run_skips_live_fetch(tmp_path) -> None:
    config_path = _write_source_config(
        tmp_path,
        fixture_path=None,
        cache_only=False,
        dry_run=True,
    )

    result = collect_sources(
        config=config_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="crawl4ai-dry-run-boundary",
    )

    assert result.evidence_count == 0
    assert result.source_counts["crawl4ai_competitor_cache"] == 0
    assert result.source_counts["source_modes"]["crawl4ai_competitor_cache"] == "dry_run"
    assert result.source_errors == {}


def _write_fixture(tmp_path: Path) -> Path:
    fixture_path = tmp_path / "crawl4ai-pages.json"
    fixture_path.write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "query": "csv cleanup automation alternative",
                        "url": "https://cleansheet.example/csv-cleanup",
                        "title": "CleanSheet CSV Cleanup",
                        "positioning": (
                            "CSV cleanup automation for client exports with schema repair."
                        ),
                        "body": (
                            "CleanSheet automates CSV cleanup automation for client exports, "
                            "delimiter detection, header repair, and broken column checks."
                        ),
                        "page_kind": "competitor",
                        "pricing_hint": "$29/mo",
                        "target_candidate": "CSV cleanup automation for client exports",
                        "target_icp": "small SaaS operators",
                        "captured_at": "2026-05-21T15:00:00+00:00",
                    },
                    {
                        "query": "csv cleanup automation workaround",
                        "url": "https://cleansheet.example/blog/manual-csv-cleanup",
                        "title": "Manual CSV cleanup checklist",
                        "positioning": "Manual workaround guide for cleaning client CSV exports.",
                        "body": (
                            "The workaround is a spreadsheet macro plus manual delimiter "
                            "checks after every client export."
                        ),
                        "page_kind": "workaround",
                        "target_candidate": "CSV cleanup automation for client exports",
                        "captured_at": "2026-05-21T15:05:00+00:00",
                    },
                    {
                        "query": "csv cleanup automation hype",
                        "url": "https://docs.example/ai-data-platform",
                        "title": "AI data platform",
                        "positioning": "Generic AI data platform copy.",
                        "body": (
                            "This page is broad AI platform hype and does not describe "
                            "the CSV cleanup automation pain or ICP."
                        ),
                        "page_kind": "irrelevant",
                        "target_candidate": "CSV cleanup automation for client exports",
                        "captured_at": "2026-05-21T15:10:00+00:00",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    return fixture_path


def _write_source_config(
    tmp_path: Path,
    *,
    fixture_path: Path | None,
    cache_only: bool,
    dry_run: bool,
) -> Path:
    source = {
        "source_name": "crawl4ai_competitor_cache",
        "source_type": "crawl4ai",
        "trust_level": "medium",
        "freshness_window_days": 30,
        "enabled": True,
        "cursor_support": True,
        "raw_snapshot_policy": "metadata_only",
        "approval_required": False,
        "credential_env_vars": [],
        "rate_limit_policy": {
            "requests_per_minute": 2,
            "burst_limit": 1,
        },
        "allowed_domains": ["cleansheet.example", "docs.example"],
        "urls": ["https://cleansheet.example/csv-cleanup"],
        "queries": ["csv cleanup automation alternative"],
        "max_pages_per_run": 3,
        "max_pages_per_domain": 2,
        "cache_only": cache_only,
        "dry_run": dry_run,
    }
    if fixture_path is not None:
        source["fixture_path"] = str(fixture_path.name)
    config_path = tmp_path / "crawl4ai-source-config.json"
    config_path.write_text(
        json.dumps(
            {
                "run_id": "crawl4ai-cache-boundary",
                "sources": [source],
            }
        ),
        encoding="utf-8",
    )
    return config_path


def _config() -> LiveSourceConfig:
    return LiveSourceConfig(
        source_name="crawl4ai_fixture",
        source_type="crawl4ai",
        trust_level="medium",
        freshness_window_days=30,
        enabled=True,
        cursor_support=True,
        raw_snapshot_policy="metadata_only",
        rate_limit_policy=RateLimitPolicy(requests_per_minute=2),
        approval_required=False,
        credential_requirements=(),
    )
