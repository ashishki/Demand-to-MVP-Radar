"""SQLite repositories for domain records."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from demand_mvp_radar.models import DecisionRecord, EvidenceRecord
from demand_mvp_radar.observability import span


class EvidenceRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def write(self, evidence: EvidenceRecord) -> int:
        params = {
            "run_id": evidence.run_id,
            "source_type": evidence.source_type,
            "source_id": evidence.source_id,
            "source_url": evidence.source_url,
            "captured_at": evidence.captured_at.isoformat(),
            "title": evidence.title,
            "snippet": evidence.snippet,
            "normalized_text": evidence.normalized_text,
            "content_hash": evidence.content_hash,
            "source_fingerprint": evidence.source_fingerprint,
        }
        with span("sqlite.write_evidence"):
            self.connection.execute(
                """
                INSERT INTO evidence (
                    run_id,
                    source_type,
                    source_id,
                    source_url,
                    captured_at,
                    title,
                    snippet,
                    normalized_text,
                    content_hash,
                    source_fingerprint
                )
                VALUES (
                    :run_id,
                    :source_type,
                    :source_id,
                    :source_url,
                    :captured_at,
                    :title,
                    :snippet,
                    :normalized_text,
                    :content_hash,
                    :source_fingerprint
                )
                ON CONFLICT(source_fingerprint) DO NOTHING
                """,
                params,
            )
            row = self.connection.execute(
                """
                SELECT id
                FROM evidence
                WHERE source_fingerprint = :source_fingerprint
                """,
                {"source_fingerprint": evidence.source_fingerprint},
            ).fetchone()
            self.connection.commit()
        if row is None:
            raise RuntimeError("evidence write failed")
        return int(row["id"])


class OpportunityRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(self, title: str, status: str = "new") -> int:
        with span("sqlite.create_opportunity"):
            cursor = self.connection.execute(
                """
                INSERT INTO opportunities (title, status)
                VALUES (:title, :status)
                """,
                {"title": title, "status": status},
            )
            self.connection.commit()
        return int(cursor.lastrowid)


class DecisionRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def add(self, decision: DecisionRecord) -> int:
        created_at = decision.created_at or decision.decided_at or datetime.now(UTC)
        reason = decision.reason or decision.rationale
        with span("sqlite.add_decision"):
            cursor = self.connection.execute(
                """
                INSERT INTO decisions (
                    opportunity_id,
                    decision,
                    actor,
                    decided_at,
                    created_at,
                    rationale,
                    reason,
                    source_report_path
                )
                VALUES (
                    :opportunity_id,
                    :decision,
                    :actor,
                    :decided_at,
                    :created_at,
                    :rationale,
                    :reason,
                    :source_report_path
                )
                """,
                {
                    "opportunity_id": decision.opportunity_id,
                    "decision": decision.decision,
                    "actor": decision.actor,
                    "decided_at": created_at.isoformat(),
                    "created_at": created_at.isoformat(),
                    "rationale": reason,
                    "reason": reason,
                    "source_report_path": decision.source_report_path,
                },
            )
            self.connection.commit()
        return int(cursor.lastrowid)

    def count_for_opportunity(self, opportunity_id: int) -> int:
        with span("sqlite.count_decisions"):
            row = self.connection.execute(
                """
                SELECT COUNT(*) AS decision_count
                FROM decisions
                WHERE opportunity_id = :opportunity_id
                """,
                {"opportunity_id": opportunity_id},
            ).fetchone()
        return int(row["decision_count"])

    def list_for_opportunity(self, opportunity_id: int) -> tuple[sqlite3.Row, ...]:
        with span("sqlite.list_decisions"):
            rows = self.connection.execute(
                """
                SELECT
                    id,
                    opportunity_id,
                    decision,
                    actor,
                    COALESCE(created_at, decided_at) AS created_at,
                    COALESCE(reason, rationale) AS reason,
                    source_report_path
                FROM decisions
                WHERE opportunity_id = :opportunity_id
                ORDER BY COALESCE(created_at, decided_at) ASC, id ASC
                """,
                {"opportunity_id": opportunity_id},
            ).fetchall()
        return tuple(rows)
