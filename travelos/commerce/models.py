from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ProductType(str, Enum):
    FLIGHT = "FLIGHT"
    ACCOMMODATION = "ACCOMMODATION"
    EXPERIENCE = "EXPERIENCE"


class MerchantOfRecord(str, Enum):
    TRALVANA = "TRALVANA"
    SUPPLIER = "SUPPLIER"
    UNCONFIRMED = "UNCONFIRMED"


class CustomerPaymentMethod(str, Enum):
    TRALVANA_GATEWAY = "TRALVANA_GATEWAY"
    SUPPLIER_HOSTED = "SUPPLIER_HOSTED"
    UNCONFIRMED = "UNCONFIRMED"


class SupplierSettlementMethod(str, Enum):
    PREFUNDED_BALANCE = "PREFUNDED_BALANCE"
    SUPPLIER_COLLECTS = "SUPPLIER_COLLECTS"
    UNCONFIRMED = "UNCONFIRMED"


class CheckoutReadiness(str, Enum):
    BLOCKED = "BLOCKED"
    EXTERNAL_APPROVAL_PENDING = "EXTERNAL_APPROVAL_PENDING"
    INTEGRATION_PENDING = "INTEGRATION_PENDING"
    READY = "READY"


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("money amount cannot be negative")
        currency = self.currency.strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("currency must be a three-letter ISO code")
        object.__setattr__(self, "currency", currency)


@dataclass(frozen=True, slots=True)
class CommercePolicy:
    supplier: str
    product_type: ProductType
    merchant_of_record: MerchantOfRecord
    customer_payment_method: CustomerPaymentMethod
    supplier_settlement_method: SupplierSettlementMethod
    markup_allowed: bool
    checkout_readiness: CheckoutReadiness
    blocker: str | None = None

    @property
    def checkout_enabled(self) -> bool:
        return self.checkout_readiness is CheckoutReadiness.READY
