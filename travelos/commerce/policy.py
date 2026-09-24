from __future__ import annotations

from travelos.commerce.models import (
    CheckoutReadiness,
    CommercePolicy,
    CustomerPaymentMethod,
    MerchantOfRecord,
    ProductType,
    SupplierSettlementMethod,
)


_POLICIES = {
    ("ratehawk", ProductType.ACCOMMODATION): CommercePolicy(
        supplier="ratehawk",
        product_type=ProductType.ACCOMMODATION,
        merchant_of_record=MerchantOfRecord.TRALVANA,
        customer_payment_method=CustomerPaymentMethod.TRALVANA_GATEWAY,
        supplier_settlement_method=SupplierSettlementMethod.PREFUNDED_BALANCE,
        markup_allowed=True,
        checkout_readiness=CheckoutReadiness.EXTERNAL_APPROVAL_PENDING,
        blocker="RateHawk API approval, credentials and certification are pending.",
    ),
    ("viator", ProductType.EXPERIENCE): CommercePolicy(
        supplier="viator",
        product_type=ProductType.EXPERIENCE,
        merchant_of_record=MerchantOfRecord.SUPPLIER,
        customer_payment_method=CustomerPaymentMethod.SUPPLIER_HOSTED,
        supplier_settlement_method=SupplierSettlementMethod.SUPPLIER_COLLECTS,
        markup_allowed=False,
        checkout_readiness=CheckoutReadiness.EXTERNAL_APPROVAL_PENDING,
        blocker="Viator Full + Booking API activation and certification are pending.",
    ),
    ("duffel", ProductType.FLIGHT): CommercePolicy(
        supplier="duffel",
        product_type=ProductType.FLIGHT,
        merchant_of_record=MerchantOfRecord.UNCONFIRMED,
        customer_payment_method=CustomerPaymentMethod.UNCONFIRMED,
        supplier_settlement_method=SupplierSettlementMethod.UNCONFIRMED,
        markup_allowed=False,
        checkout_readiness=CheckoutReadiness.BLOCKED,
        blocker="Duffel must confirm the approved live payment and settlement method.",
    ),
}


def commerce_policy_for(supplier: str, product_type: ProductType) -> CommercePolicy:
    key = (supplier.strip().casefold(), product_type)
    try:
        return _POLICIES[key]
    except KeyError as exc:
        raise ValueError("unsupported supplier and product commerce policy") from exc
