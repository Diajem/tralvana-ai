from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re
from typing import TextIO

from app.domains.commercial.entities import (
    AffiliateConversion,
    CommissionRecord,
    CommissionStatus,
    ConversionStatus,
    utc_now,
)
from app.domains.commercial.repository import CommercialRepository
from app.domains.commercial.service import CommercialValidationError


CANONICAL_FIELDS = {
    "partner_slug",
    "programme_name",
    "transaction_reference",
    "click_sub_id",
    "gross_value",
    "commission_amount",
    "currency",
    "conversion_status",
    "commission_status",
    "commission_reference",
    "booked_at",
    "approved_at",
    "paid_at",
    "source",
}
REQUIRED_FIELDS = {
    "partner_slug",
    "programme_name",
    "transaction_reference",
    "gross_value",
    "commission_amount",
    "currency",
    "conversion_status",
    "commission_status",
}
_REFERENCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}")


class CanonicalCommissionCsvError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CanonicalCommissionRow:
    row_number: int
    partner_slug: str
    programme_name: str
    transaction_reference: str
    gross_value: Decimal
    commission_amount: Decimal
    currency: str
    conversion_status: ConversionStatus
    commission_status: CommissionStatus
    click_sub_id: str | None = None
    commission_reference: str | None = None
    booked_at: datetime | None = None
    approved_at: datetime | None = None
    paid_at: datetime | None = None
    source: str = "manual"


@dataclass(frozen=True, slots=True)
class ReconciliationIssue:
    row_number: int
    message: str


@dataclass(slots=True)
class ReconciliationSummary:
    processed: int = 0
    conversions_created: int = 0
    conversions_updated: int = 0
    commissions_created: int = 0
    commissions_updated: int = 0
    clicks_matched: int = 0
    clicks_unmatched: int = 0
    issues: list[ReconciliationIssue] = field(default_factory=list)

    @property
    def successful(self) -> int:
        return self.processed - len(self.issues)


def load_canonical_commission_csv(stream: TextIO) -> list[CanonicalCommissionRow]:
    reader = csv.DictReader(stream)
    headers = set(reader.fieldnames or ())
    missing = REQUIRED_FIELDS - headers
    unknown = headers - CANONICAL_FIELDS
    if missing:
        raise CanonicalCommissionCsvError(
            f"missing required columns: {', '.join(sorted(missing))}"
        )
    if unknown:
        raise CanonicalCommissionCsvError(
            f"unsupported columns: {', '.join(sorted(unknown))}"
        )

    rows: list[CanonicalCommissionRow] = []
    for row_number, raw in enumerate(reader, start=2):
        try:
            rows.append(_canonical_row(row_number, raw))
        except (KeyError, ValueError, InvalidOperation) as exc:
            raise CanonicalCommissionCsvError(f"row {row_number}: {exc}") from exc
    return rows


class CommissionReconciliationService:
    """Imports a canonical report without assuming any affiliate network's raw schema."""

    def __init__(self, repository: CommercialRepository) -> None:
        self._repository = repository

    def reconcile(
        self, rows: list[CanonicalCommissionRow]
    ) -> ReconciliationSummary:
        summary = ReconciliationSummary(processed=len(rows))
        for row in rows:
            try:
                self._reconcile_row(row, summary)
            except (CommercialValidationError, ValueError) as exc:
                summary.issues.append(ReconciliationIssue(row.row_number, str(exc)))
        return summary

    def _reconcile_row(
        self, row: CanonicalCommissionRow, summary: ReconciliationSummary
    ) -> None:
        partner = self._repository.get_partner_by_slug(row.partner_slug)
        if partner is None:
            raise CommercialValidationError("commercial partner is not configured")
        programme = self._repository.get_programme_by_partner_and_name(
            partner.id, row.programme_name
        )
        if programme is None:
            raise CommercialValidationError("affiliate programme is not configured")
        click = None
        if row.click_sub_id:
            click = self._repository.get_latest_click_by_sub_id(
                programme.id, row.click_sub_id
            )
            if click:
                summary.clicks_matched += 1
            else:
                summary.clicks_unmatched += 1

        now = utc_now()
        conversion = self._repository.get_conversion_by_external_reference(
            programme.id, row.transaction_reference
        )
        if conversion is None:
            conversion = AffiliateConversion(
                programme_id=programme.id,
                external_reference=row.transaction_reference,
                gross_value=row.gross_value,
                currency=row.currency,
                click_id=click.id if click else None,
                status=row.conversion_status,
                booked_at=row.booked_at or now,
                confirmed_at=now if row.conversion_status == ConversionStatus.CONFIRMED else None,
                conversion_metadata={"import_source": row.source},
            )
            self._repository.add_conversion(conversion)
            summary.conversions_created += 1
        else:
            _prevent_terminal_conversion_regression(conversion.status, row.conversion_status)
            if conversion.currency != row.currency:
                raise CommercialValidationError(
                    "transaction currency cannot change between reports"
                )
            conversion.gross_value = row.gross_value
            conversion.status = row.conversion_status
            conversion.click_id = conversion.click_id or (click.id if click else None)
            conversion.booked_at = row.booked_at or conversion.booked_at
            if row.conversion_status == ConversionStatus.CONFIRMED:
                conversion.confirmed_at = conversion.confirmed_at or now
            conversion.conversion_metadata = {
                **conversion.conversion_metadata,
                "import_source": row.source,
            }
            conversion.updated_at = now
            self._repository.update_conversion(conversion)
            summary.conversions_updated += 1

        commission_reference = row.commission_reference or (
            f"{programme.id}:{row.transaction_reference}"
        )
        commission = self._repository.get_commission_by_external_reference(
            commission_reference
        )
        if commission is None:
            commission = CommissionRecord(
                conversion_id=conversion.id,
                amount=row.commission_amount,
                currency=row.currency,
                status=row.commission_status,
                external_reference=commission_reference,
                expected_at=now,
                approved_at=row.approved_at,
                paid_at=row.paid_at,
            )
            self._repository.add_commission(commission)
            summary.commissions_created += 1
        else:
            if commission.conversion_id != conversion.id:
                raise CommercialValidationError(
                    "commission reference belongs to a different conversion"
                )
            if commission.currency != row.currency:
                raise CommercialValidationError(
                    "commission currency cannot change between reports"
                )
            _prevent_terminal_commission_regression(
                commission.status, row.commission_status
            )
            commission.amount = row.commission_amount
            commission.status = row.commission_status
            commission.approved_at = row.approved_at or commission.approved_at
            commission.paid_at = row.paid_at or commission.paid_at
            commission.updated_at = now
            self._repository.update_commission(commission)
            summary.commissions_updated += 1


def _canonical_row(row_number: int, raw: dict[str, str | None]) -> CanonicalCommissionRow:
    transaction_reference = _reference(raw.get("transaction_reference"), "transaction reference")
    commission_reference = _optional_reference(
        raw.get("commission_reference"), "commission reference"
    )
    click_sub_id = _optional_reference(raw.get("click_sub_id"), "click sub-ID", 100)
    currency = (raw.get("currency") or "").strip().upper()
    if len(currency) != 3 or not currency.isalpha():
        raise ValueError("currency must be a three-letter ISO code")
    gross_value = _money(raw.get("gross_value"), "gross value")
    commission_amount = _money(raw.get("commission_amount"), "commission amount")
    return CanonicalCommissionRow(
        row_number=row_number,
        partner_slug=(raw.get("partner_slug") or "").strip().lower(),
        programme_name=(raw.get("programme_name") or "").strip(),
        transaction_reference=transaction_reference,
        click_sub_id=click_sub_id,
        gross_value=gross_value,
        commission_amount=commission_amount,
        currency=currency,
        conversion_status=ConversionStatus((raw.get("conversion_status") or "").strip().upper()),
        commission_status=CommissionStatus((raw.get("commission_status") or "").strip().upper()),
        commission_reference=commission_reference,
        booked_at=_datetime(raw.get("booked_at"), "booked_at"),
        approved_at=_datetime(raw.get("approved_at"), "approved_at"),
        paid_at=_datetime(raw.get("paid_at"), "paid_at"),
        source=_source(raw.get("source")),
    )


def _money(value: str | None, label: str) -> Decimal:
    amount = Decimal((value or "").strip())
    if (
        amount < 0
        or amount > Decimal("999999999999.99")
        or amount.as_tuple().exponent < -2
    ):
        raise ValueError(f"{label} must be non-negative with at most two decimal places")
    return amount


def _reference(value: str | None, label: str, maximum: int = 200) -> str:
    cleaned = (value or "").strip()
    if len(cleaned) > maximum or not _REFERENCE.fullmatch(cleaned):
        raise ValueError(f"{label} contains unsupported characters")
    return cleaned


def _optional_reference(
    value: str | None, label: str, maximum: int = 200
) -> str | None:
    cleaned = (value or "").strip()
    return _reference(cleaned, label, maximum) if cleaned else None


def _datetime(value: str | None, label: str) -> datetime | None:
    cleaned = (value or "").strip()
    if not cleaned:
        return None
    parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _source(value: str | None) -> str:
    cleaned = (value or "manual").strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,49}", cleaned):
        raise ValueError("source contains unsupported characters")
    return cleaned


def _prevent_terminal_conversion_regression(
    current: ConversionStatus, incoming: ConversionStatus
) -> None:
    if current in {ConversionStatus.REJECTED, ConversionStatus.CANCELLED} and incoming != current:
        raise CommercialValidationError("terminal conversion status cannot be regressed")


def _prevent_terminal_commission_regression(
    current: CommissionStatus, incoming: CommissionStatus
) -> None:
    if current in {CommissionStatus.REJECTED, CommissionStatus.PAID} and incoming != current:
        raise CommercialValidationError("terminal commission status cannot be regressed")
