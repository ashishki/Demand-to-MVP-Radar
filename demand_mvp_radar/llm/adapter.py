"""Provider boundary for bounded LLM calls."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from demand_mvp_radar.retrieval.query import EvidencePacket


class LLMProvider(Protocol):
    def complete_json(self, *, prompt: str, evidence_packets: Sequence[EvidencePacket]) -> str:
        """Return a JSON string for a structured extraction request."""


class FakeLLMProvider:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[tuple[str, tuple[EvidencePacket, ...]]] = []

    def complete_json(self, *, prompt: str, evidence_packets: Sequence[EvidencePacket]) -> str:
        self.calls.append((prompt, tuple(evidence_packets)))
        return self.response
