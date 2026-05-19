"""Saved store metadata fixture reader."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class StoreListing(BaseModel):
    model_config = ConfigDict(frozen=True)

    listing_id: str
    store: str
    title: str
    description: str
    rating: float
    review_count: int
    captured_at: datetime


def read_store_metadata(path: Path) -> StoreListing:
    payload = json.loads(path.read_text())
    return StoreListing(
        listing_id=payload["listing_id"],
        store=payload["store"],
        title=payload["title"],
        description=payload["description"],
        rating=payload["rating"],
        review_count=payload["review_count"],
        captured_at=datetime.fromisoformat(payload["captured_at"]),
    )
