"""
Failover Policy — if the preferred provider fails, try the next eligible
one, preserving the original failure as a warning rather than discarding
it (docs/CACHING_AND_FAILOVER.md). Deliberately agnostic of retry/rate-
limit/cache mechanics — `gateway.py` supplies `call`, already wrapped
with those concerns, so this stays a small, independently testable loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from travelos.intelligence_gateway.provider_contract import Provider, ProviderRequest
from travelos.intelligence_gateway.provider_result import ProviderResult


@dataclass
class FailoverOutcome:
    result: ProviderResult | None
    provider_used: str | None
    warnings: list[str] = field(default_factory=list)

    @property
    def all_failed(self) -> bool:
        return self.result is None


def run_with_failover(
    providers: list[Provider],
    request: ProviderRequest,
    call: Callable[[Provider, ProviderRequest], ProviderResult],
) -> FailoverOutcome:
    """Try each provider in order until one succeeds. `call` may raise —
    any exception is recorded as a warning and the next provider is
    tried. Returns a result with no `provider_used` only if every
    provider in `providers` failed (including an empty list)."""
    warnings: list[str] = []

    for provider in providers:
        try:
            result = call(provider, request)
        except Exception as exc:
            warnings.append(f"{provider.provider_name} failed: {exc}")
            continue

        if warnings:
            result.warnings = [*warnings, *result.warnings]
        return FailoverOutcome(result=result, provider_used=provider.provider_name, warnings=warnings)

    return FailoverOutcome(result=None, provider_used=None, warnings=warnings)
