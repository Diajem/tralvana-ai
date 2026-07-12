"""Bearer-token authentication — a single secret sent as an Authorization header."""

from __future__ import annotations

from dataclasses import dataclass

from travelos.intelligence_gateway.exceptions import ProviderConfigurationError
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.auth.auth_strategy import AuthStrategy


@dataclass
class BearerTokenAuthStrategy(AuthStrategy):
    secret: SecretReference

    def is_configured(self) -> bool:
        return self.secret.is_present()

    def headers(self) -> dict[str, str]:
        if not self.is_configured():
            raise ProviderConfigurationError(
                f"Bearer token not configured — set {self.secret.env_var} to use this provider."
            )
        return {"Authorization": f"Bearer {self.secret.resolve()}"}
