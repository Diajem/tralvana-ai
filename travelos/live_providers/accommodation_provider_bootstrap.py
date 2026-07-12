"""
Accommodation provider composition root (T-039) — the one place that
decides, at application startup, whether Duffel Stays gets registered
for real. Mirrors travelos/live_providers/flight_provider_bootstrap.py
(T-038) exactly: not a second dependency-injection system, only calls
the existing ConfigurationManager, SecretReference, and
travelos.intelligence_gateway.provider_registry.

Called once from services/api/app/main.py (the actual composition
root) — never from a route handler, never from
ai/discovery/accommodation/ (so the Discovery layer and Trip Brain stay
completely unaware this decision is even being made).
"""

from __future__ import annotations

from travelos.config.configuration_manager import config
from travelos.intelligence_gateway.provider_registry import ProviderRegistry, provider_registry
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.adapters.duffel_stays_provider import register_duffel_stays_provider
from travelos.live_providers.httpx_transport import HttpxTransport
from travelos.logging.travel_logger import TravelLogger

_logger = TravelLogger.for_service("AccommodationProviderBootstrap")

DUFFEL_TOKEN_ENV_VAR = "DUFFEL_API_TOKEN"


class AccommodationProviderMisconfiguredError(RuntimeError):
    """Raised at startup — never at request time — when
    TRALVANA_ACCOMMODATION_PROVIDER_MODE=LIVE_SANDBOX but DUFFEL_API_TOKEN
    isn't set. Fails the application process immediately rather than
    starting in a mode that can never actually serve a live search."""


def configure_accommodation_provider(registry: ProviderRegistry | None = None) -> None:
    """Idempotent-in-intent — call once at process startup. In MOCK mode
    (the default) this is a no-op: no Transport is constructed, no
    provider is registered, no credential is required. In LIVE_SANDBOX
    mode, constructs one shared HttpxTransport and registers
    DuffelStaysProvider — selection between it and the existing mock
    accommodation provider is still entirely the Intelligence Gateway's
    job (per-capability environment resolution,
    travelos/intelligence_gateway/gateway.py), not this function's.

    Note (T-039): even with DUFFEL_API_TOKEN present and this function
    successfully registering DuffelStaysProvider, a live search may
    still fail with a 403 if Duffel Stays itself isn't enabled on the
    account — that is a per-request provider failure
    (LiveAccommodationSearchUnavailableError), not a startup
    misconfiguration, since a valid token for Flights doesn't imply
    Stays access. See docs/DUFFEL_STAYS_INTEGRATION.md."""
    target = registry or provider_registry

    if config.accommodation_provider_mode != "LIVE_SANDBOX":
        _logger.info(
            "Accommodation provider mode is MOCK — Duffel Stays not registered",
            mode=config.accommodation_provider_mode,
        )
        return

    token = SecretReference(env_var=DUFFEL_TOKEN_ENV_VAR, required=True, description="Duffel API token (Stays)")
    if not token.is_present():
        raise AccommodationProviderMisconfiguredError(
            "TRALVANA_ACCOMMODATION_PROVIDER_MODE=LIVE_SANDBOX requires DUFFEL_API_TOKEN to be set. "
            "See docs/LIVE_ACCOMMODATION_SEARCH.md."
        )

    already_registered = any(
        p.provider_name == "duffel_stays_provider" for p in target.get_providers(Capability.ACCOMMODATION)
    )
    if already_registered:
        _logger.info("duffel_stays_provider already registered — skipping")
        return

    transport = HttpxTransport()
    register_duffel_stays_provider(transport=transport, registry=target, environment=ProviderEnvironment.SANDBOX)
    _logger.info("Duffel Stays provider registered for LIVE_SANDBOX mode")
