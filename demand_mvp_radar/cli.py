"""Command-line entrypoint for Demand-to-MVP Radar."""

from __future__ import annotations

import argparse
import json
import sqlite3
from decimal import Decimal
from pathlib import Path

from demand_mvp_radar.config import Settings, load_settings
from demand_mvp_radar.pipeline import run_weekly_pipeline


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
    return 0


def _settings_from_run_args(args: argparse.Namespace) -> Settings:
    settings = load_settings()
    updates: dict[str, object] = {}
    if args.data_dir:
        updates["data_dir"] = Path(args.data_dir)
    if args.report_dir:
        updates["report_dir"] = Path(args.report_dir)
    if args.max_weekly_llm_cost_usd:
        updates["max_weekly_llm_cost_usd"] = Decimal(str(args.max_weekly_llm_cost_usd))
    return settings.model_copy(update=updates)


def _database_status(database_path: Path) -> dict[str, object]:
    if not database_path.exists():
        return {
            "status": "not_initialized",
            "corpus_version": None,
            "index_age_days": None,
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
    except sqlite3.Error:
        return {"status": "error", "corpus_version": None, "index_age_days": None}
    if row is None:
        return {"status": "initialized", "corpus_version": None, "index_age_days": None}

    index_age_days = None
    if row["ended_at"]:
        ended_at = datetime_from_isoformat(row["ended_at"])
        index_age_days = max((datetime_from_isoformat("now") - ended_at).days, 0)
    return {
        "status": "ok",
        "corpus_version": row["corpus_version"],
        "index_age_days": index_age_days,
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
