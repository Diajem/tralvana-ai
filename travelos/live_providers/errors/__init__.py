"""
Standard provider error types (docs/PROVIDER_ERROR_MODEL.md). Re-exported
from `travelos.intelligence_gateway.exceptions` — the Live Provider
Framework does not define a second, parallel error hierarchy. Mock
providers (T-025) and live providers (T-026) raise from the same set, so
`travelos/intelligence_gateway/retry_policy.py` and
`failover_policy.py` handle both identically with no special-casing.

`ProviderRateLimitError` and `ProviderConfigurationError` are the names
this task's brief specifies; they are the exact same classes as T-025's
`ProviderRateLimitedError` and `ProviderMisconfiguredError` — see that
module's reconciliation note.
"""

from travelos.intelligence_gateway.exceptions import (
    AllProvidersFailedError,
    MissingSecretError,
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderError,
    ProviderMisconfiguredError,
    ProviderRateLimitedError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderValidationError,
)

__all__ = [
    "ProviderError",
    "ProviderAuthenticationError",
    "ProviderValidationError",
    "ProviderRateLimitError",
    "ProviderRateLimitedError",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
    "ProviderResponseError",
    "ProviderConfigurationError",
    "ProviderMisconfiguredError",
    "AllProvidersFailedError",
    "MissingSecretError",
]
