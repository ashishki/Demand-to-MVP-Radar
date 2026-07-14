from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from demand_mvp_radar.cli import main
from demand_mvp_radar.config import Settings
from demand_mvp_radar.llm.adapter import FakeLLMProvider
from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.mvp_weekly import CandidateAggregate, _selected_source_mix, run_mvp_of_week
from demand_mvp_radar.proof import WeeklyReportProofReceipt


def test_mvp_of_week_imports_seed_export_and_writes_artifact(tmp_path, capsys) -> None:
    export_path = tmp_path / "telegram_seeds.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "telegram:@capitan:1001",
                    "captured_at": "2026-05-20T10:00:00+00:00",
                    "title": "Telegram content is hard to search",
                    "text": (
                        "Channel owners keep asking how to turn Telegram posts "
                        "into searchable SEO pages."
                    ),
                    "snippet": "Channel owners ask for searchable SEO pages from Telegram posts.",
                    "source_url": "https://t.me/its_capitan/1001",
                    "channel_username": "@its_capitan",
                    "bucket": "strong",
                    "demand_surfaces": ["creator_content_gap", "search_intent"],
                    "mvp_shape": "Telegram Channel SEO Site Generator",
                    "verification_needed": ["pricing or willingness-to-pay signal"],
                    "anti_complexity_note": "Static preview plus SEO report only.",
                },
                {
                    "upstream_id": "telegram:@example:1002",
                    "captured_at": "2026-05-20T12:00:00+00:00",
                    "text": (
                        "Creators copy posts into websites manually because "
                        "Telegram search is weak."
                    ),
                    "source_url": "https://t.me/example/1002",
                    "channel_username": "@example",
                    "bucket": "watch",
                    "demand_surfaces": ["manual_workaround", "creator_content_gap"],
                    "mvp_shape": "Telegram Channel SEO Site Generator",
                },
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "mvp-of-week",
            "--telegram-export",
            str(export_path),
            "--run-id",
            "mvp-weekly-test",
            "--data-dir",
            str(tmp_path / "data"),
            "--report-dir",
            str(tmp_path / "reports"),
        ]
    )
    output = json.loads(capsys.readouterr().out)
    report_path = tmp_path / "reports" / "mvp_of_week" / "mvp-weekly-test.md"
    json_path = tmp_path / "reports" / "mvp_of_week" / "mvp-weekly-test.json"
    receipt_path = tmp_path / "reports" / "mvp_of_week" / "mvp-weekly-test.receipt.json"
    connection = sqlite3.connect(tmp_path / "data" / "radar.sqlite3")
    connection.row_factory = sqlite3.Row
    run = connection.execute(
        "SELECT status, source_counts FROM runs WHERE run_id = ?",
        ("mvp-weekly-test",),
    ).fetchone()

    assert exit_code == 0
    assert output["status"] == "selected"
    assert output["selected_title"] == "Telegram Channel SEO Site Generator"
    assert output["proof_receipt_path"] == str(receipt_path)
    assert report_path.exists()
    assert json_path.exists()
    assert receipt_path.exists()
    report_text = report_path.read_text()
    assert "Candidate Dossier: Telegram Channel SEO Site Generator" in report_text
    assert "Status: investigate" in report_text
    assert "## Validation Query Pack" in report_text
    assert 'search_demand: "Telegram Channel SEO Site Generator"' in report_text
    assert "## Matched External Evidence" in report_text
    assert "## What Would Change The Decision" in report_text
    assert "- Market context: context only, not proof." in report_text
    assert "## Next Experiment" in report_text
    assert "## Kill Criteria" in report_text
    receipt = WeeklyReportProofReceipt.model_validate(
        json.loads(receipt_path.read_text(encoding="utf-8"))
    )
    assert receipt.artifact_ref == str(report_path)
    assert receipt.verifier_status == "passed"
    assert {ref.source_url for ref in receipt.evidence_refs} == {
        "https://t.me/its_capitan/1001",
        "https://t.me/example/1002",
    }
    assert run["status"] == "mvp_of_week"
    assert json.loads(run["source_counts"])["telegram_research_agent"] == 2
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["result"]["dossier_status"] == "investigate"
    assert payload["selected"]["dossier_status"] == "investigate"
    assert (
        payload["selected"]["candidate_id"]
        == "candidate:telegram-channel-seo-site-generator"
    )
    assert payload["selected"]["decision_reason"] == "source_mix_gate"
    assert payload["selected"]["next_experiment"]
    assert payload["selected"]["kill_criteria"] == [
        "No second independent non-Telegram source supports the same pain.",
        "Users describe curiosity but no repeated workaround, budget, or urgency.",
        "The only plausible implementation expands into a broad platform.",
    ]
    assert payload["candidates"][0]["candidate_id"] == payload["selected"]["candidate_id"]
    assert payload["candidates"][0]["kill_criteria"] == payload["selected"]["kill_criteria"]
    assert payload["result"]["selected_source_mix"]["readiness"] == "telegram_only"
    assert payload["selected"]["source_mix"]["selected_external_evidence_count"] == 0
    assert payload["selected"]["source_mix"]["reddit_api_status"] == "not_used"
    assert (
        payload["selected"]["validation_queries"]["queries_by_intent"]["search_demand"][0][
            "target_candidate"
        ]
        == "Telegram Channel SEO Site Generator"
    )
    assert payload["validation_queries"]["schema_version"] == "radar_validation_evidence.v1"
    assert payload["matched_external_evidence"] == []
    assert payload["selected"]["matched_external_evidence"] == []
    assert payload["decision_change_action"]["matched_external_evidence_count"] == 0
    assert payload["decision_change_action"]["next_query"]
    assert output["decision_change_action"]["next_query"]
    assert payload["validation_adapter_status"]["search_demand"]["status"] == "adapter_disabled"
    assert (
        payload["decision_context"]["external_research_context"]["source_gate_satisfied"] is False
    )


def test_mvp_of_week_keeps_market_context_out_of_candidate_ranking(tmp_path) -> None:
    export_path = tmp_path / "telegram_seeds.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "market-context-lens:2026-W28",
                    "captured_at": "2026-07-09T07:39:06+00:00",
                    "title": "Context Only: Market Lens Baseline + Weekly Delta",
                    "text": (
                        "Persistent market lens: rank up narrow utilities with WTP, "
                        "rank down paid-ads-dependent platforms. Context only."
                    ),
                    "snippet": "Persistent market lens for MVP ranking.",
                    "source_kind": "market_analyst_context",
                    "radar_role": "context_only",
                    "context_only": True,
                    "build_ready_evidence": False,
                    "market_context_lens_kind": "current",
                },
                {
                    "upstream_id": "telegram:@capitan:1001",
                    "captured_at": "2026-05-20T10:00:00+00:00",
                    "title": "Telegram content is hard to search",
                    "text": (
                        "Channel owners keep asking how to turn Telegram posts "
                        "into searchable SEO pages."
                    ),
                    "snippet": "Channel owners ask for searchable SEO pages from Telegram posts.",
                    "source_url": "https://t.me/its_capitan/1001",
                    "channel_username": "@its_capitan",
                    "bucket": "strong",
                    "demand_surfaces": ["creator_content_gap", "search_intent"],
                    "mvp_shape": "Telegram Channel SEO Site Generator",
                },
            ]
        ),
        encoding="utf-8",
    )

    result = run_mvp_of_week(
        telegram_export=export_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="mvp-weekly-context-only",
        llm_provider=None,
    )
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))
    report_text = result.report_path.read_text(encoding="utf-8")

    assert result.selected_title == "Telegram Channel SEO Site Generator"
    assert all(
        candidate["title"] != "Context Only: Market Lens Baseline + Weekly Delta"
        for candidate in payload["candidates"]
    )
    assert payload["decision_context"]["context_only_record_count"] == 1
    assert payload["decision_context"]["market_context"]["source_gate_satisfied"] is False
    assert payload["selected"]["evidence_count"] == 1
    assert payload["result"]["source_counts"]["telegram_research_agent"] == 1
    assert payload["result"]["source_counts"]["context_only_record_count"] == 1
    assert "## Market Context Lens" in report_text
    assert "Source gate: not satisfied by market context." in report_text


def test_mvp_of_week_downgrades_focused_experiment_without_external_evidence(tmp_path) -> None:
    export_path = tmp_path / "telegram_seeds.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "telegram:@capitan:1003",
                    "captured_at": "2026-05-20T10:00:00+00:00",
                    "title": "Java plugin demand",
                    "text": "A Telegram post claims teams need a Java plugin for workflow routing.",
                    "snippet": "Teams need a Java plugin for workflow routing.",
                    "source_url": "https://t.me/its_capitan/1003",
                    "channel_username": "@its_capitan",
                    "bucket": "strong",
                    "demand_surfaces": ["workflow_automation"],
                    "mvp_shape": "Java Workflow Routing Plugin",
                }
            ]
        ),
        encoding="utf-8",
    )
    provider = FakeLLMProvider(
        json.dumps(
            {
                "selected_title": "Java Workflow Routing Plugin",
                "recommendation": "focused_experiment",
                "score": 88,
                "markdown": (
                    "# MVP of the Week: Java Workflow Routing Plugin\n\n"
                    "## Why This Week\nTelegram seed only.\n"
                ),
            }
        )
    )

    result = run_mvp_of_week(
        telegram_export=export_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="mvp-weekly-gated",
        llm_provider=provider,
    )
    report_text = result.report_path.read_text(encoding="utf-8")
    receipt = WeeklyReportProofReceipt.model_validate(
        json.loads(result.proof_receipt_path.read_text(encoding="utf-8"))
    )

    assert result.recommendation == "needs_more_evidence"
    assert result.score == 49
    assert receipt.artifact_sha256
    assert receipt.evidence_refs[0].supports == "mvp:java-workflow-routing-plugin"
    assert result.source_counts["external_evidence_count"] == 0
    assert "Source Mix Gate" in report_text
    assert "## Decision Gate" in report_text
    assert "## Build-Worthy Recommendations" in report_text
    assert "- No build-worthy recommendations passed the Decision Gate." in report_text
    assert "## Interesting Signals" in report_text
    assert "does not yet have two independent non-Telegram evidence sources" in report_text
    assert "operator profile" in report_text
    assert "Operator fit profile" in provider.calls[0][0]


def test_mvp_of_week_ignores_llm_title_outside_shortlist(tmp_path) -> None:
    export_path = tmp_path / "telegram_seeds.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "telegram:@capitan:1004",
                    "captured_at": "2026-05-20T10:00:00+00:00",
                    "title": "Guardrail logs are hard to monitor",
                    "text": "Teams need a small watchdog for LLM cost and guardrail logs.",
                    "snippet": "Teams need a watchdog for LLM cost and guardrail logs.",
                    "source_url": "https://t.me/its_capitan/1004",
                    "channel_username": "@capitan",
                    "bucket": "strong",
                    "demand_surfaces": ["workflow_automation", "cost_control"],
                    "mvp_shape": "LLM Guardrail Watchdog",
                },
                {
                    "upstream_id": "telegram:@capitan:1005",
                    "captured_at": "2026-05-20T11:00:00+00:00",
                    "title": "Dictation workflow",
                    "text": "Creators want hotkey dictation workflows.",
                    "snippet": "Creators want hotkey dictation workflows.",
                    "source_url": "https://t.me/its_capitan/1005",
                    "channel_username": "@capitan",
                    "bucket": "watch",
                    "demand_surfaces": ["workflow_automation"],
                    "mvp_shape": "Hotkey Dictation Workflow Probe",
                },
            ]
        ),
        encoding="utf-8",
    )
    provider = FakeLLMProvider(
        json.dumps(
            {
                "selected_title": "Imaginary Candidate Outside Shortlist",
                "recommendation": "revisit_with_evidence_gap",
                "score": 64,
                "markdown": (
                    "# Candidate Dossier: Imaginary Candidate Outside Shortlist\n\n"
                    "## Why This Candidate\nLLM tried to rename the candidate.\n"
                ),
            }
        )
    )

    result = run_mvp_of_week(
        telegram_export=export_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="mvp-weekly-title-gate",
        llm_provider=provider,
    )
    report_text = result.report_path.read_text(encoding="utf-8")
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert result.selected_title == "LLM Guardrail Watchdog"
    assert report_text.startswith("# Candidate Dossier: LLM Guardrail Watchdog")
    assert "Imaginary Candidate Outside Shortlist" not in report_text.splitlines()[0]
    assert payload["result"]["selected_title"] == payload["selected"]["title"]


def test_mvp_of_week_includes_live_intelligence_without_satisfying_source_gate(tmp_path) -> None:
    export_path = tmp_path / "telegram_seeds.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "telegram:@capitan:1010",
                    "captured_at": "2026-05-20T10:00:00+00:00",
                    "title": "Telegram channel archive search",
                    "text": "Creators want searchable mirrors of Telegram channel archives.",
                    "snippet": "Creators want searchable mirrors of Telegram archives.",
                    "source_url": "https://t.me/its_capitan/1010",
                    "channel_username": "@its_capitan",
                    "bucket": "strong",
                    "demand_surfaces": ["creator_content_gap", "search_intent"],
                    "mvp_shape": "Telegram Channel SEO Site Generator",
                }
            ]
        ),
        encoding="utf-8",
    )
    live_path = tmp_path / "live.json"
    live_path.write_text(
        json.dumps(
            {
                "schema_version": "live_source_intelligence.v1",
                "generated_at": "2026-05-20T12:00:00Z",
                "generation_mode": "deterministic_event_log",
                "events_scanned": 12,
                "window": {"days": 14},
                "pathway": {"status": "not_installed"},
                "channels": [{"channel_username": "@capitan", "event_count": 8}],
                "demand_surfaces": [{"surface": "creator_content_gap", "count": 5}],
                "repeated_claim_candidates": [
                    {
                        "claim_key": "claim:1",
                        "normalized_claim": "telegram archive search",
                        "event_count": 2,
                    }
                ],
                "radar_context": {
                    "summary": "12 live source events; context only.",
                    "context_only": True,
                },
            }
        ),
        encoding="utf-8",
    )

    result = run_mvp_of_week(
        telegram_export=export_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="mvp-weekly-live-context",
        live_intelligence_path=live_path,
    )
    report_text = result.report_path.read_text(encoding="utf-8")
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert "## Live Source Intelligence" in report_text
    assert "Context only: this snapshot does not satisfy external evidence gates." in report_text
    assert result.source_counts["external_evidence_count"] == 0
    assert result.selected_source_mix["readiness"] == "telegram_only"
    assert result.source_counts["live_intelligence"]["events_scanned"] == 12
    assert payload["live_intelligence"]["repeated_claim_count"] == 1
    assert payload["selected"]["source_mix"]["selected_external_evidence_count"] == 0


def test_mvp_of_week_exposes_source_mix_and_missing_reddit_credentials(
    tmp_path,
    monkeypatch,
) -> None:
    for env_var in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT"):
        monkeypatch.delenv(env_var, raising=False)
    export_path = tmp_path / "telegram_seeds.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "telegram:@capitan:1006",
                    "captured_at": "2026-05-20T10:00:00+00:00",
                    "title": "Telegram SEO demand",
                    "text": (
                        "Creators ask for public searchable mirrors of Telegram channel archives."
                    ),
                    "snippet": "Creators want searchable mirrors of Telegram archives.",
                    "source_url": "https://t.me/its_capitan/1006",
                    "channel_username": "@its_capitan",
                    "bucket": "strong",
                    "demand_surfaces": ["creator_content_gap", "search_intent"],
                    "mvp_shape": "Telegram Channel SEO Site Generator",
                }
            ]
        ),
        encoding="utf-8",
    )
    source_config = tmp_path / "mvp_sources.json"
    source_config.write_text(
        json.dumps(
            {
                "run_id": "mvp-weekly-source-mix",
                "sources": [
                    {
                        "source_name": "reddit_demand_live",
                        "source_type": "reddit",
                        "trust_level": "medium",
                        "freshness_window_days": 14,
                        "enabled": True,
                        "cursor_support": True,
                        "raw_snapshot_policy": "metadata_only",
                        "approval_required": True,
                        "credential_env_vars": [
                            "REDDIT_CLIENT_ID",
                            "REDDIT_CLIENT_SECRET",
                            "REDDIT_USER_AGENT",
                        ],
                        "rate_limit_policy": {
                            "requests_per_minute": 4,
                            "burst_limit": 1,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = run_mvp_of_week(
        telegram_export=export_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="mvp-weekly-source-mix",
        source_config=source_config,
        llm_provider=None,
    )
    report_text = result.report_path.read_text(encoding="utf-8")
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))
    source_mix = payload["selected"]["source_mix"]

    assert result.selected_source_mix["readiness"] == "credential_limited"
    assert source_mix["readiness"] == "credential_limited"
    assert source_mix["selected_telegram_seed_evidence_count"] == 1
    assert source_mix["selected_external_evidence_count"] == 0
    assert source_mix["missing_credentials"] == ["reddit_demand_live"]
    assert source_mix["missing_credential_env_vars"] == [
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USER_AGENT",
    ]
    assert source_mix["reddit_api_status"] == "missing_credentials"
    assert "Readiness: credential_limited" in report_text
    assert "Missing credentials/source errors: reddit_demand_live" in report_text
    assert "Reddit API: missing_credentials" in report_text


def test_mvp_of_week_uses_cache_only_serp_validation_queries(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    mvp_shape = "Hotkey Dictation Workflow Probe"
    export_path = tmp_path / "telegram_seeds.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "telegram:@capitan:1201",
                    "captured_at": _now_iso(),
                    "title": f"{mvp_shape} demand",
                    "text": "Operators ask for hotkey dictation workflow probes.",
                    "snippet": "Operators ask for hotkey dictation workflow probes.",
                    "source_url": "https://t.me/its_capitan/1201",
                    "channel_username": "@its_capitan",
                    "bucket": "strong",
                    "demand_surfaces": ["workflow_automation", "search_intent"],
                    "mvp_shape": mvp_shape,
                }
            ]
        ),
        encoding="utf-8",
    )
    serp_path = tmp_path / "serp-cache.json"
    serp_path.write_text(
        json.dumps(
            {
                "provider": "serpapi",
                "captured_at": _now_iso(),
                "searches": [
                    {
                        "query": "hotkey dictation workflow probe",
                        "captured_at": _now_iso(),
                        "provider_metadata": {"engine": "google"},
                        "results": [
                            {
                                "rank": 1,
                                "title": mvp_shape,
                                "url": "https://example.com/hotkey-dictation-workflow",
                                "snippet": (
                                    "Operators search for a hotkey dictation workflow "
                                    "probe to remove manual note cleanup."
                                ),
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    source_config = tmp_path / "serp-cache-config.json"
    source_config.write_text(
        json.dumps(
            {
                "run_id": "mvp-weekly-serp-cache",
                "sources": [
                    {
                        "source_name": "serp_search_intent_cache",
                        "source_type": "serp",
                        "trust_level": "medium",
                        "freshness_window_days": 14,
                        "enabled": True,
                        "cursor_support": True,
                        "raw_snapshot_policy": "metadata_only",
                        "approval_required": True,
                        "credential_env_vars": ["SERPAPI_API_KEY"],
                        "rate_limit_policy": {
                            "requests_per_minute": 10,
                            "burst_limit": 1,
                        },
                        "fixture_path": str(serp_path.name),
                        "queries": ["hotkey dictation workflow probe"],
                        "provider": "serpapi",
                        "daily_budget_limit": 10,
                        "per_run_budget_limit": 1,
                        "cache_only": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = run_mvp_of_week(
        telegram_export=export_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="mvp-weekly-serp-cache",
        source_config=source_config,
        llm_provider=None,
    )
    report_text = result.report_path.read_text(encoding="utf-8")
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert payload["validation_adapter_status"]["search_demand"]["status"] == "cache_only"
    assert payload["matched_external_evidence"][0]["query"] == ("hotkey dictation workflow probe")
    assert payload["matched_external_evidence"][0]["evidence_kind"] == "manual_workaround"
    assert payload["selected"]["source_mix"]["selected_external_evidence_count"] == 1
    assert "query=hotkey dictation workflow probe" in report_text
    assert "supports_gate=yes" in report_text
    assert result.recommendation == "revisit_with_evidence_gap"


def test_mvp_of_week_uses_cache_only_reddit_complaint_validation(
    tmp_path,
    monkeypatch,
) -> None:
    for env_var in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT"):
        monkeypatch.delenv(env_var, raising=False)
    mvp_shape = "CSV cleanup automation for client exports"
    export_path = tmp_path / "telegram_seeds.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "telegram:@capitan:1301",
                    "captured_at": _now_iso(),
                    "title": f"{mvp_shape} demand",
                    "text": (
                        "Operators ask for CSV cleanup automation for client exports "
                        "instead of manual spreadsheet cleanup."
                    ),
                    "snippet": "Operators ask for CSV cleanup automation.",
                    "source_url": "https://t.me/its_capitan/1301",
                    "channel_username": "@its_capitan",
                    "bucket": "strong",
                    "demand_surfaces": ["workflow_automation", "manual_workaround"],
                    "mvp_shape": mvp_shape,
                }
            ]
        ),
        encoding="utf-8",
    )
    reddit_path = tmp_path / "reddit-cache.json"
    reddit_path.write_text(
        json.dumps(
            {
                "rate_limit": {
                    "limited": False,
                    "remaining": 42,
                },
                "posts": [
                    {
                        "query": "csv cleanup automation",
                        "subreddit": "SaaS",
                        "post_id": "reddit-post-001",
                        "url": (
                            "https://www.reddit.com/r/SaaS/comments/"
                            "reddit-post-001/csv_cleanup_automation/"
                        ),
                        "title": mvp_shape,
                        "body": (
                            "I keep cleaning client CSV exports by hand every week and "
                            "need automation for delimiter detection, headers, and broken "
                            "columns."
                        ),
                        "score": 37,
                        "comment_count": 11,
                        "created_at": "2026-05-20T10:00:00+00:00",
                        "captured_at": "2026-05-21T15:00:00+00:00",
                        "comments": [
                            {
                                "comment_id": "reddit-comment-001",
                                "author_id": "reddit-user-private-001",
                                "body": (
                                    "Same CSV cleanup pain here; the workaround is a "
                                    "brittle spreadsheet macro and manual checks after "
                                    "every export."
                                ),
                                "score": 9,
                                "created_at": "2026-05-20T12:00:00+00:00",
                                "captured_at": "2026-05-21T15:05:00+00:00",
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    source_config = tmp_path / "reddit-cache-config.json"
    source_config.write_text(
        json.dumps(
            {
                "run_id": "mvp-weekly-reddit-cache",
                "sources": [
                    {
                        "source_name": "reddit_demand_cache",
                        "source_type": "reddit",
                        "trust_level": "medium",
                        "freshness_window_days": 14,
                        "enabled": True,
                        "cursor_support": True,
                        "raw_snapshot_policy": "metadata_only",
                        "approval_required": True,
                        "credential_env_vars": [
                            "REDDIT_CLIENT_ID",
                            "REDDIT_CLIENT_SECRET",
                            "REDDIT_USER_AGENT",
                        ],
                        "rate_limit_policy": {
                            "requests_per_minute": 4,
                            "burst_limit": 1,
                        },
                        "fixture_path": str(reddit_path.name),
                        "allowed_subreddits": ["SaaS"],
                        "queries": ["csv cleanup automation"],
                        "cache_only": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = run_mvp_of_week(
        telegram_export=export_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="mvp-weekly-reddit-cache",
        source_config=source_config,
        llm_provider=None,
    )
    report_text = result.report_path.read_text(encoding="utf-8")
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))
    matches = payload["matched_external_evidence"]
    connection = sqlite3.connect(tmp_path / "data" / "radar.sqlite3")
    connection.row_factory = sqlite3.Row
    persisted_rows = connection.execute(
        """
        SELECT
            source_id,
            search_query,
            subreddit,
            source_created_at,
            author_hash,
            comment_id,
            score,
            comment_count
        FROM evidence
        WHERE run_id = ? AND source_type = 'reddit'
        ORDER BY id ASC
        """,
        ("mvp-weekly-reddit-cache",),
    ).fetchall()

    assert payload["validation_adapter_status"]["reddit_forum_complaints"]["status"] == (
        "cache_only"
    )
    assert [item["query"] for item in matches] == [
        "csv cleanup automation",
        "csv cleanup automation",
    ]
    assert {item["evidence_kind"] for item in matches} == {
        "manual_workaround",
        "repeated_complaint",
    }
    assert {item["subreddit"] for item in matches} == {"SaaS"}
    assert any(item["comment_id"] == "reddit-comment-001" for item in matches)
    assert any(item["author_hash"] for item in matches)
    assert payload["selected"]["source_mix"]["selected_external_evidence_count"] == 2
    assert payload["selected"]["source_mix"]["selected_external_source_types"] == ["reddit"]
    assert payload["selected"]["source_mix"]["reddit_api_status"] == "used"
    assert "query=csv cleanup automation" in report_text
    assert "reddit/r/SaaS" in report_text
    assert result.recommendation == "revisit_with_evidence_gap"
    assert len(persisted_rows) == 2
    assert persisted_rows[0]["search_query"] == "csv cleanup automation"
    assert persisted_rows[0]["subreddit"] == "SaaS"
    assert persisted_rows[0]["source_created_at"] == "2026-05-20T10:00:00+00:00"
    assert persisted_rows[0]["score"] == 37
    assert persisted_rows[0]["comment_count"] == 11
    assert persisted_rows[1]["comment_id"] == "reddit-comment-001"
    assert persisted_rows[1]["author_hash"]


def test_mvp_of_week_uses_cache_only_crawler_validation(
    tmp_path,
) -> None:
    mvp_shape = "CSV cleanup automation for client exports"
    export_path = tmp_path / "telegram_seeds.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "telegram:@capitan:1401",
                    "captured_at": _now_iso(),
                    "title": f"{mvp_shape} demand",
                    "text": (
                        "Operators ask for CSV cleanup automation for client exports "
                        "and want competitor/workaround validation."
                    ),
                    "snippet": "Operators ask for CSV cleanup automation.",
                    "source_url": "https://t.me/its_capitan/1401",
                    "channel_username": "@its_capitan",
                    "bucket": "strong",
                    "demand_surfaces": ["workflow_automation", "competitor_traction"],
                    "mvp_shape": mvp_shape,
                }
            ]
        ),
        encoding="utf-8",
    )
    crawler_path = tmp_path / "crawl4ai-cache.json"
    crawler_path.write_text(
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
                        "target_candidate": mvp_shape,
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
                        "target_candidate": mvp_shape,
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
                        "target_candidate": mvp_shape,
                        "captured_at": "2026-05-21T15:10:00+00:00",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    source_config = tmp_path / "crawler-cache-config.json"
    source_config.write_text(
        json.dumps(
            {
                "run_id": "mvp-weekly-crawler-cache",
                "sources": [
                    {
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
                        "fixture_path": str(crawler_path.name),
                        "allowed_domains": ["cleansheet.example", "docs.example"],
                        "urls": ["https://cleansheet.example/csv-cleanup"],
                        "queries": ["csv cleanup automation alternative"],
                        "max_pages_per_run": 3,
                        "max_pages_per_domain": 2,
                        "cache_only": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = run_mvp_of_week(
        telegram_export=export_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="mvp-weekly-crawler-cache",
        source_config=source_config,
        llm_provider=None,
    )
    report_text = result.report_path.read_text(encoding="utf-8")
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))
    matches = payload["matched_external_evidence"]

    assert (
        payload["validation_adapter_status"]["competitor_workaround_crawler"]["status"]
        == "cache_only"
    )
    assert {item["evidence_kind"] for item in matches} == {
        "competitor_traction",
        "manual_workaround",
        "negative_signal",
    }
    competitor = next(item for item in matches if item["evidence_kind"] == "competitor_traction")
    negative = next(item for item in matches if item["evidence_kind"] == "negative_signal")
    assert competitor["page_kind"] == "competitor"
    assert competitor["pricing_hint"] == "$29/mo"
    assert competitor["target_icp"] == "small SaaS operators"
    assert competitor["supports_gate"] is True
    assert negative["page_kind"] == "irrelevant"
    assert negative["supports_gate"] is False
    assert payload["selected"]["source_mix"]["selected_external_evidence_count"] == 2
    assert payload["selected"]["source_mix"]["selected_external_source_types"] == ["crawl4ai"]
    assert "query=csv cleanup automation alternative" in report_text
    assert "crawl4ai/competitor" in report_text
    assert "negative_signal: crawl4ai/irrelevant" in report_text
    assert "supports_gate=no" in report_text
    assert result.recommendation == "revisit_with_evidence_gap"


def test_mvp_of_week_uses_cache_only_x_corrob_without_gate_support(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    mvp_shape = "CSV cleanup automation for client exports"
    export_path = tmp_path / "telegram_seeds.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "telegram:@capitan:1501",
                    "captured_at": _now_iso(),
                    "title": f"{mvp_shape} demand",
                    "text": (
                        "Operators ask for CSV cleanup automation for client exports "
                        "and want lower-confidence X corroboration separated from gates."
                    ),
                    "snippet": "Operators ask for CSV cleanup automation.",
                    "source_url": "https://t.me/its_capitan/1501",
                    "channel_username": "@its_capitan",
                    "bucket": "strong",
                    "demand_surfaces": ["workflow_automation"],
                    "mvp_shape": mvp_shape,
                }
            ]
        ),
        encoding="utf-8",
    )
    x_path = tmp_path / "x-cache.json"
    x_path.write_text(
        json.dumps(
            {
                "rate_limit": {
                    "limited": False,
                    "remaining": 12,
                },
                "discussions": [
                    {
                        "query": "csv cleanup automation",
                        "discussion_id": "1001",
                        "url": "https://x.com/example/status/1001",
                        "author_id": "x-user-private-001",
                        "title": "X discussion about CSV cleanup",
                        "text": (
                            "CSV cleanup automation for client exports keeps coming up; "
                            "people still fix broken headers and delimiters manually."
                        ),
                        "discussion_kind": "pain",
                        "target_candidate": mvp_shape,
                        "like_count": 21,
                        "reply_count": 4,
                        "created_at": "2026-05-20T10:00:00+00:00",
                        "captured_at": "2026-05-21T15:00:00+00:00",
                    },
                    {
                        "query": "csv cleanup automation",
                        "discussion_id": "1002",
                        "url": "https://x.com/example/status/1002",
                        "author_id": "x-user-private-002",
                        "title": "Generic AI automation trend",
                        "text": (
                            "Everyone is posting broad AI automation takes without "
                            "a concrete CSV cleanup pain, workaround, or buying signal."
                        ),
                        "discussion_kind": "trend_chatter",
                        "target_candidate": mvp_shape,
                        "like_count": 3,
                        "reply_count": 0,
                        "created_at": "2026-05-20T11:00:00+00:00",
                        "captured_at": "2026-05-21T15:05:00+00:00",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    source_config = tmp_path / "x-cache-config.json"
    source_config.write_text(
        json.dumps(
            {
                "run_id": "mvp-weekly-x-cache",
                "sources": [
                    {
                        "source_name": "x_discussions_cache",
                        "source_type": "x",
                        "trust_level": "low",
                        "freshness_window_days": 7,
                        "enabled": True,
                        "cursor_support": True,
                        "raw_snapshot_policy": "metadata_only",
                        "approval_required": True,
                        "credential_env_vars": ["XAI_API_KEY"],
                        "rate_limit_policy": {
                            "requests_per_minute": 1,
                            "burst_limit": 1,
                        },
                        "fixture_path": str(x_path.name),
                        "queries": ["csv cleanup automation"],
                        "max_results_per_run": 3,
                        "cache_only": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = run_mvp_of_week(
        telegram_export=export_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="mvp-weekly-x-cache",
        source_config=source_config,
        llm_provider=None,
    )
    report_text = result.report_path.read_text(encoding="utf-8")
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))
    matches = payload["matched_external_evidence"]

    assert payload["validation_adapter_status"]["x_discussions"]["status"] == "cache_only"
    assert {item["evidence_kind"] for item in matches} == {
        "negative_signal",
        "repeated_complaint",
    }
    assert all(item["lower_confidence"] is True for item in matches)
    assert all(item["corroboration_required"] is True for item in matches)
    assert all(item["supports_gate"] is False for item in matches)
    assert payload["selected"]["source_mix"]["selected_external_evidence_count"] == 0
    assert payload["selected"]["source_mix"]["selected_external_source_types"] == []
    assert "x/pain" in report_text
    assert "negative_signal: x/trend_chatter" in report_text
    assert "supports_gate=no" in report_text
    assert result.recommendation == "revisit_with_evidence_gap"


def test_mvp_of_week_kir_gate_blocks_telegram_seed_without_kir_metadata(
    tmp_path,
) -> None:
    mvp_shape = "LLM Workflow Evidence Router"
    export_path = tmp_path / "telegram_seeds.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "telegram:@capitan:1101",
                    "captured_at": _now_iso(),
                    "title": f"{mvp_shape} demand",
                    "text": (
                        "LLM workflow teams ask for evidence routing that keeps "
                        "research claims tied to source URLs."
                    ),
                    "snippet": "Teams ask for LLM workflow evidence routing.",
                    "source_url": "https://t.me/its_capitan/1101",
                    "channel_username": "@its_capitan",
                    "bucket": "strong",
                    "demand_surfaces": ["workflow_automation", "search_intent"],
                    "mvp_shape": mvp_shape,
                }
            ]
        ),
        encoding="utf-8",
    )
    source_config = _write_decision_grade_external_sources(
        tmp_path,
        mvp_shape=mvp_shape,
        run_id="mvp-weekly-kir-missing",
    )

    result = run_mvp_of_week(
        telegram_export=export_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="mvp-weekly-kir-missing",
        source_config=source_config,
        llm_provider=None,
    )
    report_text = result.report_path.read_text(encoding="utf-8")
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))
    source_mix = payload["selected"]["source_mix"]

    assert result.recommendation == "revisit_with_evidence_gap"
    assert result.dossier_status == "investigate"
    assert source_mix["decision_grade_external"] is True
    assert source_mix["kir_required"] is True
    assert source_mix["kir_gate_status"] == "missing_kir_thread"
    assert source_mix["kir_source_atom_count"] == 0
    assert "- Reason: kir_gate" in report_text
    assert "## KIR Evidence" in report_text
    assert "- KIR gate: missing_kir_thread" in report_text
    assert "- Gate: KIR evidence gap remains" in report_text
    assert "Recommendation: **focused_experiment**" not in report_text


def test_mvp_of_week_allows_kir_backed_telegram_seed_with_external_evidence(
    tmp_path,
) -> None:
    mvp_shape = "LLM Workflow Evidence Router"
    export_path = tmp_path / "telegram_seeds.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "knowledge-thread:llm-workflow-evidence-router",
                    "captured_at": _now_iso(),
                    "title": mvp_shape,
                    "text": (
                        "LLM workflow teams repeatedly ask for an evidence router "
                        "that keeps research claims tied to source URLs."
                    ),
                    "snippet": "Teams ask for LLM workflow evidence routing.",
                    "source_url": "https://t.me/market_ai/1101",
                    "source_urls": [
                        "https://t.me/market_ai/1101",
                        "https://t.me/operators/1102",
                    ],
                    "channel_username": "@market_ai,@operators",
                    "bucket": "knowledge_thread",
                    "demand_surfaces": ["workflow_automation", "search_intent"],
                    "mvp_shape": mvp_shape,
                    "source_kind": "knowledge_thread",
                    "knowledge_thread_slug": "llm-workflow-evidence-router",
                    "knowledge_thread_title": "LLM Workflow Evidence Router",
                    "knowledge_thread_status": "active",
                    "knowledge_atom_types": ["market_signal", "workflow_pattern"],
                    "source_atom_ids": [1101, 1102],
                }
            ]
        ),
        encoding="utf-8",
    )
    source_config = _write_decision_grade_external_sources(
        tmp_path,
        mvp_shape=mvp_shape,
        run_id="mvp-weekly-kir-passed",
    )

    result = run_mvp_of_week(
        telegram_export=export_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="mvp-weekly-kir-passed",
        source_config=source_config,
        llm_provider=None,
    )
    report_text = result.report_path.read_text(encoding="utf-8")
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))
    source_mix = payload["selected"]["source_mix"]

    assert result.recommendation == "focused_experiment"
    assert result.dossier_status == "focused_experiment"
    assert source_mix["decision_grade_external"] is True
    assert source_mix["selected_external_evidence_count"] == 2
    assert sorted(source_mix["selected_external_source_types"]) == ["github_public", "serp"]
    assert source_mix["kir_gate_status"] == "passed"
    assert source_mix["kir_source_kind"] == "knowledge_thread"
    assert source_mix["kir_thread_slug"] == "llm-workflow-evidence-router"
    assert source_mix["kir_thread_status"] == "active"
    assert source_mix["kir_source_atom_count"] == 2
    assert source_mix["kir_has_fresh_thread"] is True
    assert "- KIR gate: passed" in report_text
    assert "- Gate: decision-grade external evidence present" in report_text
    assert "## Matched External Evidence" in report_text
    assert "developer_issue: github_public" in report_text
    assert "search_demand: serp" in report_text
    assert "query=llm workflow evidence router" in report_text
    assert f"- {mvp_shape}:" in report_text
    assert len(payload["matched_external_evidence"]) == 2
    assert {item["evidence_kind"] for item in payload["matched_external_evidence"]} == {
        "developer_issue",
        "search_demand",
    }
    assert all(item["supports_gate"] for item in payload["matched_external_evidence"])


def test_selected_source_mix_marks_repeated_github_variants() -> None:
    captured_at = datetime(2026, 5, 20, 10, tzinfo=UTC)
    evidence = [
        EvidenceRecord(
            run_id="mvp-weekly-source-mix",
            source_type="github_public",
            source_id=f"github-{index}",
            source_url=f"https://github.com/example/repo/issues/{index}",
            captured_at=captured_at,
            title="Telegram SEO issue",
            snippet="Users ask for searchable Telegram archives.",
            normalized_text="Users ask for searchable Telegram archives.",
            content_hash=f"hash-{index}",
            source_fingerprint=f"github_public:{index}:hash-{index}",
            provider_metadata={"mvp_shape": "Telegram Channel SEO Site Generator"},
        )
        for index in (1, 2)
    ]
    candidate = CandidateAggregate(
        key="telegram-channel-seo-site-generator",
        title="Telegram Channel SEO Site Generator",
        evidence=evidence,
    )

    source_mix = _selected_source_mix(
        candidate,
        {
            "external_evidence_count": 2,
            "external_source_types": ("github_public",),
            "telegram_seed_evidence_count": 0,
        },
    )

    assert source_mix["readiness"] == "externally_corroborated"
    assert source_mix["selected_external_source_types"] == ["github_public"]
    assert source_mix["github_evidence_role"] == "repeated_variants_only"


def test_mvp_of_week_rewrites_contradictory_llm_gate_sections(tmp_path) -> None:
    export_path = tmp_path / "telegram_seeds.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "telegram:@capitan:1004",
                    "captured_at": "2026-05-20T10:00:00+00:00",
                    "title": "Telegram SEO demand",
                    "text": (
                        "Creators keep asking for a way to publish Telegram channel "
                        "archives as searchable SEO pages."
                    ),
                    "snippet": "Creators ask for searchable SEO pages from Telegram posts.",
                    "source_url": "https://t.me/its_capitan/1004",
                    "channel_username": "@its_capitan",
                    "bucket": "strong",
                    "demand_surfaces": ["creator_content_gap", "search_intent"],
                    "mvp_shape": "Telegram Channel SEO Site Generator",
                }
            ]
        ),
        encoding="utf-8",
    )
    provider = FakeLLMProvider(
        json.dumps(
            {
                "selected_title": "Telegram Channel SEO Site Generator",
                "recommendation": "focused_experiment",
                "score": 91,
                "markdown": (
                    "# MVP of the Week: Telegram Channel SEO Site Generator\n\n"
                    "Recommendation: **focused_experiment**\n"
                    "Score: 91/100\n\n"
                    "## Why This Week\nTelegram seed only.\n\n"
                    "## Decision Gate\n"
                    "- Recommendation allowed: yes\n"
                    "- Reason: focused_experiment\n\n"
                    "## Build-Worthy Recommendations\n"
                    "- Build Telegram Channel SEO Site Generator now.\n"
                ),
            }
        )
    )

    result = run_mvp_of_week(
        telegram_export=export_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="mvp-weekly-contradiction",
        llm_provider=provider,
    )
    report_text = result.report_path.read_text(encoding="utf-8")
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert result.recommendation == "revisit_with_evidence_gap"
    assert result.dossier_status == "investigate"
    assert payload["result"]["recommendation"] == "revisit_with_evidence_gap"
    assert payload["result"]["dossier_status"] == "investigate"
    assert payload["selected"]["recommendation"] == "revisit_with_evidence_gap"
    assert payload["selected"]["dossier_status"] == "investigate"
    assert report_text.startswith("# Candidate Dossier: Telegram Channel SEO Site Generator")
    assert "Status: investigate" in report_text
    assert (
        "Decision: Investigate missing evidence before treating this as build-ready." in report_text
    )
    assert "Recommendation: **revisit_with_evidence_gap**" in report_text
    assert "Recommendation: **focused_experiment**" not in report_text
    assert "- Recommendation allowed: no" in report_text
    assert "- Recommendation allowed: yes" not in report_text
    assert "- Reason: source_mix_gate" in report_text
    assert "- Reason: focused_experiment" not in report_text
    assert "- No build-worthy recommendations passed the Decision Gate." in report_text
    assert "Build Telegram Channel SEO Site Generator now" not in report_text
    assert "Downgraded from focused_experiment" in report_text


def test_mvp_of_week_existing_project_context_is_not_new_mvp(tmp_path) -> None:
    export_path = tmp_path / "telegram_seeds.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "telegram:@agents:1005",
                    "captured_at": "2026-05-20T10:00:00+00:00",
                    "title": "Workflow-to-agent signal",
                    "text": "Operators ask how to turn recurring workflows into agent templates.",
                    "snippet": "Operators ask for workflow-to-agent templates.",
                    "source_url": "https://t.me/agents/1005",
                    "channel_username": "@agents",
                    "bucket": "strong",
                    "demand_surfaces": ["workflow_automation"],
                    "mvp_shape": "Workflow-to-Agent Studio",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = run_mvp_of_week(
        telegram_export=export_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="mvp-weekly-existing-project",
        llm_provider=None,
    )
    report_text = result.report_path.read_text(encoding="utf-8")
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert result.recommendation == "existing_project_context"
    assert result.dossier_status == "investigate"
    assert payload["selected"]["dossier_status"] == "investigate"
    assert report_text.startswith("# Candidate Dossier: Workflow-to-Agent Studio")
    assert "Status: investigate" in report_text
    assert "Apply this to an existing project/backlog" in report_text
    assert "standalone new MVP" in report_text
    assert "1. Attach this evidence to the existing project as context." in report_text
    assert "The signal cannot be tied to a concrete existing-project backlog change." in report_text


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _write_decision_grade_external_sources(tmp_path, *, mvp_shape: str, run_id: str):
    captured_at = _now_iso()
    serp_path = tmp_path / "serp-kir.json"
    serp_path.write_text(
        json.dumps(
            {
                "provider": "serpapi",
                "captured_at": captured_at,
                "searches": [
                    {
                        "query": "llm workflow evidence router",
                        "captured_at": captured_at,
                        "provider_metadata": {"engine": "google"},
                        "results": [
                            {
                                "rank": 1,
                                "title": mvp_shape,
                                "url": "https://example.com/llm-workflow-evidence-router",
                                "snippet": (
                                    "Operators search for LLM workflow evidence routing "
                                    "that preserves citations and source URLs for claims."
                                ),
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    github_path = tmp_path / "github-kir.json"
    github_path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "kind": "issue",
                        "repository": "acme/evidence-router",
                        "number": 77,
                        "title": mvp_shape,
                        "body": (
                            "Our LLM workflow review loses track of source URLs and "
                            "claim evidence after research handoff. We need an evidence router."
                        ),
                        "url": "https://github.com/acme/evidence-router/issues/77",
                        "labels": ["workflow", "evidence"],
                        "created_at": captured_at,
                        "updated_at": captured_at,
                        "captured_at": captured_at,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    source_config = tmp_path / "kir-source-config.json"
    source_config.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "sources": [
                    {
                        "source_name": "serp_kir_fixture",
                        "source_type": "serp",
                        "trust_level": "medium",
                        "freshness_window_days": 14,
                        "enabled": True,
                        "cursor_support": True,
                        "raw_snapshot_policy": "metadata_only",
                        "approval_required": False,
                        "credential_env_vars": [],
                        "rate_limit_policy": {
                            "requests_per_minute": 10,
                            "burst_limit": 2,
                        },
                        "fixture_path": str(serp_path.name),
                        "queries": ["llm workflow evidence router"],
                        "provider": "serpapi",
                        "daily_budget_limit": 10,
                        "per_run_budget_limit": 10,
                    },
                    {
                        "source_name": "github_kir_fixture",
                        "source_type": "github_public",
                        "trust_level": "medium",
                        "freshness_window_days": 14,
                        "enabled": True,
                        "cursor_support": True,
                        "raw_snapshot_policy": "metadata_only",
                        "approval_required": False,
                        "credential_env_vars": [],
                        "rate_limit_policy": {
                            "requests_per_minute": 10,
                            "burst_limit": 2,
                        },
                        "fixture_path": str(github_path.name),
                        "queries": ["llm workflow evidence router"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return source_config
