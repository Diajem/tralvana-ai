from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RelationshipType(str, Enum):
    # Geographic
    LOCATED_IN = "LOCATED_IN"        # Hotel/Museum/Attraction → City, City → Country
    BELONGS_TO = "BELONGS_TO"        # Restaurant/FootballClub → City
    IN_REGION = "IN_REGION"          # City → Region
    HAS_REGION = "HAS_REGION"        # Country → Region
    NEIGHBOUR = "NEIGHBOUR"          # Country ↔ Country

    # Transport
    SERVES = "SERVES"                # Airport → City, Restaurant → Cuisine (overloaded)
    CONNECTS = "CONNECTS"            # RailStation → City, Airport ↔ Airport
    OPERATES_FROM = "OPERATES_FROM"  # Airline → Airport (hub)

    # Economy / Society
    USES_CURRENCY = "USES_CURRENCY"  # Country → Currency
    SPEAKS = "SPEAKS"                # Country → Language

    # Experience
    NEAR = "NEAR"                    # Attraction → City
    PART_OF = "PART_OF"              # Event → City
    HOSTS = "HOSTS"                  # City → SportsVenue; SportsVenue → Event
    PLAYS_IN = "PLAYS_IN"            # FootballClub → City (home city)
    PLAYS_AT = "PLAYS_AT"            # FootballClub → SportsVenue

    # Seasonal / Environmental
    HAS_WEATHER = "HAS_WEATHER"      # City → Weather
    HAS_SEASON = "HAS_SEASON"        # City/Region → TravelSeason

    # Regulatory
    REQUIRES_VISA = "REQUIRES_VISA"  # Country → Country (via VisaRequirement node)

    # Traveller (for future use — traveller edges not stored in the static graph)
    HAS_DNA = "HAS_DNA"              # Traveller → TravellerDNA
    INTERESTED_IN = "INTERESTED_IN"  # Traveller → Interest (tag string as target metadata)
    VISITED = "VISITED"              # Traveller → City
    PREFERS = "PREFERS"              # Traveller → Airline
    VISITS = "VISITS"                # Trip → City (destination)


@dataclass
class Relationship:
    source_id: str
    source_type: str
    relationship_type: RelationshipType
    target_id: str
    target_type: str
    weight: float = 1.0     # 0.0–1.0 strength/confidence
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"({self.source_type}:{self.source_id})"
            f"-[{self.relationship_type.value}]->"
            f"({self.target_type}:{self.target_id})"
        )
