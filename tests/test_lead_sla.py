from __future__ import annotations

import json
from pathlib import Path

from demand_mvp_radar.cli import main
from demand_mvp_radar.lead_sla import analyze_lead_sla_csv
from demand_mvp_radar.reports.lead_sla import render_lead_sla_report

FIXTURE = "tests/fixtures/lead_sla/open_proxy_leads.csv"


def test_lead_sla_analysis_handles_public_proxy_csv() -> None:
    analysis = analyze_lead_sla_csv(
        csv_path=Path(FIXTURE),
        sla_minutes=5,
        hash_lead_id=True,
        dataset_label="public proxy fixture",
        public_source_url="https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset",
    )

    assert analysis.total_rows == 12
    assert analysis.valid_rows == 10
    assert len(analysis.invalid_rows) == 2
    assert analysis.responded_leads == 8
    assert analysis.unresponded_leads == 2
    assert analysis.response_breach_count == 5
    assert analysis.total_sla_miss_count == 7
    assert analysis.median_response_minutes == 18
    assert analysis.p90_response_minutes == 180
    assert all(record.lead_id.startswith("lead_") for record in analysis.records)
    assert any("Ignored private columns" in warning for warning in analysis.warnings)


def test_lead_sla_report_redacts_private_fields() -> None:
    analysis = analyze_lead_sla_csv(
        csv_path=Path(FIXTURE),
        sla_minutes=5,
        hash_lead_id=True,
    )

    report = render_lead_sla_report(analysis, top_n=5)

    assert "# Lead Response SLA Report" in report
    assert "Total SLA misses including no response: 7" in report
    assert "Breakdown By Source" in report
    assert "lead1@example.com" not in report
    assert "Example One" not in report


def test_lead_sla_cli_writes_report(tmp_path, capsys) -> None:
    output = tmp_path / "lead_sla.md"

    exit_code = main(
        [
            "lead-sla-report",
            "--input",
            FIXTURE,
            "--output",
            str(output),
            "--sla-minutes",
            "5",
            "--hash-lead-id",
            "--dataset-label",
            "open support proxy",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["sla_misses"] == 7
    assert output.exists()
    assert "open support proxy" in output.read_text()


def test_lead_sla_cli_rejects_missing_required_columns(tmp_path, capsys) -> None:
    input_path = tmp_path / "bad.csv"
    input_path.write_text("lead_id,source\nL001,demo\n")

    exit_code = main(
        [
            "lead-sla-report",
            "--input",
            str(input_path),
            "--output",
            str(tmp_path / "report.md"),
        ]
    )

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "missing required column" in payload["error"]
