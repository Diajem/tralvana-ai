# RateHawk accommodation integration

## Current state

RateHawk issued Diajem Group Ltd sandbox credentials on 25 September 2026.
Credentials belong only in deployment secrets and must never be committed.
Customer-facing search and booking remain disabled until the destination
catalogue, complete booking lifecycle and RateHawk certification are ready.

## Required environment variables

| Variable | Purpose |
| --- | --- |
| `RATEHAWK_SANDBOX_KEY_ID` | HTTP Basic username for sandbox |
| `RATEHAWK_SANDBOX_API_KEY` | HTTP Basic password for sandbox |
| `RATEHAWK_PRODUCTION_KEY_ID` | Production username, after certification |
| `RATEHAWK_PRODUCTION_API_KEY` | Production password, after certification |

Do not reuse sandbox IDs, content or credentials in production.

## Supplier-required flow

1. Download, store and regularly update RateHawk static hotel and region data.
2. Search by region, coordinates, or mapped hotel IDs.
3. Retrieve hotelpage only after the traveller selects a property.
4. Prebook the selected rate and obtain explicit consent if the price changes.
5. Create and start the booking process only after the traveller confirms.
6. Poll final booking status (and later add a webhook for redundancy).
7. Support retrieval and cancellation after booking.

RateHawk must be one contributor to Tralvana's accommodation market search.
It must never suppress valid inventory from HBX or Duffel Stays.

## Safe sandbox verification

The read-only verifier searches RateHawk's two mandatory certification hotels
with two adults and children aged 7 and 10. It never calls a booking endpoint.

```bash
python scripts/verify_ratehawk_sandbox.py
```

## Certification gate

Before requesting certification, Tralvana must map hotels `10004834` and
`8819557`, implement children and multi-room rules, price-change consent,
tax/meal/cancellation display, resilient final-status polling, cancellation,
sanitised audit logs, and a complete search-to-cancellation test flow.
Production access must remain blocked until RateHawk approves certification.
