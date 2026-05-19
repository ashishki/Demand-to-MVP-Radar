"""SQLite connection helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from demand_mvp_radar.observability import span


def connect_database(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    with span("sqlite.connect"):
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
    return connection
