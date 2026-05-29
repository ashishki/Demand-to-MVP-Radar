from __future__ import annotations

from datetime import UTC, datetime

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.source_trust import build_source_trust_records


def test_source_trust_records_repeated_signals() -> None:
    records = (
        _evidence("telegram-1", "telegram_research_agent", "Telegram Channel SEO Site Generator"),
        _evidence("telegram-2", "telegram_research_agent", "Telegram Channel SEO Site Generator"),
        _evidence("github-1", "github_public", "Telegram Channel SEO Site Generator"),
    )

    trust_records = build_source_trust_records(records)
    telegram = next(
        record for record in trust_records if record.source_type == "telegram_research_agent"
    )
    github = next(record for record in trust_records if record.source_type == "github_public")

    assert telegram.evidence_count == 2
    assert telegram.unique_signal_count == 1
    assert telegram.repeated_signal_count == 1
    assert telegram.evidence_density == 2.0
    assert "telegram seed requires external corroboration" in telegram.rejection_reasons
    assert "repeated signal variants need source diversity" in telegram.rejection_reasons
    assert github.repeated_signal_count == 0


def _evidence(source_id: str, source_type: str, mvp_shape: str) -> EvidenceRecord:
    return EvidenceRecord(
        run_id="run-source-trust-records",
        source_type=source_type,
        source_id=source_id,
        source_url=f"https://example.com/{source_id}",
        captured_at=datetime(2026, 5, 29, tzinfo=UTC),
        title=mvp_shape,
        snippet=f"Repeated demand for {mvp_shape}",
        normalized_text=f"Operators repeatedly ask for {mvp_shape}",
        content_hash=f"hash-{source_id}",
        source_fingerprint=f"{source_type}:{source_id}:hash-{source_id}",
        provider_metadata={"mvp_shape": mvp_shape},
    )
