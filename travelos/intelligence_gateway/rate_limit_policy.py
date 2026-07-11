"""
In-memory, per-provider rate-limit tracking suitable for development and
tests (docs/CACHING_AND_FAILOVER.md). No distributed rate limiter — a
plain dict, reset on a fixed window. A provider with no configured limit
is treated as unlimited (the default for every mock provider today).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class RateLimitState:
    limit: int
    remaining: int
    window_seconds: int
    reset_at: datetime


class RateLimitTracker:
    def __init__(self) -> None:
        self._configs: dict[str, tuple[int, int]] = {}
        self._state: dict[str, RateLimitState] = {}

    def configure(self, provider_name: str, limit: int, window_seconds: int) -> None:
        self._configs[provider_name] = (limit, window_seconds)
        self._state.pop(provider_name, None)  # re-derive on next check

    def check(self, provider_name: str) -> bool:
        """True if a call is currently allowed."""
        state = self._current_state(provider_name)
        return state is None or state.remaining > 0

    def record_call(self, provider_name: str) -> None:
        state = self._current_state(provider_name)
        if state is not None and state.remaining > 0:
            state.remaining -= 1

    def status_for(self, provider_name: str) -> RateLimitState | None:
        """None means unconfigured (unlimited)."""
        return self._current_state(provider_name)

    def reset(self) -> None:
        self._state.clear()

    def _current_state(self, provider_name: str) -> RateLimitState | None:
        if provider_name not in self._configs:
            return None
        limit, window_seconds = self._configs[provider_name]
        state = self._state.get(provider_name)
        now = datetime.now(timezone.utc)
        if state is None or now >= state.reset_at:
            state = RateLimitState(
                limit=limit, remaining=limit, window_seconds=window_seconds,
                reset_at=now + timedelta(seconds=window_seconds),
            )
            self._state[provider_name] = state
        return state
