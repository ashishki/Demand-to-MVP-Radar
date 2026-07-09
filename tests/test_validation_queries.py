from __future__ import annotations

from demand_mvp_radar.validation_queries import (
    build_validation_query_pack,
    validation_adapter_status,
)


def test_validation_query_pack_is_candidate_specific_and_deterministic() -> None:
    pack = build_validation_query_pack(
        candidate_title="Hotkey Dictation Workflow Probe",
        surfaces=("workflow_automation", "manual_workaround"),
        missing_evidence=(
            "non-Telegram public evidence for the same pain",
            "pricing or willingness-to-pay signal",
        ),
    )
    repeated = build_validation_query_pack(
        candidate_title="Hotkey Dictation Workflow Probe",
        surfaces=("workflow_automation", "manual_workaround"),
        missing_evidence=(
            "non-Telegram public evidence for the same pain",
            "pricing or willingness-to-pay signal",
        ),
    )

    assert pack == repeated
    assert pack["contract"]["context_only_records_satisfy_gates"] is False
    assert pack["contract"]["unmatched_external_results_satisfy_gates"] is False
    assert pack["contract"]["live_api_calls"] is False
    assert pack["queries_by_intent"]["search_demand"][0]["query"] == (
        '"Hotkey Dictation Workflow Probe"'
    )
    assert (
        "hotkey dictation workflow probe"
        in pack["queries_by_intent"]["manual_workarounds"][0]["query"]
    )
    assert pack["queries_by_intent"]["x_discussions"][0]["lower_confidence"] is True
    assert (
        pack["missing_evidence_by_category"]["external_corroboration"]["next_intent"]
        == "search_demand"
    )
    assert pack["missing_evidence_by_category"]["wtp_signals"]["next_intent"] == ("wtp_signals")


def test_validation_adapter_status_is_failure_tolerant_before_live_adapters() -> None:
    statuses = validation_adapter_status()

    assert statuses["search_demand"]["status"] == "adapter_disabled"
    assert statuses["reddit_forum_complaints"]["status"] == "adapter_disabled"
    assert statuses["competitor_workaround_crawler"]["status"] == "adapter_disabled"
    assert statuses["x_discussions"]["status"] == "adapter_disabled"


def test_validation_adapter_status_maps_serp_modes_and_credentials() -> None:
    credential_limited = validation_adapter_status(
        {
            "configured_sources": {
                "serp_search": 0,
                "source_modes": {"serp_search": "live"},
                "source_types": {"serp_search": "serp"},
            },
            "source_errors": {
                "serp_search": (
                    "serp_search: missing required credential environment variable; "
                    "status=missing; env_vars=SERPAPI_API_KEY"
                )
            },
        }
    )
    cache_only = validation_adapter_status(
        {
            "configured_sources": {
                "serp_search": 1,
                "source_modes": {"serp_search": "cache_only"},
                "source_types": {"serp_search": "serp"},
            }
        }
    )

    assert credential_limited["search_demand"]["status"] == "credential_limited"
    assert cache_only["search_demand"]["status"] == "cache_only"


def test_validation_adapter_status_maps_reddit_modes_credentials_and_rate_limits() -> None:
    credential_limited = validation_adapter_status(
        {
            "configured_sources": {
                "reddit_demand_live": 0,
                "source_modes": {"reddit_demand_live": "live"},
                "source_types": {"reddit_demand_live": "reddit"},
            },
            "source_errors": {
                "reddit_demand_live": (
                    "reddit_demand_live: missing required credential environment variable; "
                    "status=missing; env_vars=REDDIT_CLIENT_ID,REDDIT_CLIENT_SECRET"
                )
            },
        }
    )
    cache_only = validation_adapter_status(
        {
            "configured_sources": {
                "reddit_demand_cache": 2,
                "source_modes": {"reddit_demand_cache": "cache_only"},
                "source_types": {"reddit_demand_cache": "reddit"},
            }
        }
    )
    rate_limited = validation_adapter_status(
        {
            "configured_sources": {
                "reddit_demand_live": 0,
                "source_modes": {"reddit_demand_live": "live"},
                "source_types": {"reddit_demand_live": "reddit"},
                "source_health": {
                    "reddit_demand_live": {
                        "rate_limit_state": {
                            "limited": True,
                            "retry_after_seconds": 60,
                        }
                    }
                },
            }
        }
    )

    assert credential_limited["reddit_forum_complaints"]["status"] == "credential_limited"
    assert cache_only["reddit_forum_complaints"]["status"] == "cache_only"
    assert rate_limited["reddit_forum_complaints"]["status"] == "rate_limited"


def test_validation_adapter_status_maps_crawler_modes_and_skipped_sources() -> None:
    cache_only = validation_adapter_status(
        {
            "configured_sources": {
                "crawl4ai_competitor_cache": 3,
                "source_modes": {"crawl4ai_competitor_cache": "cache_only"},
                "source_types": {"crawl4ai_competitor_cache": "crawl4ai"},
            }
        }
    )
    skipped = validation_adapter_status(
        {
            "configured_sources": {
                "crawl4ai_competitor_disabled": 0,
                "skipped_sources": ("crawl4ai_competitor_disabled",),
                "source_modes": {"crawl4ai_competitor_disabled": "live"},
                "source_types": {"crawl4ai_competitor_disabled": "crawl4ai"},
            }
        }
    )

    assert cache_only["competitor_workaround_crawler"]["status"] == "cache_only"
    assert skipped["competitor_workaround_crawler"]["status"] == "adapter_disabled"


def test_validation_adapter_status_maps_x_modes_credentials_and_rate_limits() -> None:
    credential_limited = validation_adapter_status(
        {
            "configured_sources": {
                "x_discussions_live": 0,
                "source_modes": {"x_discussions_live": "live"},
                "source_types": {"x_discussions_live": "x"},
            },
            "source_errors": {
                "x_discussions_live": (
                    "x_discussions_live: missing required credential environment variable; "
                    "status=missing; env_vars=XAI_API_KEY"
                )
            },
        }
    )
    cache_only = validation_adapter_status(
        {
            "configured_sources": {
                "x_discussions_cache": 2,
                "source_modes": {"x_discussions_cache": "cache_only"},
                "source_types": {"x_discussions_cache": "x"},
            }
        }
    )
    rate_limited = validation_adapter_status(
        {
            "configured_sources": {
                "x_discussions_live": 0,
                "source_modes": {"x_discussions_live": "live"},
                "source_types": {"x_discussions_live": "x"},
                "source_health": {
                    "x_discussions_live": {
                        "rate_limit_state": {
                            "limited": True,
                            "retry_after_seconds": 120,
                        }
                    }
                },
            }
        }
    )

    assert credential_limited["x_discussions"]["status"] == "credential_limited"
    assert cache_only["x_discussions"]["status"] == "cache_only"
    assert rate_limited["x_discussions"]["status"] == "rate_limited"
