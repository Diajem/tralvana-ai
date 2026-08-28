"""Offline HBX destination catalogue.

HBX explicitly advises clients not to query Content API during customer
searches.  This catalogue is populated by a separate sync operation and gives
the live Booking API adapter a local city-name -> HBX destination-code lookup.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from travelos.persistence.hbx_orm import HbxDestinationRow
from travelos.persistence.session import (
    create_engine_from_url,
    create_session_factory,
    database_url,
    session_scope,
)


@dataclass(frozen=True)
class HbxDestination:
    code: str
    name: str
    country_code: str
    zones: tuple[dict, ...] = ()


class HbxDestinationCatalog(Protocol):
    def resolve(self, destination: str, country_code: str | None = None) -> HbxDestination | None: ...

    def upsert_many(self, destinations: list[HbxDestination]) -> int: ...


class InMemoryHbxDestinationCatalog:
    def __init__(self, destinations: list[HbxDestination] | None = None) -> None:
        self._items: dict[str, HbxDestination] = {}
        self.upsert_many(destinations or [])

    def resolve(self, destination: str, country_code: str | None = None) -> HbxDestination | None:
        candidates = _candidate_names(destination)
        countries = _country_code_aliases(country_code)
        matches = [
            item
            for item in self._items.values()
            if _normalize_name(item.name) in candidates
            and (not countries or item.country_code.upper() in countries)
        ]
        return matches[0] if len(matches) == 1 else None

    def upsert_many(self, destinations: list[HbxDestination]) -> int:
        for item in destinations:
            self._items[item.code] = item
        return len(destinations)


class SqlAlchemyHbxDestinationCatalog:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self._factory = factory

    def resolve(self, destination: str, country_code: str | None = None) -> HbxDestination | None:
        candidates = _candidate_names(destination)
        if not candidates:
            return None
        with session_scope(self._factory) as session:
            statement = select(HbxDestinationRow).where(
                HbxDestinationRow.normalized_name.in_(candidates)
            )
            countries = _country_code_aliases(country_code)
            if countries:
                statement = statement.where(HbxDestinationRow.country_code.in_(countries))
            rows = list(session.scalars(statement.limit(2)))
        if len(rows) != 1:
            return None
        row = rows[0]
        return HbxDestination(
            code=row.code,
            name=row.name,
            country_code=row.country_code,
            zones=tuple(row.zones or []),
        )

    def upsert_many(self, destinations: list[HbxDestination]) -> int:
        now = datetime.now(timezone.utc)
        with session_scope(self._factory) as session:
            for item in destinations:
                row = session.get(HbxDestinationRow, item.code)
                if row is None:
                    row = HbxDestinationRow(
                        code=item.code,
                        name=item.name,
                        normalized_name=_normalize_name(item.name),
                        country_code=item.country_code.upper(),
                        zones=list(item.zones),
                        updated_at=now,
                    )
                    session.add(row)
                else:
                    row.name = item.name
                    row.normalized_name = _normalize_name(item.name)
                    row.country_code = item.country_code.upper()
                    row.zones = list(item.zones)
                    row.updated_at = now
        return len(destinations)


def build_hbx_destination_catalog() -> HbxDestinationCatalog:
    url = database_url()
    if not url:
        return InMemoryHbxDestinationCatalog()
    engine = create_engine_from_url(url)
    return SqlAlchemyHbxDestinationCatalog(create_session_factory(engine))


def _candidate_names(value: str) -> set[str]:
    value = (value or "").strip()
    if not value:
        return set()
    candidates = {_normalize_name(value)}
    if "," in value:
        candidates.add(_normalize_name(value.split(",", 1)[0]))
    return {candidate for candidate in candidates if candidate}


def _normalize_name(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.casefold()).strip()


def _country_code_aliases(value: str | None) -> tuple[str, ...]:
    country = (value or "").strip().upper()
    if not country:
        return ()
    if country in {"GB", "UK"}:
        return ("GB", "UK")
    return (country,)
