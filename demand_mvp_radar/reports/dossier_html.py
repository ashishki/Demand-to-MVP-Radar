"""Optional HTML rendering for opportunity dossiers."""

from __future__ import annotations

from demand_mvp_radar.models import OpportunityDossier
from demand_mvp_radar.reports.dossier_markdown import render_dossier_markdown
from demand_mvp_radar.reports.html import render_html_from_markdown


def render_dossier_html(dossier: OpportunityDossier) -> str:
    return render_html_from_markdown(render_dossier_markdown(dossier))
