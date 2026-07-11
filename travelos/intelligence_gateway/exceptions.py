"""
Provider exception hierarchy. `RetryPolicy` (retry_policy.py) decides
retryability by type — transient failures are retryable, validation/auth/
configuration failures never are, per this task's explicit constraint.
"""

from __future__ import annotations


class ProviderError(Exception):
    """Base class for every Intelligence Gateway error."""


class ProviderUnavailableError(ProviderError):
    """Transient — the provider could not be reached. Retryable."""


class ProviderTimeoutError(ProviderError):
    """Transient — the provider took too long to respond. Retryable."""


class ProviderRateLimitedError(ProviderError):
    """The provider itself reports it is rate-limited. Not retried in
    place — the gateway fails over to the next eligible provider instead
    (docs/CACHING_AND_FAILOVER.md)."""


class ProviderValidationError(ProviderError):
    """The request itself is invalid for this provider. Never retryable —
    retrying an invalid request produces the same invalid request."""


class ProviderAuthenticationError(ProviderError):
    """Credentials rejected or missing. Never retryable."""


class ProviderMisconfiguredError(ProviderError):
    """The provider is not set up correctly (e.g. a missing required
    secret). Never retryable."""


class AllProvidersFailedError(ProviderError):
    """Every eligible provider for a capability failed or was
    unavailable. Raised only where a caller explicitly asks the gateway
    to raise rather than return an UNAVAILABLE ProviderResult."""


class MissingSecretError(ProviderMisconfiguredError):
    """A required SecretReference has no value in the environment."""
