from __future__ import annotations

import re
import time
from typing import Any

from travelos.intelligence_gateway.provider_contract import ProviderRequest
from travelos.intelligence_gateway.provider_status import Capability
from travelos.live_providers.adapters.viator_experience_provider import (
    ViatorExperienceProvider,
)
from travelos.live_providers.httpx_transport import HttpxTransport

_DESTINATION_TTL_SECONDS = 24 * 60 * 60


class ExperienceDiscoveryService:
    def __init__(self, provider: ViatorExperienceProvider | None = None) -> None:
        self._provider = provider
        self._destinations: list[dict[str, str]] = []
        self._destinations_loaded_at = 0.0

    def search(
        self,
        *,
        destination: str,
        start_date: str | None,
        end_date: str | None,
        currency: str,
        count: int,
    ) -> dict[str, Any]:
        match = self._resolve_destination(destination)
        provider = self._provider_instance()
        result = provider.execute(
            ProviderRequest(
                capability=Capability.EXPERIENCES,
                operation="search",
                params={
                    "destination_id": match["destination_id"],
                    "start_date": start_date,
                    "end_date": end_date,
                    "currency": currency,
                    "count": count,
                },
            )
        )
        return {
            "destination": match["name"],
            "destination_id": match["destination_id"],
            "products": result.data,
            "provider": result.provider_name,
            "environment": provider.environment.value,
            "booking_enabled": False,
            "retrieved_at": result.retrieved_at,
        }

    def details(
        self,
        product_code: str,
        *,
        currency: str,
        include_schedule: bool,
    ) -> dict[str, Any]:
        product = self._execute_product_operation(
            "product_details", product_code, currency
        )
        schedule = (
            self._execute_product_operation(
                "availability_schedule", product_code, currency
            ).data
            if include_schedule
            else None
        )
        return {
            "product": product.data,
            "availability_schedule": schedule,
            "provider": product.provider_name,
            "environment": self._provider_instance().environment.value,
            "booking_enabled": False,
            "retrieved_at": product.retrieved_at,
        }

    def _execute_product_operation(
        self, operation: str, product_code: str, currency: str
    ):
        return self._provider_instance().execute(
            ProviderRequest(
                capability=Capability.EXPERIENCES,
                operation=operation,
                params={"product_code": product_code, "currency": currency},
            )
        )

    def _resolve_destination(self, requested: str) -> dict[str, str]:
        destinations = self._destination_catalogue()
        wanted = _normalise(requested)
        exact = [
            item for item in destinations if _normalise(item["name"]) == wanted
        ]
        candidates = exact or [
            item
            for item in destinations
            if wanted in _normalise(item["name"])
            or _normalise(item["name"]) in wanted
        ]
        if not candidates:
            raise ValueError(f"Viator destination not found: {requested}")
        candidates.sort(
            key=lambda item: (
                item["type"].upper() != "CITY",
                len(item["name"]),
            )
        )
        return candidates[0]

    def _destination_catalogue(self) -> list[dict[str, str]]:
        now = time.monotonic()
        cache_is_fresh = (
            now - self._destinations_loaded_at < _DESTINATION_TTL_SECONDS
        )
        if self._destinations and cache_is_fresh:
            return self._destinations
        result = self._provider_instance().execute(
            ProviderRequest(
                capability=Capability.EXPERIENCES,
                operation="destinations",
            )
        )
        self._destinations = [
            item
            for item in result.data
            if item.get("destination_id") and item.get("name")
        ]
        self._destinations_loaded_at = now
        return self._destinations

    def _provider_instance(self) -> ViatorExperienceProvider:
        if self._provider is None:
            self._provider = ViatorExperienceProvider(HttpxTransport())
        return self._provider


def _normalise(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


experience_discovery_service = ExperienceDiscoveryService()
