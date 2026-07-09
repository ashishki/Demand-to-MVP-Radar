from __future__ import annotations

from demand_mvp_radar.validation_queries import (
    build_validation_query_pack,
    validation_adapter_status,
)


def test_validation_query_pack_is_candidate_specific_and_deterministic() -> None:
    pack = build_validation_query_pack(
        candidate_title="Hotkey Dictation Workflow Probe",
        surfaces=("workflow_automation", "manual_workaround"),
        missing_evidence=(
            "non-Telegram public evidence for the same pain",
            "pricing or willingness-to-pay signal",
        ),
    )
    repeated = build_validation_query_pack(
        candidate_title="Hotkey Dictation Workflow Probe",
        surfaces=("workflow_automation", "manual_workaround"),
        missing_evidence=(
            "non-Telegram public evidence for the same pain",
            "pricing or willingness-to-pay signal",
        ),
    )

    assert pack == repeated
    assert pack["contract"]["context_only_records_satisfy_gates"] is False
    assert pack["contract"]["unmatched_external_results_satisfy_gates"] is False
    assert pack["contract"]["live_api_calls"] is False
    assert pack["queries_by_intent"]["search_demand"][0]["query"] == (
        '"Hotkey Dictation Workflow Probe"'
    )
    assert (
        "hotkey dictation workflow probe"
        in pack["queries_by_intent"]["manual_workarounds"][0]["query"]
    )
    assert pack["queries_by_intent"]["x_discussions"][0]["lower_confidence"] is True
    assert (
        pack["missing_evidence_by_category"]["external_corroboration"]["next_intent"]
        == "search_demand"
    )
    assert pack["missing_evidence_by_category"]["wtp_signals"]["next_intent"] == ("wtp_signals")


def test_validation_adapter_status_is_failure_tolerant_before_live_adapters() -> None:
    statuses = validation_adapter_status()

    assert statuses["search_demand"]["status"] == "adapter_disabled"
    assert statuses["reddit_forum_complaints"]["status"] == "adapter_disabled"
    assert statuses["competitor_workaround_crawler"]["status"] == "adapter_disabled"
    assert statuses["x_discussions"]["status"] == "adapter_disabled"
