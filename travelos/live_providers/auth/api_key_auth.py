"""API-key authentication — a single secret sent as a request header."""

from __future__ import annotations

from dataclasses import dataclass

from travelos.intelligence_gateway.exceptions import ProviderConfigurationError
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.auth.auth_strategy import AuthStrategy


@dataclass
class ApiKeyAuthStrategy(AuthStrategy):
    secret: SecretReference
    header_name: str = "X-API-Key"

    def is_configured(self) -> bool:
        return self.secret.is_present()

    def headers(self) -> dict[str, str]:
        if not self.is_configured():
            raise ProviderConfigurationError(
                f"API key not configured — set {self.secret.env_var} to use this provider."
            )
        return {self.header_name: self.secret.resolve()}
