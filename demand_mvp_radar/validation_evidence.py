"""Candidate-level matching for external Radar validation evidence."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import datetime

from demand_mvp_radar.models import EvidenceRecord

SCHEMA_VERSION = "radar_validation_evidence.v1"

EVIDENCE_KINDS = {
    "repeated_complaint",
    "manual_workaround",
    "search_demand",
    "competitor_traction",
    "wtp_signal",
    "developer_issue",
    "negative_signal",
}

DEFAULT_EXTERNAL_SOURCE_TYPES = {
    "serp",
    "github_public",
    "stack_exchange",
    "reddit",
    "product_hunt",
    "youtube",
    "rss",
    "hacker_news",
    "store",
    "reviews",
    "forum",
    "news",
}


def match_external_evidence(
    *,
    candidate_title: str,
    records: Iterable[EvidenceRecord],
    external_source_types: Iterable[str] = DEFAULT_EXTERNAL_SOURCE_TYPES,
) -> list[dict[str, object]]:
    """Return external records explicitly matched to one candidate.

    Matching is conservative by design. Search results or public records do not
    become gate-supporting evidence merely because they were collected during
    the same run.
    """

    source_types = {str(source_type) for source_type in external_source_types}
    matches: list[dict[str, object]] = []
    for record in records:
        if record.source_type not in source_types:
            continue
        match_basis = _match_basis(candidate_title, record)
        if match_basis is None:
            continue
        evidence_kind = _evidence_kind(record)
        negative_signal = evidence_kind == "negative_signal"
        decision_grade = bool(record.source_url) and not negative_signal
        supports_gate = decision_grade
        matches.append(
            {
                "schema_version": SCHEMA_VERSION,
                "evidence_kind": evidence_kind,
                "source_type": record.source_type,
                "source_name": record.source_name,
                "source_id": record.source_id,
                "source_url": record.source_url,
                "source_title": record.title,
                "source_snippet": record.snippet,
                "captured_at": _iso(record.captured_at),
                "source_created_at": _iso(record.created_at) if record.created_at else None,
                "query": record.search_query,
                "subreddit": record.subreddit,
                "comment_id": record.comment_id,
                "author_hash": record.author_hash,
                "matched_candidate_title": candidate_title,
                "match_basis": match_basis,
                "decision_grade": decision_grade,
                "supports_gate": supports_gate,
                "negative_signal": negative_signal,
                "source_fingerprint": record.source_fingerprint,
            }
        )
    return matches


def matched_external_fingerprints(matches: Iterable[dict[str, object]]) -> set[str]:
    return {
        str(match.get("source_fingerprint"))
        for match in matches
        if str(match.get("source_fingerprint") or "").strip()
    }


def matched_external_source_types(matches: Iterable[dict[str, object]]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                str(match.get("source_type"))
                for match in matches
                if bool(match.get("supports_gate")) and str(match.get("source_type") or "")
            }
        )
    )


def decision_grade_match_count(matches: Iterable[dict[str, object]]) -> int:
    return sum(1 for match in matches if bool(match.get("supports_gate")))


def external_research_context(
    *,
    candidate_title: str | None,
    records: Iterable[EvidenceRecord],
    matched_fingerprints: set[str],
    external_source_types: Iterable[str] = DEFAULT_EXTERNAL_SOURCE_TYPES,
    limit: int = 5,
) -> dict[str, object]:
    """Return context-only unmatched external research for JSON decision context."""

    source_types = {str(source_type) for source_type in external_source_types}
    context_records = []
    for record in records:
        if record.source_type not in source_types:
            continue
        if record.source_fingerprint in matched_fingerprints:
            continue
        context_records.append(
            {
                "source_type": record.source_type,
                "source_name": record.source_name,
                "source_id": record.source_id,
                "source_url": record.source_url,
                "source_title": record.title,
                "captured_at": _iso(record.captured_at),
                "query": record.search_query,
                "context_only": True,
                "source_gate_satisfied": False,
                "reason": "external result was not matched to the selected candidate",
            }
        )
    return {
        "status": "context_only",
        "candidate_title": candidate_title,
        "context_only": True,
        "source_gate_satisfied": False,
        "record_count": len(context_records),
        "records": context_records[: max(0, limit)],
        "summary": (
            "Unmatched external research is decision context only and cannot satisfy source gates."
        ),
    }


def missing_evidence_by_kind(
    *,
    matched_evidence: Iterable[dict[str, object]],
    validation_queries: dict[str, object] | None,
    current_missing: Iterable[str],
) -> dict[str, dict[str, object]]:
    """Explain missing validation categories in terms of evidence kinds."""

    existing = {
        str(item.get("evidence_kind"))
        for item in matched_evidence
        if bool(item.get("supports_gate"))
    }
    categories: dict[str, dict[str, object]] = {}
    for gap in current_missing:
        category = _category_from_gap(str(gap))
        _add_missing_category(
            categories,
            category=category,
            evidence_kind=_evidence_kind_for_category(category),
            reason=str(gap),
            validation_queries=validation_queries,
        )
    for category, evidence_kind in (
        ("search_demand", "search_demand"),
        ("manual_workarounds", "manual_workaround"),
        ("wtp_signals", "wtp_signal"),
    ):
        if evidence_kind not in existing:
            _add_missing_category(
                categories,
                category=category,
                evidence_kind=evidence_kind,
                reason=f"missing matched {evidence_kind} evidence",
                validation_queries=validation_queries,
            )
    source_types = matched_external_source_types(matched_evidence)
    if decision_grade_match_count(matched_evidence) < 2 or len(source_types) < 2:
        _add_missing_category(
            categories,
            category="independent_external_sources",
            evidence_kind="search_demand",
            reason="missing two independent matched external source types",
            validation_queries=validation_queries,
        )
    return categories


def _add_missing_category(
    categories: dict[str, dict[str, object]],
    *,
    category: str,
    evidence_kind: str,
    reason: str,
    validation_queries: dict[str, object] | None,
) -> None:
    entry = categories.setdefault(
        category,
        {
            "evidence_kind": evidence_kind,
            "missing_evidence": [],
            "next_intent": _intent_for_category(category),
            "next_query": None,
        },
    )
    missing = entry["missing_evidence"]
    if isinstance(missing, list) and reason not in missing:
        missing.append(reason)
    if entry.get("next_query") is None:
        entry["next_query"] = _next_query_for_category(
            validation_queries,
            category=category,
        )


def _next_query_for_category(
    validation_queries: dict[str, object] | None,
    *,
    category: str,
) -> str | None:
    if not validation_queries:
        return None
    intent = _intent_for_category(category)
    queries_by_intent = validation_queries.get("queries_by_intent")
    if not isinstance(queries_by_intent, dict):
        return None
    records = queries_by_intent.get(intent)
    if not isinstance(records, list) or not records:
        return None
    first = records[0]
    if not isinstance(first, dict):
        return None
    query = first.get("query")
    return str(query) if query else None


def _match_basis(candidate_title: str, record: EvidenceRecord) -> str | None:
    metadata = record.provider_metadata
    candidate_key = _normalize(candidate_title)
    for field_name in ("matched_candidate_title", "target_candidate", "mvp_shape"):
        value = _metadata_text(metadata, field_name)
        if value and _normalize(value) == candidate_key:
            return f"provider_metadata.{field_name}"
    if _normalize(record.title) == candidate_key:
        return "title_exact"
    candidate_phrase = _core_phrase(candidate_title)
    if not candidate_phrase:
        return None
    query = record.search_query or _metadata_text(metadata, "query")
    if query and candidate_phrase in _normalize(query):
        return "search_query_candidate_phrase"
    text = _normalize(f"{record.title} {record.snippet} {record.normalized_text}")
    if candidate_phrase in text:
        return "text_candidate_phrase"
    return None


def _evidence_kind(record: EvidenceRecord) -> str:
    explicit = _metadata_text(record.provider_metadata, "evidence_kind")
    if explicit in EVIDENCE_KINDS:
        return explicit
    text = _normalize(
        " ".join(
            value
            for value in (
                record.search_query or "",
                record.title,
                record.snippet,
                record.normalized_text,
            )
            if value
        )
    )
    if any(token in text for token in ("no demand", "not a problem", "irrelevant")):
        return "negative_signal"
    if any(token in text for token in ("pricing", "price", "paid", "pay for", "budget")):
        return "wtp_signal"
    if any(token in text for token in ("workaround", "manual", "spreadsheet")):
        return "manual_workaround"
    if any(token in text for token in ("alternative", "competitor", "vs ", "compare")):
        return "competitor_traction"
    if record.source_type == "github_public":
        return "developer_issue"
    if record.source_type in {"reddit", "forum", "stack_exchange"}:
        return "repeated_complaint"
    if record.source_type in {"product_hunt", "store", "reviews"}:
        return "competitor_traction"
    return "search_demand"


def _category_from_gap(gap: str) -> str:
    normalized = gap.lower()
    if any(token in normalized for token in ("pricing", "pay", "willingness", "wtp")):
        return "wtp_signals"
    if "workaround" in normalized or "manual" in normalized:
        return "manual_workarounds"
    if "competitor" in normalized or "alternative" in normalized:
        return "competitors"
    if "github" in normalized or "developer" in normalized or "issue" in normalized:
        return "developer_issues"
    if "reddit" in normalized or "forum" in normalized or "complaint" in normalized:
        return "reddit_forum_complaints"
    return "external_corroboration"


def _intent_for_category(category: str) -> str:
    return {
        "competitors": "competitors",
        "developer_issues": "github_discussions",
        "external_corroboration": "search_demand",
        "independent_external_sources": "search_demand",
        "manual_workarounds": "manual_workarounds",
        "reddit_forum_complaints": "reddit_forum_complaints",
        "search_demand": "search_demand",
        "wtp_signals": "wtp_signals",
    }.get(category, "search_demand")


def _evidence_kind_for_category(category: str) -> str:
    return {
        "competitors": "competitor_traction",
        "developer_issues": "developer_issue",
        "external_corroboration": "search_demand",
        "independent_external_sources": "search_demand",
        "manual_workarounds": "manual_workaround",
        "reddit_forum_complaints": "repeated_complaint",
        "search_demand": "search_demand",
        "wtp_signals": "wtp_signal",
    }.get(category, "search_demand")


def _metadata_text(metadata: dict[str, str], field_name: str) -> str | None:
    value = metadata.get(field_name)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _core_phrase(value: str) -> str:
    tokens = re.findall(r"[a-z0-9а-яё]+", _normalize(value))
    return " ".join(tokens[:6])


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9а-яё]+", " ", value.lower()).strip()


def _iso(value: datetime) -> str:
    return value.isoformat()
