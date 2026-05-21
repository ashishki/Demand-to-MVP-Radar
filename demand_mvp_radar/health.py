"""Runtime health assembly."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

from demand_mvp_radar.config import Settings
from demand_mvp_radar.credentials import CredentialRequirement, resolve_credentials


def build_live_source_health(
    settings: Settings,
    database_status: dict[str, object],
    *,
    env: Mapping[str, str] | None = None,
) -> tuple[dict[str, dict[str, object]], list[str]]:
    run_source_health = dict(database_status.get("source_health", {}))
    run_errors = dict(database_status.get("last_source_errors", {}))
    live_sources: dict[str, dict[str, object]] = {}

    for source in settings.source_catalog:
        source_name = source.source_type
        credential_status = _credential_status(source_name, source.credential_env_vars, env=env)
        run_state = dict(run_source_health.get(source_name, {}))
        credential_required = bool(source.credential_env_vars)
        live_sources[source_name] = _source_health_payload(
            source_name=source_name,
            enabled=source.enabled,
            freshness_window_days=source.freshness_window_days,
            credential_status=credential_status,
            credential_required=credential_required,
            access_mode=str(
                run_state.get(
                    "access_mode",
                    "credentialed" if credential_required else "public",
                )
            ),
            run_state=run_state,
            run_error=run_errors.get(source_name),
        )

    for source_name, run_state_value in run_source_health.items():
        if source_name in live_sources:
            continue
        run_state = dict(run_state_value)
        credential_required = bool(run_state.get("credential_required", False))
        live_sources[source_name] = _source_health_payload(
            source_name=source_name,
            enabled=bool(run_state.get("enabled", True)),
            freshness_window_days=int(run_state.get("freshness_window_days", 7)),
            credential_status=str(run_state.get("credential_status", "not_required")),
            credential_required=credential_required,
            access_mode=str(
                run_state.get(
                    "access_mode",
                    "credentialed" if credential_required else "public",
                )
            ),
            run_state=run_state,
            run_error=run_errors.get(source_name),
        )

    warnings = [
        source_name
        for source_name, source_health in live_sources.items()
        if source_health["freshness_status"] in {"stale", "failing"}
    ]
    return live_sources, warnings


def _source_health_payload(
    *,
    source_name: str,
    enabled: bool,
    freshness_window_days: int,
    credential_status: str,
    credential_required: bool,
    access_mode: str,
    run_state: dict[str, object],
    run_error: object,
) -> dict[str, object]:
    last_success_at = run_state.get("last_success_at")
    last_collected_at = run_state.get("last_collected_at")
    last_error_class = run_state.get("last_error_class")
    if run_error and last_error_class is None:
        last_error_class = "source_error"

    cursor_age_days = _age_days(str(last_collected_at)) if last_collected_at else None
    freshness_status = _freshness_status(
        enabled=enabled,
        last_success_at=str(last_success_at) if last_success_at else None,
        last_error_class=str(last_error_class) if last_error_class else None,
        freshness_window_days=freshness_window_days,
    )
    return {
        "source_name": source_name,
        "enabled": enabled,
        "last_success_at": last_success_at,
        "last_error_class": last_error_class,
        "cursor_age_days": cursor_age_days,
        "freshness_status": freshness_status,
        "credential_status": credential_status,
        "credential_required": credential_required,
        "access_mode": access_mode,
        "rate_limit_state": run_state.get(
            "rate_limit_state",
            {"limited": False},
        ),
    }


def _credential_status(
    source_name: str,
    credential_env_vars: tuple[str, ...],
    *,
    env: Mapping[str, str] | None,
) -> str:
    resolution = resolve_credentials(
        source_name=source_name,
        requirements=tuple(
            CredentialRequirement(env_var_name=env_var_name)
            for env_var_name in credential_env_vars
        ),
        env=env,
    )
    return resolution.status


def _freshness_status(
    *,
    enabled: bool,
    last_success_at: str | None,
    last_error_class: str | None,
    freshness_window_days: int,
) -> str:
    if not enabled:
        return "disabled"
    if last_error_class and last_success_at is None:
        return "failing"
    if last_success_at is None:
        return "unknown"
    if _age_days(last_success_at) > freshness_window_days:
        return "stale"
    return "current"


def _age_days(value: str) -> int:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return max((datetime.now(UTC) - parsed.astimezone(UTC)).days, 0)
