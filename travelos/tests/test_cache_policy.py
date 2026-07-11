"""Cache key generation, TTL, stale-data indication, bypass — docs/CACHING_AND_FAILOVER.md."""

from __future__ import annotations

import time

from travelos.intelligence_gateway.cache_policy import (
    DEFAULT_TTL_SECONDS,
    InMemoryCachePolicy,
    build_cache_key,
)
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import Capability, ProviderStatus


def _result() -> ProviderResult:
    return ProviderResult(
        provider_name="p", capability=Capability.FLIGHTS, status=ProviderStatus.AVAILABLE, data={"x": 1},
    )


class TestCacheKeyGeneration:
    def test_same_params_produce_same_key(self):
        k1 = build_cache_key(Capability.FLIGHTS, "search", {"a": 1, "b": 2})
        k2 = build_cache_key(Capability.FLIGHTS, "search", {"b": 2, "a": 1})  # different order
        assert k1 == k2

    def test_different_params_produce_different_keys(self):
        k1 = build_cache_key(Capability.FLIGHTS, "search", {"a": 1})
        k2 = build_cache_key(Capability.FLIGHTS, "search", {"a": 2})
        assert k1 != k2

    def test_different_capability_produces_different_key(self):
        k1 = build_cache_key(Capability.FLIGHTS, "search", {"a": 1})
        k2 = build_cache_key(Capability.WEATHER, "search", {"a": 1})
        assert k1 != k2

    def test_different_operation_produces_different_key(self):
        k1 = build_cache_key(Capability.WEATHER, "month", {"a": 1})
        k2 = build_cache_key(Capability.WEATHER, "year", {"a": 1})
        assert k1 != k2


class TestCacheHitAndMiss:
    def test_miss_on_empty_cache(self):
        cache = InMemoryCachePolicy()
        assert cache.get("missing-key") is None

    def test_hit_after_set(self):
        cache = InMemoryCachePolicy()
        result = _result()
        cache.set("key", result, ttl_seconds=60)
        assert cache.get("key") is result

    def test_set_stamps_expires_at_on_the_result(self):
        cache = InMemoryCachePolicy()
        result = _result()
        cache.set("key", result, ttl_seconds=60)
        assert result.expires_at is not None


class TestTTLExpiry:
    def test_entry_not_returned_after_ttl_elapses(self):
        cache = InMemoryCachePolicy()
        cache.set("key", _result(), ttl_seconds=0.01)
        time.sleep(0.02)
        assert cache.get("key") is None

    def test_is_stale_true_only_after_expiry(self):
        cache = InMemoryCachePolicy()
        cache.set("key", _result(), ttl_seconds=0.01)
        assert cache.is_stale("key") is False
        time.sleep(0.02)
        assert cache.is_stale("key") is True

    def test_get_stale_returns_expired_entry_marked_stale(self):
        cache = InMemoryCachePolicy()
        cache.set("key", _result(), ttl_seconds=0.01)
        time.sleep(0.02)
        stale = cache.get_stale("key")
        assert stale is not None
        assert stale.stale is True

    def test_get_stale_returns_none_for_never_cached_key(self):
        cache = InMemoryCachePolicy()
        assert cache.get_stale("never-set") is None


class TestCapabilitySpecificTTLDefaults:
    def test_flights_ttl_is_short(self):
        cache = InMemoryCachePolicy()
        assert cache.ttl_for(Capability.FLIGHTS) == DEFAULT_TTL_SECONDS[Capability.FLIGHTS]
        assert cache.ttl_for(Capability.FLIGHTS) <= 600

    def test_visa_ttl_is_longer_than_flights(self):
        cache = InMemoryCachePolicy()
        assert cache.ttl_for(Capability.VISA) > cache.ttl_for(Capability.FLIGHTS)

    def test_destinations_ttl_is_longer_than_flights(self):
        cache = InMemoryCachePolicy()
        assert cache.ttl_for(Capability.DESTINATIONS) > cache.ttl_for(Capability.FLIGHTS)

    def test_ttl_override_takes_precedence(self):
        cache = InMemoryCachePolicy(ttl_overrides={Capability.FLIGHTS: 999})
        assert cache.ttl_for(Capability.FLIGHTS) == 999

    def test_every_capability_has_a_default_ttl(self):
        cache = InMemoryCachePolicy()
        for capability in Capability:
            assert cache.ttl_for(capability) > 0


class TestCacheBypassAndClear:
    def test_clear_removes_all_entries(self):
        cache = InMemoryCachePolicy()
        cache.set("key", _result(), ttl_seconds=60)
        cache.clear()
        assert cache.get("key") is None

    def test_disabled_cache_flag_is_readable(self):
        cache = InMemoryCachePolicy(enabled=False)
        assert cache.enabled is False
