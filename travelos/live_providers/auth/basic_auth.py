"""HTTP Basic authentication backed by environment-only secrets."""

from __future__ import annotations

import base64
from dataclasses import dataclass

from travelos.intelligence_gateway.exceptions import ProviderConfigurationError
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.auth.auth_strategy import AuthStrategy


@dataclass
class BasicAuthStrategy(AuthStrategy):
    username: SecretReference
    password: SecretReference

    def is_configured(self) -> bool:
        return self.username.is_present() and self.password.is_present()

    def headers(self) -> dict[str, str]:
        if not self.is_configured():
            raise ProviderConfigurationError(
                "Basic authentication is not configured — set "
                f"{self.username.env_var} and {self.password.env_var}."
            )
        credentials = f"{self.username.resolve()}:{self.password.resolve()}".encode("utf-8")
        encoded = base64.b64encode(credentials).decode("ascii")
        return {"Authorization": f"Basic {encoded}"}
