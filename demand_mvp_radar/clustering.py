"""Deterministic opportunity clustering for normalized evidence."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence

from demand_mvp_radar.models import EvidenceRecord, OpportunityCandidate
from demand_mvp_radar.observability import span

TOKEN_RE = re.compile(r"[a-z0-9]+")


def cluster_evidence(
    evidence_records: Sequence[EvidenceRecord],
) -> tuple[OpportunityCandidate, ...]:
    clusters: dict[tuple[str, str, str, str], list[EvidenceRecord]] = {}
    with span("clustering.cluster_evidence"):
        for evidence in evidence_records:
            normalized_pain = normalize_pain(evidence)
            target_audience = normalize_target_audience(evidence)
            workflow = normalize_workflow(evidence)
            acquisition_channel = normalize_acquisition_channel(evidence)
            key = (normalized_pain, target_audience, workflow, acquisition_channel)
            clusters.setdefault(key, []).append(evidence)

    candidates = [
        _build_candidate(
            normalized_pain=key[0],
            target_audience=key[1],
            workflow=key[2],
            acquisition_channel=key[3],
            records=tuple(records),
        )
        for key, records in clusters.items()
    ]
    return tuple(sorted(candidates, key=lambda candidate: candidate.opportunity_id))


def normalize_pain(evidence: EvidenceRecord) -> str:
    text = _combined_text(evidence)
    tokens = _tokenize(text)
    if {"spreadsheet", "spreadsheets", "excel"} & tokens and {"formula", "formulas"} & tokens:
        return "spreadsheet formula troubleshooting"
    if {"prerender", "rendering"} & tokens and {"seo", "index", "indexing"} & tokens:
        return "javascript seo prerendering"
    if {"review", "reviews"} & tokens and {"gap", "gaps", "missing"} & tokens:
        return "review gap mining"
    return " ".join(sorted(tokens)[:5]) or "unknown pain"


def normalize_target_audience(evidence: EvidenceRecord) -> str:
    text = _combined_text(evidence)
    tokens = _tokenize(text)
    if "operators" in tokens:
        return "operators"
    if "students" in tokens:
        return "students"
    if "indie" in tokens and "teams" in tokens:
        return "indie teams"
    if {"founder", "founders"} & tokens:
        return "founders"
    if {"seller", "sellers", "store"} & tokens:
        return "store sellers"
    return "general users"


def normalize_workflow(evidence: EvidenceRecord) -> str:
    text = _combined_text(evidence)
    tokens = _tokenize(text)
    if {"fix", "repair", "broken", "explain", "explained"} & tokens:
        return "troubleshooting"
    if {"search", "index", "indexing"} & tokens:
        return "discovery"
    if {"cluster", "clustering", "summaries", "summary"} & tokens:
        return "analysis"
    return "workflow"


def normalize_acquisition_channel(evidence: EvidenceRecord) -> str:
    text = _combined_text(evidence)
    tokens = _tokenize(text)
    if {"search", "seo", "serp"} & tokens or evidence.source_type == "serp":
        return "search"
    if evidence.source_type in {"telegram", "reddit", "x"}:
        return "community"
    if evidence.source_type == "store":
        return "marketplace"
    return evidence.source_type


def _build_candidate(
    *,
    normalized_pain: str,
    target_audience: str,
    workflow: str,
    acquisition_channel: str,
    records: tuple[EvidenceRecord, ...],
) -> OpportunityCandidate:
    source_evidence_ids = tuple(sorted(record.source_id for record in records))
    opportunity_id = _opportunity_id(
        normalized_pain=normalized_pain,
        target_audience=target_audience,
        workflow=workflow,
        acquisition_channel=acquisition_channel,
    )
    return OpportunityCandidate(
        opportunity_id=opportunity_id,
        normalized_pain=normalized_pain,
        target_audience=target_audience,
        workflow=workflow,
        acquisition_channel=acquisition_channel,
        source_evidence_ids=source_evidence_ids,
        candidate_title=_candidate_title(normalized_pain, target_audience),
    )


def _opportunity_id(
    *,
    normalized_pain: str,
    target_audience: str,
    workflow: str,
    acquisition_channel: str,
) -> str:
    raw = "|".join((normalized_pain, target_audience, workflow, acquisition_channel))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"opp_{digest}"


def _candidate_title(normalized_pain: str, target_audience: str) -> str:
    return f"{normalized_pain.title()} for {target_audience.title()}"


def _combined_text(evidence: EvidenceRecord) -> str:
    return f"{evidence.title} {evidence.snippet} {evidence.normalized_text}".lower()


def _tokenize(text: str) -> set[str]:
    return {match.group(0) for match in TOKEN_RE.finditer(text)}
