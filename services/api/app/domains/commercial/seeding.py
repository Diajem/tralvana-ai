from __future__ import annotations

from app.domains.commercial.catalogue import VERIFIED_AFFILIATE_CATALOGUE
from app.domains.commercial.entities import PartnerStatus, ProgrammeStatus
from app.domains.commercial.repository import CommercialRepository
from app.domains.commercial.service import CommercialLedgerService


def seed_verified_affiliates(repository: CommercialRepository) -> dict[str, int]:
    """Insert the verified catalogue once; existing rows are never overwritten."""
    service = CommercialLedgerService(repository)
    created = {"partners": 0, "programmes": 0}
    for item in VERIFIED_AFFILIATE_CATALOGUE:
        partner = repository.get_partner_by_slug(item.slug)
        if partner is None:
            partner = service.register_partner(
                slug=item.slug,
                name=item.name,
                website_url=item.website_url,
                status=PartnerStatus.ACTIVE,
            )
            created["partners"] += 1
        for programme in item.programmes:
            if repository.get_programme_by_partner_and_name(partner.id, programme.name):
                continue
            service.register_programme(
                partner_id=partner.id,
                name=programme.name,
                vertical=programme.vertical,
                tracking_template=programme.tracking_url,
                affiliate_identifier=programme.affiliate_identifier,
                allowed_destination_hosts=(programme.destination_host,),
                allowed_tracking_hosts=(programme.tracking_host,),
                status=ProgrammeStatus.ACTIVE,
            )
            created["programmes"] += 1
    return created
