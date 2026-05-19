"""Shared observability primitives."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def span(_operation_name: str) -> Iterator[None]:
    yield
