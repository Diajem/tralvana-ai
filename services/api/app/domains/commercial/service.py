from __future__ import annotations

from decimal import Decimal

from app.domains.commercial.entities import (
    AffiliateConversion,
    AffiliateProgramme,
    CommissionRecord,
    CommercialVertical,
    OutboundClick,
    Partner,
)
from app.domains.commercial.repository import CommercialRepository


class CommercialValidationError(ValueError):
    pass


class CommercialLedgerService:
    """Application service for durable attribution; it performs no redirects or bookings."""

    def __init__(self, repository: CommercialRepository) -> None:
        self._repository = repository

    def register_partner(self, *, slug: str, name: str, website_url: str) -> Partner:
        return self._repository.add_partner(Partner(
            slug=slug.strip().lower(), name=name.strip(), website_url=website_url.strip()
        ))

    def register_programme(
        self,
        *,
        partner_id: str,
        name: str,
        vertical: CommercialVertical,
        tracking_template: str,
        affiliate_identifier: str,
        default_currency: str = "GBP",
    ) -> AffiliateProgramme:
        if not self._repository.get_partner(partner_id):
            raise CommercialValidationError("partner does not exist")
        _currency(default_currency)
        return self._repository.add_programme(AffiliateProgramme(
            partner_id=partner_id,
            name=name.strip(),
            vertical=vertical,
            tracking_template=tracking_template.strip(),
            affiliate_identifier=affiliate_identifier.strip(),
            default_currency=default_currency.upper(),
        ))

    def record_click(
        self,
        *,
        programme_id: str,
        destination_url: str,
        tracking_url: str,
        trip_reference: str | None = None,
        recommendation_reference: str | None = None,
        anonymous_session_hash: str | None = None,
    ) -> OutboundClick:
        if not self._repository.get_programme(programme_id):
            raise CommercialValidationError("affiliate programme does not exist")
        return self._repository.add_click(OutboundClick(
            programme_id=programme_id,
            destination_url=destination_url,
            tracking_url=tracking_url,
            trip_reference=trip_reference,
            recommendation_reference=recommendation_reference,
            anonymous_session_hash=anonymous_session_hash,
        ))

    def record_conversion(
        self,
        *,
        programme_id: str,
        external_reference: str,
        gross_value: Decimal,
        currency: str,
        click_id: str | None = None,
    ) -> AffiliateConversion:
        if gross_value < 0:
            raise CommercialValidationError("gross value cannot be negative")
        if not self._repository.get_programme(programme_id):
            raise CommercialValidationError("affiliate programme does not exist")
        if click_id:
            click = self._repository.get_click(click_id)
            if not click:
                raise CommercialValidationError("click does not exist")
            if click.programme_id != programme_id:
                raise CommercialValidationError("click belongs to a different programme")
        _currency(currency)
        return self._repository.add_conversion(AffiliateConversion(
            programme_id=programme_id,
            click_id=click_id,
            external_reference=external_reference,
            gross_value=gross_value,
            currency=currency.upper(),
        ))

    def record_commission(
        self,
        *,
        conversion_id: str,
        amount: Decimal,
        currency: str,
        external_reference: str | None = None,
    ) -> CommissionRecord:
        conversion = self._repository.get_conversion(conversion_id)
        if not conversion:
            raise CommercialValidationError("conversion does not exist")
        if amount < 0:
            raise CommercialValidationError("commission amount cannot be negative")
        _currency(currency)
        if conversion.currency != currency.upper():
            raise CommercialValidationError("commission currency must match conversion currency")
        return self._repository.add_commission(CommissionRecord(
            conversion_id=conversion_id,
            amount=amount,
            currency=currency.upper(),
            external_reference=external_reference,
        ))


def _currency(value: str) -> None:
    if len(value.strip()) != 3 or not value.isalpha():
        raise CommercialValidationError("currency must be a three-letter ISO code")
