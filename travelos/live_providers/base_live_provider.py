"""
BaseLiveProvider — the reusable base every future live external provider
must extend (docs/LIVE_PROVIDER_FRAMEWORK.md, docs/LIVE_PROVIDER_ADAPTER_GUIDE.md).

Implements `travelos.intelligence_gateway.provider_contract.Provider`
concretely for `execute()` as a template method — a concrete subclass
only ever implements `build_request()` and `parse_response()` (the
vendor-specific parts); everything else (auth header injection, HTTP
status mapping, retry-relevant error classification, metrics, tracing,
logging) is handled once, here, for every live provider.

    execute() lifecycle:
        validate -> authenticate -> build_request -> send_request
        -> (check HTTP status) -> parse_response -> ProviderResult

Because this is still a `Provider` subclass, it needs zero changes to
`travelos/intelligence_gateway/gateway.py`, `provider_registry.py`, or
`provider_selector.py` to be registered, selected, retried, and failed
over exactly like a mock provider — see
docs/ADR/ADR-021-live-provider-framework.md.
"""

from __future__ import annotations

import time
import uuid
from abc import abstractmethod
from datetime import datetime, timezone

from travelos.intelligence_gateway.exceptions import (
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitedError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderValidationError,
)
from travelos.intelligence_gateway.provider_contract import Provider, ProviderRequest
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment, ProviderStatus
from travelos.live_providers.auth.auth_strategy import AuthStrategy
from travelos.live_providers.health.health_result import ProviderHealthResult
from travelos.live_providers.metrics.provider_metrics import ProviderMetricsTracker, provider_metrics
from travelos.live_providers.tracing.request_trace import start_trace
from travelos.live_providers.transport import Transport, TransportRequest, TransportResponse
from travelos.logging.travel_logger import TravelLogger

_logger = TravelLogger.for_service("LiveProvider")

_STATUS_ERROR_MAP: dict[int, type[ProviderError]] = {
    401: ProviderAuthenticationError,
    403: ProviderAuthenticationError,
    408: ProviderTimeoutError,
    429: ProviderRateLimitedError,
}


class BaseLiveProvider(Provider):
    def __init__(
        self,
        provider_name: str,
        capability: Capability,
        environment: ProviderEnvironment,
        transport: Transport,
        auth: AuthStrategy,
        priority: int = 100,
        metrics: ProviderMetricsTracker | None = None,
    ) -> None:
        if environment == ProviderEnvironment.MOCK:
            raise ValueError(
                "BaseLiveProvider environment must be SANDBOX or PRODUCTION — "
                "MOCK stays on the existing Intelligence Gateway mock providers (T-025)."
            )
        self._provider_name = provider_name
        self._capability = capability
        self._environment = environment
        self._transport = transport
        self._auth = auth
        self._priority = priority
        self._metrics = metrics or provider_metrics

    # ------------------------------------------------------------------
    # Provider contract
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def capability(self) -> Capability:
        return self._capability

    @property
    def environment(self) -> ProviderEnvironment:
        return self._environment

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def auth_configured(self) -> bool:
        return self._auth.is_configured()

    def health_check(self) -> ProviderStatus:
        if not self._auth.is_configured():
            return ProviderStatus.MISCONFIGURED
        return ProviderStatus.AVAILABLE

    def health_check_detailed(self) -> ProviderHealthResult:
        """Richer health result than the plain `Provider.health_check()`
        status — not part of the shared `Provider` contract (see this
        package's __init__.py for why); the diagnostics endpoint duck-
        types for it."""
        start = time.monotonic()
        status = self.health_check()
        latency_ms = (time.monotonic() - start) * 1000
        message = "" if status == ProviderStatus.AVAILABLE else "Authentication is not configured."
        return ProviderHealthResult(
            provider_name=self.provider_name,
            capability=self.capability,
            environment=self.environment,
            status=status,
            checked_at=_now_iso(),
            latency_ms=latency_ms,
            message=message,
            metadata={"auth_configured": self._auth.is_configured()},
        )

    # ------------------------------------------------------------------
    # Lifecycle steps a concrete provider must implement
    # ------------------------------------------------------------------

    @abstractmethod
    def build_request(self, request: ProviderRequest) -> TransportRequest:
        """Internal ProviderRequest -> vendor-shaped TransportRequest.
        Never include an auth header here — authenticate() supplies
        those, merged in by execute()."""
        ...

    @abstractmethod
    def parse_response(self, response: TransportResponse) -> ProviderResult:
        """Vendor-shaped TransportResponse -> ProviderResult. Called only
        after a successful HTTP status check — raise ProviderResponseError
        here if the body doesn't have the shape expected."""
        ...

    # ------------------------------------------------------------------
    # Lifecycle steps with a reusable default — override for vendor-specific behaviour
    # ------------------------------------------------------------------

    def authenticate(self) -> dict[str, str]:
        """Returns the headers to merge into the outgoing request. Raises
        if not configured — see AuthStrategy.headers()."""
        return self._auth.headers()

    def send_request(self, transport_request: TransportRequest) -> TransportResponse:
        return self._transport.send(transport_request)

    def map_error(self, error: Exception) -> Exception:
        """Default: pass a known ProviderError through unchanged; wrap
        anything else as ProviderUnavailableError (a safe, retryable
        default). Override for vendor-specific error-body translation."""
        if isinstance(error, ProviderError):
            return error
        return ProviderUnavailableError(f"{self.provider_name}: {error}")

    # ------------------------------------------------------------------
    # The template method
    # ------------------------------------------------------------------

    def execute(self, request: ProviderRequest) -> ProviderResult:
        request_id = str(uuid.uuid4())
        trace = start_trace(self.provider_name, self.capability)
        start = time.monotonic()

        try:
            if not self.supports(request):
                raise ProviderValidationError(
                    f"{self.provider_name} does not support operation '{request.operation}'"
                )

            auth_headers = self.authenticate()
            transport_request = self.build_request(request)
            transport_request.headers = {**transport_request.headers, **auth_headers}

            response = self.send_request(transport_request)
            self._check_response_status(response)
            result = self.parse_response(response)

            latency_ms = (time.monotonic() - start) * 1000
            result.latency_ms = latency_ms
            result.request_id = request_id
            if not result.retrieved_at:
                result.retrieved_at = _now_iso()

            self._metrics.record_success(self.provider_name, latency_ms=latency_ms)
            _logger.info(
                "Live provider executed", provider=self.provider_name, capability=self.capability.value,
                status=result.status.value, latency_ms=round(latency_ms, 1), request_id=request_id,
            )
            trace.finish(status=result.status.value, provider_request_id=result.source_metadata.get("provider_request_id"))
            return result

        except Exception as exc:
            mapped = self.map_error(exc)
            if isinstance(mapped, ProviderRateLimitedError):
                self._metrics.record_rate_limited(self.provider_name)
            else:
                self._metrics.record_failure(self.provider_name)
            _logger.warning(
                "Live provider execution failed", provider=self.provider_name, capability=self.capability.value,
                error_type=type(mapped).__name__, request_id=request_id,
            )
            trace.finish(status="error")
            raise mapped from exc

    # ------------------------------------------------------------------

    def _check_response_status(self, response: TransportResponse) -> None:
        if 200 <= response.status_code < 300:
            return
        error_cls = _STATUS_ERROR_MAP.get(response.status_code)
        if error_cls:
            raise error_cls(f"{self.provider_name} returned HTTP {response.status_code}")
        if response.status_code >= 500:
            raise ProviderUnavailableError(f"{self.provider_name} returned HTTP {response.status_code}")
        raise ProviderResponseError(f"{self.provider_name} returned unexpected HTTP {response.status_code}")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
