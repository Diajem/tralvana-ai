# ADR-029: Safe Affiliate Links

**Date**: 2026-07-19

**Status**: Accepted

**Task**: T-043

## Context

T-042 created a durable commercial ledger but deliberately exposed no
traveller-facing redirect. Tralvana already publishes several tracked affiliate
links, while other partner names on the existing site resolve only to ordinary
websites or placeholder IDs. Treating all of them as active would create false
commission expectations, and accepting arbitrary destinations would create an
open-redirect risk.

## Decision

1. Seed only affiliate links already verified in Tralvana's published source:
   Expedia, four Awin merchants, and six Amazon regions.
2. Keep Travelpayouts widget account values as placement configuration, not as
   ordinary redirect destinations. Prefer the deployed `trs=432320` value over
   the stale legacy helper value.
3. Require both the partner and programme to be active before creating or
   following an outbound link.
4. Store explicit destination and tracking host allow-lists per programme.
   Permit HTTPS only, reject credentials, localhost, IP addresses, and host
   suffix tricks, and revalidate the stored tracking URL at redirect time.
5. Require the traveller-facing UI to display the programme disclosure before
   it sends an acknowledged link request.
6. Record attribution without raw personal data. Public input accepts only
   restricted reference tokens and an explicitly formatted SHA-256 session hash.
7. Keep inventory, price, checkout, payment, refunds, and fulfilment with the
   partner. A Tralvana recommendation is not presented as a reservation.

## Consequences

- A disclosed recommendation-to-partner journey can now produce auditable click
  attribution without making Tralvana a booking or payment processor.
- Docker startup migrates and idempotently seeds the verified catalogue.
- Ordinary links and placeholder programmes remain inactive until a genuine
  tracked link or public affiliate identifier is supplied and verified.
- Conversion ingestion, partner webhook authentication, reconciliation, and
  payout reporting remain separate future work.
