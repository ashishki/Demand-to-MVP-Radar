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


def test_reddit_adjacent_pain_remains_context_only() -> None:
    captured_at = datetime(2026, 7, 9, 10, tzinfo=UTC)
    reddit_record = _record(
        source_type="reddit",
        source_id="reddit:csv-cleanup",
        title="CSV cleanup automation for client exports",
        text=(
            "SaaS operators complain about weekly CSV cleanup and brittle spreadsheet "
            "macros after client exports."
        ),
        source_url="https://www.reddit.com/r/SaaS/comments/reddit-post-001/csv_cleanup/",
        captured_at=captured_at,
    )

    matches = match_external_evidence(
        candidate_title="Hotkey Dictation Workflow Probe",
        records=(reddit_record,),
    )
    context = external_research_context(
        candidate_title="Hotkey Dictation Workflow Probe",
        records=(reddit_record,),
        matched_fingerprints=matched_external_fingerprints(matches),
    )

    assert matches == []
    assert context["record_count"] == 1
    assert context["records"][0]["source_gate_satisfied"] is False
    assert context["records"][0]["reason"] == (
        "external result was not matched to the selected candidate"
    )


def test_crawler_competitor_requires_target_icp_for_gate_support() -> None:
    captured_at = datetime(2026, 7, 9, 10, tzinfo=UTC)
    without_icp = _record(
        source_type="crawl4ai",
        source_id="crawl4ai:competitor-without-icp",
        title="CleanSheet CSV Cleanup",
        text="CSV cleanup automation for client exports with pricing and alternatives.",
        source_url="https://cleansheet.example/csv-cleanup",
        captured_at=captured_at,
        provider_metadata={
            "evidence_kind": "competitor_traction",
            "page_kind": "competitor",
            "target_candidate": "CSV cleanup automation for client exports",
        },
    )
    with_icp = _record(
        source_type="crawl4ai",
        source_id="crawl4ai:competitor-with-icp",
        title="CleanSheet CSV Cleanup",
        text="CSV cleanup automation for client exports with pricing and alternatives.",
        source_url="https://cleansheet.example/csv-cleanup",
        captured_at=captured_at,
        provider_metadata={
            "evidence_kind": "competitor_traction",
            "page_kind": "competitor",
            "target_candidate": "CSV cleanup automation for client exports",
            "target_icp": "small SaaS operators",
        },
    )

    weak_match = match_external_evidence(
        candidate_title="CSV cleanup automation for client exports",
        records=(without_icp,),
    )
    decision_grade_match = match_external_evidence(
        candidate_title="CSV cleanup automation for client exports",
        records=(with_icp,),
    )

    assert weak_match[0]["decision_grade"] is False
    assert weak_match[0]["supports_gate"] is False
    assert weak_match[0]["target_icp"] is None
    assert decision_grade_match[0]["decision_grade"] is True
    assert decision_grade_match[0]["supports_gate"] is True
    assert decision_grade_match[0]["target_icp"] == "small SaaS operators"


def test_crawler_adjacent_pain_remains_context_only() -> None:
    captured_at = datetime(2026, 7, 9, 10, tzinfo=UTC)
    crawler_record = _record(
        source_type="crawl4ai",
        source_id="crawl4ai:csv-competitor",
        title="CleanSheet CSV Cleanup",
        text="CSV cleanup automation for client exports with pricing and alternatives.",
        source_url="https://cleansheet.example/csv-cleanup",
        captured_at=captured_at,
        provider_metadata={
            "evidence_kind": "competitor_traction",
            "page_kind": "competitor",
            "target_candidate": "CSV cleanup automation for client exports",
            "target_icp": "small SaaS operators",
        },
    )

    matches = match_external_evidence(
        candidate_title="Hotkey Dictation Workflow Probe",
        records=(crawler_record,),
    )
    context = external_research_context(
        candidate_title="Hotkey Dictation Workflow Probe",
        records=(crawler_record,),
        matched_fingerprints=matched_external_fingerprints(matches),
    )

    assert matches == []
    assert context["record_count"] == 1
    assert context["records"][0]["source_gate_satisfied"] is False


def test_x_discussion_matches_but_never_supports_gate() -> None:
    captured_at = datetime(2026, 7, 9, 10, tzinfo=UTC)
    x_record = _record(
        source_type="x",
        source_id="x:discussion:1001",
        title="X discussion about CSV cleanup",
        text="CSV cleanup automation for client exports keeps coming up as a manual pain.",
        source_url="https://x.com/example/status/1001",
        captured_at=captured_at,
        provider_metadata={
            "evidence_kind": "repeated_complaint",
            "discussion_kind": "pain",
            "target_candidate": "CSV cleanup automation for client exports",
        },
    )

    matches = match_external_evidence(
        candidate_title="CSV cleanup automation for client exports",
        records=(x_record,),
    )

    assert len(matches) == 1
    assert matches[0]["lower_confidence"] is True
    assert matches[0]["corroboration_required"] is True
    assert matches[0]["discussion_kind"] == "pain"
    assert matches[0]["decision_grade"] is False
    assert matches[0]["supports_gate"] is False


def _record(
    *,
    source_type: str,
    source_id: str,
    title: str,
    text: str,
    source_url: str,
    captured_at: datetime,
    provider_metadata: dict[str, str] | None = None,
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
        provider_metadata=provider_metadata or {},
    )
