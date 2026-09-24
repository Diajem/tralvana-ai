from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.database.base import Base
from app.database.session import create_engine_from_url, create_session_factory
from app.domains.commerce import (
    BookingStatus,
    CheckoutIntent,
    CheckoutStatus,
    PaymentAttempt,
    PaymentStatus,
    RefundRecord,
    RefundStatus,
    SqlAlchemyCommerceRepository,
    SupplierBooking,
)


NOW = datetime(2026, 9, 24, 0, 0, tzinfo=UTC)


def _checkout(**changes):
    values = dict(id="checkout-1", traveller_id="user-1", trip_reference="trip-1", supplier="ratehawk", product_type="ACCOMMODATION", idempotency_key="checkout-key-1", status=CheckoutStatus.CREATED, currency="GBP", customer_total=Decimal("235.50"), supplier_net=Decimal("200.00"), markup=Decimal("30.00"), taxes_and_fees=Decimal("5.50"), created_at=NOW, updated_at=NOW)
    values.update(changes)
    return CheckoutIntent(**values)


@pytest.fixture
def ledger(tmp_path):
    engine = create_engine_from_url(f"sqlite+pysqlite:///{tmp_path / 'commerce.db'}")
    Base.metadata.create_all(engine)
    yield SqlAlchemyCommerceRepository(create_session_factory(engine))
    engine.dispose()


def test_checkout_is_durable_idempotent_and_owner_scoped(ledger):
    checkout = _checkout()
    ledger.add_checkout(checkout)
    assert ledger.get_checkout(checkout.id, "user-1") == checkout
    assert ledger.get_checkout(checkout.id, "another-user") is None
    assert ledger.get_checkout_by_idempotency("user-1", "checkout-key-1") == checkout
    with pytest.raises(IntegrityError):
        ledger.add_checkout(_checkout(id="checkout-2"))


def test_checkout_total_must_match_components():
    with pytest.raises(ValueError, match="must equal"):
        _checkout(customer_total=Decimal("999.00"))


def test_checkout_transition_rejects_skipping_required_steps(ledger):
    ledger.add_checkout(_checkout())
    pending = ledger.transition_checkout("checkout-1", "user-1", CheckoutStatus.PAYMENT_PENDING, NOW + timedelta(seconds=1))
    assert pending.status is CheckoutStatus.PAYMENT_PENDING
    paid = ledger.transition_checkout("checkout-1", "user-1", CheckoutStatus.PAID, NOW + timedelta(seconds=2))
    assert paid.status is CheckoutStatus.PAID
    with pytest.raises(ValueError, match="invalid checkout transition"):
        ledger.transition_checkout("checkout-1", "user-1", CheckoutStatus.BOOKED, NOW + timedelta(seconds=3))


def test_payment_booking_and_refund_references_persist_without_card_data(ledger):
    ledger.add_checkout(_checkout())
    payment = PaymentAttempt(id="payment-1", checkout_id="checkout-1", provider="stripe", provider_reference="pi_safe_reference", idempotency_key="payment-key-1", status=PaymentStatus.SUCCEEDED, amount=Decimal("235.50"), currency="GBP", created_at=NOW, updated_at=NOW)
    booking = SupplierBooking(id="booking-1", checkout_id="checkout-1", supplier="ratehawk", supplier_reference="rh-safe-reference", status=BookingStatus.CONFIRMED, booked_at=NOW, created_at=NOW, updated_at=NOW)
    refund = RefundRecord(id="refund-1", checkout_id="checkout-1", payment_attempt_id="payment-1", supplier_booking_id="booking-1", provider_reference="re_safe_reference", idempotency_key="refund-key-1", status=RefundStatus.REQUESTED, amount=Decimal("50.00"), currency="GBP", reason_code="CUSTOMER_REQUEST", created_at=NOW, updated_at=NOW)
    ledger.add_payment(payment)
    ledger.add_booking(booking)
    ledger.add_refund(refund)
    assert ledger.list_payments("checkout-1") == [payment]
    assert ledger.list_bookings("checkout-1") == [booking]
    assert ledger.list_refunds("checkout-1") == [refund]
    columns = set(Base.metadata.tables["commerce_payment_attempts"].columns)
    assert columns.isdisjoint({"card_number", "pan", "cvv", "cvc", "expiry", "client_secret"})
