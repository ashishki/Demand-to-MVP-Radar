"""Convert Telegram weekly digest artifacts into Radar seed exports."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DigestSeedExportResult:
    output_path: Path
    seed_count: int
    skipped_count: int
    skipped_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "output_path": str(self.output_path),
            "seed_count": self.seed_count,
            "skipped_count": self.skipped_count,
            "skipped_reasons": self.skipped_reasons,
        }


def convert_digest_to_seed_export(digest_path: Path, output_path: Path) -> DigestSeedExportResult:
    payload = json.loads(digest_path.read_text(encoding="utf-8"))
    seeds, skipped_reasons = digest_to_seed_rows(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(seeds, ensure_ascii=False, indent=2), encoding="utf-8")
    return DigestSeedExportResult(
        output_path=output_path,
        seed_count=len(seeds),
        skipped_count=len(skipped_reasons),
        skipped_reasons=tuple(skipped_reasons),
    )


def digest_to_seed_rows(payload: dict[str, Any]) -> tuple[list[dict[str, object]], list[str]]:
    if not isinstance(payload, dict):
        raise ValueError("digest payload must be an object")
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    evidence_rows = payload.get("evidence")
    if not isinstance(evidence_rows, list):
        raise ValueError("digest payload must contain an evidence list")

    generated_at = _captured_at_from_meta(meta)
    week_label = _text(meta.get("week_label")) or "unknown-week"
    seeds: list[dict[str, object]] = []
    skipped: list[str] = []
    for index, row in enumerate(evidence_rows):
        if not isinstance(row, dict):
            skipped.append(f"row-{index}: row is not an object")
            continue
        row_id = _text(row.get("id")) or f"row-{index}"
        excerpt = _text(row.get("excerpt"))
        url = _text(row.get("url"))
        if not excerpt:
            skipped.append(f"{row_id}: missing excerpt")
            continue
        if not _safe_source_url(url):
            skipped.append(f"{row_id}: missing safe public/source URL")
            continue
        captured_at = _row_captured_at(row, fallback=generated_at)
        channel = _text(row.get("channel"))
        normalized_excerpt = _normalize_text(excerpt)
        seeds.append(
            {
                "upstream_id": f"digest:{week_label}:{row_id}",
                "captured_at": captured_at.isoformat(),
                "title": _title_from_text(normalized_excerpt),
                "text": normalized_excerpt,
                "snippet": normalized_excerpt[:160],
                "source_url": url,
                "channel_username": channel,
                "bucket": _bucket_for_text(normalized_excerpt),
                "demand_surfaces": _demand_surfaces(normalized_excerpt),
                "mvp_shape": _mvp_shape(normalized_excerpt),
                "verification_needed": [
                    "non-Telegram public evidence for the same pain",
                    "competitor or workaround corroboration",
                ],
                "anti_complexity_note": (
                    "Use as Telegram seed input only; do not treat as market validation."
                ),
            }
        )
    return seeds, skipped


def _captured_at_from_meta(meta: dict[str, Any]) -> datetime:
    generated_at = _text(meta.get("generated_at"))
    if generated_at:
        return _parse_datetime(generated_at)
    return datetime.now(UTC)


def _row_captured_at(row: dict[str, Any], *, fallback: datetime) -> datetime:
    row_date = _text(row.get("date"))
    if not row_date:
        return fallback
    try:
        return _parse_datetime(row_date)
    except ValueError:
        return fallback


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _safe_source_url(value: str | None) -> bool:
    return bool(value and re.match(r"^https?://", value))


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _title_from_text(value: str) -> str:
    sentence = re.split(r"[.!?]", value, maxsplit=1)[0].strip()
    return sentence[:80] or value[:80]


def _bucket_for_text(value: str) -> str:
    lowered = value.lower()
    if any(term in lowered for term in ("need", "нуж", "ask", "спрос", "pain", "проблем")):
        return "strong"
    return "watch"


def _demand_surfaces(value: str) -> list[str]:
    lowered = value.lower()
    surfaces: list[str] = []
    if any(term in lowered for term in ("ask", "question", "вопрос", "спраш")):
        surfaces.append("repeated_questions")
    if any(term in lowered for term in ("manual", "copy", "вручн", "workaround")):
        surfaces.append("manual_workaround")
    if any(term in lowered for term in ("search", "seo", "channel", "creator", "контент")):
        surfaces.append("creator_content_gap")
    if any(term in lowered for term in ("competitor", "alternative", "pricing", "marketplace")):
        surfaces.append("competitor_traction")
    if not surfaces:
        surfaces.append("telegram_intelligence_seed")
    return surfaces


def _mvp_shape(value: str) -> str:
    lowered = value.lower()
    if "инструкц" in lowered or "instruction" in lowered or "prompt" in lowered:
        return "Agent Instruction Conflict Review"
    if "skills" in lowered or "скилл" in lowered:
        return "Agent Skills Marketplace Radar"
    if "telegram" in lowered and ("seo" in lowered or "search" in lowered):
        return "Telegram Channel SEO Site Generator"
    if "production" in lowered or "продакш" in lowered or "fallback" in lowered:
        return "Agent Production Readiness Checklist"
    return f"{_title_from_text(value)} Signal"
