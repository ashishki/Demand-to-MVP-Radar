from __future__ import annotations

from demand_mvp_radar.reports.source_value import (
    SourceValueInput,
    build_source_value_report,
    render_source_value_markdown,
)


def test_source_value_report_contains_required_metrics() -> None:
    report = build_source_value_report(
        (
            SourceValueInput(
                source_name="hacker-news",
                source_type="hacker_news",
                evidence_count=12,
                cited_count=5,
                decision_influence_count=2,
                quarantined_count=1,
                failure_count=0,
                freshness_days=2,
                estimated_cost_usd=0,
            ),
        )
    )
    row = report.rows[0]

    assert row.evidence_count == 12
    assert row.cited_count == 5
    assert row.decision_influence_count == 2
    assert row.quarantine_rate == 0.08
    assert row.freshness_days == 2
    assert row.failure_count == 0
    assert row.estimated_cost_usd == 0
    assert row.recommendation == "keep"


def test_source_value_report_flags_low_value_sources() -> None:
    report = build_source_value_report(
        (
            SourceValueInput(
                source_name="expensive-serp",
                source_type="serp",
                evidence_count=3,
                cited_count=0,
                decision_influence_count=0,
                quarantined_count=4,
                failure_count=3,
                freshness_days=45,
                estimated_cost_usd=12.5,
            ),
        )
    )
    row = report.rows[0]

    assert row.recommendation == "disable"
    assert "high quarantine rate" in row.recommendation_reasons
    assert "high failure count" in row.recommendation_reasons
    assert "stale evidence" in row.recommendation_reasons
    assert "excessive cost without influence" in row.recommendation_reasons


def test_source_value_report_redacts_private_fields() -> None:
    report = build_source_value_report(
        (
            SourceValueInput(
                source_name="discord-live",
                source_type="discord",
                evidence_count=1,
                cited_count=0,
                decision_influence_count=0,
                quarantined_count=0,
                failure_count=0,
                freshness_days=1,
                estimated_cost_usd=0,
                private_locator="guild-private-001/channel-private-001",
                credential_env_vars=("DISCORD_BOT_TOKEN",),
                last_error="DISCORD_BOT_TOKEN missing",
            ),
        )
    )
    markdown = render_source_value_markdown(report)

    assert "guild-private-001" not in report.model_dump_json()
    assert "channel-private-001" not in report.model_dump_json()
    assert "DISCORD_BOT_TOKEN" not in report.model_dump_json()
    assert "guild-private-001" not in markdown
    assert "DISCORD_BOT_TOKEN" not in markdown
