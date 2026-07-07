# Travel Ontology

The TravelOS Travel Ontology defines the conceptual vocabulary of the Travel Intelligence Layer — entity types, relationship semantics, and the controlled vocabularies used throughout the system.

## Entity Hierarchy

```
TravelEntity (abstract)
├── GeographicEntity
│   ├── Country
│   ├── Region
│   ├── City
│   ├── Airport
│   └── RailStation
├── AccommodationEntity
│   └── Hotel
├── TransportEntity
│   ├── Airline
│   └── Transport
├── CulinaryEntity
│   ├── Restaurant
│   └── Cuisine
├── CulturalEntity
│   ├── Attraction
│   ├── Museum
│   └── Event
├── SportEntity
│   ├── FootballClub
│   └── SportsVenue
├── EnvironmentalEntity
│   ├── Weather
│   └── TravelSeason
├── SocioeconomicEntity
│   ├── Currency
│   └── Language
├── RegulatoryEntity
│   └── VisaRequirement
└── ProfileEntity
    └── TravellerDNA
```

## Controlled Vocabularies

### TIP: `budget_style`
| Value | Meaning |
|-------|---------|
| `backpacker` | Hostel, street food, free activities |
| `budget` | Budget hotels, local restaurants |
| `balanced` | Mid-range hotels, mix of dining |
| `comfort` | 4-star hotels, fine dining |
| `luxury` | 5-star hotels, first-class, private experiences |

### TIP: `cabin_class`
`economy` | `business` | `first`

### TIP: `accommodation_type`
`hotel` | `apartment` | `hostel` | `resort`

### TIP: `travel_interests`
`beach` | `city` | `adventure` | `culture` | `food_drink` | `wellness` | `sport` | `nature` | `luxury` | `business` | `history` | `religious` | `pilgrimage` | `spiritual` | `heritage` | `diaspora` | `roots` | `family`

### Hotel / Restaurant: `price_tier`
`budget` | `mid-range` | `luxury`

### Airline: `tier`
`economy` | `premium` | `luxury`

### Airline: `alliance`
`Star Alliance` | `OneWorld` | `SkyTeam` | `""` (independent)

### Attraction: `attraction_type`
`landmark` | `natural` | `cultural` | `entertainment` | `sport` | `religious` | `historic`

### Museum: `category`
`art` | `history` | `science` | `sport` | `natural` | `military` | `cultural`

### SportsVenue: `venue_type`
`stadium` | `arena` | `circuit` | `court` | `velodrome` | `ground`

### Event: `event_type`
`festival` | `conference` | `sport` | `concert` | `cultural` | `exhibition` | `pilgrimage`

### Transport: `transport_type`
`rail` | `metro` | `bus` | `ferry` | `taxi` | `rideshare` | `tram` | `cable-car` | `monorail`

### VisaRequirement: `requirement`
`visa-free` | `visa-on-arrival` | `evisa` | `required`

### Country: `safety_level`
`low` | `medium` | `high` | `critical`

### Weather: `condition`
`sunny` | `partly-cloudy` | `cloudy` | `rainy` | `snowy` | `hot` | `humid` | `cold` | `mild` | `harmattan`

### Weather / TravelSeason: `season`
`spring` | `summer` | `autumn` | `winter` | `dry` | `wet` | `harmattan`

### TravelSeason: `season_type`
`peak` | `shoulder` | `off-peak` | `festival` | `dry` | `wet` | `harmattan`

### Region: `region_type`
`state` | `province` | `territory` | `emirate` | `county` | `district`

## Relationship Semantics

| Relationship | Cardinality | Semantic |
|-------------|-------------|----------|
| `LOCATED_IN` | Many→One | Spatial containment (hotel in city, city in country) |
| `BELONGS_TO` | Many→One | Membership (restaurant in city, transport in city) |
| `SERVES` | Many→Many | Airport serves city; restaurant serves cuisine |
| `PLAYS_IN` | Many→One | Football club plays home games in city |
| `PLAYS_AT` | Many→One | Football club plays at sports venue |
| `HOSTS` | One→Many | City hosts sports venues |
| `OPERATES_FROM` | Many→One | Airline's hub airport |
| `USES_CURRENCY` | One→One | Country's primary currency |
| `SPEAKS` | Many→Many | Languages spoken in country |
| `HAS_REGION` | One→Many | Country has administrative regions |
| `IN_REGION` | Many→One | City is in a region |
| `HAS_WEATHER` | One→Many | City has monthly weather records |
| `HAS_SEASON` | Many→Many | City experiences travel seasons |
| `NEAR` | Many→One | Attraction is near a city |
| `PART_OF` | Many→One | Event is part of a city's calendar |
| `CONNECTS` | Many→One | Rail station connects to a city |
| `REQUIRES_VISA` | Many→Many | Passport country → destination visa rule |
| `HAS_DNA` | One→One | Traveller's inferred DNA |
| `VISITED` | Many→Many | Traveller has visited cities |
| `PREFERS` | Many→Many | Traveller prefers airlines |
| `VISITS` | Many→Many | Trip visits destinations |
| `INTERESTED_IN` | Many→Many | Traveller interested in interests |

## Ontology Versioning

| Version | Changes |
|---------|---------|
| 2.0 | 20 entity types, 22 relationship types, 12 DNA archetypes (current) |
| 1.0 | 16 entity types, 18 relationship types, 10 DNA archetypes (superseded) |

Breaking changes (field renames, relationship semantic changes) require a version bump and a migration script in `scripts/migrations/`.
