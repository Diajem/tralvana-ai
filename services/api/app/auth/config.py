"""Environment-backed authentication configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum


class AuthConfigurationError(RuntimeError):
    """Raised when an authentication mode is unsafe or incomplete."""


class AuthMode(str, Enum):
    DISABLED = "DISABLED"
    CLERK = "CLERK"


@dataclass(frozen=True)
class AuthSettings:
    mode: AuthMode
    jwt_key: str | None
    authorized_parties: tuple[str, ...]

    @classmethod
    def from_environment(cls) -> "AuthSettings":
        environment = os.environ.get("TRAVELOS_ENV", "development").strip().lower()
        default_mode = AuthMode.CLERK.value if environment == "production" else AuthMode.DISABLED.value
        raw_mode = os.environ.get("TRALVANA_AUTH_MODE", default_mode).strip().upper()
        try:
            mode = AuthMode(raw_mode)
        except ValueError as exc:
            raise AuthConfigurationError(
                "TRALVANA_AUTH_MODE must be DISABLED or CLERK"
            ) from exc

        if environment == "production" and mode is not AuthMode.CLERK:
            raise AuthConfigurationError(
                "Production requires TRALVANA_AUTH_MODE=CLERK"
            )

        jwt_key = os.environ.get("CLERK_JWT_KEY")
        parties = tuple(
            party.strip()
            for party in os.environ.get("CLERK_AUTHORIZED_PARTIES", "").split(",")
            if party.strip()
        )
        if mode is AuthMode.CLERK:
            missing = []
            if not jwt_key:
                missing.append("CLERK_JWT_KEY")
            if not parties:
                missing.append("CLERK_AUTHORIZED_PARTIES")
            if missing:
                raise AuthConfigurationError(
                    "Clerk authentication is incomplete; missing " + ", ".join(missing)
                )

        return cls(mode=mode, jwt_key=jwt_key, authorized_parties=parties)
