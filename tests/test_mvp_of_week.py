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
    assert payload["result"]["selected_source_mix"]["readiness"] == "telegram_only"
    assert payload["selected"]["source_mix"]["selected_external_evidence_count"] == 0
    assert payload["selected"]["source_mix"]["reddit_api_status"] == "not_used"


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
