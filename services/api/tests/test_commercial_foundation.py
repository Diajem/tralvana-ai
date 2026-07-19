from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.database.base import Base
from app.database.session import create_engine_from_url, create_session_factory
from app.domains.commercial.entities import CommercialVertical
from app.domains.commercial.repository import SqlAlchemyCommercialRepository
from app.domains.commercial.service import CommercialLedgerService, CommercialValidationError


@pytest.fixture
def ledger():
    engine = create_engine_from_url("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    with factory() as session:
        yield CommercialLedgerService(SqlAlchemyCommercialRepository(session)), session
    engine.dispose()


def _programme(service: CommercialLedgerService):
    partner = service.register_partner(
        slug="example-travel", name="Example Travel", website_url="https://example.test"
    )
    return service.register_programme(
        partner_id=partner.id,
        name="Example Affiliate",
        vertical=CommercialVertical.ACCOMMODATION,
        tracking_template="https://example.test/hotel?aid={affiliate_id}&subid={sub_id}",
        affiliate_identifier="tralvana-uk",
        default_currency="GBP",
    )


def test_full_attribution_and_commission_chain_is_persisted(ledger):
    service, session = ledger
    programme = _programme(service)
    click = service.record_click(
        programme_id=programme.id,
        destination_url="https://example.test/hotel/42",
        tracking_url="https://example.test/hotel/42?aid=tralvana-uk&subid=abc",
        trip_reference="trip-42",
        recommendation_reference="recommendation-9",
        anonymous_session_hash="sha256:already-hashed",
    )
    conversion = service.record_conversion(
        programme_id=programme.id,
        click_id=click.id,
        external_reference="booking-123",
        gross_value=Decimal("840.50"),
        currency="GBP",
    )
    commission = service.record_commission(
        conversion_id=conversion.id,
        amount=Decimal("42.03"),
        currency="GBP",
        external_reference="commission-123",
    )
    session.commit()

    counts = SqlAlchemyCommercialRepository(session).counts()
    assert counts == {
        "partners": 1, "programmes": 1, "clicks": 1,
        "conversions": 1, "commissions": 1,
    }
    assert SqlAlchemyCommercialRepository(session).get_conversion(conversion.id).gross_value == Decimal("840.50")
    assert commission.currency == "GBP"


def test_conversion_rejects_click_from_another_programme(ledger):
    service, _ = ledger
    first = _programme(service)
    second_partner = service.register_partner(
        slug="other", name="Other", website_url="https://other.test"
    )
    second = service.register_programme(
        partner_id=second_partner.id,
        name="Other Programme",
        vertical=CommercialVertical.FLIGHTS,
        tracking_template="https://other.test/{affiliate_id}",
        affiliate_identifier="tralvana",
    )
    click = service.record_click(
        programme_id=first.id,
        destination_url="https://example.test",
        tracking_url="https://example.test/?tracked=1",
    )

    with pytest.raises(CommercialValidationError, match="different programme"):
        service.record_conversion(
            programme_id=second.id,
            click_id=click.id,
            external_reference="bad-link",
            gross_value=Decimal("10"),
            currency="GBP",
        )


@pytest.mark.parametrize("amount", [Decimal("-0.01"), Decimal("-100")])
def test_negative_commercial_amounts_are_rejected(ledger, amount):
    service, _ = ledger
    programme = _programme(service)
    with pytest.raises(CommercialValidationError, match="cannot be negative"):
        service.record_conversion(
            programme_id=programme.id,
            external_reference="negative",
            gross_value=amount,
            currency="GBP",
        )


def test_duplicate_partner_slug_is_database_enforced(ledger):
    service, session = ledger
    service.register_partner(slug="same", name="One", website_url="https://one.test")
    with pytest.raises(IntegrityError):
        service.register_partner(slug="same", name="Two", website_url="https://two.test")
    session.rollback()


def test_raw_personal_data_is_not_part_of_click_schema():
    columns = set(Base.metadata.tables["outbound_clicks"].columns.keys())
    assert "anonymous_session_hash" in columns
    assert {"email", "ip_address", "user_agent", "traveller_name"}.isdisjoint(columns)


def test_commercial_status_is_safe_when_database_is_unconfigured(client, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    body = client.get("/internal/commercial/status").json()
    assert body == {
        "configured": False,
        "reachable": False,
        "schema_version": "unconfigured",
        "counts": {
            "partners": 0, "programmes": 0, "clicks": 0,
            "conversions": 0, "commissions": 0,
        },
    }
    assert all(term not in str(body).lower() for term in ("password", "database_url", "hostname"))


def test_no_public_booking_route_and_only_safe_commercial_routes_exist(client):
    routes = {route.path for route in client.app.routes}
    assert "/book" not in routes
    assert "/redirect" not in routes
    assert {route for route in routes if route.startswith("/commercial/")} == {
        "/commercial/programmes",
        "/commercial/outbound-links",
        "/commercial/outbound-links/{click_id}/redirect",
    }
