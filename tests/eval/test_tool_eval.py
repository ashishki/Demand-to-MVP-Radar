from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_tool_eval_baseline_contains_required_metrics() -> None:
    content = (ROOT / "docs" / "tool_eval.md").read_text()
    expected = (
        r"\| 2026-05-19 \| T18 \| "
        r"`python scripts/eval_tools.py --fixture tests/fixtures/tool_eval.json, "
        r"run 2026-05-19` \| "
        r"1.00 \| 1.00 \| 1.00 \| 1.00 \| "
        r"scenario_count=4; fixture_version=tool-eval-v1 \|"
    )

    assert re.search(expected, content)
