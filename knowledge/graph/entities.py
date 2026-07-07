from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Country:
    id: str
    name: str
    iso_code: str            # ISO 3166-1 alpha-2
    continent: str
    capital_city_id: str | None = None
    languages: list[str] = field(default_factory=list)
    currency_code: str = ""
    safety_level: str = "low"  # low | medium | high | critical


@dataclass
class City:
    id: str
    name: str
    country_id: str
    timezone: str = ""
    population: int | None = None
    tags: list[str] = field(default_factory=list)
    # tags: beach, mountain, urban, historic, desert, tropical, cultural, coastal


@dataclass
class Airport:
    id: str
    name: str
    iata_code: str
    city_id: str
    is_international: bool = True


@dataclass
class Hotel:
    id: str
    name: str
    city_id: str
    star_rating: int = 3
    price_tier: str = "mid-range"  # budget | mid-range | luxury
    amenities: list[str] = field(default_factory=list)


@dataclass
class Airline:
    id: str
    name: str
    iata_code: str
    hub_airport_id: str
    tier: str = "economy"  # economy | premium | luxury


@dataclass
class Attraction:
    id: str
    name: str
    city_id: str
    attraction_type: str = "landmark"
    # landmark | natural | cultural | entertainment | sport | religious | historic
    tags: list[str] = field(default_factory=list)


@dataclass
class Restaurant:
    id: str
    name: str
    city_id: str
    cuisine: str = ""
    price_tier: str = "mid-range"  # budget | mid-range | luxury
    tags: list[str] = field(default_factory=list)


@dataclass
class Museum:
    id: str
    name: str
    city_id: str
    category: str = "history"
    # art | history | science | sport | natural | military | cultural
    tags: list[str] = field(default_factory=list)


@dataclass
class Sport:
    id: str
    name: str
    category: str = "team"
    # team | individual | water | winter | extreme | motorsport


@dataclass
class FootballClub:
    id: str
    name: str
    city_id: str
    league: str = ""
    stadium: str = ""
    founded_year: int | None = None


@dataclass
class Event:
    id: str
    name: str
    city_id: str
    event_type: str = "festival"
    # festival | conference | sport | concert | cultural | exhibition
    month: int | None = None  # peak month
    tags: list[str] = field(default_factory=list)


@dataclass
class Transport:
    id: str
    name: str
    transport_type: str = "metro"
    # rail | metro | bus | ferry | taxi | rideshare | tram | cable-car
    city_id: str | None = None


@dataclass
class VisaRequirement:
    id: str
    from_country_iso: str   # passport country ISO
    to_country_iso: str     # destination country ISO
    requirement: str = "required"
    # visa-free | visa-on-arrival | evisa | required
    max_stay_days: int | None = None
    notes: str = ""


@dataclass
class Currency:
    id: str
    code: str    # ISO 4217
    name: str
    symbol: str
    country_isos: list[str] = field(default_factory=list)


@dataclass
class Weather:
    id: str
    city_id: str
    month: int           # 1–12
    avg_temp_c: float = 20.0
    condition: str = "sunny"
    # sunny | partly-cloudy | cloudy | rainy | snowy | hot | humid | cold | mild
    season: str = "summer"  # spring | summer | autumn | winter


@dataclass
class TravellerDNA:
    traveller_id: str
    primary_type: str
    secondary_types: list[str] = field(default_factory=list)
    confidence: float = 0.0
    traits: dict[str, float] = field(default_factory=dict)
    inferred_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "traveller_id": self.traveller_id,
            "primary_type": self.primary_type,
            "secondary_types": self.secondary_types,
            "confidence": round(self.confidence, 2),
            "traits": {k: round(v, 2) for k, v in self.traits.items()},
            "inferred_at": self.inferred_at,
        }
