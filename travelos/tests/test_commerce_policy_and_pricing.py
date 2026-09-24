from decimal import Decimal

import pytest

from travelos.commerce import (
    CheckoutReadiness,
    CustomerPaymentMethod,
    MerchantOfRecord,
    Money,
    ProductType,
    SupplierSettlementMethod,
    build_customer_price,
    commerce_policy_for,
)


def test_ratehawk_uses_tralvana_gateway_prefunded_settlement_and_markup():
    policy = commerce_policy_for("RateHawk", ProductType.ACCOMMODATION)

    assert policy.merchant_of_record is MerchantOfRecord.TRALVANA
    assert policy.customer_payment_method is CustomerPaymentMethod.TRALVANA_GATEWAY
    assert policy.supplier_settlement_method is SupplierSettlementMethod.PREFUNDED_BALANCE
    assert policy.markup_allowed is True
    assert policy.checkout_readiness is CheckoutReadiness.EXTERNAL_APPROVAL_PENDING
    assert policy.checkout_enabled is False

    price = build_customer_price(
        policy=policy,
        supplier_net=Money(Decimal("200.00"), "gbp"),
        markup=Money(Decimal("30.00"), "GBP"),
        taxes_and_fees=Money(Decimal("5.50"), "GBP"),
    )
    assert price.customer_total == Money(Decimal("235.50"), "GBP")


def test_viator_remains_supplier_mor_and_rejects_tralvana_markup():
    policy = commerce_policy_for("viator", ProductType.EXPERIENCE)

    assert policy.merchant_of_record is MerchantOfRecord.SUPPLIER
    assert policy.customer_payment_method is CustomerPaymentMethod.SUPPLIER_HOSTED
    assert policy.supplier_settlement_method is SupplierSettlementMethod.SUPPLIER_COLLECTS
    assert policy.markup_allowed is False
    assert policy.checkout_enabled is False

    with pytest.raises(ValueError, match="markup is not allowed"):
        build_customer_price(
            policy=policy,
            supplier_net=Money(Decimal("100.00"), "GBP"),
            markup=Money(Decimal("1.00"), "GBP"),
            taxes_and_fees=Money(Decimal("0.00"), "GBP"),
        )


def test_duffel_checkout_stays_blocked_until_live_payment_model_is_confirmed():
    policy = commerce_policy_for("duffel", ProductType.FLIGHT)

    assert policy.merchant_of_record is MerchantOfRecord.UNCONFIRMED
    assert policy.customer_payment_method is CustomerPaymentMethod.UNCONFIRMED
    assert policy.supplier_settlement_method is SupplierSettlementMethod.UNCONFIRMED
    assert policy.markup_allowed is False
    assert policy.checkout_readiness is CheckoutReadiness.BLOCKED
    assert policy.checkout_enabled is False


def test_price_components_must_share_one_currency():
    policy = commerce_policy_for("ratehawk", ProductType.ACCOMMODATION)

    with pytest.raises(ValueError, match="same currency"):
        build_customer_price(
            policy=policy,
            supplier_net=Money(Decimal("100.00"), "GBP"),
            markup=Money(Decimal("10.00"), "USD"),
            taxes_and_fees=Money(Decimal("0.00"), "GBP"),
        )


@pytest.mark.parametrize("amount", [Decimal("-0.01"), Decimal("-100")])
def test_money_rejects_negative_amounts(amount):
    with pytest.raises(ValueError, match="cannot be negative"):
        Money(amount, "GBP")


def test_unknown_supplier_policy_fails_closed():
    with pytest.raises(ValueError, match="unsupported supplier"):
        commerce_policy_for("unknown", ProductType.ACCOMMODATION)
