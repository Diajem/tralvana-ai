from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domains.commerce.entities import (
    BookingStatus,
    CheckoutIntent,
    CheckoutStatus,
    PaymentAttempt,
    PaymentStatus,
    RefundRecord,
    RefundStatus,
    SupplierBooking,
    validate_checkout_transition,
)
from app.domains.commerce.orm import CheckoutIntentRow, PaymentAttemptRow, RefundRecordRow, SupplierBookingRow


class SqlAlchemyCommerceRepository:
    """Transactional ledger storing references only, never payment credentials."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._sessions = session_factory

    def add_checkout(self, entity: CheckoutIntent) -> CheckoutIntent:
        with self._sessions.begin() as session:
            session.add(CheckoutIntentRow(**_checkout_values(entity)))
        return entity

    def get_checkout(self, checkout_id: str, traveller_id: str) -> CheckoutIntent | None:
        with self._sessions() as session:
            row = session.scalar(select(CheckoutIntentRow).where(CheckoutIntentRow.id == checkout_id, CheckoutIntentRow.traveller_id == traveller_id))
            return _checkout(row) if row else None

    def get_checkout_by_idempotency(self, traveller_id: str, idempotency_key: str) -> CheckoutIntent | None:
        with self._sessions() as session:
            row = session.scalar(select(CheckoutIntentRow).where(CheckoutIntentRow.traveller_id == traveller_id, CheckoutIntentRow.idempotency_key == idempotency_key))
            return _checkout(row) if row else None

    def transition_checkout(self, checkout_id: str, traveller_id: str, target: CheckoutStatus, updated_at) -> CheckoutIntent:
        with self._sessions.begin() as session:
            row = session.scalar(select(CheckoutIntentRow).where(CheckoutIntentRow.id == checkout_id, CheckoutIntentRow.traveller_id == traveller_id))
            if row is None:
                raise ValueError("checkout does not exist")
            validate_checkout_transition(CheckoutStatus(row.status), target)
            row.status = target.value
            row.updated_at = updated_at
            session.flush()
            return _checkout(row)

    def add_payment(self, entity: PaymentAttempt) -> PaymentAttempt:
        with self._sessions.begin() as session:
            session.add(PaymentAttemptRow(**_payment_values(entity)))
        return entity

    def list_payments(self, checkout_id: str) -> list[PaymentAttempt]:
        with self._sessions() as session:
            rows = session.scalars(select(PaymentAttemptRow).where(PaymentAttemptRow.checkout_id == checkout_id).order_by(PaymentAttemptRow.created_at)).all()
            return [_payment(row) for row in rows]

    def add_booking(self, entity: SupplierBooking) -> SupplierBooking:
        with self._sessions.begin() as session:
            session.add(SupplierBookingRow(**_booking_values(entity)))
        return entity

    def list_bookings(self, checkout_id: str) -> list[SupplierBooking]:
        with self._sessions() as session:
            rows = session.scalars(select(SupplierBookingRow).where(SupplierBookingRow.checkout_id == checkout_id).order_by(SupplierBookingRow.created_at)).all()
            return [_booking(row) for row in rows]

    def add_refund(self, entity: RefundRecord) -> RefundRecord:
        with self._sessions.begin() as session:
            session.add(RefundRecordRow(**_refund_values(entity)))
        return entity

    def list_refunds(self, checkout_id: str) -> list[RefundRecord]:
        with self._sessions() as session:
            rows = session.scalars(select(RefundRecordRow).where(RefundRecordRow.checkout_id == checkout_id).order_by(RefundRecordRow.created_at)).all()
            return [_refund(row) for row in rows]


def _checkout_values(entity: CheckoutIntent) -> dict:
    return {field: getattr(entity, field) for field in ("id", "traveller_id", "trip_reference", "supplier", "product_type", "idempotency_key", "currency", "customer_total", "supplier_net", "markup", "taxes_and_fees", "created_at", "updated_at")} | {"status": entity.status.value}


def _payment_values(entity: PaymentAttempt) -> dict:
    return {field: getattr(entity, field) for field in ("id", "checkout_id", "provider", "provider_reference", "idempotency_key", "amount", "currency", "failure_code", "created_at", "updated_at")} | {"status": entity.status.value}


def _booking_values(entity: SupplierBooking) -> dict:
    return {field: getattr(entity, field) for field in ("id", "checkout_id", "supplier", "supplier_reference", "booked_at", "created_at", "updated_at")} | {"status": entity.status.value}


def _refund_values(entity: RefundRecord) -> dict:
    return {field: getattr(entity, field) for field in ("id", "checkout_id", "payment_attempt_id", "supplier_booking_id", "provider_reference", "idempotency_key", "amount", "currency", "reason_code", "created_at", "updated_at")} | {"status": entity.status.value}


def _checkout(row: CheckoutIntentRow) -> CheckoutIntent:
    return CheckoutIntent(id=row.id, traveller_id=row.traveller_id, trip_reference=row.trip_reference, supplier=row.supplier, product_type=row.product_type, idempotency_key=row.idempotency_key, status=CheckoutStatus(row.status), currency=row.currency, customer_total=row.customer_total, supplier_net=row.supplier_net, markup=row.markup, taxes_and_fees=row.taxes_and_fees, created_at=_utc(row.created_at), updated_at=_utc(row.updated_at))


def _payment(row: PaymentAttemptRow) -> PaymentAttempt:
    return PaymentAttempt(id=row.id, checkout_id=row.checkout_id, provider=row.provider, provider_reference=row.provider_reference, idempotency_key=row.idempotency_key, status=PaymentStatus(row.status), amount=row.amount, currency=row.currency, failure_code=row.failure_code, created_at=_utc(row.created_at), updated_at=_utc(row.updated_at))


def _booking(row: SupplierBookingRow) -> SupplierBooking:
    return SupplierBooking(id=row.id, checkout_id=row.checkout_id, supplier=row.supplier, supplier_reference=row.supplier_reference, status=BookingStatus(row.status), booked_at=_utc(row.booked_at) if row.booked_at else None, created_at=_utc(row.created_at), updated_at=_utc(row.updated_at))


def _refund(row: RefundRecordRow) -> RefundRecord:
    return RefundRecord(id=row.id, checkout_id=row.checkout_id, payment_attempt_id=row.payment_attempt_id, supplier_booking_id=row.supplier_booking_id, provider_reference=row.provider_reference, idempotency_key=row.idempotency_key, status=RefundStatus(row.status), amount=row.amount, currency=row.currency, reason_code=row.reason_code, created_at=_utc(row.created_at), updated_at=_utc(row.updated_at))


def _utc(value: datetime) -> datetime:
    """Normalise SQLite's timezone-naive round trip to the UTC domain contract."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
