"""Verified public affiliate configuration carried over from tralvana.com.

Only links already published with tracking identifiers are active here. Provider
websites without a tracked link deliberately remain outside this catalogue.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.domains.commercial.entities import CommercialVertical


@dataclass(frozen=True, slots=True)
class ProgrammeSeed:
    name: str
    vertical: CommercialVertical
    tracking_url: str
    affiliate_identifier: str
    destination_host: str
    tracking_host: str


@dataclass(frozen=True, slots=True)
class PartnerSeed:
    slug: str
    name: str
    website_url: str
    programmes: tuple[ProgrammeSeed, ...]


VERIFIED_AFFILIATE_CATALOGUE = (
    PartnerSeed(
        slug="expedia",
        name="Expedia",
        website_url="https://www.expedia.com",
        programmes=(
            ProgrammeSeed(
                name="Expedia tracked landing page",
                vertical=CommercialVertical.PACKAGES,
                tracking_url="https://expedia.com/affiliate/mZObD29",
                affiliate_identifier="mZObD29",
                destination_host="expedia.com",
                tracking_host="expedia.com",
            ),
        ),
    ),
    PartnerSeed(
        slug="awin",
        name="Awin",
        website_url="https://www.awin.com",
        programmes=(
            ProgrammeSeed(
                name="Bee Parking Heathrow",
                vertical=CommercialVertical.PARKING,
                tracking_url="https://www.awin1.com/cread.php?awinmid=121428&awinaffid=1773696",
                affiliate_identifier="1773696:121428",
                destination_host="awin1.com",
                tracking_host="awin1.com",
            ),
            ProgrammeSeed(
                name="TTfone",
                vertical=CommercialVertical.RETAIL,
                tracking_url="https://www.awin1.com/cread.php?awinmid=28737&awinaffid=1773696",
                affiliate_identifier="1773696:28737",
                destination_host="awin1.com",
                tracking_host="awin1.com",
            ),
            ProgrammeSeed(
                name="WorldSIM",
                vertical=CommercialVertical.ESIM,
                tracking_url="https://www.awin1.com/cread.php?awinmid=104675&awinaffid=1773696",
                affiliate_identifier="1773696:104675",
                destination_host="awin1.com",
                tracking_host="awin1.com",
            ),
            ProgrammeSeed(
                name="GoWithGuide",
                vertical=CommercialVertical.ACTIVITIES,
                tracking_url="https://www.awin1.com/cread.php?s=4750813&v=87121&q=496538&r=1773696",
                affiliate_identifier="1773696:87121",
                destination_host="awin1.com",
                tracking_host="awin1.com",
            ),
        ),
    ),
    PartnerSeed(
        slug="amazon-associates",
        name="Amazon Associates",
        website_url="https://affiliate-program.amazon.com",
        programmes=tuple(
            ProgrammeSeed(
                name=f"Amazon {region}",
                vertical=CommercialVertical.RETAIL,
                tracking_url=f"https://www.{host}/?tag={tag}",
                affiliate_identifier=tag,
                destination_host=host,
                tracking_host=host,
            )
            for region, host, tag in (
                ("UK", "amazon.co.uk", "diajemglobal-21"),
                ("US", "amazon.com", "diajemgroup-20"),
                ("Spain", "amazon.es", "diajemgroup00-21"),
                ("Germany", "amazon.de", "diajemgroup0c-21"),
                ("France", "amazon.fr", "diajemgroup0a-21"),
                ("Italy", "amazon.it", "diajemgroup04-21"),
            )
        ),
    ),
)


TRAVELPAYOUTS_WIDGET_ACCOUNT = {"trs": "432320", "shmarker": "493614"}
