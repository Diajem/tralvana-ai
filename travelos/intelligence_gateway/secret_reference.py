"""
SecretReference — a pointer to an environment-variable-backed credential,
never the credential itself in any logged, printed, or serialised form.
See docs/SECRET_MANAGEMENT.md.

A future live provider adapter calls `.resolve()` at the point it makes
an outbound HTTP call — the only place a raw secret value is ever held in
memory. Every other surface (`describe()`, `__repr__`, diagnostics,
ProviderResult) only ever sees whether the secret is configured, never
its value.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from travelos.intelligence_gateway.exceptions import MissingSecretError


@dataclass(frozen=True)
class SecretReference:
    env_var: str
    required: bool = True
    description: str = ""

    def is_present(self) -> bool:
        return bool(os.environ.get(self.env_var))

    def resolve(self) -> str:
        """Read the actual secret value. Only call this immediately before
        using it (e.g. an outbound Authorization header) — never store or
        log the result."""
        value = os.environ.get(self.env_var)
        if not value:
            if self.required:
                raise MissingSecretError(
                    f"Required secret '{self.env_var}' is not set. "
                    "Set it in your environment or .env file — see .env.example."
                )
            return ""
        return value

    def describe(self) -> dict[str, Any]:
        """Safe, loggable summary — never includes the value itself."""
        return {
            "env_var": self.env_var,
            "required": self.required,
            "configured": self.is_present(),
            "description": self.description,
        }

    def __repr__(self) -> str:
        return f"SecretReference(env_var={self.env_var!r}, configured={self.is_present()})"
