# Travel Ontology

The TravelOS Travel Ontology defines the conceptual vocabulary of the knowledge graph — entity types, relationship semantics, and the controlled vocabularies (tag lists, enums) used throughout the system.

## Entity Hierarchy

```
TravelEntity (abstract)
├── GeographicEntity
│   ├── Country
│   ├── City
│   └── Airport
├── AccommodationEntity
│   └── Hotel
├── TransportEntity
│   ├── Airline
│   └── Transport
├── ExperienceEntity
│   ├── Attraction
│   ├── Restaurant
│   ├── Museum
│   ├── Event
│   └── Sport
├── SportEntity
│   └── FootballClub
├── RegulatoryEntity
│   └── VisaRequirement
├── EconomicEntity
│   └── Currency
├── EnvironmentalEntity
│   └── Weather
└── ProfileEntity
    └── TravellerDNA
```

## Controlled Vocabularies

### budget_style (TIP)
| Value | Meaning |
|-------|---------|
| `backpacker` | Hostel, street food, free activities |
| `budget` | Budget hotels, local restaurants |
| `balanced` | Mid-range hotels, mix of dining |
| `comfort` | 4-star hotels, fine dining |
| `luxury` | 5-star hotels, first-class, private experiences |

### cabin_class (TIP)
`economy` | `business` | `first`

### accommodation_type (TIP)
`hotel` | `apartment` | `hostel` | `resort`

### travel_interests (TIP)
`beach` | `city` | `adventure` | `culture` | `food_drink` | `wellness` | `sport` | `nature` | `luxury` | `business` | `history`

### Hotel price_tier
`budget` | `mid-range` | `luxury`

### Airline tier
`economy` | `premium` | `luxury`

### Attraction attraction_type
`landmark` | `natural` | `cultural` | `entertainment` | `sport` | `religious` | `historic`

### Museum category
`art` | `history` | `science` | `sport` | `natural` | `military` | `cultural`

### Event event_type
`festival` | `conference` | `sport` | `concert` | `cultural` | `exhibition`

### Transport transport_type
`rail` | `metro` | `bus` | `ferry` | `taxi` | `rideshare` | `tram` | `cable-car`

### VisaRequirement requirement
`visa-free` | `visa-on-arrival` | `evisa` | `required`

### Country safety_level
`low` | `medium` | `high` | `critical`

### Weather condition
`sunny` | `partly-cloudy` | `cloudy` | `rainy` | `snowy` | `hot` | `humid` | `cold` | `mild`

### Weather season
`spring` | `summer` | `autumn` | `winter` | `dry` | `wet`

## Relationship Semantics

| Relationship | Cardinality | Notes |
|-------------|-------------|-------|
| `LOCATED_IN` | Many→One | A city is in one country; an airport serves one city |
| `BELONGS_TO` | Many→One | Hotels, restaurants, clubs belong to a city |
| `OPERATES_FROM` | Many→One | Airline has one hub airport |
| `USES_CURRENCY` | One→One | Country uses one primary currency |
| `HAS_WEATHER` | One→Many | City has many monthly weather records |
| `NEAR` | Many→One | Attractions are near a city |
| `PART_OF` | Many→One | Events are part of a city |
| `HAS_DNA` | One→One | Traveller has one active DNA record |
| `REQUIRES_VISA` | Many→Many | Multiple country pairs with visa rules |

## DNA Type Ontology

The 10 DNA archetypes form a hierarchy of travel motivations:

```
TravellerDNA (abstract)
├── Independent (self-directed travel)
│   ├── Explorer
│   ├── Budget
│   ├── Adventure Traveller
│   └── Digital Nomad
├── Culture-Led
│   ├── Photography Traveller
│   └── Food Traveller
├── Comfort-Led
│   ├── Luxury
│   └── Family Traveller
└── Purpose-Led
    ├── Business Traveller
    └── Football Traveller
```

## Ontology Versioning

The ontology version is stored in the `knowledge_graph` stats as `ontology_version`. Breaking changes (adding required fields, renaming entities, changing relationship semantics) require a version bump and a migration script in `scripts/migrations/`.

| Version | Changes |
|---------|---------|
| 1.0 | Initial 16 entity types, 18 relationship types, 10 DNA archetypes |
