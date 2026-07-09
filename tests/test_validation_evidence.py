from __future__ import annotations

from datetime import UTC, datetime

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.validation_evidence import (
    decision_grade_match_count,
    external_research_context,
    match_external_evidence,
    matched_external_fingerprints,
    matched_external_source_types,
    missing_evidence_by_kind,
)
from demand_mvp_radar.validation_queries import build_validation_query_pack


def test_external_evidence_must_match_candidate_before_supporting_gate() -> None:
    captured_at = datetime(2026, 7, 9, 10, tzinfo=UTC)
    matched = _record(
        source_type="serp",
        source_id="serp:matched",
        title="Hotkey Dictation Workflow Probe",
        text="Operators search for a hotkey dictation workflow probe.",
        source_url="https://example.com/hotkey-dictation",
        captured_at=captured_at,
    )
    unmatched = _record(
        source_type="github_public",
        source_id="github:unmatched",
        title="Unrelated CRM Dashboard",
        text="A different dashboard problem that should remain context only.",
        source_url="https://github.com/acme/crm-dashboard/issues/1",
        captured_at=captured_at,
    )
    matches = match_external_evidence(
        candidate_title="Hotkey Dictation Workflow Probe",
        records=(matched, unmatched),
    )
    context = external_research_context(
        candidate_title="Hotkey Dictation Workflow Probe",
        records=(matched, unmatched),
        matched_fingerprints=matched_external_fingerprints(matches),
    )

    assert decision_grade_match_count(matches) == 1
    assert matched_external_source_types(matches) == ("serp",)
    assert matches[0]["source_id"] == "serp:matched"
    assert matches[0]["supports_gate"] is True
    assert context["source_gate_satisfied"] is False
    assert context["record_count"] == 1
    assert context["records"][0]["source_id"] == "github:unmatched"


def test_missing_evidence_by_kind_names_absent_validation_kinds() -> None:
    query_pack = build_validation_query_pack(
        candidate_title="Hotkey Dictation Workflow Probe",
        surfaces=("workflow_automation",),
        missing_evidence=("pricing or willingness-to-pay signal",),
    )

    missing = missing_evidence_by_kind(
        matched_evidence=[],
        validation_queries=query_pack,
        current_missing=("pricing or willingness-to-pay signal",),
    )

    assert missing["wtp_signals"]["evidence_kind"] == "wtp_signal"
    assert missing["manual_workarounds"]["evidence_kind"] == "manual_workaround"
    assert missing["search_demand"]["evidence_kind"] == "search_demand"
    assert missing["independent_external_sources"]["next_intent"] == "search_demand"
    assert missing["wtp_signals"]["next_query"] == '"hotkey dictation workflow probe" pricing'


def test_external_evidence_matcher_handles_cyrillic_candidate_titles() -> None:
    captured_at = datetime(2026, 7, 9, 10, tzinfo=UTC)
    record = _record(
        source_type="serp",
        source_id="serp:cyrillic",
        title="Проба диктовки по горячей клавише",
        text="Операторы ищут пробу диктовки по горячей клавише для рабочих процессов.",
        source_url="https://example.com/dictation",
        captured_at=captured_at,
    )

    matches = match_external_evidence(
        candidate_title="Проба диктовки по горячей клавише",
        records=(record,),
    )

    assert len(matches) == 1
    assert matches[0]["match_basis"] == "title_exact"
    assert matches[0]["supports_gate"] is True


def _record(
    *,
    source_type: str,
    source_id: str,
    title: str,
    text: str,
    source_url: str,
    captured_at: datetime,
) -> EvidenceRecord:
    return EvidenceRecord(
        run_id="test",
        source_type=source_type,
        source_id=source_id,
        source_url=source_url,
        captured_at=captured_at,
        title=title,
        snippet=text,
        normalized_text=text,
        content_hash=f"hash:{source_id}",
        source_fingerprint=f"{source_type}:{source_id}",
    )
