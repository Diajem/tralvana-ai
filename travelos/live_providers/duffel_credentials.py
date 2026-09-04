"""Resolve per-product Duffel credentials without exposing their values."""

import os

from travelos.intelligence_gateway.secret_reference import SecretReference


def duffel_token_variable(product: str, live: bool) -> str:
    """Dedicated credentials override the legacy shared token, including empty values."""
    dedicated = f"DUFFEL_{product.upper()}_API_TOKEN"
    name = dedicated if dedicated in os.environ else "DUFFEL_API_TOKEN"
    secret = SecretReference(name)
    if not secret.is_present():
        raise ValueError(f"Duffel {product} requires {name} to be set.")
    value = secret.resolve()
    if live and not value.startswith("duffel_live_"):
        raise ValueError(f"Duffel {product} LIVE mode requires a live token in {name}.")
    if not live and value.startswith("duffel_live_"):
        raise ValueError(f"Duffel {product} sandbox mode cannot use a live token in {name}.")
    return name
