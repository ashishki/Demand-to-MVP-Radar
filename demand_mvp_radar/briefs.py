"""Source-grounded opportunity brief assembly."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from demand_mvp_radar.models import OpportunityCandidate, OpportunityExtraction, OpportunityScore
from demand_mvp_radar.retrieval.query import EvidencePacket


class OpportunityBrief(BaseModel):
    model_config = ConfigDict(frozen=True)

    candidate: OpportunityCandidate
    score: OpportunityScore
    extraction: OpportunityExtraction
    evidence_packets: tuple[EvidencePacket, ...]


def build_opportunity_brief(
    *,
    candidate: OpportunityCandidate,
    score: OpportunityScore,
    extraction: OpportunityExtraction,
    evidence_packets: tuple[EvidencePacket, ...],
) -> OpportunityBrief:
    return OpportunityBrief(
        candidate=candidate,
        score=score,
        extraction=extraction,
        evidence_packets=evidence_packets,
    )
