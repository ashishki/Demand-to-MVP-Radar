from __future__ import annotations

import json
from datetime import UTC, datetime

from demand_mvp_radar.models import EvidenceRecord
from demand_mvp_radar.reports.evidence_delta import generate_evidence_delta_report
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.storage.repositories import EvidenceRepository


def test_delta_report_summarizes_source_counts(tmp_path) -> None:
    connection = _build_delta_fixture(tmp_path)

    report = generate_evidence_delta_report(
        connection,
        run_id="import-current",
        previous_run_id="import-previous",
        as_of=datetime(2026, 5, 20, tzinfo=UTC),
        stale_after_days=30,
    )

    assert report.source_type_counts["telegram_research_agent"].new_count == 1
    assert report.source_type_counts["operator_note"].new_count == 1
    assert report.source_type_counts["operator_note"].duplicate_count == 1
    assert report.source_type_counts["operator_note"].stale_count == 1
    assert report.source_type_counts["operator_note"].quarantined_count == 1
    assert report.source_type_counts["github_repo"].new_count == 1
    assert report.source_type_counts["serp"].skipped_count == 1


def test_delta_report_lists_changed_clusters(tmp_path) -> None:
    connection = _build_delta_fixture(tmp_path)

    report = generate_evidence_delta_report(
        connection,
        run_id="import-current",
        previous_run_id="import-previous",
        as_of=datetime(2026, 5, 20, tzinfo=UTC),
    )

    cluster_by_label = {cluster.cluster_label: cluster for cluster in report.changed_clusters}
    webhook_cluster = cluster_by_label["webhook replay debugging"]

    assert "github_repo" in webhook_cluster.source_types
    assert "changed" in webhook_cluster.change_types
    assert "https://github.example.local/operator/repo/issues/1" in webhook_cluster.source_refs


def test_delta_report_redacts_private_source_details(tmp_path) -> None:
    connection = _build_delta_fixture(tmp_path)

    report = generate_evidence_delta_report(
        connection,
        run_id="import-current",
        previous_run_id="import-previous",
        as_of=datetime(2026, 5, 20, tzinfo=UTC),
    )
    rendered_refs = " ".join(
        source_ref for cluster in report.changed_clusters for source_ref in cluster.source_refs
    )

    assert "/home/" not in rendered_refs
    assert "token=" not in rendered_refs
    assert "private_signal.md" not in rendered_refs
    assert "operator_note:redacted" in rendered_refs
    assert report.redaction_warnings == ("redacted private source reference for operator_note",)


def _build_delta_fixture(tmp_path):
    connection = connect_database(tmp_path / "radar.sqlite3")
    create_schema(connection)
    repository = EvidenceRepository(connection)
    _insert_run(connection, "import-previous", source_counts={}, error_counts={})
    _insert_run(
        connection,
        "import-current",
        source_counts={"skipped_sources": ["serp"]},
        error_counts={"operator_notes": 1},
    )

    previous = (
        _evidence(
            "import-previous",
            "operator_note",
            "note-dup-prev",
            "operator_note:redacted",
            datetime(2026, 4, 1, tzinfo=UTC),
            "Private note duplicate",
            "hash-note-dup",
        ),
        _evidence(
            "import-previous",
            "github_repo",
            "repo-1",
            "https://github.example.local/operator/repo/issues/1",
            datetime(2026, 5, 1, tzinfo=UTC),
            "Webhook replay debugging",
            "hash-github-old",
        ),
    )
    current = (
        _evidence(
            "import-current",
            "telegram_research_agent",
            "telegram-1",
            "https://t.me/operators/source-1",
            datetime(2026, 5, 19, tzinfo=UTC),
            "Ledger reconciliation demand",
            "hash-telegram-new",
        ),
        _evidence(
            "import-current",
            "operator_note",
            "note-dup-current",
            "operator_note:redacted",
            datetime(2026, 4, 1, tzinfo=UTC),
            "Private note duplicate",
            "hash-note-dup",
        ),
        _evidence(
            "import-current",
            "operator_note",
            "note-private-current",
            "/home/ashishki/private_signal.md?token=test-key",
            datetime(2026, 5, 19, tzinfo=UTC),
            "Private note Flowbot",
            "hash-note-private-new",
        ),
        _evidence(
            "import-current",
            "github_repo",
            "repo-1",
            "https://github.example.local/operator/repo/issues/1",
            datetime(2026, 5, 19, tzinfo=UTC),
            "Webhook replay debugging",
            "hash-github-new",
        ),
    )
    for evidence in (*previous, *current):
        repository.write(evidence)
    return connection


def _insert_run(
    connection,
    run_id: str,
    *,
    source_counts: dict[str, object],
    error_counts: dict[str, int],
) -> None:
    connection.execute(
        """
        INSERT INTO runs (
            run_id,
            started_at,
            ended_at,
            status,
            source_counts,
            error_counts,
            duplicate_count,
            corpus_version,
            index_schema_version,
            max_weekly_llm_cost_usd
        )
        VALUES (
            :run_id,
            :started_at,
            :ended_at,
            :status,
            :source_counts,
            :error_counts,
            :duplicate_count,
            :corpus_version,
            :index_schema_version,
            :max_weekly_llm_cost_usd
        )
        """,
        {
            "run_id": run_id,
            "started_at": "2026-05-20T00:00:00+00:00",
            "ended_at": f"2026-05-20T00:00:00+00:00-{run_id}",
            "status": "imported",
            "source_counts": json.dumps(source_counts, sort_keys=True),
            "error_counts": json.dumps(error_counts, sort_keys=True),
            "duplicate_count": 0,
            "corpus_version": f"{run_id}-corpus",
            "index_schema_version": "retrieval-index-v1",
            "max_weekly_llm_cost_usd": "0",
        },
    )
    connection.commit()


def _evidence(
    run_id: str,
    source_type: str,
    source_id: str,
    source_url: str,
    captured_at: datetime,
    title: str,
    content_hash: str,
) -> EvidenceRecord:
    text = f"{title} evidence"
    return EvidenceRecord(
        run_id=run_id,
        source_type=source_type,
        source_id=source_id,
        source_url=source_url,
        captured_at=captured_at,
        title=title,
        snippet=text,
        normalized_text=text,
        content_hash=content_hash,
        source_fingerprint=f"{source_type}:{source_id}:{content_hash}",
    )
