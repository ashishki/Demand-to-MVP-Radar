from __future__ import annotations

import json
import sqlite3

from demand_mvp_radar.cli import main


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
    connection = sqlite3.connect(tmp_path / "data" / "radar.sqlite3")
    connection.row_factory = sqlite3.Row
    run = connection.execute(
        "SELECT status, source_counts FROM runs WHERE run_id = ?",
        ("mvp-weekly-test",),
    ).fetchone()

    assert exit_code == 0
    assert output["status"] == "selected"
    assert output["selected_title"] == "Telegram Channel SEO Site Generator"
    assert report_path.exists()
    assert json_path.exists()
    assert "MVP of the Week: Telegram Channel SEO Site Generator" in report_path.read_text()
    assert "This Week's Experiment" in report_path.read_text()
    assert run["status"] == "mvp_of_week"
    assert json.loads(run["source_counts"])["telegram_research_agent"] == 2
