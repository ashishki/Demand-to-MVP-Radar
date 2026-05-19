"""SQLite schema migrations."""

from __future__ import annotations

import sqlite3

from demand_mvp_radar.observability import span

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        started_at TEXT NOT NULL,
        ended_at TEXT,
        status TEXT NOT NULL,
        source_counts TEXT NOT NULL DEFAULT '{}',
        error_counts TEXT NOT NULL DEFAULT '{}',
        duplicate_count INTEGER NOT NULL DEFAULT 0,
        corpus_version TEXT NOT NULL,
        index_schema_version TEXT NOT NULL DEFAULT 'retrieval-index-v1',
        max_weekly_llm_cost_usd TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        source_type TEXT NOT NULL,
        source_id TEXT NOT NULL,
        source_url TEXT,
        captured_at TEXT NOT NULL,
        title TEXT NOT NULL,
        snippet TEXT NOT NULL,
        normalized_text TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        source_fingerprint TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opportunity_id INTEGER NOT NULL,
        score_name TEXT NOT NULL,
        score_value REAL NOT NULL,
        rationale TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS briefs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opportunity_id INTEGER NOT NULL,
        content_markdown TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opportunity_id INTEGER NOT NULL,
        decision TEXT NOT NULL,
        actor TEXT NOT NULL,
        decided_at TEXT NOT NULL,
        created_at TEXT,
        rationale TEXT,
        reason TEXT,
        source_report_path TEXT,
        FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tool_audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        tool_name TEXT NOT NULL,
        version TEXT NOT NULL,
        success INTEGER NOT NULL,
        latency_ms INTEGER NOT NULL,
        audit_fields TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS retrieval_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        evidence_id INTEGER NOT NULL,
        corpus_version TEXT NOT NULL,
        chunk_text TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        content_hash TEXT NOT NULL,
        metadata TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (evidence_id) REFERENCES evidence(id)
    )
    """,
]


def create_schema(connection: sqlite3.Connection) -> None:
    with span("sqlite.create_schema"):
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.commit()
