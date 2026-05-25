"""Lead response SLA CSV analysis."""

from __future__ import annotations

import csv
import hashlib
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

PII_FIELD_NAMES = {
    "email",
    "customer email",
    "assignee email",
    "phone",
    "customer phone",
    "full_name",
    "full name",
    "name",
    "customer name",
    "company",
    "company_name",
    "company name",
    "message",
    "message_body",
    "ticket description",
    "description",
    "crm_url",
    "url",
}

FIELD_ALIASES = {
    "lead_id": ("lead_id", "lead id", "ticket id", "case id", "conversation_id"),
    "created_at": (
        "created_at",
        "created at",
        "created",
        "creation date",
        "ticket created at",
        "case created",
        "lead_created_ts",
        "submit time",
    ),
    "first_response_at": (
        "first_response_at",
        "first response at",
        "first response datetime",
        "first reply time",
    ),
    "first_response_duration": (
        "first response time",
        "first response time minutes",
        "first response time (secs)",
        "first_response_minutes",
        "initialresponsemin",
    ),
    "source": ("source", "ticket channel", "channel name", "initial channel", "form_name"),
    "owner": ("owner", "assignee name", "assigned agent name", "agent", "rep"),
    "status": ("status", "ticket status", "case status"),
}


@dataclass(frozen=True)
class LeadSlaIssue:
    row_number: int
    reason: str


@dataclass(frozen=True)
class LeadSlaRecord:
    row_number: int
    lead_id: str
    created_at: datetime
    first_response_at: datetime | None
    source: str
    owner: str
    status: str
    response_minutes: float | None
    breached_sla: bool
    unresponded: bool


@dataclass(frozen=True)
class LeadSlaBreakdown:
    key: str
    total: int
    responded: int
    unresponded: int
    breach_count: int
    median_response_minutes: float | None
    p90_response_minutes: float | None


@dataclass(frozen=True)
class LeadSlaAnalysis:
    source_path: Path
    dataset_label: str
    public_source_url: str | None
    sla_minutes: float
    total_rows: int
    valid_rows: int
    invalid_rows: tuple[LeadSlaIssue, ...]
    warnings: tuple[str, ...]
    records: tuple[LeadSlaRecord, ...]
    total_leads: int
    responded_leads: int
    unresponded_leads: int
    response_breach_count: int
    total_sla_miss_count: int
    median_response_minutes: float | None
    p90_response_minutes: float | None
    max_response_minutes: float | None
    by_source: tuple[LeadSlaBreakdown, ...]
    by_owner: tuple[LeadSlaBreakdown, ...]
    by_status: tuple[LeadSlaBreakdown, ...]


def analyze_lead_sla_csv(
    csv_path: Path,
    *,
    sla_minutes: float,
    hash_lead_id: bool = True,
    dataset_label: str = "",
    public_source_url: str | None = None,
) -> LeadSlaAnalysis:
    if sla_minutes <= 0:
        raise ValueError("sla_minutes must be greater than 0")

    with csv_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        field_map = _map_fields(fieldnames)
        rows = list(reader)

    _validate_required_fields(field_map)
    pii_headers = sorted(name for name in fieldnames if _normalize_header(name) in PII_FIELD_NAMES)
    warnings: list[str] = []
    if pii_headers:
        warnings.append(f"Ignored private columns: {', '.join(pii_headers)}")

    records: list[LeadSlaRecord] = []
    invalid_rows: list[LeadSlaIssue] = []
    for index, row in enumerate(rows, start=2):
        try:
            records.append(
                _parse_row(
                    row,
                    row_number=index,
                    field_map=field_map,
                    sla_minutes=sla_minutes,
                    hash_lead_id=hash_lead_id,
                    warnings=warnings,
                )
            )
        except ValueError as exc:
            invalid_rows.append(LeadSlaIssue(row_number=index, reason=str(exc)))

    response_minutes = [
        record.response_minutes for record in records if record.response_minutes is not None
    ]
    response_breaches = sum(
        1 for record in records if record.breached_sla and not record.unresponded
    )
    unresponded = sum(1 for record in records if record.unresponded)
    return LeadSlaAnalysis(
        source_path=csv_path,
        dataset_label=dataset_label or csv_path.name,
        public_source_url=public_source_url,
        sla_minutes=sla_minutes,
        total_rows=len(rows),
        valid_rows=len(records),
        invalid_rows=tuple(invalid_rows),
        warnings=tuple(dict.fromkeys(warnings)),
        records=tuple(records),
        total_leads=len(records),
        responded_leads=len(records) - unresponded,
        unresponded_leads=unresponded,
        response_breach_count=response_breaches,
        total_sla_miss_count=response_breaches + unresponded,
        median_response_minutes=_median(response_minutes),
        p90_response_minutes=_percentile(response_minutes, 0.9),
        max_response_minutes=max(response_minutes) if response_minutes else None,
        by_source=_build_breakdown(records, key="source"),
        by_owner=_build_breakdown(records, key="owner"),
        by_status=_build_breakdown(records, key="status"),
    )


def _map_fields(fieldnames: list[str]) -> dict[str, str]:
    normalized_to_original = {_normalize_header(name): name for name in fieldnames}
    mapped: dict[str, str] = {}
    for canonical, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in normalized_to_original:
                mapped[canonical] = normalized_to_original[alias]
                break
    return mapped


def _validate_required_fields(field_map: dict[str, str]) -> None:
    missing = []
    if "created_at" not in field_map:
        missing.append("created_at")
    if "first_response_at" not in field_map and "first_response_duration" not in field_map:
        missing.append("first_response_at or first_response_duration")
    if missing:
        raise ValueError(f"missing required column(s): {', '.join(missing)}")


def _parse_row(
    row: dict[str, str],
    *,
    row_number: int,
    field_map: dict[str, str],
    sla_minutes: float,
    hash_lead_id: bool,
    warnings: list[str],
) -> LeadSlaRecord:
    created_at = _parse_datetime(_row_value(row, field_map, "created_at"), field="created_at")
    first_response_at = _first_response_at(row, field_map, created_at=created_at)
    if created_at.tzinfo is None:
        warnings.append("Naive timestamps treated as local/source time.")
    if first_response_at and first_response_at.tzinfo is None:
        warnings.append("Naive timestamps treated as local/source time.")
    if first_response_at and first_response_at < created_at:
        raise ValueError("first_response_at is earlier than created_at")

    response_minutes = (
        (first_response_at - created_at).total_seconds() / 60 if first_response_at else None
    )
    raw_lead_id = _row_value(row, field_map, "lead_id") or f"row-{row_number}"
    lead_id = _safe_lead_id(raw_lead_id, hash_lead_id=hash_lead_id)
    unresponded = first_response_at is None
    return LeadSlaRecord(
        row_number=row_number,
        lead_id=lead_id,
        created_at=created_at,
        first_response_at=first_response_at,
        source=_row_value(row, field_map, "source") or "unknown",
        owner=_row_value(row, field_map, "owner") or "unknown",
        status=_row_value(row, field_map, "status") or "unknown",
        response_minutes=response_minutes,
        breached_sla=unresponded
        or (response_minutes is not None and response_minutes > sla_minutes),
        unresponded=unresponded,
    )


def _first_response_at(
    row: dict[str, str],
    field_map: dict[str, str],
    *,
    created_at: datetime,
) -> datetime | None:
    if "first_response_at" in field_map:
        raw = _row_value(row, field_map, "first_response_at")
        return _parse_optional_datetime(raw, field="first_response_at")
    raw_duration = _row_value(row, field_map, "first_response_duration")
    if not raw_duration:
        return None
    duration = _parse_duration_minutes(raw_duration)
    return created_at + timedelta(minutes=duration)


def _parse_datetime(value: str, *, field: str) -> datetime:
    parsed = _parse_optional_datetime(value, field=field)
    if parsed is None:
        raise ValueError(f"{field} is required")
    return parsed


def _parse_optional_datetime(value: str, *, field: str) -> datetime | None:
    clean = value.strip()
    if not clean:
        return None
    try:
        return datetime.fromisoformat(clean.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} is not an ISO timestamp") from exc


def _parse_duration_minutes(value: str) -> float:
    clean = value.strip()
    if not clean:
        raise ValueError("first response duration is empty")
    try:
        return float(clean)
    except ValueError as exc:
        raise ValueError("first response duration is not numeric minutes") from exc


def _safe_lead_id(value: str, *, hash_lead_id: bool) -> str:
    if not hash_lead_id:
        return value.strip() or "unknown"
    digest = hashlib.sha256(value.strip().encode("utf-8")).hexdigest()[:12]
    return f"lead_{digest}"


def _build_breakdown(records: list[LeadSlaRecord], *, key: str) -> tuple[LeadSlaBreakdown, ...]:
    groups: dict[str, list[LeadSlaRecord]] = {}
    for record in records:
        groups.setdefault(getattr(record, key), []).append(record)
    breakdowns = []
    for value, items in groups.items():
        response_minutes = [
            record.response_minutes for record in items if record.response_minutes is not None
        ]
        breakdowns.append(
            LeadSlaBreakdown(
                key=value,
                total=len(items),
                responded=sum(1 for record in items if not record.unresponded),
                unresponded=sum(1 for record in items if record.unresponded),
                breach_count=sum(1 for record in items if record.breached_sla),
                median_response_minutes=_median(response_minutes),
                p90_response_minutes=_percentile(response_minutes, 0.9),
            )
        )
    return tuple(sorted(breakdowns, key=lambda item: (-item.breach_count, item.key)))


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return sorted_values[midpoint]
    return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    sorted_values = sorted(values)
    index = max(math.ceil(percentile * len(sorted_values)) - 1, 0)
    return sorted_values[index]


def _row_value(row: dict[str, str], field_map: dict[str, str], canonical: str) -> str:
    mapped = field_map.get(canonical)
    if not mapped:
        return ""
    return (row.get(mapped) or "").strip()


def _normalize_header(value: str) -> str:
    return value.strip().lower().replace("_", " ")
