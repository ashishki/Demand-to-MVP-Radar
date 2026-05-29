"""Source trust records for repeated-signal and evidence-density review."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from demand_mvp_radar.models import EvidenceRecord

DEFAULT_LOW_TRUST_SOURCE_TYPES = {
    "operator_note",
    "manual_note",
    "news",
    "rss",
    "reddit",
    "product_hunt",
    "telegram_research_agent",
}


@dataclass(frozen=True)
class SourceTrustRecord:
    source_type: str
    source_name: str
    evidence_count: int
    unique_signal_count: int
    repeated_signal_count: int
    evidence_density: float
    rejection_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "source_type": self.source_type,
            "source_name": self.source_name,
            "evidence_count": self.evidence_count,
            "unique_signal_count": self.unique_signal_count,
            "repeated_signal_count": self.repeated_signal_count,
            "evidence_density": self.evidence_density,
            "rejection_reasons": self.rejection_reasons,
        }


def build_source_trust_records(
    records: Iterable[EvidenceRecord],
    *,
    low_trust_source_types: Iterable[str] = DEFAULT_LOW_TRUST_SOURCE_TYPES,
    minimum_evidence_count: int = 2,
) -> tuple[SourceTrustRecord, ...]:
    low_trust = set(low_trust_source_types)
    grouped: dict[tuple[str, str], list[EvidenceRecord]] = defaultdict(list)
    for record in records:
        grouped[(record.source_type, record.source_name or record.source_type)].append(record)

    trust_records: list[SourceTrustRecord] = []
    for (source_type, source_name), source_records in sorted(grouped.items()):
        signal_counts = Counter(_signal_key(record) for record in source_records)
        evidence_count = len(source_records)
        unique_signal_count = len(signal_counts)
        repeated_signal_count = sum(count - 1 for count in signal_counts.values() if count > 1)
        evidence_density = round(evidence_count / max(unique_signal_count, 1), 2)
        reasons = _rejection_reasons(
            source_type=source_type,
            evidence_count=evidence_count,
            repeated_signal_count=repeated_signal_count,
            evidence_density=evidence_density,
            low_trust_source_types=low_trust,
            minimum_evidence_count=minimum_evidence_count,
            records=source_records,
        )
        trust_records.append(
            SourceTrustRecord(
                source_type=source_type,
                source_name=source_name,
                evidence_count=evidence_count,
                unique_signal_count=unique_signal_count,
                repeated_signal_count=repeated_signal_count,
                evidence_density=evidence_density,
                rejection_reasons=reasons,
            )
        )
    return tuple(trust_records)


def _signal_key(record: EvidenceRecord) -> str:
    metadata = record.provider_metadata
    value = (
        metadata.get("mvp_shape")
        or metadata.get("demand_signal_type")
        or metadata.get("demand_surfaces")
        or record.title
        or record.normalized_text[:80]
    )
    return " ".join(value.lower().split())


def _rejection_reasons(
    *,
    source_type: str,
    evidence_count: int,
    repeated_signal_count: int,
    evidence_density: float,
    low_trust_source_types: set[str],
    minimum_evidence_count: int,
    records: list[EvidenceRecord],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if evidence_count < minimum_evidence_count:
        reasons.append("low evidence count")
    if source_type in low_trust_source_types:
        reasons.append("low-trust source requires corroboration")
    if source_type == "telegram_research_agent":
        reasons.append("telegram seed requires external corroboration")
    if repeated_signal_count:
        reasons.append("repeated signal variants need source diversity")
    if evidence_density >= 2:
        reasons.append("high evidence density from few unique signals")
    if any(not record.source_url for record in records):
        reasons.append("missing source URL")
    return tuple(reasons)
