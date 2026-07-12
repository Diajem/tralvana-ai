"""
OAuth2 client-credentials authentication — interface only.

T-026 constraint: no real token fetch, no live authentication call. A
real implementation would POST `client_id`/`client_secret` to
`token_url`, cache the returned bearer token, and refresh it once it
expires — none of that HTTP exchange is implemented here.
`set_cached_token()` exists only so tests can simulate an
already-authenticated state and exercise `headers()`'s success path
without a live call.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from travelos.intelligence_gateway.exceptions import ProviderConfigurationError
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.auth.auth_strategy import AuthStrategy


@dataclass
class OAuth2ClientCredentialsAuthStrategy(AuthStrategy):
    client_id: SecretReference
    client_secret: SecretReference
    token_url: str
    _cached_token: str | None = field(default=None, repr=False)

    def is_configured(self) -> bool:
        """Whether client_id/client_secret are present — independent of
        whether a token has actually been fetched (token exchange isn't
        implemented; see module docstring)."""
        return self.client_id.is_present() and self.client_secret.is_present()

    def headers(self) -> dict[str, str]:
        if not self.is_configured():
            raise ProviderConfigurationError(
                f"OAuth2 client credentials not configured — set {self.client_id.env_var} "
                f"and {self.client_secret.env_var} to use this provider."
            )
        if self._cached_token is None:
            raise ProviderConfigurationError(
                "OAuth2 token exchange is not implemented (T-026, interface only) — "
                "a real adapter must fetch a token from the vendor's token endpoint "
                "before this strategy can authenticate a live request."
            )
        return {"Authorization": f"Bearer {self._cached_token}"}

    def set_cached_token(self, token: str) -> None:
        """Test/simulation hook only — never populated by a live call in
        this framework version."""
        self._cached_token = token
