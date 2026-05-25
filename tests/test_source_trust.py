from __future__ import annotations

from datetime import UTC, datetime

from demand_mvp_radar.models import EvidenceRecord, OpportunityCandidate
from demand_mvp_radar.retrieval.ingestion import build_corpus
from demand_mvp_radar.retrieval.query import query_evidence
from demand_mvp_radar.scoring import ScoringConfig, score_opportunity
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.storage.repositories import EvidenceRepository


def test_retrieval_applies_source_specific_freshness(tmp_path) -> None:
    as_of = datetime(2026, 5, 20, tzinfo=UTC)
    connection = connect_database(tmp_path / "radar.sqlite3")
    create_schema(connection)
    corpus_version = "corpus-t25-source-trust-v1"
    rows = _write_corpus(
        connection,
        corpus_version=corpus_version,
        records=(
            _evidence(
                "github-stale-001",
                "github_repo",
                "https://github.com/acme/formula/issues/1",
                datetime(2026, 5, 1, tzinfo=UTC),
                "Spreadsheet formula helper demand from stale GitHub issue",
            ),
            _evidence(
                "telegram-fresh-001",
                "telegram_research_agent",
                "https://t.me/operators/201",
                datetime(2026, 5, 18, tzinfo=UTC),
                "Spreadsheet formula helper demand from operator research export",
            ),
            _evidence(
                "reviews-fresh-001",
                "reviews",
                "https://reviews.example.com/formula-helper",
                datetime(2026, 5, 19, tzinfo=UTC),
                "Spreadsheet formula helper demand repeated in user reviews",
            ),
        ),
    )
    build_corpus(connection, rows, corpus_version=corpus_version)

    response = query_evidence(
        connection,
        "spreadsheet formula helper demand",
        corpus_version=corpus_version,
        min_independent_sources=2,
        top_k=3,
        max_age_days=365,
        source_freshness_windows={"github_repo": 7, "telegram_research_agent": 30},
        as_of=as_of,
    )

    assert response.status == "ok"
    assert {packet.source_url for packet in response.evidence_packets} == {
        "https://t.me/operators/201",
        "https://reviews.example.com/formula-helper",
    }


def test_scoring_applies_source_trust_and_type_caps() -> None:
    as_of = datetime(2026, 5, 20, tzinfo=UTC)
    evidence = (
        _score_evidence("note-001", "operator_note", as_of, "Formula helper complaint one"),
        _score_evidence("note-002", "operator_note", as_of, "Formula helper complaint two"),
        _score_evidence("note-003", "operator_note", as_of, "Formula helper complaint three"),
        _score_evidence(
            "github-001",
            "github_repo",
            as_of,
            "Formula helper issue with competitor alternative and pricing",
        ),
    )
    candidate = _candidate(*(record.source_id for record in evidence))

    score = score_opportunity(
        candidate,
        evidence,
        config=ScoringConfig(
            minimum_evidence_count=2,
            source_trust_weights={"operator_note": 0.2, "github_repo": 1.0},
            source_type_caps={"operator_note": 1},
        ),
        as_of=as_of,
    )

    assert score.components["demand"].value == 42.0
    assert "1.20 trust-adjusted supporting evidence records" in score.components["demand"].rationale


def test_low_trust_stale_support_cannot_trigger_build() -> None:
    as_of = datetime(2026, 5, 20, tzinfo=UTC)
    evidence = (
        _score_evidence(
            "news-001",
            "news",
            datetime(2026, 5, 1, tzinfo=UTC),
            "Formula helper demand mentioned in a news roundup",
        ),
        _score_evidence(
            "news-002",
            "news",
            datetime(2026, 5, 2, tzinfo=UTC),
            "Formula helper demand mentioned again without primary user proof",
        ),
    )
    candidate = _candidate("news-001", "news-002")

    score = score_opportunity(
        candidate,
        evidence,
        config=ScoringConfig(
            minimum_evidence_count=2,
            build_threshold=1,
            revisit_threshold=1,
            max_fresh_days=7,
            low_trust_source_types=("news",),
        ),
        as_of=as_of,
    )

    assert score.recommendation != "build"
    assert "low-trust sources require corroborating higher-trust source" in score.threshold_reasons
    assert "fresh evidence required for build recommendation" in score.threshold_reasons


def _write_corpus(
    connection,
    *,
    corpus_version: str,
    records: tuple[EvidenceRecord, ...],
) -> list[tuple[int, EvidenceRecord]]:
    repository = EvidenceRepository(connection)
    return [(repository.write(record), record) for record in records]


def _candidate(*source_evidence_ids: str) -> OpportunityCandidate:
    return OpportunityCandidate(
        opportunity_id="opp-source-trust",
        normalized_pain="spreadsheet formula troubleshooting",
        target_audience="operators",
        workflow="spreadsheet troubleshooting",
        acquisition_channel="search",
        source_evidence_ids=tuple(source_evidence_ids),
        candidate_title="Spreadsheet Formula Helper for Operators",
    )


def _score_evidence(
    source_id: str,
    source_type: str,
    captured_at: datetime,
    text: str,
) -> EvidenceRecord:
    return EvidenceRecord(
        run_id="run-source-trust-scoring",
        source_type=source_type,
        source_id=source_id,
        source_url=f"https://example.com/{source_id}",
        captured_at=captured_at,
        title="Spreadsheet formula helper",
        snippet=text,
        normalized_text=text,
        content_hash=f"hash-{source_id}",
        source_fingerprint=f"{source_type}:{source_id}:hash-{source_id}",
    )


def _evidence(
    source_id: str,
    source_type: str,
    source_url: str,
    captured_at: datetime,
    text: str,
) -> EvidenceRecord:
    return EvidenceRecord(
        run_id="run-source-trust-retrieval",
        source_type=source_type,
        source_id=source_id,
        source_url=source_url,
        captured_at=captured_at,
        title="Spreadsheet formula helper",
        snippet=text,
        normalized_text=text,
        content_hash=f"hash-{source_id}",
        source_fingerprint=f"{source_type}:{source_id}:hash-{source_id}",
    )
