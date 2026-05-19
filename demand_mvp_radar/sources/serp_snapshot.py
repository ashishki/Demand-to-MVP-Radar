"""Saved SERP snapshot reader."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class SerpResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    query: str
    provider: str
    rank: int
    title: str
    url: str
    snippet: str
    captured_at: datetime


def read_serp_snapshot(path: Path) -> tuple[SerpResult, ...]:
    payload = json.loads(path.read_text())
    query = payload["query"]
    provider = payload["provider"]
    captured_at = payload["captured_at"]
    return tuple(
        SerpResult(
            query=query,
            provider=provider,
            rank=item["rank"],
            title=item["title"],
            url=item["url"],
            snippet=item["snippet"],
            captured_at=datetime.fromisoformat(captured_at),
        )
        for item in payload["results"]
    )
