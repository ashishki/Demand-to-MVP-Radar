"""Configuration loading primitives."""

from __future__ import annotations

import os
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from demand_mvp_radar.models import SourceCatalogEntry


def default_source_catalog() -> tuple[SourceCatalogEntry, ...]:
    return (
        SourceCatalogEntry(
            source_type="github",
            priority="P1",
            trust_level="medium",
            freshness_window_days=14,
            access_method="public_api",
        ),
        SourceCatalogEntry(
            source_type="hacker_news",
            priority="P1",
            trust_level="medium",
            freshness_window_days=14,
            access_method="public_api",
        ),
        SourceCatalogEntry(
            source_type="stack_exchange",
            priority="P1",
            trust_level="medium",
            freshness_window_days=30,
            access_method="public_api",
        ),
        SourceCatalogEntry(
            source_type="product_hunt",
            priority="P1",
            trust_level="medium",
            freshness_window_days=30,
            access_method="credentialed_api",
            approval_required=True,
            credential_env_vars=("PRODUCT_HUNT_TOKEN",),
        ),
        SourceCatalogEntry(
            source_type="serp",
            priority="P2",
            trust_level="medium",
            freshness_window_days=14,
            access_method="paid_api",
            approval_required=True,
            credential_env_vars=("SERPAPI_API_KEY",),
        ),
        SourceCatalogEntry(
            source_type="youtube",
            priority="P2",
            trust_level="medium",
            freshness_window_days=30,
            access_method="credentialed_api",
            approval_required=True,
            credential_env_vars=("YOUTUBE_API_KEY",),
        ),
        SourceCatalogEntry(
            source_type="app_stores",
            priority="P2",
            trust_level="medium",
            freshness_window_days=30,
            access_method="manual_snapshot",
            approval_required=True,
        ),
        SourceCatalogEntry(
            source_type="g2",
            priority="P2",
            trust_level="medium",
            freshness_window_days=30,
            access_method="paid_api",
            approval_required=True,
            credential_env_vars=("G2_API_KEY",),
        ),
        SourceCatalogEntry(
            source_type="reddit",
            priority="P3",
            trust_level="low",
            freshness_window_days=14,
            access_method="credentialed_api",
            approval_required=True,
            credential_env_vars=("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"),
        ),
    )


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    data_dir: Path = Path("data")
    report_dir: Path = Path("reports")
    max_weekly_llm_cost_usd: Decimal = Field(default=Decimal("5.00"), ge=0)
    fetch_timeout_seconds: int = Field(default=20, ge=1)
    max_index_age_days: int = Field(default=7, ge=1)
    source_catalog: tuple[SourceCatalogEntry, ...] = Field(default_factory=default_source_catalog)

    @field_validator("data_dir", "report_dir", mode="before")
    @classmethod
    def parse_path(cls, value: object) -> Path | object:
        return Path(value) if isinstance(value, str) else value

    @field_validator("max_weekly_llm_cost_usd", mode="before")
    @classmethod
    def parse_decimal(cls, value: object) -> Decimal:
        return Decimal(str(value))

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.data_dir / 'radar.sqlite3'}"


ENV_FIELD_MAP = {
    "DMR_DATA_DIR": "data_dir",
    "DMR_REPORT_DIR": "report_dir",
    "DMR_MAX_WEEKLY_LLM_COST_USD": "max_weekly_llm_cost_usd",
    "DMR_FETCH_TIMEOUT_SECONDS": "fetch_timeout_seconds",
    "DMR_MAX_INDEX_AGE_DAYS": "max_index_age_days",
}


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    source = os.environ if env is None else env
    values = {
        field_name: source[env_name]
        for env_name, field_name in ENV_FIELD_MAP.items()
        if env_name in source
    }
    return Settings(**values)
