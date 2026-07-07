from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RelationshipType(str, Enum):
    LOCATED_IN = "LOCATED_IN"        # City → Country, Airport → City, Hotel → City
    BELONGS_TO = "BELONGS_TO"        # FootballClub → City, Restaurant → City
    SERVES = "SERVES"                # Airline → Airport (hub or route)
    OPERATES_FROM = "OPERATES_FROM"  # Airline → Airport
    HAS_DNA = "HAS_DNA"              # Traveller → TravellerDNA
    INTERESTED_IN = "INTERESTED_IN"  # Traveller → Interest tag
    VISITED = "VISITED"              # Traveller → City
    DEPARTS_FROM = "DEPARTS_FROM"    # Trip → Airport
    REQUIRES_VISA = "REQUIRES_VISA"  # Country → Country (via VisaRequirement)
    USES_CURRENCY = "USES_CURRENCY"  # Country → Currency
    HAS_WEATHER = "HAS_WEATHER"      # City → Weather
    NEAR = "NEAR"                    # Attraction → City
    PART_OF = "PART_OF"              # Museum → Attraction group, Event → City
    HOSTS = "HOSTS"                  # City → Event, City → FootballClub
    HAS_CUISINE = "HAS_CUISINE"      # Restaurant → Cuisine tag
    COMPETES_IN = "COMPETES_IN"      # FootballClub → League
    CONNECTS = "CONNECTS"            # Airport → Airport (route)
    NEIGHBOUR = "NEIGHBOUR"          # Country → Country (geographic neighbour)


@dataclass
class Relationship:
    source_id: str
    source_type: str
    relationship_type: RelationshipType
    target_id: str
    target_type: str
    weight: float = 1.0   # 0.0–1.0 strength/confidence
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"({self.source_type}:{self.source_id})"
            f"-[{self.relationship_type.value}]->"
            f"({self.target_type}:{self.target_id})"
        )
