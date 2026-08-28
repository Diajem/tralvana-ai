# Viator integration preparation

## Current state

Tralvana has no active Viator integration. T-080 adds only a disabled,
provider-neutral experiences contract and a fail-closed Viator adapter shell.
It contains no API URL, credential reference, external request, booking route,
payment path or frontend activation.

The requested commercial outcome is an international, fully transactional
experience flow inside Tralvana. Redirect-only Basic or Full affiliate access
does not meet that product rule. Viator qualification must establish whether
Diajem Global Ltd is eligible for either:

1. Merchant API access, where Diajem Global Ltd is merchant of record; or
2. Full + Booking affiliate access, where the transaction remains inside
   Tralvana and Viator is merchant of record.

## Consultation brief

- Appointment: Tuesday, 1 September 2026 at 10:00 London time.
- Company: Diajem Global Ltd.
- Product: Tralvana, a pre-launch international AI travel-planning and booking
  platform.
- Customer flow: search, price, pay, book, receive confirmation/voucher, cancel
  and manage reservations inside Tralvana.
- Markets: international origins, destinations, nationalities and currencies;
  not UK-only.
- Stage: pre-launch; HBX Hotels and Duffel Flights sandbox search integrations
  already exist, while all public transactions remain disabled.
- Safety position: no live bookings or payments before supplier qualification,
  KYC, certification, servicing and refund controls are complete.

## Commercial and qualification questions

1. Which programme best fits Tralvana: Merchant API or Full + Booking affiliate?
2. Is a pre-launch startup eligible, and what evidence, forecast or traffic
   threshold is required?
3. Can every customer-facing step stay inside Tralvana without a redirect?
4. Who is merchant of record in the offered model?
5. Who contracts with, charges and refunds the customer?
6. What deposit, credit, guarantee or reserve applies before production?
7. What commissions, net rates, settlement schedules, chargeback rules and
   currency-conversion terms apply?
8. Which countries, destinations, languages and customer currencies are
   supported for Tralvana's planned launch?

## Technical and certification questions

1. Which sandbox environment, credentials and endpoint set will Tralvana
   receive after qualification?
2. Which ingestion model is recommended at startup: real-time search, local
   catalogue ingestion, or a hybrid?
3. Which endpoints and request limits apply to product search, product details,
   availability schedules, real-time availability and pricing?
4. Which booking flow is assigned: single booking hold/book or cart hold/book?
5. What are the required hold expiry, idempotency and price-revalidation rules?
6. Which payment integration is available, and what PCI DSS scope does it place
   on Tralvana?
7. What booking timeout and uncertain-outcome recovery flow is mandatory?
8. How are PENDING/manual-confirmation bookings surfaced and rechecked?
9. How are vouchers, barcodes and supplier confirmations retrieved and delivered?
10. What are the required cancel-quote, cancellation-reason, refund and final
    cancellation flows?
11. Are supplier cancellations and amendments delivered by webhook, polling,
    modified-since feeds, or a combination? What acknowledgement SLA applies?
12. What post-booking customer service must Diajem Global Ltd provide, including
    operating hours and emergency coverage?
13. What frontend and backend certification artefacts, test bookings, screen
    recordings and security evidence are required?
14. What is the typical development, certification and production-approval
    timeline after credentials are issued?

## Recorded implementation gates

The Viator adapter must remain disabled until all of these are true:

- programme and merchant-of-record model are confirmed in writing;
- sandbox credentials are stored only as Render secrets;
- approved endpoint access and rate limits are documented;
- product, availability, price, age-band and booking-question mappings are tested;
- hold, booking-status recovery, voucher and cancellation workflows are tested;
- payment and PCI responsibilities are implemented and reviewed;
- persistence, audit, idempotency and customer-approval boundaries are complete;
- customer-service, cancellation and refund operating procedures are ready;
- Viator frontend and backend certification are passed; and
- production access is explicitly approved.

## Official references reviewed

- [Viator Partner API technical documentation](https://docs.viator.com/partner-api/technical/)
- [Viator API certification guide](https://partnerresources.viator.com/travel-commerce/certification/)
- [Viator certification back-end checks](https://partnerresources.viator.com/travel-commerce/back-end-checks/)
- [Viator API access levels](https://partnerresources.viator.com/travel-commerce/levels-of-access/)
- [Viator Merchant API solution](https://partnerresources.viator.com/travel-commerce/merchant/)
