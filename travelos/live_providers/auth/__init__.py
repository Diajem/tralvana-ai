"""
Authentication strategies for live provider adapters
(docs/PROVIDER_AUTHENTICATION.md). Every strategy loads its credential
through `travelos.intelligence_gateway.secret_reference.SecretReference`
— never a hardcoded value — and never logs or returns the raw secret.
"""

from travelos.live_providers.auth.api_key_auth import ApiKeyAuthStrategy
from travelos.live_providers.auth.auth_strategy import AuthStrategy
from travelos.live_providers.auth.bearer_token_auth import BearerTokenAuthStrategy
from travelos.live_providers.auth.oauth2_client_credentials_auth import (
    OAuth2ClientCredentialsAuthStrategy,
)

__all__ = [
    "AuthStrategy",
    "ApiKeyAuthStrategy",
    "BearerTokenAuthStrategy",
    "OAuth2ClientCredentialsAuthStrategy",
]
