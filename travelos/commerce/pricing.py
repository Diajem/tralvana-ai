from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from travelos.commerce.models import CommercePolicy, Money


_MINOR_UNIT = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class PriceBreakdown:
    supplier_net: Money
    markup: Money
    taxes_and_fees: Money
    customer_total: Money


def build_customer_price(
    *,
    policy: CommercePolicy,
    supplier_net: Money,
    markup: Money,
    taxes_and_fees: Money,
) -> PriceBreakdown:
    currencies = {supplier_net.currency, markup.currency, taxes_and_fees.currency}
    if len(currencies) != 1:
        raise ValueError("all price components must use the same currency")
    if markup.amount and not policy.markup_allowed:
        raise ValueError(f"markup is not allowed for {policy.supplier} {policy.product_type.value}")

    total = (supplier_net.amount + markup.amount + taxes_and_fees.amount).quantize(
        _MINOR_UNIT,
        rounding=ROUND_HALF_UP,
    )
    return PriceBreakdown(
        supplier_net=supplier_net,
        markup=markup,
        taxes_and_fees=taxes_and_fees,
        customer_total=Money(total, supplier_net.currency),
    )
