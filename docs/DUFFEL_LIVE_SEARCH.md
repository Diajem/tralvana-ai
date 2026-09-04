# Production Duffel search

T-081 connects search in Tralvana AI (app.tralvana.com). It does not enable bookings or payments.

## Configuration

| Product | Mode | Credential | Response source |
| --- | --- | --- | --- |
| Flights | `TRALVANA_FLIGHT_PROVIDER_MODE=LIVE` | `DUFFEL_FLIGHTS_API_TOKEN` | `DUFFEL_LIVE` |
| Stays | `TRALVANA_ACCOMMODATION_PROVIDER_MODE=LIVE` | `DUFFEL_STAYS_API_TOKEN` | `DUFFEL_STAYS_LIVE` |

Each dedicated credential overrides the legacy `DUFFEL_API_TOKEN`. An explicitly empty override fails startup. LIVE requires a `duffel_live_` token; sandbox modes reject live credentials. Keep mock fallback disabled to surface provider access errors. Other supplier modes remain available.

Duffel must enable the relevant product for the credential's organisation. Completing payment details alone does not verify API access. Set each product independently after verifying permissions. Store tokens only in the deployment's secret environment, never in source control or browser frontend variables.

## Verification

Run from the deployed repository with the corresponding live mode and token configured:

```sh
python services/api/scripts/verify_duffel_live_search.py --product flights
python services/api/scripts/verify_duffel_live_search.py --product stays
```

The verifier only allows offer requests, place suggestions and Stays searches. It reports status codes, provider error codes, result counts and limited offer fields without credentials. It never calls order, booking or payment endpoints. Stays verifies a London family stay with a child's age.

Successful search must return AVAILABLE and the expected live source. An access-denied response requires Duffel to enable the product; do not hide it with mock results. Real offers still require repricing and a separately implemented booking lifecycle before purchase is available.

## Regression checks

Production routing and provenance, separate bearer credentials, cross-environment rejection, empty overrides, the Duffel Stays data envelope, child ages and no booking requests are covered by `services/api/tests/test_duffel_production_search.py`.
