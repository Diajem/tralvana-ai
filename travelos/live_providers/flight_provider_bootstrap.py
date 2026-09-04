"""
Flight provider composition root (T-038) — the one place that decides,
at application startup, whether Duffel gets registered for real. Not a
second dependency-injection system: this function only calls the
existing `ConfigurationManager`, `SecretReference`, and
`travelos.intelligence_gateway.provider_registry`, exactly the pattern
`travelos/intelligence_gateway/discovery_adapters.py`'s
`register_default_providers()` already established for mock providers.

Called once from `services/api/app/main.py` (the actual composition
root) — never from a route handler, never from `ai/discovery/flights/`
(so the Discovery layer and Trip Brain stay completely unaware this
decision is even being made, per T-038's "avoid changing Trip Brain
architecture" constraint).
"""

from __future__ import annotations

from travelos.config.configuration_manager import config
from travelos.intelligence_gateway.provider_registry import ProviderRegistry, provider_registry
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment
from travelos.live_providers.duffel_credentials import duffel_token_variable
from travelos.live_providers.adapters.duffel_flight_provider import register_duffel_flight_provider
from travelos.live_providers.httpx_transport import HttpxTransport
from travelos.logging.travel_logger import TravelLogger

_logger = TravelLogger.for_service("FlightProviderBootstrap")

DUFFEL_TOKEN_ENV_VAR = "DUFFEL_API_TOKEN"


class FlightProviderMisconfiguredError(RuntimeError):
    """Raised at startup when the selected Duffel mode has no matching token."""


def configure_flight_provider(registry: ProviderRegistry | None = None) -> None:
    """Idempotent-in-intent, like `register_default_providers()` — call
    once at process startup. In MOCK mode (the default) this is a no-op:
    no Transport is constructed, no provider is registered, no
    credential is required, matching "make no network calls" literally.
    In LIVE or LIVE_SANDBOX mode, constructs one shared `HttpxTransport` and
    registers `DuffelFlightProvider` — selection between it and the
    existing mock flight provider is still entirely the Intelligence
    Gateway's job (see `travelos/intelligence_gateway/gateway.py`'s
    per-capability environment resolution), not this function's."""
    target = registry or provider_registry

    if config.flight_provider_mode == "MOCK":
        _logger.info("Flight provider mode is MOCK — Duffel not registered", mode=config.flight_provider_mode)
        return

    live = config.flight_provider_mode == "LIVE"
    try:
        token_env_var = duffel_token_variable("flights", live)
    except ValueError as exc:
        raise FlightProviderMisconfiguredError(str(exc)) from None

    already_registered = any(
        p.provider_name == "duffel_flight_provider" for p in target.get_providers(Capability.FLIGHTS)
    )
    if already_registered:
        _logger.info("duffel_flight_provider already registered — skipping")
        return

    transport = HttpxTransport()
    register_duffel_flight_provider(
        transport=transport, registry=target, token_env_var=token_env_var,
        environment=ProviderEnvironment.PRODUCTION if live else ProviderEnvironment.SANDBOX,
    )
    _logger.info("Duffel flight provider registered", mode=config.flight_provider_mode)
