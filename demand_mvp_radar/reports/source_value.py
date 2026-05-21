"""Source value reporting."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SourceValueInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_name: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    evidence_count: int = Field(ge=0)
    cited_count: int = Field(ge=0)
    decision_influence_count: int = Field(ge=0)
    quarantined_count: int = Field(ge=0)
    failure_count: int = Field(ge=0)
    freshness_days: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0)
    private_locator: str | None = None
    credential_env_vars: tuple[str, ...] = ()
    last_error: str | None = None


class SourceValueRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_name: str
    source_type: str
    evidence_count: int
    cited_count: int
    decision_influence_count: int
    quarantine_rate: float
    failure_count: int
    freshness_days: int | None
    estimated_cost_usd: float
    recommendation: str
    recommendation_reasons: tuple[str, ...]


class SourceValueReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    rows: tuple[SourceValueRow, ...]


def build_source_value_report(
    sources: tuple[SourceValueInput, ...],
    *,
    max_freshness_days: int = 30,
    max_quarantine_rate: float = 0.35,
    max_failure_count: int = 2,
    max_cost_without_influence_usd: float = 5.0,
) -> SourceValueReport:
    rows = tuple(
        _row_for_source(
            source,
            max_freshness_days=max_freshness_days,
            max_quarantine_rate=max_quarantine_rate,
            max_failure_count=max_failure_count,
            max_cost_without_influence_usd=max_cost_without_influence_usd,
        )
        for source in sources
    )
    return SourceValueReport(rows=rows)


def render_source_value_markdown(report: SourceValueReport) -> str:
    lines = [
        "# Source Value Report",
        "",
        "| Source | Type | Evidence | Cited | Influence | Quarantine | Freshness | Cost | Recommendation |",
        "|--------|------|----------|-------|-----------|------------|-----------|------|----------------|",
    ]
    for row in report.rows:
        freshness = "n/a" if row.freshness_days is None else f"{row.freshness_days}d"
        reasons = ", ".join(row.recommendation_reasons) or "none"
        lines.append(
            "| "
            f"{row.source_name} | "
            f"{row.source_type} | "
            f"{row.evidence_count} | "
            f"{row.cited_count} | "
            f"{row.decision_influence_count} | "
            f"{row.quarantine_rate:.2f} | "
            f"{freshness} | "
            f"${row.estimated_cost_usd:.2f} | "
            f"{row.recommendation}: {reasons} |"
        )
    return "\n".join(lines) + "\n"


def _row_for_source(
    source: SourceValueInput,
    *,
    max_freshness_days: int,
    max_quarantine_rate: float,
    max_failure_count: int,
    max_cost_without_influence_usd: float,
) -> SourceValueRow:
    total_seen = source.evidence_count + source.quarantined_count
    quarantine_rate = round(source.quarantined_count / total_seen, 2) if total_seen else 0.0
    reasons = _recommendation_reasons(
        source,
        quarantine_rate=quarantine_rate,
        max_freshness_days=max_freshness_days,
        max_quarantine_rate=max_quarantine_rate,
        max_failure_count=max_failure_count,
        max_cost_without_influence_usd=max_cost_without_influence_usd,
    )
    return SourceValueRow(
        source_name=source.source_name,
        source_type=source.source_type,
        evidence_count=source.evidence_count,
        cited_count=source.cited_count,
        decision_influence_count=source.decision_influence_count,
        quarantine_rate=quarantine_rate,
        failure_count=source.failure_count,
        freshness_days=source.freshness_days,
        estimated_cost_usd=round(source.estimated_cost_usd, 2),
        recommendation=_recommendation_from_reasons(reasons),
        recommendation_reasons=reasons,
    )


def _recommendation_reasons(
    source: SourceValueInput,
    *,
    quarantine_rate: float,
    max_freshness_days: int,
    max_quarantine_rate: float,
    max_failure_count: int,
    max_cost_without_influence_usd: float,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if source.evidence_count == 0:
        reasons.append("no evidence collected")
    if source.cited_count == 0:
        reasons.append("no cited evidence")
    if source.decision_influence_count == 0:
        reasons.append("no decision influence")
    if quarantine_rate > max_quarantine_rate:
        reasons.append("high quarantine rate")
    if source.failure_count > max_failure_count:
        reasons.append("high failure count")
    if source.freshness_days is not None and source.freshness_days > max_freshness_days:
        reasons.append("stale evidence")
    if (
        source.estimated_cost_usd > max_cost_without_influence_usd
        and source.decision_influence_count == 0
    ):
        reasons.append("excessive cost without influence")
    return tuple(reasons)


def _recommendation_from_reasons(reasons: tuple[str, ...]) -> str:
    disable_reasons = {
        "no evidence collected",
        "high quarantine rate",
        "high failure count",
        "excessive cost without influence",
    }
    if any(reason in disable_reasons for reason in reasons):
        return "disable"
    if reasons:
        return "demote"
    return "keep"
