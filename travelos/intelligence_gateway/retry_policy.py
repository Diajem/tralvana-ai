"""
Retry Policy — lightweight, stdlib-only retry handling for transient
provider failures (docs/CACHING_AND_FAILOVER.md). No external retry
library — none is present in services/api/requirements.txt, and the
constraint says not to add one unless already present.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from travelos.intelligence_gateway.exceptions import (
    ProviderAuthenticationError,
    ProviderMisconfiguredError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderValidationError,
)

_DEFAULT_RETRYABLE: tuple[type[Exception], ...] = (
    ProviderUnavailableError,
    ProviderTimeoutError,
    ProviderResponseError,
    ConnectionError,
    TimeoutError,
)

# Never retried, regardless of `retryable_exceptions` — retrying an
# invalid request or bad credentials just reproduces the same failure.
_NEVER_RETRYABLE: tuple[type[Exception], ...] = (
    ProviderValidationError,
    ProviderAuthenticationError,
    ProviderMisconfiguredError,
)


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.0  # 0 keeps tests/dev deterministic and fast
    backoff_multiplier: float = 2.0
    retryable_exceptions: tuple[type[Exception], ...] = field(default=_DEFAULT_RETRYABLE)

    def is_retryable(self, exc: Exception) -> bool:
        if isinstance(exc, _NEVER_RETRYABLE):
            return False
        return isinstance(exc, self.retryable_exceptions)

    def delay_for_attempt(self, attempt: int) -> float:
        """`attempt` is 1-indexed — the delay *before* this attempt runs."""
        if attempt <= 1:
            return 0.0
        return self.base_delay_seconds * (self.backoff_multiplier ** (attempt - 2))
