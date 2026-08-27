"""HBX Group API Suite authentication.

HBX requires an ``Api-key`` header plus an ``X-Signature`` containing the
SHA-256 hex digest of ``api_key + shared_secret + unix_timestamp``.  Secret
values are resolved only while headers are being built and are never stored
on the strategy or exposed through diagnostics.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from travelos.intelligence_gateway.exceptions import ProviderConfigurationError
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.auth.auth_strategy import AuthStrategy


@dataclass
class HbxSignatureAuthStrategy(AuthStrategy):
    api_key: SecretReference
    shared_secret: SecretReference
    clock: Callable[[], float] = field(default=time.time, repr=False)

    def is_configured(self) -> bool:
        return self.api_key.is_present() and self.shared_secret.is_present()

    def headers(self) -> dict[str, str]:
        if not self.is_configured():
            raise ProviderConfigurationError(
                "HBX authentication is not configured — set "
                f"{self.api_key.env_var} and {self.shared_secret.env_var}."
            )

        api_key = self.api_key.resolve()
        shared_secret = self.shared_secret.resolve()
        timestamp = str(int(self.clock()))
        signature = hashlib.sha256(
            f"{api_key}{shared_secret}{timestamp}".encode("utf-8")
        ).hexdigest()
        return {"Api-key": api_key, "X-Signature": signature}
