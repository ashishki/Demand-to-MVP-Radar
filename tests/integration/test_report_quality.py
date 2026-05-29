from __future__ import annotations

import json

from demand_mvp_radar.config import Settings
from demand_mvp_radar.mvp_weekly import run_mvp_of_week


def test_report_separates_interest_from_build_recommendation(tmp_path) -> None:
    export_path = tmp_path / "telegram_seeds.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "telegram:@capitan:1001",
                    "captured_at": "2026-05-20T10:00:00+00:00",
                    "title": "Telegram content is hard to search",
                    "text": "Channel owners ask for searchable SEO pages from Telegram posts.",
                    "source_url": "https://t.me/its_capitan/1001",
                    "channel_username": "@its_capitan",
                    "bucket": "strong",
                    "demand_surfaces": ["creator_content_gap", "search_intent"],
                    "mvp_shape": "Telegram Channel SEO Site Generator",
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
                    "demand_surfaces": ["manual_workaround"],
                    "mvp_shape": "Telegram Channel SEO Site Generator",
                },
            ]
        ),
        encoding="utf-8",
    )

    result = run_mvp_of_week(
        telegram_export=export_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="mvp-weekly-report-quality",
    )

    report_text = result.report_path.read_text(encoding="utf-8")

    assert result.recommendation == "revisit_with_evidence_gap"
    assert "## Build-Worthy Recommendations" in report_text
    assert "- No build-worthy recommendations passed the Decision Gate." in report_text
    assert "## Interesting Signals" in report_text
    assert "Telegram Channel SEO Site Generator" in report_text
    assert "- Recommendation allowed: no" in report_text
    assert "- Reason: source_mix_gate" in report_text
    assert "## Source Trust And Repeated Signals" in report_text
    assert "repeated_signals=1" in report_text
