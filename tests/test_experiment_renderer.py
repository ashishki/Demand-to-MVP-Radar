from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from demand_mvp_radar.experiments import build_experiment_pack
from demand_mvp_radar.reports.experiment_markdown import (
    render_experiment_markdown,
    write_experiment_markdown,
)


def test_experiment_markdown_contains_required_sections() -> None:
    markdown = render_experiment_markdown(build_experiment_pack(_experiment_payload()))

    expected_sections = [
        "# MVP Experiment: 101",
        "## Scope",
        "## Target User",
        "## Validation Method",
        "## First 10 Targets",
        "## Thresholds",
    ]
    positions = [markdown.index(section) for section in expected_sections]

    assert positions == sorted(positions)
    assert "Upload ledger rows and flag likely duplicate payments." in markdown
    assert "Finance operators reconciling invoices weekly." in markdown
    assert "concierge_test" in markdown
    assert "1. finance operator 1" in markdown
    assert "10. finance operator 10" in markdown
    assert "- Success: 3 of 10 operators submit real ledger samples." in markdown
    assert "- Kill: 0 operators agree to a follow-up workflow review." in markdown
    assert "- Revisit: 2 operators want it but need stronger privacy guarantees." in markdown
    assert "Timebox: 10 days" in markdown


def test_experiment_markdown_includes_context() -> None:
    markdown = render_experiment_markdown(build_experiment_pack(_experiment_payload()))

    assert "| [1] | telegram_research_agent | telegram-live-001 | 2026-05-20 |" in markdown
    assert "https://t.me/operators/ledgerpulse-001" in markdown
    assert "Operators repeatedly ask for invoice reconciliation help." in markdown
    assert "## Risk Flags" in markdown
    assert "- Accounting data may create compliance concerns." in markdown


def test_experiment_write_is_atomic_and_idempotent(tmp_path) -> None:
    pack = build_experiment_pack(_experiment_payload())
    report_dir = tmp_path / "experiments"

    first_path = write_experiment_markdown(report_dir, pack, run_id="run-001")
    first_content = first_path.read_text()
    second_path = write_experiment_markdown(report_dir, pack, run_id="run-002")

    assert first_path != second_path
    assert first_path.read_text() == first_content
    assert second_path.exists()

    updated_pack = pack.model_copy(update={"success_threshold": "5 of 10 operators opt in."})
    updated_path = write_experiment_markdown(report_dir, updated_pack, run_id="run-001")

    assert updated_path == first_path
    assert "5 of 10 operators opt in." in first_path.read_text()
    assert second_path.read_text() == render_experiment_markdown(pack)

    def failing_writer(path: Path, content: str) -> None:
        path.write_text(content)
        raise RuntimeError("interrupted write")

    try:
        write_experiment_markdown(report_dir, pack, run_id="run-001", writer=failing_writer)
    except RuntimeError:
        pass

    assert "5 of 10 operators opt in." in first_path.read_text()
    assert not (report_dir / ".101-run-001.md.tmp").exists()


def _experiment_payload() -> dict[str, object]:
    captured_at = datetime(2026, 5, 20, tzinfo=UTC).isoformat()
    return {
        "opportunity_id": "101",
        "one_function_scope": "Upload ledger rows and flag likely duplicate payments.",
        "target_user": "Finance operators reconciling invoices weekly.",
        "validation_method": "concierge_test",
        "first_10_targets": tuple(f"finance operator {index}" for index in range(1, 11)),
        "success_threshold": "3 of 10 operators submit real ledger samples.",
        "kill_threshold": "0 operators agree to a follow-up workflow review.",
        "revisit_threshold": "2 operators want it but need stronger privacy guarantees.",
        "timebox_days": 10,
        "source_citations": (
            {
                "citation_number": 1,
                "source_type": "telegram_research_agent",
                "source_title_or_id": "telegram-live-001",
                "captured_at": captured_at,
                "snippet": "Operators repeatedly ask for invoice reconciliation help.",
                "source_ref": "https://t.me/operators/ledgerpulse-001",
            },
        ),
        "risk_flags": ("Accounting data may create compliance concerns.",),
        "human_decision": "build",
        "human_decision_reason": "Operator approved a focused validation run.",
    }
