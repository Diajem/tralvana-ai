"""Viator experiences providers.

The live adapter intentionally exposes discovery operations only. Booking,
payment, hold and cancellation remain on the fail-closed provider until
Full + Booking approval and certification are complete.
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
from travelos.intelligence_gateway.exceptions import (
    ProviderResponseError,
    ProviderValidationError,
)
from travelos.intelligence_gateway.provider_contract import Provider, ProviderRequest
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import (
    Capability,
    ProviderEnvironment,
    ProviderStatus,
)
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.auth.api_key_auth import ApiKeyAuthStrategy
from travelos.live_providers.base_live_provider import BaseLiveProvider
from travelos.live_providers.transport import Transport, TransportRequest, TransportResponse

_SANDBOX_BASE_URL = "https://api.sandbox.viator.com/partner"
_PRODUCTION_BASE_URL = "https://api.viator.com/partner"
_DISCOVERY_OPERATIONS = {"search", "product_details", "availability_schedule"}


class ViatorExperienceProvider(BaseLiveProvider):
    """Read-only Viator Partner API adapter for discovery and schedules."""

    def __init__(
        self,
        transport: Transport,
        *,
        environment: ProviderEnvironment = ProviderEnvironment.SANDBOX,
        api_key_env_var: str = "VIATOR_SANDBOX_API_KEY",
        priority: int = 10,
    ) -> None:
        if environment not in (
            ProviderEnvironment.SANDBOX,
            ProviderEnvironment.PRODUCTION,
        ):
            raise ValueError("Viator environment must be SANDBOX or PRODUCTION")
        super().__init__(
            provider_name="viator_experience_provider",
            capability=Capability.EXPERIENCES,
            environment=environment,
            transport=transport,
            auth=ApiKeyAuthStrategy(
                secret=SecretReference(
                    env_var=api_key_env_var,
                    required=True,
                    description="Viator Partner API key",
                ),
                header_name="exp-api-key",
            ),
            priority=priority,
        )

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "description": "Read-only Viator experiences discovery.",
            "enabled": True,
            "external_calls_enabled": True,
            "booking_enabled": False,
            "payment_enabled": False,
            "certification_required": True,
        }

    def supports(self, request: ProviderRequest) -> bool:
        return (
            request.capability == self.capability
            and request.operation in _DISCOVERY_OPERATIONS
        )

    def build_request(self, request: ProviderRequest) -> TransportRequest:
        base_url = (
            _SANDBOX_BASE_URL
            if self.environment == ProviderEnvironment.SANDBOX
            else _PRODUCTION_BASE_URL
        )
        headers = {
            "Accept": "application/json;version=2.0",
            "Accept-Language": str(request.params.get("language", "en")),
        }

        if request.operation == "search":
            destination_id = str(request.params.get("destination_id", "")).strip()
            if not destination_id:
                raise ProviderValidationError(
                    f"{self.provider_name}: destination_id is required"
                )
            currency = str(request.params.get("currency", "GBP")).strip().upper()
            count = int(request.params.get("count", 20))
            if not 1 <= count <= 50:
                raise ProviderValidationError(
                    f"{self.provider_name}: count must be between 1 and 50"
                )
            filtering: dict[str, Any] = {"destination": destination_id}
            for source, target in (("start_date", "startDate"), ("end_date", "endDate")):
                value = str(request.params.get(source, "")).strip()
                if value:
                    filtering[target] = value
            return TransportRequest(
                method="POST",
                url=f"{base_url}/products/search",
                headers={**headers, "Content-Type": "application/json;version=2.0"},
                json_body={
                    "filtering": filtering,
                    "sorting": {"sort": "DEFAULT", "order": "DESCENDING"},
                    "pagination": {"start": 1, "count": count},
                    "currency": currency,
                },
                timeout_seconds=_provider_timeout(),
            )

        product_code = str(request.params.get("product_code", "")).strip()
        if not product_code:
            raise ProviderValidationError(
                f"{self.provider_name}: product_code is required"
            )
        suffix = (
            f"products/{product_code}"
            if request.operation == "product_details"
            else f"availability/schedules/{product_code}"
        )
        return TransportRequest(
            method="GET",
            url=f"{base_url}/{suffix}",
            headers=headers,
            query_params={
                "currency": str(request.params.get("currency", "GBP")).upper()
            },
            timeout_seconds=_provider_timeout(),
        )

    def parse_response(self, response: TransportResponse) -> ProviderResult:
        if not isinstance(response.body, dict):
            raise ProviderResponseError(
                f"{self.provider_name}: response body is not an object"
            )
        body = response.body
        products = body.get("products")
        if products is not None:
            if not isinstance(products, list):
                raise ProviderResponseError(
                    f"{self.provider_name}: products is not a list"
                )
            data: Any = [_map_product_summary(item) for item in products if isinstance(item, dict)]
        else:
            data = body
        return ProviderResult(
            provider_name=self.provider_name,
            capability=self.capability,
            status=ProviderStatus.AVAILABLE,
            data=data,
            confidence=0.9,
            warnings=["Viator sandbox data — booking and payment are disabled."],
            source_metadata={
                "environment": self.environment.value,
                "booking_enabled": False,
                "result_count": len(data) if isinstance(data, list) else 1,
            },
        )


def _map_product_summary(product: dict[str, Any]) -> dict[str, Any]:
    reviews = product.get("reviews") if isinstance(product.get("reviews"), dict) else {}
    pricing = product.get("pricing") if isinstance(product.get("pricing"), dict) else {}
    images = product.get("images") if isinstance(product.get("images"), list) else []
    return {
        "provider": "VIATOR",
        "product_reference": str(product.get("productCode", "")),
        "title": str(product.get("title", "")),
        "description": str(product.get("description", "")),
        "rating": reviews.get("combinedAverageRating"),
        "review_count": reviews.get("totalReviews"),
        "price_from": pricing.get("summary", {}).get("fromPrice")
        if isinstance(pricing.get("summary"), dict)
        else None,
        "currency": pricing.get("currency"),
        "images": images,
        "booking_enabled": False,
    }


def _provider_timeout() -> float:
    from travelos.config.configuration_manager import config

    return config.provider_http_timeout_seconds


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
