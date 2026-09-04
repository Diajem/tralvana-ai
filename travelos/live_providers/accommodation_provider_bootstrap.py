"""Accommodation supplier composition root for Duffel Stays and HBX."""

from __future__ import annotations

from travelos.config.configuration_manager import config
from travelos.intelligence_gateway.provider_registry import ProviderRegistry, provider_registry
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.adapters.duffel_stays_provider import register_duffel_stays_provider
from travelos.live_providers.adapters.hbx_hotels_provider import register_hbx_hotels_provider
from travelos.live_providers.hbx_destination_catalog import (
    HbxDestinationCatalog,
    build_hbx_destination_catalog,
)
from travelos.live_providers.httpx_transport import HttpxTransport
from travelos.live_providers.duffel_credentials import duffel_token_variable
from travelos.live_providers.transport import Transport
from travelos.logging.travel_logger import TravelLogger

_logger = TravelLogger.for_service("AccommodationProviderBootstrap")

DUFFEL_TOKEN_ENV_VAR = "DUFFEL_API_TOKEN"
HBX_API_KEY_ENV_VAR = "HBX_HOTELS_API_KEY"
HBX_SECRET_ENV_VAR = "HBX_HOTELS_SECRET"


class AccommodationProviderMisconfiguredError(RuntimeError):
    """Selected supplier mode cannot start with the configured credentials."""


def configure_accommodation_provider(
    registry: ProviderRegistry | None = None,
    destination_catalog: HbxDestinationCatalog | None = None,
    transport: Transport | None = None,
) -> None:
    target = registry or provider_registry
    mode = config.accommodation_provider_mode
    if mode == "MOCK":
        _logger.info("Accommodation provider mode is MOCK — no live supplier registered", mode=mode)
        return

    wants_duffel = mode in {"LIVE_SANDBOX", "DUFFEL_SANDBOX", "MULTI_SANDBOX", "LIVE"}
    wants_hbx = mode in {"HBX_SANDBOX", "MULTI_SANDBOX"}

    duffel_token_env = DUFFEL_TOKEN_ENV_VAR
    if wants_duffel:
        try:
            duffel_token_env = duffel_token_variable("stays", mode == "LIVE")
        except ValueError as exc:
            raise AccommodationProviderMisconfiguredError(str(exc)) from None
    if wants_hbx:
        missing = [
            name
            for name in (HBX_API_KEY_ENV_VAR, HBX_SECRET_ENV_VAR)
            if not SecretReference(name).is_present()
        ]
        if missing:
            raise AccommodationProviderMisconfiguredError(
                f"TRALVANA_ACCOMMODATION_PROVIDER_MODE={mode} requires " + " and ".join(missing) + "."
            )

    names = {p.provider_name for p in target.get_providers(Capability.ACCOMMODATION)}
    desired_names: set[str] = set()
    if wants_hbx:
        desired_names.add("hbx_hotels_provider")
    if wants_duffel:
        desired_names.add("duffel_stays_provider")
    if desired_names <= names:
        _logger.info("Accommodation suppliers already registered — skipping", mode=mode)
        return
    provider_transport = transport or HttpxTransport()

    if wants_hbx and "hbx_hotels_provider" not in names:
        register_hbx_hotels_provider(
            transport=provider_transport,
            destination_catalog=destination_catalog or build_hbx_destination_catalog(),
            registry=target,
            environment=ProviderEnvironment.SANDBOX,
            priority=10,
        )
        _logger.info("HBX Hotels provider registered for sandbox mode")

    if wants_duffel and "duffel_stays_provider" not in names:
        register_duffel_stays_provider(
            transport=provider_transport,
            registry=target,
            environment=ProviderEnvironment.PRODUCTION if mode == "LIVE" else ProviderEnvironment.SANDBOX,
            token_env_var=duffel_token_env,
            priority=20 if wants_hbx else 10,
        )
        _logger.info("Duffel Stays provider registered", mode=mode)
