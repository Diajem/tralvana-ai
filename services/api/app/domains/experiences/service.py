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

# Viator returns ISO country codes, while travellers normally type country
# names and familiar abbreviations.  Keep this deliberately explicit: a
# missing alias should fail closed instead of letting a similarly named city
# in another country leak into a plan.
_COUNTRY_ALIASES = {
    "australia": "AU",
    "austria": "AT",
    "canada": "CA",
    "croatia": "HR",
    "france": "FR",
    "germany": "DE",
    "ireland": "IE",
    "italy": "IT",
    "jamaica": "JM",
    "japan": "JP",
    "mexico": "MX",
    "netherlands": "NL",
    "new zealand": "NZ",
    "south africa": "ZA",
    "spain": "ES",
    "uae": "AE",
    "u a e": "AE",
    "united arab emirates": "AE",
    "uk": "GB",
    "u k": "GB",
    "united kingdom": "GB",
    "great britain": "GB",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "usa": "US",
    "u s a": "US",
    "us": "US",
    "u s": "US",
    "united states": "US",
    "united states of america": "US",
}


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
            "country_code": self._destination_country_code(match),
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
        place_names, requested_country = _requested_destination(requested)
        candidates = [
            item
            for item in destinations
            if _destination_name_variants(item["name"]) & place_names
        ]
        if requested_country:
            candidates = [
                item
                for item in candidates
                if self._destination_country_code(item) == requested_country
            ]
        if not candidates:
            raise ValueError(f"Viator destination not found: {requested}")

        city_candidates = [
            item for item in candidates if item.get("type", "").upper() == "CITY"
        ]
        if city_candidates:
            candidates = city_candidates

        # Multiple exact city matches without a usable country are unsafe
        # (Sydney AU/CA, Cambridge GB/US, and similar cases).  Never guess.
        unique_ids = {item["destination_id"] for item in candidates}
        if len(unique_ids) != 1:
            raise ValueError(f"Viator destination is ambiguous: {requested}")
        return candidates[0]

    def _destination_country_code(self, destination: dict[str, str]) -> str:
        """Resolve an item's country through its own data or parent chain."""
        by_id = {item["destination_id"]: item for item in self._destinations}
        current = destination
        visited: set[str] = set()
        while current:
            country_code = str(current.get("country_code") or "").upper()
            if country_code:
                return country_code
            if current.get("type", "").upper() == "COUNTRY":
                inferred = _COUNTRY_ALIASES.get(_normalise(current.get("name", "")))
                if inferred:
                    return inferred
            parent_id = str(current.get("parent_destination_id") or "")
            if not parent_id or parent_id in visited:
                break
            visited.add(parent_id)
            current = by_id.get(parent_id, {})
        return ""

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


def _destination_name_variants(value: str) -> set[str]:
    normalised = _normalise(value)
    variants = {normalised}
    if normalised.endswith(" city"):
        variants.add(normalised.removesuffix(" city"))
    else:
        variants.add(f"{normalised} city")
    return variants


def _requested_destination(value: str) -> tuple[set[str], str | None]:
    components = [
        _normalise(component)
        for component in re.split(r"[,;/]", value)
        if _normalise(component)
    ]
    normalised = _normalise(value)
    requested_country = next(
        (
            country_code
            for alias, country_code in _COUNTRY_ALIASES.items()
            if alias in components or normalised == alias
        ),
        None,
    )
    place_components = [
        component
        for component in components
        if _COUNTRY_ALIASES.get(component) is None
    ]
    primary = place_components[0] if place_components else normalised
    return _destination_name_variants(primary), requested_country


experience_discovery_service = ExperienceDiscoveryService()
