from __future__ import annotations

from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domains.commercial.entities import (
    AffiliateConversion,
    AffiliateProgramme,
    CommissionRecord,
    CommercialVertical,
    ConversionStatus,
    OutboundClick,
    Partner,
    PartnerStatus,
    ProgrammeStatus,
)
from app.domains.commercial.orm import (
    AffiliateConversionRow,
    AffiliateProgrammeRow,
    CommissionRecordRow,
    OutboundClickRow,
    PartnerRow,
)


class CommercialRepository(Protocol):
    def add_partner(self, partner: Partner) -> Partner: ...
    def get_partner(self, partner_id: str) -> Partner | None: ...
    def get_partner_by_slug(self, slug: str) -> Partner | None: ...
    def add_programme(self, programme: AffiliateProgramme) -> AffiliateProgramme: ...
    def get_programme(self, programme_id: str) -> AffiliateProgramme | None: ...
    def get_programme_by_partner_and_name(
        self, partner_id: str, name: str
    ) -> AffiliateProgramme | None: ...
    def list_active_programmes(self) -> list[AffiliateProgramme]: ...
    def add_click(self, click: OutboundClick) -> OutboundClick: ...
    def get_click(self, click_id: str) -> OutboundClick | None: ...
    def add_conversion(self, conversion: AffiliateConversion) -> AffiliateConversion: ...
    def get_conversion(self, conversion_id: str) -> AffiliateConversion | None: ...
    def add_commission(self, commission: CommissionRecord) -> CommissionRecord: ...
    def counts(self) -> dict[str, int]: ...


class SqlAlchemyCommercialRepository:
    """SQLAlchemy adapter for the commercial attribution ledger."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add_partner(self, entity: Partner) -> Partner:
        self._session.add(PartnerRow(
            id=entity.id, slug=entity.slug, name=entity.name,
            website_url=entity.website_url, status=entity.status.value,
            created_at=entity.created_at, updated_at=entity.updated_at,
        ))
        self._session.flush()
        return entity

    def get_partner(self, partner_id: str) -> Partner | None:
        row = self._session.get(PartnerRow, partner_id)
        return _partner(row) if row else None

    def get_partner_by_slug(self, slug: str) -> Partner | None:
        row = self._session.scalar(select(PartnerRow).where(PartnerRow.slug == slug))
        return _partner(row) if row else None

    def add_programme(self, entity: AffiliateProgramme) -> AffiliateProgramme:
        self._session.add(AffiliateProgrammeRow(
            id=entity.id, partner_id=entity.partner_id, name=entity.name,
            vertical=entity.vertical.value, tracking_template=entity.tracking_template,
            affiliate_identifier=entity.affiliate_identifier,
            allowed_destination_hosts=list(entity.allowed_destination_hosts),
            allowed_tracking_hosts=list(entity.allowed_tracking_hosts),
            default_currency=entity.default_currency, disclosure_text=entity.disclosure_text,
            terms_url=entity.terms_url, status=entity.status.value,
            created_at=entity.created_at, updated_at=entity.updated_at,
        ))
        self._session.flush()
        return entity

    def get_programme(self, programme_id: str) -> AffiliateProgramme | None:
        row = self._session.get(AffiliateProgrammeRow, programme_id)
        return _programme(row) if row else None

    def get_programme_by_partner_and_name(
        self, partner_id: str, name: str
    ) -> AffiliateProgramme | None:
        row = self._session.scalar(select(AffiliateProgrammeRow).where(
            AffiliateProgrammeRow.partner_id == partner_id,
            AffiliateProgrammeRow.name == name,
        ))
        return _programme(row) if row else None

    def list_active_programmes(self) -> list[AffiliateProgramme]:
        rows = self._session.scalars(
            select(AffiliateProgrammeRow)
            .where(AffiliateProgrammeRow.status == ProgrammeStatus.ACTIVE.value)
            .order_by(AffiliateProgrammeRow.vertical, AffiliateProgrammeRow.name)
        ).all()
        return [_programme(row) for row in rows]

    def add_click(self, entity: OutboundClick) -> OutboundClick:
        self._session.add(OutboundClickRow(
            id=entity.id, programme_id=entity.programme_id,
            destination_url=entity.destination_url, tracking_url=entity.tracking_url,
            trip_reference=entity.trip_reference,
            recommendation_reference=entity.recommendation_reference,
            campaign=entity.campaign, sub_id=entity.sub_id,
            anonymous_session_hash=entity.anonymous_session_hash,
            attribution_metadata=entity.attribution_metadata,
            occurred_at=entity.occurred_at,
        ))
        self._session.flush()
        return entity

    def get_click(self, click_id: str) -> OutboundClick | None:
        row = self._session.get(OutboundClickRow, click_id)
        return _click(row) if row else None

    def add_conversion(self, entity: AffiliateConversion) -> AffiliateConversion:
        self._session.add(AffiliateConversionRow(
            id=entity.id, programme_id=entity.programme_id, click_id=entity.click_id,
            external_reference=entity.external_reference, gross_value=entity.gross_value,
            currency=entity.currency, status=entity.status.value,
            booked_at=entity.booked_at, confirmed_at=entity.confirmed_at,
            conversion_metadata=entity.conversion_metadata,
            created_at=entity.created_at, updated_at=entity.updated_at,
        ))
        self._session.flush()
        return entity

    def get_conversion(self, conversion_id: str) -> AffiliateConversion | None:
        row = self._session.get(AffiliateConversionRow, conversion_id)
        return _conversion(row) if row else None

    def add_commission(self, entity: CommissionRecord) -> CommissionRecord:
        self._session.add(CommissionRecordRow(
            id=entity.id, conversion_id=entity.conversion_id, amount=entity.amount,
            currency=entity.currency, status=entity.status.value,
            external_reference=entity.external_reference, expected_at=entity.expected_at,
            approved_at=entity.approved_at, paid_at=entity.paid_at,
            created_at=entity.created_at, updated_at=entity.updated_at,
        ))
        self._session.flush()
        return entity

    def counts(self) -> dict[str, int]:
        tables = {
            "partners": PartnerRow,
            "programmes": AffiliateProgrammeRow,
            "clicks": OutboundClickRow,
            "conversions": AffiliateConversionRow,
            "commissions": CommissionRecordRow,
        }
        return {
            name: self._session.scalar(select(func.count()).select_from(table)) or 0
            for name, table in tables.items()
        }


def _partner(row: PartnerRow) -> Partner:
    return Partner(id=row.id, slug=row.slug, name=row.name, website_url=row.website_url,
                   status=PartnerStatus(row.status), created_at=row.created_at, updated_at=row.updated_at)


def _programme(row: AffiliateProgrammeRow) -> AffiliateProgramme:
    return AffiliateProgramme(
        id=row.id, partner_id=row.partner_id, name=row.name,
        vertical=CommercialVertical(row.vertical), tracking_template=row.tracking_template,
        affiliate_identifier=row.affiliate_identifier, default_currency=row.default_currency,
        allowed_destination_hosts=tuple(row.allowed_destination_hosts),
        allowed_tracking_hosts=tuple(row.allowed_tracking_hosts),
        disclosure_text=row.disclosure_text, terms_url=row.terms_url,
        status=ProgrammeStatus(row.status), created_at=row.created_at, updated_at=row.updated_at,
    )


def _click(row: OutboundClickRow) -> OutboundClick:
    return OutboundClick(
        id=row.id, programme_id=row.programme_id, destination_url=row.destination_url,
        tracking_url=row.tracking_url, trip_reference=row.trip_reference,
        recommendation_reference=row.recommendation_reference, campaign=row.campaign,
        sub_id=row.sub_id, anonymous_session_hash=row.anonymous_session_hash,
        attribution_metadata=row.attribution_metadata, occurred_at=row.occurred_at,
    )


def _conversion(row: AffiliateConversionRow) -> AffiliateConversion:
    return AffiliateConversion(
        id=row.id, programme_id=row.programme_id, click_id=row.click_id,
        external_reference=row.external_reference, gross_value=row.gross_value,
        currency=row.currency, status=ConversionStatus(row.status), booked_at=row.booked_at,
        confirmed_at=row.confirmed_at, conversion_metadata=row.conversion_metadata,
        created_at=row.created_at, updated_at=row.updated_at,
    )
