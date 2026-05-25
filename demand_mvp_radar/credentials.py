"""Credential resolution and redaction helpers."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

CredentialResolutionStatus = Literal["available", "missing", "invalid", "not_required"]

_ENV_VAR_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


class CredentialRequirement(BaseModel):
    model_config = ConfigDict(frozen=True)

    env_var_name: str = Field(pattern=_ENV_VAR_PATTERN.pattern)
    required: bool = True
    purpose: str | None = None


class CredentialResolution(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_name: str = Field(min_length=1)
    status: CredentialResolutionStatus
    env_var_names: tuple[str, ...] = ()
    missing_env_vars: tuple[str, ...] = ()
    invalid_env_vars: tuple[str, ...] = ()

    _secret_values: dict[str, str] = PrivateAttr(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        source_name: str,
        status: CredentialResolutionStatus,
        env_var_names: tuple[str, ...],
        missing_env_vars: tuple[str, ...] = (),
        invalid_env_vars: tuple[str, ...] = (),
        secret_values: Mapping[str, str] | None = None,
    ) -> CredentialResolution:
        resolution = cls(
            source_name=source_name,
            status=status,
            env_var_names=env_var_names,
            missing_env_vars=missing_env_vars,
            invalid_env_vars=invalid_env_vars,
        )
        resolution._secret_values = dict(secret_values or {})
        return resolution

    def secret_value(self, env_var_name: str) -> str:
        return self._secret_values[env_var_name]

    def to_source_error(self) -> SourceCredentialError | None:
        if self.status in {"available", "not_required"}:
            return None
        if self.status == "missing":
            reason = "missing required credential environment variable"
            affected = self.missing_env_vars
        else:
            reason = "invalid credential environment variable"
            affected = self.invalid_env_vars
        return SourceCredentialError(
            source_name=self.source_name,
            status=self.status,
            env_var_names=affected,
            reason=reason,
        )


class SourceCredentialError(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_name: str = Field(min_length=1)
    status: Literal["missing", "invalid"]
    env_var_names: tuple[str, ...]
    reason: str = Field(min_length=1)

    def __str__(self) -> str:
        return self.log_message()

    def log_message(self) -> str:
        return (
            f"{self.source_name}: {self.reason}; "
            f"status={self.status}; env_vars={','.join(self.env_var_names)}"
        )

    def to_manifest_value(self) -> str:
        return self.log_message()


class LiveSourceCredentialState(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_name: str = Field(min_length=1)
    requested_enabled: bool
    effective_enabled: bool
    credential_status: CredentialResolutionStatus
    env_var_names: tuple[str, ...] = ()
    source_error: SourceCredentialError | None = None


class CredentialedSourceConfig(Protocol):
    source_name: str
    enabled: bool
    credential_requirements: tuple[CredentialRequirement, ...]


def resolve_credentials(
    *,
    source_name: str,
    requirements: Iterable[CredentialRequirement],
    env: Mapping[str, str] | None = None,
) -> CredentialResolution:
    requirements_tuple = tuple(requirements)
    env_source = os.environ if env is None else env
    env_var_names = tuple(requirement.env_var_name for requirement in requirements_tuple)
    if not requirements_tuple:
        return CredentialResolution.create(
            source_name=source_name,
            status="not_required",
            env_var_names=(),
        )

    missing = tuple(
        requirement.env_var_name
        for requirement in requirements_tuple
        if requirement.required and requirement.env_var_name not in env_source
    )
    invalid = tuple(
        requirement.env_var_name
        for requirement in requirements_tuple
        if requirement.env_var_name in env_source
        and not env_source[requirement.env_var_name].strip()
    )
    secret_values = {
        requirement.env_var_name: env_source[requirement.env_var_name]
        for requirement in requirements_tuple
        if requirement.env_var_name in env_source and requirement.env_var_name not in invalid
    }

    if invalid:
        status: CredentialResolutionStatus = "invalid"
    elif missing:
        status = "missing"
    else:
        status = "available"

    return CredentialResolution.create(
        source_name=source_name,
        status=status,
        env_var_names=env_var_names,
        missing_env_vars=missing,
        invalid_env_vars=invalid,
        secret_values=secret_values,
    )


def resolve_live_source_credentials(
    configs: Iterable[CredentialedSourceConfig],
    *,
    env: Mapping[str, str] | None = None,
) -> tuple[LiveSourceCredentialState, ...]:
    states: list[LiveSourceCredentialState] = []
    for config in configs:
        resolution = resolve_credentials(
            source_name=config.source_name,
            requirements=config.credential_requirements,
            env=env,
        )
        source_error = resolution.to_source_error()
        states.append(
            LiveSourceCredentialState(
                source_name=config.source_name,
                requested_enabled=config.enabled,
                effective_enabled=config.enabled and source_error is None,
                credential_status=resolution.status,
                env_var_names=resolution.env_var_names,
                source_error=source_error,
            )
        )
    return tuple(states)
