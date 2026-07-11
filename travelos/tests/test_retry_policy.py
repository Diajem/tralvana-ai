"""Retry behaviour and non-retryable errors — docs/CACHING_AND_FAILOVER.md."""

from __future__ import annotations

from travelos.intelligence_gateway.exceptions import (
    ProviderAuthenticationError,
    ProviderMisconfiguredError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderValidationError,
)
from travelos.intelligence_gateway.retry_policy import RetryPolicy


class TestRetryableClassification:
    def test_provider_unavailable_is_retryable(self):
        policy = RetryPolicy()
        assert policy.is_retryable(ProviderUnavailableError("down")) is True

    def test_provider_timeout_is_retryable(self):
        policy = RetryPolicy()
        assert policy.is_retryable(ProviderTimeoutError("slow")) is True

    def test_connection_error_is_retryable(self):
        policy = RetryPolicy()
        assert policy.is_retryable(ConnectionError("refused")) is True


class TestNonRetryableClassification:
    def test_validation_error_never_retried(self):
        policy = RetryPolicy()
        assert policy.is_retryable(ProviderValidationError("bad input")) is False

    def test_authentication_error_never_retried(self):
        policy = RetryPolicy()
        assert policy.is_retryable(ProviderAuthenticationError("bad key")) is False

    def test_misconfigured_error_never_retried(self):
        policy = RetryPolicy()
        assert policy.is_retryable(ProviderMisconfiguredError("no secret")) is False

    def test_non_retryable_wins_even_if_explicitly_listed_as_retryable(self):
        # A caller can't accidentally make auth/validation failures
        # retryable by widening `retryable_exceptions` — the never-retry
        # list always takes precedence.
        policy = RetryPolicy(retryable_exceptions=(ProviderAuthenticationError,))
        assert policy.is_retryable(ProviderAuthenticationError("bad key")) is False

    def test_unlisted_exception_type_is_not_retryable(self):
        policy = RetryPolicy()
        assert policy.is_retryable(ValueError("unexpected")) is False


class TestMaxAttemptsAndDelay:
    def test_default_max_attempts_is_three(self):
        assert RetryPolicy().max_attempts == 3

    def test_first_attempt_has_no_delay(self):
        policy = RetryPolicy(base_delay_seconds=1.0)
        assert policy.delay_for_attempt(1) == 0.0

    def test_delay_increases_with_backoff_multiplier(self):
        policy = RetryPolicy(base_delay_seconds=1.0, backoff_multiplier=2.0)
        assert policy.delay_for_attempt(2) == 1.0
        assert policy.delay_for_attempt(3) == 2.0

    def test_zero_base_delay_never_sleeps(self):
        policy = RetryPolicy(base_delay_seconds=0.0)
        assert policy.delay_for_attempt(5) == 0.0
