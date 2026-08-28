"""Disabled Viator adapter foundation.

This class fixes Tralvana's provider-neutral boundary before qualification.
It intentionally has no endpoint URLs, authentication references or network
implementation. Every operation fails closed until a later, reviewed task
adds approved sandbox credentials and the certified partner flow.
"""

from __future__ import annotations

from typing import Any, NoReturn

from travelos.bookings.experience import (
    ExperienceAvailabilityCommand,
    ExperienceAvailabilityQuote,
    ExperienceBooking,
    ExperienceBookingCommand,
    ExperienceCancellation,
    ExperienceCancellationCommand,
    ExperienceCancellationQuote,
    ExperienceHold,
    ExperienceHoldCommand,
    ExperienceSearchCommand,
)
from travelos.intelligence_gateway.exceptions import ProviderUnavailableError
from travelos.intelligence_gateway.provider_contract import Provider, ProviderRequest
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import (
    Capability,
    ProviderEnvironment,
    ProviderStatus,
)


class DisabledViatorExperienceProvider(Provider):
    """Non-operational contract adapter; never performs external I/O."""

    @property
    def provider_name(self) -> str:
        return "viator_experience_provider"

    @property
    def capability(self) -> Capability:
        return Capability.EXPERIENCES

    @property
    def environment(self) -> ProviderEnvironment:
        return ProviderEnvironment.SANDBOX

    @property
    def priority(self) -> int:
        return 10

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "description": "Disabled Viator experiences integration foundation.",
            "enabled": False,
            "external_calls_enabled": False,
            "booking_enabled": False,
            "qualification_required": True,
            "certification_required": True,
        }

    def health_check(self) -> ProviderStatus:
        return ProviderStatus.MISCONFIGURED

    def supports(self, request: ProviderRequest) -> bool:
        return False

    def execute(self, request: ProviderRequest) -> ProviderResult:
        self._disabled()

    def search(self, command: ExperienceSearchCommand) -> tuple[dict, ...]:
        self._disabled()

    def check_availability(
        self, command: ExperienceAvailabilityCommand
    ) -> ExperienceAvailabilityQuote:
        self._disabled()

    def create_hold(self, command: ExperienceHoldCommand) -> ExperienceHold:
        self._disabled()

    def create_booking(self, command: ExperienceBookingCommand) -> ExperienceBooking:
        self._disabled()

    def get_booking(self, supplier_reference: str) -> ExperienceBooking:
        self._disabled()

    def get_voucher(self, supplier_reference: str) -> bytes:
        self._disabled()

    def quote_cancellation(
        self, supplier_reference: str
    ) -> ExperienceCancellationQuote:
        self._disabled()

    def cancel_booking(
        self, command: ExperienceCancellationCommand
    ) -> ExperienceCancellation:
        self._disabled()

    def _disabled(self) -> NoReturn:
        raise ProviderUnavailableError(
            "Viator integration is disabled pending partner qualification, "
            "sandbox credentials and certification"
        )
