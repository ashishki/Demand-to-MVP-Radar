from __future__ import annotations

import json

from demand_mvp_radar.cli import main
from demand_mvp_radar.telegram_digest import digest_to_seed_rows


def test_digest_to_seed_export_maps_evidence_rows() -> None:
    seeds, skipped = digest_to_seed_rows(_digest_payload())

    assert skipped == []
    assert len(seeds) == 2
    first = seeds[0]
    assert first["upstream_id"] == "digest:2026-W14:S1"
    assert first["captured_at"] == "2026-04-01T14:20:23+00:00"
    assert first["source_url"] == "https://t.me/llm_under_hood/788"
    assert first["channel_username"] == "@llm_under_hood"
    assert first["bucket"] == "strong"
    assert first["mvp_shape"] == "Agent Instruction Conflict Review"
    assert "repeated_questions" in first["demand_surfaces"]
    assert "non-Telegram public evidence for the same pain" in first["verification_needed"]


def test_digest_to_seed_export_skips_unusable_rows() -> None:
    payload = _digest_payload()
    payload["evidence"].append({"id": "S3", "channel": "@private", "excerpt": ""})
    payload["evidence"].append({"id": "S4", "channel": "@bad", "excerpt": "Useful but no URL"})

    seeds, skipped = digest_to_seed_rows(payload)

    assert len(seeds) == 2
    assert skipped == ["S3: missing excerpt", "S4: missing safe public/source URL"]


def test_digest_to_seed_export_cli_writes_json(tmp_path, capsys) -> None:
    digest_path = tmp_path / "digest.json"
    output_path = tmp_path / "seeds.json"
    digest_path.write_text(json.dumps(_digest_payload()), encoding="utf-8")

    exit_code = main(
        [
            "digest-to-seeds",
            "--digest",
            str(digest_path),
            "--output",
            str(output_path),
        ]
    )
    output = json.loads(capsys.readouterr().out)
    seeds = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert output["seed_count"] == 2
    assert output["skipped_count"] == 0
    assert seeds[1]["mvp_shape"] == "Agent Skills Marketplace Radar"


def _digest_payload() -> dict[str, object]:
    return {
        "meta": {
            "week_label": "2026-W14",
            "generated_at": "2026-04-01T14:20:23+00:00",
        },
        "evidence": [
            {
                "id": "S1",
                "channel": "@llm_under_hood",
                "date": "",
                "excerpt": (
                    "What should an agent do when instructions conflict? "
                    "Builders ask for a resolution layer before LLM calls."
                ),
                "url": "https://t.me/llm_under_hood/788",
            },
            {
                "id": "S2",
                "channel": "@data_secrets",
                "date": "2026-04-01T12:00:00+00:00",
                "excerpt": (
                    "Agent skills marketplaces show alternative integrations and pricing pressure."
                ),
                "url": "https://t.me/data_secrets/8943",
            },
        ],
    }
