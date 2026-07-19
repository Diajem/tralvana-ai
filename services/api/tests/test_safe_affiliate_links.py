from __future__ import annotations

from pathlib import Path

import pytest

from app.database.base import Base
from app.database.session import create_engine_from_url, create_session_factory
from app.domains.commercial.catalogue import (
    TRAVELPAYOUTS_WIDGET_ACCOUNT,
    VERIFIED_AFFILIATE_CATALOGUE,
)
from app.domains.commercial.repository import SqlAlchemyCommercialRepository
from app.domains.commercial.seeding import seed_verified_affiliates
from app.domains.commercial.service import CommercialLedgerService, CommercialValidationError


@pytest.fixture
def seeded_database(tmp_path: Path, monkeypatch):
    database_path = tmp_path / "commercial.db"
    url = f"sqlite+pysqlite:///{database_path}"
    engine = create_engine_from_url(url)
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    with factory.begin() as session:
        created = seed_verified_affiliates(SqlAlchemyCommercialRepository(session))
    monkeypatch.setenv("DATABASE_URL", url)
    yield factory, created
    engine.dispose()


def test_verified_catalogue_reuses_current_public_identifiers():
    identifiers = {
        programme.affiliate_identifier
        for partner in VERIFIED_AFFILIATE_CATALOGUE
        for programme in partner.programmes
    }
    assert {"mZObD29", "1773696:121428", "diajemglobal-21"} <= identifiers
    assert TRAVELPAYOUTS_WIDGET_ACCOUNT == {"trs": "432320", "shmarker": "493614"}
    assert "232507" not in str(VERIFIED_AFFILIATE_CATALOGUE)


def test_verified_catalogue_seed_is_idempotent(seeded_database):
    factory, created = seeded_database
    assert created == {"partners": 3, "programmes": 11}
    with factory.begin() as session:
        repository = SqlAlchemyCommercialRepository(session)
        assert seed_verified_affiliates(repository) == {"partners": 0, "programmes": 0}
        assert repository.counts()["programmes"] == 11


def test_outbound_link_requires_disclosure_and_allow_list(seeded_database):
    factory, _ = seeded_database
    with factory.begin() as session:
        repository = SqlAlchemyCommercialRepository(session)
        programme = next(
            item for item in repository.list_active_programmes() if item.name == "Amazon UK"
        )
        service = CommercialLedgerService(repository)
        with pytest.raises(CommercialValidationError, match="disclosure"):
            service.create_outbound_link(
                programme_id=programme.id,
                destination_url=programme.tracking_template,
                disclosure_acknowledged=False,
            )
        with pytest.raises(CommercialValidationError, match="destination host"):
            service.create_outbound_link(
                programme_id=programme.id,
                destination_url="https://evil.example/steal",
                disclosure_acknowledged=True,
            )
        click = service.create_outbound_link(
            programme_id=programme.id,
            destination_url=programme.tracking_template,
            disclosure_acknowledged=True,
            campaign="packing-list",
            sub_id="trip-42",
        )
        assert click.tracking_url == "https://www.amazon.co.uk/?tag=diajemglobal-21"
        assert service.safe_tracking_url_for_click(click.id) == click.tracking_url

        with pytest.raises(CommercialValidationError, match="SHA-256"):
            service.create_outbound_link(
                programme_id=programme.id,
                destination_url=programme.tracking_template,
                disclosure_acknowledged=True,
                anonymous_session_hash="somebody@example.com",
            )


def test_public_affiliate_flow_records_then_redirects(client, seeded_database):
    programmes = client.get("/commercial/programmes")
    assert programmes.status_code == 200
    amazon = next(item for item in programmes.json() if item["name"] == "Amazon UK")
    assert amazon["disclosure_text"] == "Tralvana may earn a commission from this link."
    assert "affiliate_identifier" not in amazon

    created = client.post("/commercial/outbound-links", json={
        "programme_id": amazon["id"],
        "destination_url": amazon["destination_url"],
        "disclosure_acknowledged": True,
        "recommendation_reference": "recommendation-7",
    })
    assert created.status_code == 201
    response = client.get(created.json()["redirect_path"], follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://www.amazon.co.uk/?tag=diajemglobal-21"


@pytest.mark.parametrize(
    "destination",
    (
        "http://www.amazon.co.uk/",
        "https://www.amazon.co.uk.evil.example/",
        "https://user:password@www.amazon.co.uk/",
        "https://127.0.0.1/",
    ),
)
def test_public_affiliate_flow_rejects_unsafe_destinations(client, seeded_database, destination):
    programme = next(
        item for item in client.get("/commercial/programmes").json() if item["name"] == "Amazon UK"
    )
    response = client.post("/commercial/outbound-links", json={
        "programme_id": programme["id"],
        "destination_url": destination,
        "disclosure_acknowledged": True,
    })
    assert response.status_code == 400
