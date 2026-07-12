"""
Usage and cost hooks — lightweight, in-memory, per-provider counters
(docs/PROVIDER_OBSERVABILITY.md). Not a billing system: `estimated_cost_usd`
starts at 0.0 and only ever accumulates a value a concrete adapter
explicitly reports via `record_success(..., cost_usd=...)` — this
framework never invents or assumes a per-request price for any vendor.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProviderMetricsSnapshot:
    provider_name: str
    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    rate_limited_count: int = 0
    total_latency_ms: float = 0.0
    last_latency_ms: float = 0.0
    estimated_cost_usd: float = 0.0

    @property
    def average_latency_ms(self) -> float:
        return self.total_latency_ms / self.success_count if self.success_count else 0.0

    @property
    def success_rate(self) -> float:
        return self.success_count / self.request_count if self.request_count else 0.0


class ProviderMetricsTracker:
    def __init__(self) -> None:
        self._snapshots: dict[str, ProviderMetricsSnapshot] = {}

    def record_success(self, provider_name: str, latency_ms: float, cost_usd: float | None = None) -> None:
        snap = self._get_or_create(provider_name)
        snap.request_count += 1
        snap.success_count += 1
        snap.total_latency_ms += latency_ms
        snap.last_latency_ms = latency_ms
        if cost_usd is not None:
            snap.estimated_cost_usd += cost_usd

    def record_failure(self, provider_name: str) -> None:
        snap = self._get_or_create(provider_name)
        snap.request_count += 1
        snap.failure_count += 1

    def record_rate_limited(self, provider_name: str) -> None:
        snap = self._get_or_create(provider_name)
        snap.request_count += 1
        snap.rate_limited_count += 1

    def snapshot_for(self, provider_name: str) -> ProviderMetricsSnapshot | None:
        return self._snapshots.get(provider_name)

    def reset(self) -> None:
        self._snapshots.clear()

    def _get_or_create(self, provider_name: str) -> ProviderMetricsSnapshot:
        return self._snapshots.setdefault(provider_name, ProviderMetricsSnapshot(provider_name=provider_name))


provider_metrics = ProviderMetricsTracker()
