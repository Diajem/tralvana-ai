# ADR-051: Supplier commerce boundaries

## Status

Accepted for implementation foundation. Public checkout remains disabled.

## Context

Tralvana is integrating three supplier models that must not share payment or
merchant assumptions:

- RateHawk accommodation uses supplier net rates. Tralvana adds its own markup,
  collects the customer payment as merchant of record and RateHawk deducts the
  booking cost from Tralvana's prefunded balance.
- Viator Full + Booking API keeps Viator as merchant of record. Customer payment
  uses Viator's approved hosted or API payment solution and Tralvana earns the
  agreed affiliate commission rather than adding a markup.
- Duffel flight search is live-capable, but the production payment and settlement
  method for this account is not confirmed. Duffel checkout must remain blocked
  until Duffel confirms the approved method and servicing responsibilities.

Payment details must never enter Tralvana logs, AI prompts or application
storage. Supplier credentials remain deployment secrets. Personal data passed
to suppliers must be limited to the fields required to fulfil the booking.

## Decision

Add a provider-neutral commerce policy registry and decimal-based pricing model.
Every checkout operation must resolve a policy before payment or supplier
booking. Unknown supplier/product combinations fail closed.

The first policies are:

| Supplier | Product | Merchant | Customer payment | Supplier settlement | Revenue | Checkout |
| --- | --- | --- | --- | --- | --- | --- |
| RateHawk | Accommodation | Tralvana | Tralvana gateway | Prefunded balance | Markup | Pending API approval and certification |
| Viator | Experience | Viator | Viator hosted/API payment | Viator collects | Commission | Pending Full + Booking activation and certification |
| Duffel | Flight | Unconfirmed | Unconfirmed | Unconfirmed | Blocked | Pending written payment-model confirmation |

No public checkout route, gateway secret, card field, supplier booking call or
automatic refund is introduced by this foundation.

## Required next slices

1. **Implemented foundation:** durable checkout intents, payment attempts,
   supplier bookings and refunds with idempotency, traveller ownership,
   monetary constraints and guarded checkout status transitions. Supplier
   quote snapshots and cancellation orchestration remain part of each approved
   supplier adapter; no public transaction route is enabled by this ledger.
2. A Stripe Payment Element adapter for Tralvana-merchant transactions after the
   Stripe account, webhook signing secret, settlement currencies and refund
   policy are confirmed.
3. RateHawk search, recheck, booking retrieval and cancellation adapters after
   sandbox credentials and certification guidance arrive.
4. Viator availability, hold, booking, voucher and cancellation adapters plus
   its hosted payment integration after Full + Booking access is enabled.
5. Duffel order creation only after Duffel confirms the live account's payment
   method, markup rules, balance/refund flow and support responsibilities.
6. Privacy notice, records of processing, processor contracts, retention rules,
   data-subject export/deletion and incident procedures before public launch.

## Consequences

- Supplier-specific commercial rules become explicit and testable.
- A supplier cannot become publicly bookable merely because a search API key is
  installed.
- Pricing uses decimal values and rejects mixed currencies or prohibited markup.
- Commerce work can continue while external supplier approvals are pending.
