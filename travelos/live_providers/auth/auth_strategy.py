"""The common shape every authentication strategy implements."""

from __future__ import annotations

from abc import ABC, abstractmethod


class AuthStrategy(ABC):
    @abstractmethod
    def is_configured(self) -> bool:
        """Whether every secret this strategy needs is present in the
        environment. Never raises, never reads a secret's value — only
        SecretReference.is_present() checks."""
        ...

    @abstractmethod
    def headers(self) -> dict[str, str]:
        """The headers to merge into an outgoing TransportRequest.
        Raises travelos.intelligence_gateway.exceptions.ProviderConfigurationError
        (or a MissingSecretError, its subclass) if not configured — never
        returns a partial or placeholder credential."""
        ...
