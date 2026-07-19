# Commission reconciliation

T-044 adds a provider-neutral, operator-only path for matching affiliate reports
to Tralvana clicks, conversions, and commission records. It deliberately does
not guess the raw export fields used by Awin, Expedia, Amazon, or Travelpayouts.

## Why the canonical format exists

Affiliate networks use different column names, status values, date formats, and
identifiers. A provider adapter must be built from that provider's real report
documentation or an anonymised export. Until then, reports must be transformed
into Tralvana's strict canonical CSV outside the application.

Required columns:

| Column | Meaning |
|---|---|
| `partner_slug` | Configured Tralvana partner slug |
| `programme_name` | Exact configured programme name |
| `transaction_reference` | Provider's stable booking or transaction reference |
| `gross_value` | Booking value, non-negative, maximum two decimal places |
| `commission_amount` | Reported commission, same numeric rules |
| `currency` | Three-letter ISO currency used by that transaction |
| `conversion_status` | `PENDING`, `CONFIRMED`, `REJECTED`, or `CANCELLED` |
| `commission_status` | `EXPECTED`, `APPROVED`, `REJECTED`, or `PAID` |

Optional columns are `click_sub_id`, `commission_reference`, `booked_at`,
`approved_at`, `paid_at`, and `source`. Dates must be ISO 8601 with a timezone.
Unknown columns are rejected so a raw report containing names, emails, or other
personal data cannot be imported accidentally.

## Safe operating flow

Run a dry validation first:

```bash
PYTHONPATH=services/api python services/api/scripts/reconcile_commissions.py report.csv
```

Nothing is persisted without the explicit apply flag:

```bash
PYTHONPATH=services/api python services/api/scripts/reconcile_commissions.py report.csv --apply
```

An import with any issue is rolled back in full. Repeating the same report is
idempotent: existing transactions and commissions are updated, not duplicated.
Paid or rejected commissions and cancelled or rejected conversions cannot be
silently regressed by an older report.

## Deliberate boundaries

- No upload, webhook, public API, or admin UI is exposed before authentication.
- No raw provider report is stored.
- No provider-specific adapter is claimed without verified field documentation.
- Unmatched sales are retained but counted, allowing legitimate commission to
  be reconciled even when a partner did not return Tralvana's click sub-ID.
