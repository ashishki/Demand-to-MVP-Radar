"""Deterministic local embedding adapter for retrieval ingestion tests."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict


class EmbeddingModelInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: str = "local"
    model: str = "local-hash-embedding-v1"
    dimensions: int = 8


class HashEmbeddingClient:
    """Stable deterministic embedding client used until a provider-backed model is selected."""

    model_info = EmbeddingModelInfo()

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        return [_embed_text(text, dimensions=self.model_info.dimensions) for text in texts]


def _embed_text(text: str, *, dimensions: int) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [round(digest[index] / 255, 6) for index in range(dimensions)]
