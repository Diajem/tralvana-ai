# HBX Hotels Integration

## Status

Tralvana has a provider-neutral HBX Hotels sandbox integration for live
availability and a separate transactional adapter for check-rate, booking and
cancellation foundations. It is disabled by default. No public checkout or
payment route is enabled, and sandbox inventory is labelled unavailable for
purchase.

The integration belongs to **Diajem Global Ltd**. Credentials must be stored
only in backend/deployment secrets as `HBX_HOTELS_API_KEY` and
`HBX_HOTELS_SECRET`.

## Non-redirect principle

HBX's Booking API is suitable for Tralvana's product rule because availability,
rate confirmation, reservation creation and cancellation can be performed by
Tralvana's backend without sending the customer to another booking website.
Redirect affiliate checkout is not part of this integration. The old Expedia
affiliate checkout panels have been removed from flight and accommodation
details so the app has no customer-facing supplier redirect.

## Runtime modes

| Mode | Registered suppliers |
|---|---|
| `MOCK` | Mock only; no external request |
| `LIVE_SANDBOX` | Duffel Stays (legacy alias) |
| `DUFFEL_SANDBOX` | Duffel Stays only |
| `HBX_SANDBOX` | HBX Hotels only |
| `MULTI_SANDBOX` | HBX first, Duffel fallback |

Credentials do not activate a mode. Changing a mode requires an application
restart. Missing credentials fail startup without printing values.

## Architecture

- `HbxHotelsProvider` implements search through the existing Intelligence
  Gateway, so supplier priority and failover remain centralised.
- `HbxHotelBookingClient` implements `AccommodationBookingProvider`. It is not
  registered with the discovery gateway, so transaction calls are never cached
  or automatically retried.
- The booking command and result records are provider-neutral; a later Duffel
  or other adapter can implement the same contract.
- Signed `Api-key` and timestamped `X-Signature` headers are created at request
  time. The secret never appears in results or logs.

## Destination catalogue and quota protection

HBX Booking API searches use destination codes. Content API data is static and
must not be fetched during every customer search. Tralvana resolves destination
names from the `hbx_destinations` table added by migration `0007`.

After migrations and backend secrets are configured, run:

```bash
python scripts/sync_hbx_destination_catalog.py
```

Bounded/resumable examples:

```bash
python scripts/sync_hbx_destination_catalog.py --page-size 500 --max-pages 10
python scripts/sync_hbx_destination_catalog.py --start-index 5001 --max-pages 10
```

The command refuses to run without `DATABASE_URL`, allows at most 1,000 records
per request and 50 requests per invocation, and prints counts only. It is never
called during startup, customer search, tests or CI.

## Search mapping

The adapter sends check-in/check-out dates, the locally resolved destination
code, one occupancy record per room, at least one adult per room, an explicit
age for every child, and bounded result/rate counts.

Each returned rate retains the HBX `rateKey`, `rateType`, total, currency,
board, cancellation policies, taxes and property code. Static content that
availability omits—reviews, accessibility, centre distance, amenities and
images—remains neutral and explicitly disclosed. It is never fabricated.

## Transaction safety rules

1. A `RECHECK` rate must pass `/checkrates` and become `BOOKABLE`.
2. The verified total and currency must be shown to the customer.
3. `customer_approved=True` is mandatory before booking.
4. Every child requires an age and every guest is assigned to a room.
5. HBX `tolerance` is explicit; a confirmation outside the approved
   price/currency boundary is rejected for manual handling.
6. Cancellation defaults to simulation. Real cancellation requires a second
   explicit customer approval.
7. Booking confirmation uses HBX's required minimum 60-second timeout, while
   ordinary search and read operations retain the normal shorter timeout.

These controls do not create a public checkout. Payment, idempotency records,
booking persistence, vouchers, webhooks, servicing and certification remain
go-live prerequisites.

## Safe activation sequence

1. Apply migration `0007`.
2. Store the sandbox API key and secret in backend secrets.
3. Sync the destination catalogue once.
4. Set the mode to `HBX_SANDBOX` in a non-production environment and restart.
5. Verify read-only availability with future dates and explicit child ages.
6. Complete HBX technical certification using sandbox reservations only.
7. Build and validate checkout, persistence and support flows.
8. Enable production only after commercial and compliance approval.

No step enables a redirect booking journey.
