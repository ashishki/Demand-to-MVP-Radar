from __future__ import annotations

import json
from pathlib import Path

from demand_mvp_radar.config import Settings
from demand_mvp_radar.llm.adapter import FakeLLMProvider
from demand_mvp_radar.mvp_weekly import run_mvp_of_week


def test_candidate_dossier_report_quality_contract(tmp_path) -> None:
    result = _run_mvp_report(tmp_path)
    report_text = result.report_path.read_text(encoding="utf-8")
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert report_text.startswith("# Candidate Dossier: Telegram Channel SEO Site Generator")
    assert _top_block(report_text) == [
        "# Candidate Dossier: Telegram Channel SEO Site Generator",
        "",
        "Status: investigate",
        "Decision: Investigate missing evidence before treating this as build-ready.",
        "Confidence: low",
        "Next action: Collect the missing source evidence listed below before building.",
        "Recommendation: **revisit_with_evidence_gap**",
    ]
    for heading in (
        "## Why This Candidate",
        "## Source Mix",
        "## Validation Query Pack",
        "## Matched External Evidence",
        "## What Would Change The Decision",
        "## Evidence",
        "## Missing Evidence",
        "## Next Experiment",
        "## Kill Criteria",
        "## Operator Fit",
        "## Anti-Complexity Guardrail",
    ):
        assert heading in report_text
    assert "- Readiness: telegram_only" in report_text
    assert "- Selected external evidence: 0 (types: none)" in report_text
    assert "- Gate: external evidence gap remains" in report_text
    assert "- No second independent non-Telegram source supports the same pain." in report_text
    assert "- Next validation action:" in report_text
    assert "- Market context: context only, not proof." in report_text
    assert payload["result"]["dossier_status"] == "investigate"
    assert payload["result"]["selected_source_mix"]["readiness"] == "telegram_only"
    assert payload["selected"]["dossier_status"] == "investigate"
    assert payload["selected"]["source_mix"]["readiness"] == "telegram_only"
    assert payload["decision_change_action"]["current_gate"] == "investigate"
    assert payload["selected"]["decision_change_action"]["current_gate"] == "investigate"


def test_failed_source_gate_removes_contradictory_build_ready_claims(tmp_path) -> None:
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
                    "- Build Telegram Channel SEO Site Generator now.\n\n"
                    "## Extra Claim\n"
                    "- Decision gate passed; ready to build now.\n"
                ),
            }
        )
    )

    result = _run_mvp_report(tmp_path, provider=provider)
    report_text = result.report_path.read_text(encoding="utf-8")
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert result.recommendation == "revisit_with_evidence_gap"
    assert payload["result"]["recommendation"] == "revisit_with_evidence_gap"
    assert "Recommendation: **focused_experiment**" not in report_text
    assert "- Recommendation allowed: yes" not in report_text
    assert "- Reason: focused_experiment" not in report_text
    assert "Build Telegram Channel SEO Site Generator now" not in report_text
    assert "ready to build now" not in report_text
    assert "Decision gate passed" not in report_text
    assert "- Recommendation allowed: no" in report_text
    assert "- Reason: source_mix_gate" in report_text
    assert "- No build-worthy recommendations passed the Decision Gate." in report_text
    assert "Removed contradictory build-ready claim because source gates failed." in report_text


def test_existing_project_context_report_quality_contract(tmp_path) -> None:
    result = _run_mvp_report(tmp_path, mvp_shape="Workflow-to-Agent Studio")
    report_text = result.report_path.read_text(encoding="utf-8")
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))

    assert result.recommendation == "existing_project_context"
    assert payload["result"]["dossier_status"] == "investigate"
    assert report_text.startswith("# Candidate Dossier: Workflow-to-Agent Studio")
    assert "Apply this to an existing project/backlog" in report_text
    assert "standalone new MVP" in report_text
    assert "1. Attach this evidence to the existing project as context." in report_text
    assert (
        "- The signal cannot be tied to a concrete existing-project backlog change." in report_text
    )
    assert "Status: build" not in report_text
    assert "Recommendation: **focused_experiment**" not in report_text


def _run_mvp_report(
    tmp_path,
    *,
    mvp_shape: str = "Telegram Channel SEO Site Generator",
    provider: FakeLLMProvider | None = None,
):
    export_path = tmp_path / "telegram_seeds.json"
    _write_seed_export(export_path, mvp_shape=mvp_shape)
    return run_mvp_of_week(
        telegram_export=export_path,
        settings=Settings(data_dir=tmp_path / "data", report_dir=tmp_path / "reports"),
        run_id="mvp-weekly-report-quality",
        llm_provider=provider,
    )


def _write_seed_export(path: Path, *, mvp_shape: str) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "upstream_id": "telegram:@capitan:1001",
                    "captured_at": "2026-05-20T10:00:00+00:00",
                    "title": f"{mvp_shape} demand",
                    "text": "Creators ask for searchable public archives from Telegram posts.",
                    "snippet": "Creators ask for searchable public archives from Telegram posts.",
                    "source_url": "https://t.me/its_capitan/1001",
                    "channel_username": "@its_capitan",
                    "bucket": "strong",
                    "demand_surfaces": ["creator_content_gap", "search_intent"],
                    "mvp_shape": mvp_shape,
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
                    "snippet": "Creators copy posts into websites manually.",
                    "source_url": "https://t.me/example/1002",
                    "channel_username": "@example",
                    "bucket": "watch",
                    "demand_surfaces": ["manual_workaround", "creator_content_gap"],
                    "mvp_shape": mvp_shape,
                },
            ]
        ),
        encoding="utf-8",
    )


def _top_block(report_text: str) -> list[str]:
    lines = report_text.splitlines()
    return lines[:7]
