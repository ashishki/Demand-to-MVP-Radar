"""Command-line entrypoint for Demand-to-MVP Radar."""

from __future__ import annotations

import argparse
import json
import sqlite3
from decimal import Decimal
from pathlib import Path

from demand_mvp_radar.config import Settings, load_settings
from demand_mvp_radar.decisions import DecisionValue, record_operator_decision
from demand_mvp_radar.pipeline import import_sources, run_weekly_pipeline
from demand_mvp_radar.storage.db import connect_database
from demand_mvp_radar.storage.migrations import create_schema
from demand_mvp_radar.storage.repositories import DecisionRepository

REVIEW_DECISIONS: tuple[DecisionValue, ...] = (
    "build",
    "reject",
    "revisit",
    "needs_more_evidence",
    "already_exists",
    "not_my_icp",
    "too_hard_to_distribute",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="demand-mvp-radar",
        description="Local demand intelligence pipeline.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the package version and exit.",
    )
    subparsers = parser.add_subparsers(dest="command")
    health = subparsers.add_parser("health", help="Print local runtime health.")
    health.add_argument(
        "--json",
        action="store_true",
        help="Print health as JSON.",
    )
    run = subparsers.add_parser("run", help="Run the weekly pipeline.")
    run.add_argument("--fixture", required=True, help="Path to a weekly run fixture directory.")
    run.add_argument("--run-id", help="Override the fixture run ID.")
    run.add_argument("--data-dir", help="Override the data directory.")
    run.add_argument("--report-dir", help="Override the report directory.")
    run.add_argument("--max-weekly-llm-cost-usd", help="Override the LLM budget ceiling.")
    import_sources_parser = subparsers.add_parser(
        "import-sources",
        help="Import configured owned sources without generating a weekly report.",
    )
    import_sources_parser.add_argument("--fixture", required=True, help="Path to source fixture.")
    import_sources_parser.add_argument("--run-id", help="Override the fixture run ID.")
    import_sources_parser.add_argument("--data-dir", help="Override the data directory.")
    import_sources_parser.add_argument("--report-dir", help="Override the report directory.")
    review = subparsers.add_parser(
        "review",
        help="Record a human operator decision for a generated dossier.",
    )
    review.add_argument("--opportunity-id", required=True, type=int)
    review.add_argument("--decision", required=True, choices=REVIEW_DECISIONS)
    review.add_argument("--reason")
    review.add_argument("--actor", default="operator")
    review.add_argument(
        "--dossier-path",
        "--source-dossier-path",
        dest="source_report_path",
        required=True,
    )
    review.add_argument("--data-dir", help="Override the data directory.")
    review.add_argument("--report-dir", help="Override the report directory.")
    review.add_argument(
        "--evidence-gap",
        "--requested-evidence-gap",
        dest="requested_evidence_gaps",
        action="append",
        default=[],
        help="Missing evidence gap requested by the operator; may be repeated.",
    )
    return parser


def build_health_payload(settings: Settings) -> dict[str, object]:
    database_path = settings.data_dir / "radar.sqlite3"
    database_status = _database_status(database_path)
    report_dir_status = _report_dir_status(settings.report_dir)
    return {
        "status": "ok",
        "database": {
            "status": database_status["status"],
            "url": settings.database_url,
        },
        "report_dir": {
            "path": str(settings.report_dir),
            "status": report_dir_status,
        },
        "corpus_version": database_status["corpus_version"],
        "index_age_days": database_status["index_age_days"],
        "last_scheduled_run": database_status["last_scheduled_run"],
        "configured_sources": 0,
        "max_index_age_days": settings.max_index_age_days,
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "health":
        payload = build_health_payload(load_settings())
        if args.json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"status: {payload['status']}")
    if args.command == "run":
        settings = _settings_from_run_args(args)
        result = run_weekly_pipeline(
            fixture=Path(args.fixture),
            settings=settings,
            run_id=args.run_id,
        )
        print(result.model_dump_json())
        return 0 if result.status == "completed" else 1
    if args.command == "import-sources":
        settings = _settings_from_run_args(args)
        result = import_sources(
            fixture=Path(args.fixture),
            settings=settings,
            run_id=args.run_id,
        )
        print(result.model_dump_json())
        return 0 if result.status == "imported" else 1
    if args.command == "review":
        return _run_review_command(args)
    return 0


def _run_review_command(args: argparse.Namespace) -> int:
    reason = (args.reason or "").strip()
    if args.decision == "build" and not reason:
        print(json.dumps({"status": "error", "error": "build decisions require --reason"}))
        return 2
    if not reason:
        print(json.dumps({"status": "error", "error": "operator reason is required"}))
        return 2

    settings = _settings_from_run_args(args)
    connection = connect_database(settings.data_dir / "radar.sqlite3")
    create_schema(connection)
    try:
        decision = record_operator_decision(
            DecisionRepository(connection),
            opportunity_id=args.opportunity_id,
            decision=args.decision,
            reason=reason,
            actor=args.actor,
            source_report_path=args.source_report_path,
            requested_evidence_gaps=tuple(args.requested_evidence_gaps),
        )
    except (ValueError, sqlite3.IntegrityError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 2

    print(decision.model_dump_json())
    return 0


def _settings_from_run_args(args: argparse.Namespace) -> Settings:
    settings = load_settings()
    updates: dict[str, object] = {}
    if args.data_dir:
        updates["data_dir"] = Path(args.data_dir)
    if args.report_dir:
        updates["report_dir"] = Path(args.report_dir)
    if getattr(args, "max_weekly_llm_cost_usd", None):
        updates["max_weekly_llm_cost_usd"] = Decimal(str(args.max_weekly_llm_cost_usd))
    return settings.model_copy(update=updates)


def _database_status(database_path: Path) -> dict[str, object]:
    if not database_path.exists():
        return {
            "status": "not_initialized",
            "corpus_version": None,
            "index_age_days": None,
            "last_scheduled_run": None,
        }
    try:
        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT corpus_version, ended_at
            FROM runs
            ORDER BY ended_at DESC
            LIMIT 1
            """
        ).fetchone()
        scheduled_row = connection.execute(
            """
            SELECT run_id, status, ended_at
            FROM runs
            WHERE run_id LIKE 'scheduled-%'
            ORDER BY COALESCE(ended_at, started_at) DESC
            LIMIT 1
            """
        ).fetchone()
    except sqlite3.Error:
        return {
            "status": "error",
            "corpus_version": None,
            "index_age_days": None,
            "last_scheduled_run": None,
        }
    if row is None:
        return {
            "status": "initialized",
            "corpus_version": None,
            "index_age_days": None,
            "last_scheduled_run": _scheduled_run_payload(scheduled_row),
        }

    index_age_days = None
    if row["ended_at"]:
        ended_at = datetime_from_isoformat(row["ended_at"])
        index_age_days = max((datetime_from_isoformat("now") - ended_at).days, 0)
    return {
        "status": "ok",
        "corpus_version": row["corpus_version"],
        "index_age_days": index_age_days,
        "last_scheduled_run": _scheduled_run_payload(scheduled_row),
    }


def _scheduled_run_payload(row: sqlite3.Row | None) -> dict[str, object] | None:
    if row is None:
        return None
    return {
        "run_id": row["run_id"],
        "status": row["status"],
        "ended_at": row["ended_at"],
    }


def _report_dir_status(report_dir: Path) -> str:
    report_dir.mkdir(parents=True, exist_ok=True)
    return "writable" if report_dir.is_dir() and os_access_writable(report_dir) else "not_writable"


def datetime_from_isoformat(value: str):
    from datetime import UTC, datetime

    if value == "now":
        return datetime.now(UTC)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def os_access_writable(path: Path) -> bool:
    import os

    return os.access(path, os.W_OK)


if __name__ == "__main__":
    raise SystemExit(main())
