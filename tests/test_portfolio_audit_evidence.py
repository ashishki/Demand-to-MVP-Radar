from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "reports/evidence/portfolio-audit-2026-07-13"
CORPUS_PATH = EVIDENCE_DIR / "public_corpus_v1.jsonl"
CORPUS_CARD_PATH = EVIDENCE_DIR / "CORPUS_CARD.md"
DECISION_LOG_PATH = EVIDENCE_DIR / "four_slot_decision_log.json"
DECISION_LOG_MD_PATH = EVIDENCE_DIR / "FOUR_SLOT_DECISION_LOG.md"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_sanitized_public_corpus_is_traceable_and_bounded() -> None:
    records = [json.loads(line) for line in CORPUS_PATH.read_text(encoding="utf-8").splitlines()]

    assert len(records) == 8
    assert len({record["record_id"] for record in records}) == 8
    assert {record["evidence_role"] for record in records} == {
        "operator_problem",
        "problem_context",
        "existing_alternative",
    }

    for record in records:
        report_path = ROOT / record["source_report"]
        assert report_path.is_file()
        assert _sha256(report_path) == record["source_report_sha256"]
        assert record["source_url"].startswith("https://")
        assert record["observation"]
        assert record["limitation"]


def test_sanitized_public_corpus_contains_no_private_markers() -> None:
    raw = CORPUS_PATH.read_text(encoding="utf-8")
    lowered = raw.lower()

    assert not re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", raw)
    for marker in (
        "api_key",
        "bearer ",
        "private channel",
        "operator note",
        "customer name",
        "phone number",
        "/home/",
    ):
        assert marker not in lowered


def test_four_slot_log_does_not_invent_longitudinal_or_human_evidence() -> None:
    decision_log = json.loads(DECISION_LOG_PATH.read_text(encoding="utf-8"))
    slots = decision_log["slots"]

    assert len(slots) == 4
    assert decision_log["counting_evidence_cycle_count"] == sum(
        slot["counts_toward_gate"] for slot in slots
    )
    assert decision_log["counting_evidence_cycle_count"] == 2
    assert decision_log["remaining_counting_runs"] == 2
    assert decision_log["human_recorded_decision_count"] == 0
    assert sum(slot["human_recorded_decisions"] for slot in slots) == 0
    assert decision_log["four_week_longitudinal_gate"].startswith("blocked_")

    missing_artifacts = [slot for slot in slots if not (ROOT / slot["artifact"]).is_file()]
    assert [slot["run_id"] for slot in missing_artifacts] == ["mvp-weekly-2026-W14-radar"]
    assert missing_artifacts[0]["status"] == "referenced_artifact_not_tracked_in_clean_clone"
    assert missing_artifacts[0]["artifact_sha256"] is None


def test_evidence_cards_state_non_claims() -> None:
    corpus_card = CORPUS_CARD_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_MD_PATH.read_text(encoding="utf-8")

    assert "not a live collection" in corpus_card
    assert "no human-recorded product decision" in corpus_card
    assert "does not complete the four-run or four-week" in corpus_card
    assert "It is not a four-week result" in decision_log
    assert "human-recorded decisions: `0`" in decision_log
    assert "counting evidence cycles: `2/4`" in decision_log
