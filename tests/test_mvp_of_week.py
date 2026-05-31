from __future__ import annotations

import json
import sqlite3

from demand_mvp_radar.cli import main
from demand_mvp_radar.config import Settings
from demand_mvp_radar.llm.adapter import FakeLLMProvider
from demand_mvp_radar.mvp_weekly import run_mvp_of_week
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
    assert "MVP of the Week: Telegram Channel SEO Site Generator" in report_path.read_text()
    assert "This Week's Experiment" in report_path.read_text()
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
