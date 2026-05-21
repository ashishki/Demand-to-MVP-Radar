"""Local-only review cockpit helpers."""

from __future__ import annotations

import html
import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from demand_mvp_radar.decisions import DecisionValue, RecordedDecision, record_operator_decision
from demand_mvp_radar.reports.source_value import SourceValueReport, render_source_value_markdown
from demand_mvp_radar.storage.repositories import DecisionRepository

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
SECRET_PATTERN = re.compile(r"([A-Z][A-Z0-9_]*(?:TOKEN|KEY|SECRET)[A-Z0-9_]*)|([A-Za-z0-9_-]{24,})")


class ReviewCockpitConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    host: str = "127.0.0.1"
    port: int = Field(default=8765, ge=1, le=65535)
    expose_raw_evidence: bool = False

    @field_validator("host")
    @classmethod
    def host_must_be_local(cls, value: str) -> str:
        if value not in LOCAL_HOSTS:
            raise ValueError("review cockpit must bind to localhost by default")
        return value


class ReviewCockpitPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    bind_host: str
    views: tuple[str, ...]
    opportunities: tuple[dict[str, str], ...]
    dossiers: tuple[dict[str, str], ...]
    source_value_markdown: str
    missing_evidence: tuple[str, ...]
    experiment_actions: tuple[str, ...]


def build_review_cockpit_payload(
    *,
    opportunities: tuple[dict[str, object], ...],
    dossiers: tuple[dict[str, object], ...],
    source_value_report: SourceValueReport,
    missing_evidence: tuple[str, ...],
    experiment_actions: tuple[str, ...],
    config: ReviewCockpitConfig | None = None,
) -> ReviewCockpitPayload:
    effective_config = config or ReviewCockpitConfig()
    return ReviewCockpitPayload(
        bind_host=effective_config.host,
        views=("opportunities", "dossiers", "source_value", "missing_evidence", "experiments"),
        opportunities=tuple(_redacted_mapping(item, effective_config) for item in opportunities),
        dossiers=tuple(_redacted_mapping(item, effective_config) for item in dossiers),
        source_value_markdown=_redact(render_source_value_markdown(source_value_report)),
        missing_evidence=tuple(_redact(value) for value in missing_evidence),
        experiment_actions=tuple(_redact(value) for value in experiment_actions),
    )


def render_review_cockpit_html(payload: ReviewCockpitPayload) -> str:
    sections = [
        "<h1>Demand-to-MVP Radar</h1>",
        _section("Opportunities", payload.opportunities),
        _section("Dossiers", payload.dossiers),
        (
            "<section><h2>Source Value</h2><pre>"
            f"{html.escape(payload.source_value_markdown)}</pre></section>"
        ),
        _list_section("Missing Evidence", payload.missing_evidence),
        _list_section("Experiment Actions", payload.experiment_actions),
    ]
    return "<!doctype html><html><body>" + "".join(sections) + "</body></html>"


def record_review_cockpit_decision(
    repository: DecisionRepository,
    *,
    opportunity_id: int,
    decision: DecisionValue,
    reason: str,
    actor: str,
    source_report_path: str | None,
    requested_evidence_gaps: tuple[str, ...],
    created_at: datetime | None = None,
) -> RecordedDecision:
    return record_operator_decision(
        repository,
        opportunity_id=opportunity_id,
        decision=decision,
        reason=reason,
        actor=actor,
        source_report_path=source_report_path,
        requested_evidence_gaps=requested_evidence_gaps,
        created_at=created_at,
    )


def _redacted_mapping(
    item: dict[str, object],
    config: ReviewCockpitConfig,
) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for key, value in item.items():
        if not config.expose_raw_evidence and str(key) in {"raw_evidence", "private_source"}:
            continue
        redacted[str(key)] = _redact(str(value))
    return redacted


def _section(title: str, rows: tuple[dict[str, str], ...]) -> str:
    rendered_rows = "".join(
        "<li>"
        + " | ".join(f"{html.escape(key)}: {html.escape(value)}" for key, value in row.items())
        + "</li>"
        for row in rows
    )
    return f"<section><h2>{html.escape(title)}</h2><ul>{rendered_rows}</ul></section>"


def _list_section(title: str, values: tuple[str, ...]) -> str:
    items = "".join(f"<li>{html.escape(value)}</li>" for value in values)
    return f"<section><h2>{html.escape(title)}</h2><ul>{items}</ul></section>"


def _redact(value: str) -> str:
    return SECRET_PATTERN.sub("[redacted]", value)
