from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from demand_mvp_radar.config import load_settings
from pydantic import ValidationError


def test_default_configuration_values() -> None:
    settings = load_settings(env={})

    assert settings.data_dir == Path("data")
    assert settings.report_dir == Path("reports")
    assert settings.max_index_age_days == 7


def test_environment_overrides_defaults() -> None:
    settings = load_settings(
        env={
            "DMR_DATA_DIR": "/tmp/radar-data",
            "DMR_REPORT_DIR": "/tmp/radar-reports",
            "DMR_MAX_WEEKLY_LLM_COST_USD": "2.50",
            "DMR_FETCH_TIMEOUT_SECONDS": "11",
            "DMR_MAX_INDEX_AGE_DAYS": "3",
        }
    )

    assert settings.data_dir == Path("/tmp/radar-data")
    assert settings.report_dir == Path("/tmp/radar-reports")
    assert settings.max_weekly_llm_cost_usd == Decimal("2.50")
    assert settings.fetch_timeout_seconds == 11
    assert settings.max_index_age_days == 3


def test_invalid_runtime_values_raise_validation_error() -> None:
    with pytest.raises(ValidationError):
        load_settings(env={"DMR_MAX_WEEKLY_LLM_COST_USD": "-1"})

    with pytest.raises(ValidationError):
        load_settings(env={"DMR_FETCH_TIMEOUT_SECONDS": "-1"})
