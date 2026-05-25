"""Provider boundary for bounded LLM calls."""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from demand_mvp_radar.retrieval.query import EvidencePacket


class LLMProvider(Protocol):
    def complete_json(self, *, prompt: str, evidence_packets: Sequence[EvidencePacket]) -> str:
        """Return a JSON string for a structured extraction request."""

    def complete_text(self, *, prompt: str, evidence_packets: Sequence[EvidencePacket]) -> str:
        """Return text for a bounded synthesis request."""


class FakeLLMProvider:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[tuple[str, tuple[EvidencePacket, ...]]] = []

    def complete_json(self, *, prompt: str, evidence_packets: Sequence[EvidencePacket]) -> str:
        self.calls.append((prompt, tuple(evidence_packets)))
        return self.response

    def complete_text(self, *, prompt: str, evidence_packets: Sequence[EvidencePacket]) -> str:
        self.calls.append((prompt, tuple(evidence_packets)))
        return self.response


@dataclass(frozen=True)
class AnthropicLLMProvider:
    api_key: str
    model: str
    fallback_model: str | None = None
    max_tokens: int = 4000
    temperature: float | None = None

    def complete_json(self, *, prompt: str, evidence_packets: Sequence[EvidencePacket]) -> str:
        return self._complete(
            prompt=prompt,
            evidence_packets=evidence_packets,
            system=(
                "You are Demand-to-MVP Radar's bounded synthesis model. "
                "Return valid JSON only. Do not include markdown fences."
            ),
        )

    def complete_text(self, *, prompt: str, evidence_packets: Sequence[EvidencePacket]) -> str:
        return self._complete(
            prompt=prompt,
            evidence_packets=evidence_packets,
            system=(
                "You are Demand-to-MVP Radar's bounded synthesis model. "
                "Write concise, source-grounded product opportunity analysis."
            ),
        )

    def _complete(
        self,
        *,
        prompt: str,
        evidence_packets: Sequence[EvidencePacket],
        system: str,
    ) -> str:
        try:
            from anthropic import Anthropic, APIStatusError
        except ImportError as exc:  # pragma: no cover - exercised in deployed env
            raise RuntimeError("anthropic package is not installed") from exc

        full_prompt = _prompt_with_evidence(prompt, evidence_packets)
        client = Anthropic(api_key=self.api_key)
        models = [self.model]
        if self.fallback_model and self.fallback_model not in models:
            models.append(self.fallback_model)

        last_error: Exception | None = None
        for model in models:
            try:
                request_params: dict[str, object] = {
                    "model": model,
                    "max_tokens": self.max_tokens,
                    "system": system,
                    "messages": [{"role": "user", "content": full_prompt}],
                }
                if self.temperature is not None:
                    request_params["temperature"] = self.temperature
                response = client.messages.create(
                    **request_params,
                )
                return _extract_text(response)
            except APIStatusError as exc:
                last_error = exc
                if exc.status_code not in {400, 404}:
                    raise
            except Exception as exc:  # pragma: no cover - network/provider failure
                last_error = exc
                break

        if last_error is not None:
            raise RuntimeError(f"LLM completion failed: {last_error}") from last_error
        raise RuntimeError("LLM completion failed")


def provider_from_env(env: dict[str, str] | None = None) -> LLMProvider | None:
    source = os.environ if env is None else env
    provider = source.get("DMR_LLM_PROVIDER", "").strip().lower()
    if provider in {"", "none", "off", "false"}:
        return None
    if provider != "anthropic":
        raise ValueError(f"unsupported DMR_LLM_PROVIDER: {provider}")

    api_key = (
        source.get("DMR_LLM_API_KEY", "").strip()
        or source.get("LLM_API_KEY", "").strip()
        or source.get("ANTHROPIC_API_KEY", "").strip()
    )
    if not api_key:
        return None

    model = (
        source.get("DMR_LLM_MODEL_MVP_WEEKLY", "").strip()
        or source.get("LLM_MODEL_MVP_WEEKLY", "").strip()
        or source.get("STRONG_MODEL", "").strip()
        or "claude-opus-4-7"
    )
    fallback_model = (
        source.get("DMR_LLM_FALLBACK_MODEL_MVP_WEEKLY", "").strip()
        or "claude-opus-4-1-20250805"
    )
    return AnthropicLLMProvider(
        api_key=api_key,
        model=model,
        fallback_model=fallback_model,
    )


def _prompt_with_evidence(prompt: str, evidence_packets: Sequence[EvidencePacket]) -> str:
    if not evidence_packets:
        return prompt
    lines = [prompt.rstrip(), "", "Evidence packets:"]
    for index, packet in enumerate(evidence_packets, start=1):
        lines.append(f"[{index}] {packet.model_dump(mode='json')}")
    return "\n".join(lines)


def _extract_text(response: object) -> str:
    parts: list[str] = []
    for block in getattr(response, "content", ()):
        text = getattr(block, "text", None)
        if isinstance(text, str):
            parts.append(text)
    return "\n".join(parts).strip()
