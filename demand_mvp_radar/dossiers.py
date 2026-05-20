"""Opportunity dossier construction helpers."""

from __future__ import annotations

from demand_mvp_radar.models import OpportunityDossier


def build_opportunity_dossier(payload: dict[str, object]) -> OpportunityDossier:
    """Validate and return a decision-grade opportunity dossier."""

    return OpportunityDossier.model_validate(payload)
