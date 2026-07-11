"""
In-memory cache abstraction for provider results (docs/CACHING_AND_FAILOVER.md).
No Redis, no external cache — a plain dict, matching every other
in-memory store already in this codebase (ConversationSession's
_SessionStore, the in-memory Goal/Trip repositories).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import Capability

# Suggested TTL categories (docs/CACHING_AND_FAILOVER.md): flights and
# accommodation change fastest (short); weather and events are medium;
# visa rules and destination data change slowest (longer, but every
# result still carries its own `retrieved_at`/`expires_at` so staleness
# is always visible, never silent).
DEFAULT_TTL_SECONDS: dict[Capability, int] = {
    Capability.FLIGHTS: 300,          # 5 min — short
    Capability.ACCOMMODATION: 300,    # 5 min — short
    Capability.CURRENCY: 300,         # 5 min — short
    Capability.WEATHER: 1800,         # 30 min — medium
    Capability.EVENTS: 900,           # 15 min
    Capability.BUDGET: 900,           # 15 min
    Capability.MAPS: 3600,            # 1 hour — longer
    Capability.DESTINATIONS: 3600,    # 1 hour — longer
    Capability.VISA: 86400,           # 24 hours — longer, clearly timestamped
}
_FALLBACK_TTL_SECONDS = 300


def build_cache_key(capability: Capability, operation: str, params: dict[str, Any]) -> str:
    normalized = json.dumps(params, sort_keys=True, default=str)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return f"{capability.value}:{operation}:{digest}"


@dataclass
class _CacheEntry:
    result: ProviderResult
    expires_at: datetime


class InMemoryCachePolicy:
    def __init__(self, enabled: bool = True, ttl_overrides: dict[Capability, int] | None = None) -> None:
        self.enabled = enabled
        self._ttl_overrides = ttl_overrides or {}
        self._store: dict[str, _CacheEntry] = {}

    def ttl_for(self, capability: Capability) -> int:
        if capability in self._ttl_overrides:
            return self._ttl_overrides[capability]
        return DEFAULT_TTL_SECONDS.get(capability, _FALLBACK_TTL_SECONDS)

    def get(self, key: str) -> ProviderResult | None:
        """Fresh entries only — expired entries are not returned (use
        get_stale() for graceful degradation when every provider fails)."""
        entry = self._store.get(key)
        if entry is None or self._is_expired(entry):
            return None
        return entry.result

    def get_stale(self, key: str) -> ProviderResult | None:
        """Returns the last cached value even past its TTL, marked
        `.stale = True` — used only when every provider has just failed
        and something is better than nothing, never as a substitute for
        a fresh call under normal conditions."""
        entry = self._store.get(key)
        if entry is None:
            return None
        if self._is_expired(entry):
            entry.result.stale = True
        return entry.result

    def set(self, key: str, result: ProviderResult, ttl_seconds: int) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        result.expires_at = expires_at.isoformat()
        self._store[key] = _CacheEntry(result=result, expires_at=expires_at)

    def is_stale(self, key: str) -> bool:
        entry = self._store.get(key)
        return entry is not None and self._is_expired(entry)

    def clear(self) -> None:
        self._store.clear()

    @staticmethod
    def _is_expired(entry: _CacheEntry) -> bool:
        return datetime.now(timezone.utc) >= entry.expires_at
