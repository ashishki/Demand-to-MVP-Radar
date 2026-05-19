from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

from demand_mvp_radar.models import RunManifest


def test_run_manifest_serializes_required_fields() -> None:
    manifest = RunManifest(
        run_id="run-001",
        started_at=datetime(2026, 5, 19, 12, 0, tzinfo=UTC),
        ended_at=datetime(2026, 5, 19, 12, 5, tzinfo=UTC),
        status="completed",
        source_counts={"telegram": 2},
        error_counts={"telegram": 0},
        duplicate_count=1,
        corpus_version="corpus-v1",
        max_weekly_llm_cost_usd=Decimal("5.00"),
    )

    payload = json.loads(manifest.model_dump_json())

    assert {
        "run_id",
        "started_at",
        "ended_at",
        "status",
        "source_counts",
        "error_counts",
        "duplicate_count",
        "corpus_version",
        "max_weekly_llm_cost_usd",
    } <= payload.keys()
