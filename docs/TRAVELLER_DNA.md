# Traveller DNA

Traveller DNA is TravelOS's system for inferring a traveller's primary travel archetype from their Traveller Intelligence Profile (TIP). DNA shapes every AI agent recommendation — from destination selection to hotel tier to experience curation to safety context.

## The 12 DNA Types

| DNA Type | Primary Signals | TravelOS Behaviour |
|----------|----------------|-------------------|
| **Explorer** | 3+ diverse interests, broad curiosity | Multi-city routes, off-the-beaten-path destinations |
| **Luxury Traveller** | First/business cabin, luxury budget | 5-star hotels, private transfers, exclusive experiences |
| **Budget Traveller** | Backpacker/budget style, hostel accommodation | Budget airlines, free attractions, hostel options |
| **Football Traveller** | Sport interests | Match schedules, stadium tours, fan zones |
| **Food Traveller** | food_drink interests, dietary preferences | Michelin restaurants, food tours, market visits |
| **Photography Traveller** | Nature/culture/city interests | Golden-hour spots, iconic backdrops, photography tours |
| **Family Traveller** | Resort accommodation, beach/wellness | Child-friendly venues, resort stays, low-risk routes |
| **Business Traveller** | Business cabin, business interests, airline loyalty | Airport lounges, city-centre hotels, fast Wi-Fi |
| **Adventure Traveller** | Adventure/nature interests | National parks, trekking, diving, extreme sports |
| **Digital Nomad** | City interests, apartment accommodation | Co-working spaces, long-stay apartments, monthly rentals |
| **Pilgrimage Traveller** | Religious/pilgrimage/spiritual interests | Sacred sites, holy cities, religious events |
| **Diaspora Traveller** | Heritage/diaspora/roots interests | Cultural heritage, homecoming trips, ancestral towns |

## Inference Algorithm

### Input: TIP Profile

```json
{
  "id": "traveller_abc",
  "preferences": {
    "budget_style": "balanced",
    "cabin_class": "economy",
    "travel_interests": ["food_drink", "culture", "heritage"],
    "accommodation_type": "hotel",
    "meal": "halal"
  },
  "loyalty": {
    "airline_programs": []
  }
}
```

### Phase 1 — 12 Trait Scores (0.0–1.0)

| Trait | Primary TIP Signals |
|-------|---------------------|
| `adventure_seeking` | adventure, nature, sport interests |
| `luxury_orientation` | first/business cabin; luxury/comfort budget |
| `budget_consciousness` | backpacker/budget style; hostel accommodation |
| `cultural_curiosity` | culture, history interests; breadth of interests |
| `food_focus` | food_drink interest; dietary requirements |
| `sport_focus` | sport, adventure interests |
| `business_orientation` | business cabin; airline loyalty; business interest |
| `family_orientation` | resort accommodation; beach/wellness interests |
| `digital_mobility` | city interests; apartment accommodation |
| `photography_tendency` | nature/culture/city interests (proxy) |
| `spiritual_orientation` | religious, pilgrimage, spiritual interests |
| `heritage_connection` | heritage, diaspora, roots, family interests |

### Phase 2 — DNA Type Scores

Each DNA type receives a weighted score derived from relevant trait scores. The highest-scoring type is the **primary DNA**. Types scoring above 0.15 become **secondary types**.

### Output: TravellerDNA

```python
from ai.intelligence import dna_inference_service

dna = dna_inference_service.infer(profile)

dna.primary_type       # "Diaspora Traveller"
dna.secondary_types    # ["Food Traveller", "Explorer"]
dna.confidence         # 0.73
dna.traits             # {"heritage_connection": 0.85, "food_focus": 0.50, ...}
dna.inferred_at        # "2026-07-07T14:32:00Z"
```

## DNA Ontology

```
TravellerDNA (abstract)
├── Independent (self-directed)
│   ├── Explorer
│   ├── Budget Traveller
│   ├── Adventure Traveller
│   └── Digital Nomad
├── Culture-Led
│   ├── Photography Traveller
│   ├── Food Traveller
│   ├── Pilgrimage Traveller
│   └── Diaspora Traveller
├── Comfort-Led
│   ├── Luxury Traveller
│   └── Family Traveller
└── Purpose-Led
    ├── Business Traveller
    └── Football Traveller
```

## TIP Field to DNA Mapping

| TIP Field | DNA Types Influenced |
|-----------|---------------------|
| `budget_style: luxury` | Luxury Traveller, Business Traveller |
| `budget_style: backpacker` | Budget Traveller, Adventure Traveller |
| `cabin_class: first` | Luxury Traveller |
| `cabin_class: business` | Business Traveller, Luxury Traveller |
| `travel_interests: sport` | Football Traveller, Adventure Traveller |
| `travel_interests: food_drink` | Food Traveller |
| `travel_interests: religious` | Pilgrimage Traveller |
| `travel_interests: heritage` | Diaspora Traveller |
| `accommodation_type: hostel` | Budget Traveller |
| `accommodation_type: resort` | Family Traveller, Luxury Traveller |
| `accommodation_type: apartment` | Digital Nomad |

## Evolution Roadmap

| Sprint | Enhancement |
|--------|-------------|
| 1 | Deterministic rule-based inference (current) |
| 2 | Infer secondary DNA from past trip destination history |
| 3 | ML model trained on anonymised trip patterns |
| 4 | Real-time DNA drift detection as preferences evolve |
