from __future__ import annotations

import inspect

import pytest

from travelos.bookings.experience import (
    ExperienceAvailabilityCommand,
    ExperienceBookingCommand,
    ExperienceCancellationCommand,
    ExperienceHoldCommand,
    ExperiencePassengerGroup,
    ExperienceSearchCommand,
)
from travelos.intelligence_gateway.exceptions import ProviderUnavailableError
from travelos.intelligence_gateway.provider_contract import ProviderRequest
from travelos.intelligence_gateway.provider_status import Capability, ProviderStatus
from travelos.live_providers.adapters.viator_experience_provider import (
    DisabledViatorExperienceProvider,
)


def _passengers() -> tuple[ExperiencePassengerGroup, ...]:
    return (ExperiencePassengerGroup(age_band="ADULT", count=2),)


def test_viator_foundation_is_fail_closed_and_has_no_credentials():
    provider = DisabledViatorExperienceProvider()

    assert provider.capability is Capability.EXPERIENCES
    assert provider.health_check() is ProviderStatus.MISCONFIGURED
    assert provider.metadata == {
        "description": "Disabled Viator experiences integration foundation.",
        "enabled": False,
        "external_calls_enabled": False,
        "booking_enabled": False,
        "qualification_required": True,
        "certification_required": True,
    }
    source = inspect.getsource(type(provider)).casefold()
    assert "api-key" not in source
    assert "secret" not in source
    assert "http://" not in source
    assert "https://" not in source


def test_gateway_execution_is_unsupported_and_never_claims_availability():
    provider = DisabledViatorExperienceProvider()
    request = ProviderRequest(
        capability=Capability.EXPERIENCES,
        operation="search",
        params={"destination": "Lagos"},
    )

    assert provider.supports(request) is False
    with pytest.raises(ProviderUnavailableError, match="disabled pending"):
        provider.execute(request)


@pytest.mark.parametrize(
    "operation",
    [
        lambda provider: provider.search(
            ExperienceSearchCommand(
                destination="Lagos",
                start_date="2026-09-15",
                end_date="2026-09-17",
                currency="GBP",
                passenger_groups=_passengers(),
            )
        ),
        lambda provider: provider.check_availability(
            ExperienceAvailabilityCommand(
                product_reference="product",
                option_reference="option",
                travel_date="2026-09-16",
                currency="GBP",
                passenger_groups=_passengers(),
            )
        ),
        lambda provider: provider.create_hold(
            ExperienceHoldCommand(
                availability_reference="availability",
                client_reference="TRALVANA-TEST",
                customer_checkout_intent=True,
            )
        ),
        lambda provider: provider.create_booking(
            ExperienceBookingCommand(
                hold_reference="hold",
                client_reference="TRALVANA-TEST",
                customer_approved=True,
                expected_total=100.0,
                expected_currency="GBP",
            )
        ),
        lambda provider: provider.get_booking("booking"),
        lambda provider: provider.get_voucher("booking"),
        lambda provider: provider.quote_cancellation("booking"),
        lambda provider: provider.cancel_booking(
            ExperienceCancellationCommand(
                supplier_reference="booking",
                reason_reference="reason",
                customer_approved=True,
            )
        ),
    ],
)
def test_every_viator_operation_remains_disabled(operation):
    with pytest.raises(ProviderUnavailableError, match="qualification"):
        operation(DisabledViatorExperienceProvider())
