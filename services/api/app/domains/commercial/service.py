from __future__ import annotations

from decimal import Decimal
from ipaddress import ip_address
import re
from string import Formatter
from urllib.parse import quote, urlsplit

from app.domains.commercial.entities import (
    AffiliateConversion,
    AffiliateProgramme,
    CommissionRecord,
    CommercialVertical,
    OutboundClick,
    Partner,
    PartnerStatus,
    ProgrammeStatus,
)
from app.domains.commercial.repository import CommercialRepository


class CommercialValidationError(ValueError):
    pass


class CommercialLedgerService:
    """Application service for durable attribution; it performs no redirects or bookings."""

    def __init__(self, repository: CommercialRepository) -> None:
        self._repository = repository

    def register_partner(
        self, *, slug: str, name: str, website_url: str,
        status: PartnerStatus = PartnerStatus.PENDING,
    ) -> Partner:
        _safe_https_url(website_url)
        return self._repository.add_partner(Partner(
            slug=slug.strip().lower(), name=name.strip(), website_url=website_url.strip(),
            status=status,
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
        allowed_destination_hosts: tuple[str, ...] = (),
        allowed_tracking_hosts: tuple[str, ...] = (),
        disclosure_text: str = "Tralvana may earn a commission from this link.",
        terms_url: str | None = None,
        status: ProgrammeStatus = ProgrammeStatus.DRAFT,
    ) -> AffiliateProgramme:
        if not self._repository.get_partner(partner_id):
            raise CommercialValidationError("partner does not exist")
        _currency(default_currency)
        destinations = _hosts(allowed_destination_hosts)
        tracking = _hosts(allowed_tracking_hosts)
        _validate_template(tracking_template)
        if status == ProgrammeStatus.ACTIVE and (not destinations or not tracking):
            raise CommercialValidationError("active programmes require destination and tracking hosts")
        return self._repository.add_programme(AffiliateProgramme(
            partner_id=partner_id,
            name=name.strip(),
            vertical=vertical,
            tracking_template=tracking_template.strip(),
            affiliate_identifier=affiliate_identifier.strip(),
            allowed_destination_hosts=destinations,
            allowed_tracking_hosts=tracking,
            default_currency=default_currency.upper(),
            disclosure_text=disclosure_text.strip(),
            terms_url=terms_url.strip() if terms_url else None,
            status=status,
        ))

    def create_outbound_link(
        self,
        *,
        programme_id: str,
        destination_url: str,
        disclosure_acknowledged: bool,
        trip_reference: str | None = None,
        recommendation_reference: str | None = None,
        campaign: str | None = None,
        sub_id: str | None = None,
        anonymous_session_hash: str | None = None,
    ) -> OutboundClick:
        programme = self._repository.get_programme(programme_id)
        if not programme or programme.status != ProgrammeStatus.ACTIVE:
            raise CommercialValidationError("affiliate programme is not active")
        partner = self._repository.get_partner(programme.partner_id)
        if not partner or partner.status != PartnerStatus.ACTIVE:
            raise CommercialValidationError("commercial partner is not active")
        if not disclosure_acknowledged:
            raise CommercialValidationError("affiliate disclosure must be acknowledged")
        _allowed_url(destination_url, programme.allowed_destination_hosts, "destination")
        tracking_url = _render_tracking_url(programme, destination_url, sub_id)
        _allowed_url(tracking_url, programme.allowed_tracking_hosts, "tracking")
        return self._repository.add_click(OutboundClick(
            programme_id=programme_id,
            destination_url=destination_url,
            tracking_url=tracking_url,
            trip_reference=_optional_token(trip_reference),
            recommendation_reference=_optional_token(recommendation_reference),
            campaign=_optional_token(campaign),
            sub_id=_optional_token(sub_id),
            anonymous_session_hash=_anonymous_hash(anonymous_session_hash),
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

    def safe_tracking_url_for_click(self, click_id: str) -> str:
        click = self._repository.get_click(click_id)
        if not click:
            raise CommercialValidationError("outbound click does not exist")
        programme = self._repository.get_programme(click.programme_id)
        if not programme or programme.status != ProgrammeStatus.ACTIVE:
            raise CommercialValidationError("affiliate programme is not active")
        partner = self._repository.get_partner(programme.partner_id)
        if not partner or partner.status != PartnerStatus.ACTIVE:
            raise CommercialValidationError("commercial partner is not active")
        _allowed_url(click.tracking_url, programme.allowed_tracking_hosts, "tracking")
        return click.tracking_url

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


def _hosts(values: tuple[str, ...]) -> tuple[str, ...]:
    hosts = tuple(dict.fromkeys(value.strip().lower().rstrip(".") for value in values if value.strip()))
    for host in hosts:
        if ":" in host or "/" in host or _is_ip(host) or host == "localhost" or "." not in host:
            raise CommercialValidationError(f"invalid allowed host: {host}")
    return hosts


def _is_ip(host: str) -> bool:
    try:
        ip_address(host)
        return True
    except ValueError:
        return False


def _safe_https_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise CommercialValidationError("URL must be HTTPS and must not contain credentials")
    if _is_ip(parsed.hostname) or parsed.hostname == "localhost":
        raise CommercialValidationError("local and IP destinations are not allowed")
    return value.strip()


def _allowed_url(value: str, hosts: tuple[str, ...], label: str) -> None:
    safe = _safe_https_url(value)
    host = (urlsplit(safe).hostname or "").lower().rstrip(".")
    if not any(host == allowed or host.endswith(f".{allowed}") for allowed in hosts):
        raise CommercialValidationError(f"{label} host is not allowed")


def _validate_template(value: str) -> None:
    fields = {name for _, name, _, _ in Formatter().parse(value) if name}
    if not fields.issubset({"destination_url", "affiliate_id", "sub_id"}):
        raise CommercialValidationError("tracking template contains an unsupported placeholder")
    try:
        rendered = value.format(destination_url="https%3A%2F%2Fexample.test", affiliate_id="id", sub_id="")
    except (KeyError, ValueError) as exc:
        raise CommercialValidationError("tracking template is invalid") from exc
    _safe_https_url(rendered)


def _render_tracking_url(
    programme: AffiliateProgramme, destination_url: str, sub_id: str | None
) -> str:
    return programme.tracking_template.format(
        destination_url=quote(destination_url, safe=""),
        affiliate_id=quote(programme.affiliate_identifier, safe=""),
        sub_id=quote(_optional_token(sub_id) or "", safe=""),
    )


def _optional_token(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) > 100 or not all(char.isalnum() or char in "-_.:" for char in cleaned):
        raise CommercialValidationError("attribution token contains unsupported characters")
    return cleaned


def _anonymous_hash(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().lower()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", cleaned):
        raise CommercialValidationError("anonymous session value must be a SHA-256 hash")
    return cleaned
