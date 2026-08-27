"""Explicit, offline HBX Content API destination synchronisation.

This code is never invoked from a customer search or application startup.
HBX Content API data is static catalogue data and is loaded into Tralvana's
database in bounded pages so evaluation quota is preserved for real testing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from travelos.intelligence_gateway.exceptions import (
    ProviderAuthenticationError,
    ProviderRateLimitedError,
    ProviderResponseError,
    ProviderUnavailableError,
)
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.auth.hbx_signature_auth import HbxSignatureAuthStrategy
from travelos.live_providers.hbx_destination_catalog import HbxDestination, HbxDestinationCatalog
from travelos.live_providers.transport import Transport, TransportRequest

_HBX_CONTENT_TEST_URL = "https://api.test.hotelbeds.com/hotel-content-api/1.0"
_HBX_CONTENT_PRODUCTION_URL = "https://api.hotelbeds.com/hotel-content-api/1.0"


@dataclass(frozen=True)
class HbxContentSyncResult:
    pages_requested: int
    destinations_received: int
    destinations_upserted: int
    next_index: int
    complete: bool


class HbxDestinationContentSync:
    def __init__(
        self,
        transport: Transport,
        catalog: HbxDestinationCatalog,
        *,
        production: bool = False,
        api_key_env_var: str = "HBX_HOTELS_API_KEY",
        secret_env_var: str = "HBX_HOTELS_SECRET",
    ) -> None:
        self._transport = transport
        self._catalog = catalog
        self._base_url = _HBX_CONTENT_PRODUCTION_URL if production else _HBX_CONTENT_TEST_URL
        self._auth = HbxSignatureAuthStrategy(
            api_key=SecretReference(api_key_env_var, description="HBX Hotels API key"),
            shared_secret=SecretReference(secret_env_var, description="HBX Hotels shared secret"),
        )

    def sync(
        self,
        *,
        start_index: int = 1,
        page_size: int = 1000,
        max_pages: int = 20,
        language: str = "ENG",
    ) -> HbxContentSyncResult:
        if start_index < 1:
            raise ValueError("start_index must be at least 1")
        if page_size < 1 or page_size > 1000:
            raise ValueError("page_size must be between 1 and 1000")
        if max_pages < 1 or max_pages > 50:
            raise ValueError("max_pages must be between 1 and 50")

        next_index = start_index
        pages_requested = 0
        received = 0
        upserted = 0
        complete = False

        for _ in range(max_pages):
            end_index = next_index + page_size - 1
            body = self._request_page(next_index, end_index, language)
            destinations, total, raw_count = _parse_destination_page(body)
            pages_requested += 1
            received += len(destinations)
            if destinations:
                upserted += self._catalog.upsert_many(destinations)

            next_index += raw_count
            if raw_count == 0 or raw_count < page_size or (total is not None and next_index > total):
                complete = True
                break

        return HbxContentSyncResult(
            pages_requested=pages_requested,
            destinations_received=received,
            destinations_upserted=upserted,
            next_index=next_index,
            complete=complete,
        )

    def _request_page(self, start_index: int, end_index: int, language: str) -> dict[str, Any]:
        response = self._transport.send(
            TransportRequest(
                method="GET",
                url=f"{self._base_url}/locations/destinations",
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    **self._auth.headers(),
                },
                query_params={
                    "fields": "all",
                    "language": language,
                    "from": str(start_index),
                    "to": str(end_index),
                    "useSecondaryLanguage": "false",
                },
            )
        )
        if response.status_code in (401, 403):
            raise ProviderAuthenticationError("HBX rejected the Content API credentials or access")
        if response.status_code == 429:
            raise ProviderRateLimitedError("HBX Content API quota reached")
        if not 200 <= response.status_code < 300:
            raise ProviderUnavailableError(f"HBX Content API returned HTTP {response.status_code}")
        if not isinstance(response.body, dict):
            raise ProviderResponseError("HBX Content API returned a non-object response")
        return response.body


def _parse_destination_page(body: dict[str, Any]) -> tuple[list[HbxDestination], int | None, int]:
    container = body.get("destinations")
    total: int | None = None
    if isinstance(container, dict):
        raw_destinations = container.get("destinations")
        raw_total = container.get("total")
        total = int(raw_total) if raw_total is not None else None
    else:
        raw_destinations = container
        raw_total = body.get("total")
        total = int(raw_total) if raw_total is not None else None
    if not isinstance(raw_destinations, list):
        raise ProviderResponseError("HBX Content API response missing destinations")

    parsed: list[HbxDestination] = []
    for item in raw_destinations:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or "").strip()
        name = str(item.get("name") or "").strip()
        country_code = str(item.get("countryCode") or "").strip().upper()
        if not code or not name or len(country_code) != 2:
            continue
        zones = item.get("zones") if isinstance(item.get("zones"), list) else []
        parsed.append(HbxDestination(code=code, name=name, country_code=country_code, zones=tuple(zones)))
    return parsed, total, len(raw_destinations)
