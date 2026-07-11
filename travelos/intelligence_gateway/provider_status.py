"""Enums shared across the Intelligence Gateway — see docs/PROVIDER_CONTRACT.md."""

from __future__ import annotations

from enum import Enum


class ProviderEnvironment(str, Enum):
    MOCK = "MOCK"
    SANDBOX = "SANDBOX"
    PRODUCTION = "PRODUCTION"


class ProviderStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    MISCONFIGURED = "MISCONFIGURED"


class Capability(str, Enum):
    """What a provider can be asked to do — one Discovery module domain each."""

    FLIGHTS = "FLIGHTS"
    ACCOMMODATION = "ACCOMMODATION"
    DESTINATIONS = "DESTINATIONS"
    BUDGET = "BUDGET"
    VISA = "VISA"
    WEATHER = "WEATHER"
    MAPS = "MAPS"
    CURRENCY = "CURRENCY"
    EVENTS = "EVENTS"
