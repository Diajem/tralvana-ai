from __future__ import annotations

import pytest

from travelos.intelligence_gateway.provider_contract import ProviderRequest
from travelos.intelligence_gateway.provider_status import Capability
from travelos.live_providers.adapters.hbx_hotels_provider import HbxHotelsProvider
from travelos.live_providers.hbx_destination_catalog import (
    HbxDestination,
    InMemoryHbxDestinationCatalog,
)
from travelos.live_providers.transport import FakeTransport


@pytest.fixture(autouse=True)
def _credentials(monkeypatch):
    monkeypatch.setenv("HBX_HOTELS_API_KEY", "test-key")
    monkeypatch.setenv("HBX_HOTELS_SECRET", "test-secret")


_GLOBAL_DESTINATIONS = [
    ("Lagos, Nigeria", "NG", "LOS"),
    ("Accra, Ghana", "GH", "ACC"),
    ("Nairobi, Kenya", "KE", "NBO"),
    ("Cape Town, South Africa", "ZA", "CPT"),
    ("Paris, France", "FR", "PAR"),
    ("Madrid, Spain", "ES", "MAD"),
    ("New York, United States", "US", "NYC"),
    ("Toronto, Canada", "CA", "YTO"),
    ("Fort William, United Kingdom", "GB", "FTW"),
    ("Banff, Canada", "CA", "BAN"),
]


def _catalog() -> InMemoryHbxDestinationCatalog:
    return InMemoryHbxDestinationCatalog(
        [
            HbxDestination(code=code, name=name.split(",")[0], country_code=country)
            for name, country, code in _GLOBAL_DESTINATIONS
        ]
    )


def _body(currency: str = "EUR", policies: list[dict] | None = None) -> dict:
    return {
        "auditData": {"token": "safe-test-token"},
        "hotels": {
            "hotels": [
                {
                    "code": 100,
                    "name": "Global Test Hotel",
                    "currency": currency,
                    "rooms": [
                        {
                            "code": "DBL",
                            "name": "Double",
                            "rates": [
                                {
                                    "rateKey": "rate-key",
                                    "sellingRate": "360.00",
                                    "cancellationPolicies": policies or [],
                                }
                            ],
                        }
                    ],
                }
            ]
        },
    }


def _request(destination: str, country_code: str, **overrides) -> ProviderRequest:
    params = {
        "destination": destination,
        "country_code": country_code,
        "check_in_date": "2026-11-10",
        "nights": 3,
        "adults": 2,
        "children": 0,
        "child_ages": [],
        "rooms": 1,
    }
    params.update(overrides)
    return ProviderRequest(
        capability=Capability.ACCOMMODATION,
        operation="search",
        params=params,
    )


@pytest.mark.parametrize("destination,country_code,expected_code", _GLOBAL_DESTINATIONS)
def test_hbx_global_and_remote_destinations_use_the_exact_catalogue_code(
    destination, country_code, expected_code
):
    transport = FakeTransport.always_returning(200, _body())
    provider = HbxHotelsProvider(transport=transport, destination_catalog=_catalog())

    result = provider.execute(_request(destination, country_code))

    assert transport.sent_requests[0].json_body["destination"] == {
        "code": expected_code
    }
    assert result.provider_name == "hbx_hotels_provider"
    assert result.data[0]["_provider_source"] == "hbx_hotels"
    assert "duffel" not in repr(result).casefold()


def test_family_child_ages_are_distributed_across_multiple_rooms():
    transport = FakeTransport.always_returning(200, _body())
    provider = HbxHotelsProvider(transport=transport, destination_catalog=_catalog())

    provider.execute(
        _request(
            "Lagos, Nigeria",
            "NG",
            adults=4,
            children=3,
            child_ages=[4, 8, 13],
            rooms=3,
        )
    )

    assert transport.sent_requests[0].json_body["occupancies"] == [
        {"rooms": 1, "adults": 2, "children": 1, "paxes": [{"type": "CH", "age": 4}]},
        {"rooms": 1, "adults": 1, "children": 1, "paxes": [{"type": "CH", "age": 8}]},
        {"rooms": 1, "adults": 1, "children": 1, "paxes": [{"type": "CH", "age": 13}]},
    ]


@pytest.mark.parametrize("currency", ["GBP", "EUR", "USD", "CAD", "ZAR"])
def test_hbx_preserves_supplier_currency_and_cancellation_policy(currency):
    policies = [
        {"amount": "0.00", "from": "2026-11-01T00:00:00+00:00"},
        {"amount": "360.00", "from": "2026-11-09T00:00:00+00:00"},
    ]
    provider = HbxHotelsProvider(
        transport=FakeTransport.always_returning(200, _body(currency, policies)),
        destination_catalog=_catalog(),
    )

    option = provider.execute(_request("Toronto, Canada", "CA")).data[0]

    assert option["currency"] == currency
    assert option["total_price"] == 360.0
    assert option["nightly_price"] == 120.0
    assert option["cancellation_policies"] == policies
