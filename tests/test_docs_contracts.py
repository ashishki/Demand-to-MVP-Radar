from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPERATOR_WORKFLOW = ROOT / "docs" / "OPERATOR_WORKFLOW.md"


def _operator_workflow_text() -> str:
    return OPERATOR_WORKFLOW.read_text(encoding="utf-8")


def test_operator_workflow_contains_required_sections() -> None:
    content = _operator_workflow_text()

    for section in (
        "## Weekly Inputs",
        "## Weekly Outputs",
        "## Review Time Target",
        "## Decision Taxonomy",
    ):
        assert section in content

    assert "under 15 minutes" in content
    for decision in (
        "`build`",
        "`reject`",
        "`revisit`",
        "`needs_more_evidence`",
        "`already_exists`",
        "`not_my_icp`",
        "`too_hard_to_distribute`",
    ):
        assert decision in content


def test_operator_workflow_lists_failure_conditions() -> None:
    content = _operator_workflow_text()

    assert "## Adoption Failure Conditions" in content
    for condition in (
        "generic ideas",
        "without cited source support",
        "stale evidence",
        "recently rejected ideas",
        "more than 15 minutes",
    ):
        assert condition in content


def test_operator_workflow_defines_privacy_boundaries() -> None:
    content = _operator_workflow_text()

    assert "## Privacy Boundaries" in content
    for boundary in (
        "### Telegram Exports",
        "### Operator Notes",
        "### Credentials",
    ):
        assert boundary in content

    for required_phrase in (
        "raw exports",
        "Raw notes",
        "environment variables",
        "ignored local secrets files",
        "excluded from git",
    ):
        assert required_phrase in content
