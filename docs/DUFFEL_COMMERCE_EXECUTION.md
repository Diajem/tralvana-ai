# Duffel commerce execution gate — 16 September 2026

## Current, verified code position

- Duffel Flights and Stays have independent production search adapters and
  credentials. Flights search can produce `DUFFEL_LIVE`; Stays requires its
  own entitlement and a successful `DUFFEL_STAYS_LIVE` search.
- `FlightOption` and `AccommodationOption` preserve supplier offer/property/rate
  IDs internally but omit them from public JSON. Their repositories are
  in-memory dictionaries, not durable records. Recommendation prices are not
  booking quotes.
- No public order, stay booking, checkout, card, cancellation or refund route
  exists. Never advertise a search card as purchasable until the gates below
  pass. The HBX booking client is not a deployed checkout route.

## Commerce gates, in order

1. **Supplier entitlement.** Confirm the live team and credential for each
   product, run search-only verification, and identify the bookable payment
   methods and commercial terms for that specific account. A Flights token
   does not establish Stays access.
2. **Durable selection.** Persist an authenticated traveller's selected offer
   or rate and its supplier ID, source, original search time, occupancy,
   currency and supplier expiry in PostgreSQL. Enforce ownership. Do not
   trust price, supplier IDs, card details or approval flags supplied by a
   browser. Exclude sandbox/mock/affiliate results from production checkout.
3. **Fresh quote.** Retrieve the selected Flights offer and verify expiry,
   availability, price, taxes, conditions, airline/payment methods and
   passenger requirements. For Stays, create a quote from the selected rate
   and display its final price, deposit, locally payable fees, cancellation
   terms and supported payment methods. Reject a changed price until the
   traveller explicitly accepts the updated total and currency.
4. **Payment decision.** Direct supplier card payment is an in-app checkout
   option only if Duffel approves Card access, a hosted card component keeps
   PAN off Tralvana servers, and the exact supplier amount is charged. It
   cannot contain Tralvana flight markup. An independent Tralvana gateway plus
   funded Duffel Balance permits markup but makes Tralvana responsible for
   collection, reconciliation and customer refunds, and requires liquidity.
   Duffel Payments must not be assumed available in production. Choose one
   model per product before implementation; Viator's separate Merchant-of-
   Record iframe/API checkout must not be mixed into a Duffel payment.
5. **Transaction safety.** Persist checkout intent and confirmed customer
   consent before a supplier write. Use a stable idempotency key per attempt,
   one atomic state transition, a locked checkout attempt, request/response correlation,
   and a recovery path that retrieves uncertain order/booking status before
   retrying. Do not automatically retry creation after a timeout.
6. **Servicing and reconciliation.** Persist supplier references, ticket or
   stay confirmation, card/balance/gateway references, refunds, changes,
   cancellation penalties and customer notifications. Define ownership of
   disputes and after-sales support. Verify booking, amendment and cancellation
   paths in test mode first; production writes remain disabled until approved.

## Supplier questions still requiring written answers

- Which named team has live Flights and Stays search and booking access, and
  why does the Tralvana AI Stays account still return a feature-not-enabled
  response? Can the team entitlement be enabled or transferred?
- Is Duffel Card/CardPayment available to this startup in live mode for both
  Flights and Stays? Which suppliers and rate types accept it, who is Merchant
  of Record, and what PCI/3DS steps are required?
- Is Duffel Payments available to **this account** in live mode despite the
  public new-customer restriction? If not, what are the balance-funding,
  currency, refunds and payment-failure rules for a Tralvana-owned gateway?
- Which Stays rates pay profit-share, how is the payout calculated/settled,
  and can customer-facing Stays prices be marked up without losing it?
- What are our Flights API fees, per-order charges, airline mark-up limits,
  post-booking support and chargeback responsibilities? Can Duffel introduce
  an integration contact to review the proposed checkout and servicing flow?

## Site migration gate

`tralvana.com` is a separate legacy affiliate website, not the Next.js app
in this repository. Inventory and checkout must be tested end-to-end on
`app.tralvana.com` first. Then audit the actual WordPress/site links,
replace redirect-only flight/hotel/experience widgets with internally routed
product journeys, and remove old links only when each replacement is working.
Viator discovery alone is not a booking replacement: Full + Booking access,
certification and Viator's own payment checkout are separate prerequisites.

## Official references

- Duffel payment methods: https://duffel.com/docs/guides/choosing-a-payment-method
- Duffel markups: https://duffel.com/docs/guides/margin-and-markups
- Duffel Stays quotes: https://duffel.com/docs/api/v2/quotes/create-quote
- Duffel transaction response handling: https://duffel.com/docs/api/overview/response-handling
- Duffel Payment Intents: https://duffel.com/docs/api/payment-intents
