from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.database.readiness import inspect_database_readiness
from app.database.session import create_engine_from_url, create_session_factory, database_url
from app.domains.commercial.repository import SqlAlchemyCommercialRepository
from app.domains.commercial.service import CommercialLedgerService, CommercialValidationError

router = APIRouter(prefix="/internal/commercial", tags=["internal"])
public_router = APIRouter(prefix="/commercial", tags=["commercial"])


class CommercialStatusResponse(BaseModel):
    configured: bool
    reachable: bool
    schema_version: str
    counts: dict[str, int]


@router.get("/status", response_model=CommercialStatusResponse)
def commercial_status() -> CommercialStatusResponse:
    """Safe, read-only readiness signal. Connection details are never returned."""
    database = inspect_database_readiness()
    return CommercialStatusResponse(
        configured=database.configured,
        reachable=database.reachable,
        schema_version=database.schema_version,
        counts=database.counts,
    )


class ProgrammeResponse(BaseModel):
    id: str
    partner: str
    name: str
    vertical: str
    disclosure_text: str
    destination_url: str


class OutboundLinkRequest(BaseModel):
    programme_id: str
    destination_url: str
    disclosure_acknowledged: bool = False
    trip_reference: str | None = None
    recommendation_reference: str | None = None
    campaign: str | None = None
    sub_id: str | None = None
    anonymous_session_hash: str | None = None


class OutboundLinkResponse(BaseModel):
    click_id: str
    redirect_path: str
    disclosure_text: str


def _configured_database_url() -> str:
    url = database_url()
    if not url:
        raise HTTPException(status_code=503, detail="Commercial database is not configured")
    return url


@public_router.get("/programmes", response_model=list[ProgrammeResponse])
def list_programmes() -> list[ProgrammeResponse]:
    engine = create_engine_from_url(_configured_database_url())
    factory = create_session_factory(engine)
    try:
        with factory() as session:
            repository = SqlAlchemyCommercialRepository(session)
            result = []
            for programme in repository.list_active_programmes():
                partner = repository.get_partner(programme.partner_id)
                if (
                    not partner
                    or partner.status.value != "ACTIVE"
                    or not programme.tracking_template
                    or "{" in programme.tracking_template
                ):
                    continue
                result.append(ProgrammeResponse(
                    id=programme.id,
                    partner=partner.name,
                    name=programme.name,
                    vertical=programme.vertical.value,
                    disclosure_text=programme.disclosure_text,
                    destination_url=programme.tracking_template,
                ))
            return result
    finally:
        engine.dispose()


@public_router.post("/outbound-links", response_model=OutboundLinkResponse, status_code=201)
def create_outbound_link(request: OutboundLinkRequest) -> OutboundLinkResponse:
    engine = create_engine_from_url(_configured_database_url())
    factory = create_session_factory(engine)
    try:
        with factory.begin() as session:
            repository = SqlAlchemyCommercialRepository(session)
            service = CommercialLedgerService(repository)
            try:
                click = service.create_outbound_link(**request.model_dump())
            except CommercialValidationError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            programme = repository.get_programme(click.programme_id)
            assert programme is not None
            return OutboundLinkResponse(
                click_id=click.id,
                redirect_path=f"/commercial/outbound-links/{click.id}/redirect",
                disclosure_text=programme.disclosure_text,
            )
    finally:
        engine.dispose()


@public_router.get("/outbound-links/{click_id}/redirect", response_class=RedirectResponse)
def follow_outbound_link(click_id: str) -> RedirectResponse:
    engine = create_engine_from_url(_configured_database_url())
    factory = create_session_factory(engine)
    try:
        with factory() as session:
            service = CommercialLedgerService(SqlAlchemyCommercialRepository(session))
            try:
                tracking_url = service.safe_tracking_url_for_click(click_id)
            except CommercialValidationError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            return RedirectResponse(tracking_url, status_code=307)
    finally:
        engine.dispose()
