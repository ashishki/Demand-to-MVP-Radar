"""Deterministic query planning for Radar validation evidence."""

from __future__ import annotations

import re
from collections.abc import Iterable

SCHEMA_VERSION = "radar_validation_evidence.v1"

INTENT_SOURCE_TYPES: dict[str, tuple[str, ...]] = {
    "search_demand": ("serp", "yandex_search", "yandex_wordstat"),
    "manual_workarounds": ("serp", "crawl4ai", "reddit", "forum"),
    "competitors": ("serp", "crawl4ai", "product_hunt"),
    "wtp_signals": ("serp", "crawl4ai", "product_hunt"),
    "reddit_forum_complaints": ("reddit", "forum", "serp"),
    "github_discussions": ("github_public", "serp"),
    "x_discussions": ("x", "serp"),
}

INTENT_EVIDENCE_KIND: dict[str, str] = {
    "search_demand": "search_demand",
    "manual_workarounds": "manual_workaround",
    "competitors": "competitor_traction",
    "wtp_signals": "wtp_signal",
    "reddit_forum_complaints": "repeated_complaint",
    "github_discussions": "developer_issue",
    "x_discussions": "repeated_complaint",
}

ADAPTER_STATUS_TEMPLATE: dict[str, dict[str, str]] = {
    "search_demand": {
        "status": "adapter_disabled",
        "reason": "RVE-3 search/SERP demand adapter is not implemented yet.",
    },
    "reddit_forum_complaints": {
        "status": "adapter_disabled",
        "reason": "RVE-4 Reddit/forum complaint adapter is not implemented yet.",
    },
    "competitor_workaround_crawler": {
        "status": "adapter_disabled",
        "reason": "RVE-5 competitor/workaround crawler is not implemented yet.",
    },
    "x_discussions": {
        "status": "adapter_disabled",
        "reason": "RVE-6 X/Twitter corroboration adapter is not implemented yet.",
    },
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def build_validation_query_pack(
    *,
    candidate_title: str,
    surfaces: Iterable[str] = (),
    missing_evidence: Iterable[str] = (),
) -> dict[str, object]:
    """Return a repeatable candidate-specific external validation query pack.

    This function is intentionally pure: no network, credentials, cache, or
    adapter state is touched here. Later RVE adapter tasks consume this shape.
    """

    title = " ".join(candidate_title.split()).strip() or "Untitled Candidate"
    core_phrase = _core_phrase(title)
    surface_set = {str(surface).strip().lower() for surface in surfaces if str(surface).strip()}
    missing = tuple(str(item).strip() for item in missing_evidence if str(item).strip())
    queries_by_intent = _queries_by_intent(
        title=title,
        core_phrase=core_phrase,
        surfaces=surface_set,
    )
    missing_by_category = _missing_evidence_by_category(
        missing_evidence=missing,
        queries_by_intent=queries_by_intent,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_title": title,
        "generated_by": "deterministic_rve_query_planner",
        "contract": {
            "context_only_records_satisfy_gates": False,
            "unmatched_external_results_satisfy_gates": False,
            "live_api_calls": False,
        },
        "queries_by_intent": queries_by_intent,
        "missing_evidence_by_category": missing_by_category,
        "next_query": _next_query(queries_by_intent, missing_by_category),
    }


def validation_adapter_status() -> dict[str, dict[str, str]]:
    """Return current validation adapter status without probing external APIs."""

    return {key: dict(value) for key, value in ADAPTER_STATUS_TEMPLATE.items()}


def _queries_by_intent(
    *,
    title: str,
    core_phrase: str,
    surfaces: set[str],
) -> dict[str, list[dict[str, object]]]:
    phrase = core_phrase or title
    quoted_title = _quote(title)
    quoted_phrase = _quote(phrase)
    query_templates: dict[str, tuple[str, ...]] = {
        "search_demand": (
            quoted_title,
            f"{quoted_phrase} problem",
            f"{quoted_phrase} demand",
        ),
        "manual_workarounds": (
            f"{quoted_phrase} workaround",
            f"{quoted_phrase} manual process",
        ),
        "competitors": (
            f"{quoted_phrase} alternative",
            f"{quoted_phrase} competitor pricing",
        ),
        "wtp_signals": (
            f"{quoted_phrase} pricing",
            f"{quoted_phrase} pay for",
        ),
        "reddit_forum_complaints": (
            f"site:reddit.com {quoted_phrase}",
            f"{quoted_phrase} forum complaint",
        ),
        "github_discussions": (
            f"site:github.com {quoted_phrase} issue",
            f"{quoted_phrase} github discussion",
        ),
        "x_discussions": (
            f"{quoted_phrase} workflow",
            f"{quoted_phrase} tool problem",
        ),
    }
    priorities = _intent_priorities(surfaces)
    result: dict[str, list[dict[str, object]]] = {}
    for intent, templates in query_templates.items():
        records = []
        for index, query in enumerate(_dedupe(templates), start=1):
            records.append(
                {
                    "query": query,
                    "intent": intent,
                    "expected_evidence_kind": INTENT_EVIDENCE_KIND[intent],
                    "target_candidate": title,
                    "source_types": list(INTENT_SOURCE_TYPES[intent]),
                    "priority": priorities.get(intent, 3) + index - 1,
                    "rationale": _rationale(intent),
                    "lower_confidence": intent == "x_discussions",
                }
            )
        result[intent] = records
    return result


def _intent_priorities(surfaces: set[str]) -> dict[str, int]:
    priorities = {intent: 3 for intent in INTENT_SOURCE_TYPES}
    if "search_intent" in surfaces or "creator_content_gap" in surfaces:
        priorities["search_demand"] = 1
    if "manual_workaround" in surfaces or "workflow_automation" in surfaces:
        priorities["manual_workarounds"] = 1
        priorities["reddit_forum_complaints"] = 2
    if "competitor_traction" in surfaces:
        priorities["competitors"] = 1
    if "repeated_questions" in surfaces:
        priorities["reddit_forum_complaints"] = 1
    priorities["x_discussions"] = 5
    return priorities


def _missing_evidence_by_category(
    *,
    missing_evidence: tuple[str, ...],
    queries_by_intent: dict[str, list[dict[str, object]]],
) -> dict[str, dict[str, object]]:
    if not missing_evidence:
        return {}
    categories: dict[str, dict[str, object]] = {}
    for gap in missing_evidence:
        category, intent = _category_for_gap(gap)
        category_entry = categories.setdefault(
            category,
            {
                "missing_evidence": [],
                "next_intent": intent,
                "next_query": None,
            },
        )
        category_entry["missing_evidence"].append(gap)
        if category_entry["next_query"] is None:
            first_query = (queries_by_intent.get(intent) or [{}])[0]
            category_entry["next_query"] = first_query.get("query")
    return categories


def _category_for_gap(gap: str) -> tuple[str, str]:
    normalized = gap.lower()
    if any(token in normalized for token in ("pricing", "pay", "willingness", "wtp")):
        return "wtp_signals", "wtp_signals"
    if "workaround" in normalized or "manual" in normalized:
        return "manual_workarounds", "manual_workarounds"
    if "competitor" in normalized or "alternative" in normalized:
        return "competitors", "competitors"
    if "github" in normalized or "developer" in normalized or "issue" in normalized:
        return "developer_issues", "github_discussions"
    if "reddit" in normalized or "forum" in normalized or "complaint" in normalized:
        return "reddit_forum_complaints", "reddit_forum_complaints"
    if "kir" in normalized or "knowledge thread" in normalized or "source atom" in normalized:
        return "fresh_knowledge_thread", "search_demand"
    return "external_corroboration", "search_demand"


def _next_query(
    queries_by_intent: dict[str, list[dict[str, object]]],
    missing_by_category: dict[str, dict[str, object]],
) -> dict[str, object] | None:
    for category in (
        "external_corroboration",
        "wtp_signals",
        "manual_workarounds",
        "reddit_forum_complaints",
        "competitors",
        "developer_issues",
    ):
        entry = missing_by_category.get(category)
        if not entry:
            continue
        intent = str(entry.get("next_intent") or "")
        records = queries_by_intent.get(intent) or []
        if records:
            return records[0]
    for intent in ("search_demand", "manual_workarounds", "reddit_forum_complaints"):
        records = queries_by_intent.get(intent) or []
        if records:
            return records[0]
    return None


def _core_phrase(title: str) -> str:
    tokens = [
        token
        for token in re.findall(r"[A-Za-z0-9]+", title.lower())
        if len(token) > 1 and token not in STOPWORDS
    ]
    if not tokens:
        return title
    return " ".join(tokens[:6])


def _quote(value: str) -> str:
    cleaned = value.replace('"', "").strip()
    return f'"{cleaned}"' if cleaned else '""'


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = " ".join(value.split()).strip()
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return tuple(result)


def _rationale(intent: str) -> str:
    rationales = {
        "search_demand": (
            "Check whether the exact candidate pain appears in repeatable search demand."
        ),
        "manual_workarounds": "Find concrete manual processes people use before a tool exists.",
        "competitors": "Find alternatives or vendors solving the same pain for the same audience.",
        "wtp_signals": "Look for pricing, buying intent, budget, or paid alternatives.",
        "reddit_forum_complaints": "Find independent user complaints outside Telegram.",
        "github_discussions": (
            "Check developer issue trackers and discussions for the same workflow pain."
        ),
        "x_discussions": (
            "Use social discussion only as low-confidence corroboration after lower-noise sources."
        ),
    }
    return rationales[intent]
