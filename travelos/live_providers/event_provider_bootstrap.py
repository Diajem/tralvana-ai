"""Application composition root for Ticketmaster live event discovery."""

from __future__ import annotations

from travelos.config.configuration_manager import config
from travelos.intelligence_gateway.provider_registry import (
    ProviderRegistry,
    provider_registry,
)
from travelos.intelligence_gateway.provider_status import Capability
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.adapters.ticketmaster_event_provider import (
    register_ticketmaster_event_provider,
)
from travelos.live_providers.httpx_transport import HttpxTransport
from travelos.logging.travel_logger import TravelLogger

_logger = TravelLogger.for_service("EventProviderBootstrap")
TICKETMASTER_KEY_ENV_VAR = "TICKETMASTER_API_KEY"


class EventProviderMisconfiguredError(RuntimeError):
    """Raised at startup when live mode lacks its required key."""


def configure_event_provider(registry: ProviderRegistry | None = None) -> None:
    target = registry or provider_registry
    if config.event_provider_mode != "LIVE":
        _logger.info(
            "Event provider mode is MOCK — Ticketmaster not registered",
            mode=config.event_provider_mode,
        )
        return

    key = SecretReference(
        env_var=TICKETMASTER_KEY_ENV_VAR,
        required=True,
        description="Ticketmaster Discovery API consumer key",
    )
    if not key.is_present():
        raise EventProviderMisconfiguredError(
            "TRALVANA_EVENT_PROVIDER_MODE=LIVE requires TICKETMASTER_API_KEY "
            "to be set. See docs/LIVE_EVENT_SEARCH.md."
        )

    already_registered = any(
        provider.provider_name == "ticketmaster_event_provider"
        for provider in target.get_providers(Capability.EVENTS)
    )
    if already_registered:
        return

    register_ticketmaster_event_provider(
        transport=HttpxTransport(),
        registry=target,
    )
    _logger.info("Ticketmaster event provider registered for LIVE mode")
