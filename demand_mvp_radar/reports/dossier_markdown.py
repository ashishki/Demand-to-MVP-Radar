"""Markdown rendering for decision-grade opportunity dossiers."""

from __future__ import annotations

from demand_mvp_radar.models import DossierClaim, OpportunityDossier


def render_dossier_markdown(dossier: OpportunityDossier) -> str:
    lines = [
        f"# {dossier.title}",
        "",
        f"Opportunity ID: `{dossier.opportunity_id}`",
        f"Recommendation: **{dossier.recommendation}**",
        f"Confidence: {dossier.confidence}",
        "",
        "## Decision Summary",
        "",
    ]
    if dossier.recommendation == "insufficient_evidence":
        lines.append(
            "This dossier is marked `insufficient_evidence` and must not be treated "
            "as a build recommendation."
        )
    else:
        lines.append("This dossier is advisory; the operator owns the final decision.")

    lines.extend(
        [
            "",
            "## Pain",
            "",
            _render_claim(dossier.pain),
            "",
            "## Audience",
            "",
            _render_claim(dossier.audience),
            "",
            "## Current Workaround",
            "",
            _render_claim(dossier.workaround),
            "",
            "## Evidence",
            "",
        ]
    )
    lines.extend(_render_evidence_table(dossier))
    lines.extend(
        [
            "",
            "## Competitor Shape",
            "",
            _render_claim(dossier.competitor_shape),
            "",
            "## One-Function MVP",
            "",
            _render_claim(dossier.one_function_mvp),
            "",
            "## Acquisition Angle",
            "",
            _render_claim(dossier.acquisition_angle),
            "",
            "## Risks",
            "",
        ]
    )
    lines.extend(f"- {_render_claim(risk)}" for risk in dossier.risks)
    lines.extend(
        [
            "",
            "## Missing Evidence",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in dossier.missing_evidence)
    lines.extend(
        [
            "",
            "## Score Components",
            "",
            "| Component | Score | Rationale |",
            "|-----------|-------|-----------|",
        ]
    )
    for name, component in dossier.score_components.items():
        lines.append(f"| {name} | {component.value:.2f} | {component.rationale} |")
    lines.extend(
        [
            "",
            "## Prior Decisions",
            "",
        ]
    )
    if dossier.prior_decisions:
        for decision in dossier.prior_decisions:
            decided_at = (
                decision.decided_at.date().isoformat() if decision.decided_at else "unknown date"
            )
            lines.append(f"- {decision.decision} ({decided_at}): {decision.reason}")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Why This May Be Wrong",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in dossier.why_this_may_be_wrong)
    return "\n".join(lines).rstrip() + "\n"


def _render_claim(claim: DossierClaim) -> str:
    if claim.citation_numbers:
        citations = " ".join(f"[{number}]" for number in claim.citation_numbers)
        return f"{claim.text} {citations}"
    return f"{claim.text} _(inference)_"


def _render_evidence_table(dossier: OpportunityDossier) -> list[str]:
    lines = [
        "| Citation | Source Type | Source | Captured | Reference | Snippet |",
        "|----------|-------------|--------|----------|-----------|---------|",
    ]
    for evidence in dossier.evidence:
        lines.append(
            "| "
            f"[{evidence.citation_number}] | "
            f"{evidence.source_type} | "
            f"{evidence.source_title_or_id} | "
            f"{evidence.captured_at.date().isoformat()} | "
            f"{evidence.source_ref} | "
            f"{evidence.snippet} |"
        )
    return lines
