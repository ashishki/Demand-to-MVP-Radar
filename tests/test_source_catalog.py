import pytest
from demand_mvp_radar.config import load_settings
from demand_mvp_radar.models import SourceCatalogEntry
from pydantic import ValidationError


def test_source_catalog_entry_validates_required_fields() -> None:
    entry = SourceCatalogEntry(
        source_type="github",
        priority="P1",
        trust_level="medium",
        freshness_window_days=14,
        access_method="public_api",
        enabled=False,
        approval_required=False,
    )

    assert entry.source_type == "github"
    assert entry.priority == "P1"
    assert entry.trust_level == "medium"
    assert entry.freshness_window_days == 14
    assert entry.access_method == "public_api"
    assert entry.enabled is False
    assert entry.approval_required is False


def test_invalid_source_catalog_entries_are_rejected() -> None:
    with pytest.raises(ValidationError):
        SourceCatalogEntry(
            source_type="github",
            priority="P1",
            trust_level="unknown",
            freshness_window_days=14,
            access_method="public_api",
        )

    with pytest.raises(ValidationError):
        SourceCatalogEntry(
            source_type="serp",
            priority="P2",
            trust_level="medium",
            freshness_window_days=-1,
            access_method="paid_api",
            approval_required=True,
        )

    with pytest.raises(ValidationError):
        SourceCatalogEntry(
            source_type="reddit",
            priority="P3",
            trust_level="low",
            freshness_window_days=14,
            access_method="credentialed_api",
            enabled=True,
            approval_required=False,
        )


def test_default_catalog_contains_planned_source_placeholders() -> None:
    settings = load_settings(env={})

    catalog_by_type = {entry.source_type: entry for entry in settings.source_catalog}
    expected_sources = {
        "github",
        "hacker_news",
        "stack_exchange",
        "product_hunt",
        "serp",
        "youtube",
        "app_stores",
        "g2",
        "reddit",
    }

    assert expected_sources.issubset(catalog_by_type)
    for source_type in expected_sources:
        assert catalog_by_type[source_type].enabled is False

    for source_type in ("product_hunt", "serp", "youtube", "g2", "reddit"):
        assert catalog_by_type[source_type].approval_required is True
