# Safe affiliate links

T-043 turns Tralvana's verified public affiliate configuration into a controlled
commission path. It does not add booking or payment handling.

## What is active

The seed catalogue reuses tracked links already published by Tralvana:

- Expedia (`mZObD29`)
- Awin publisher `1773696`: Bee Parking, TTfone, WorldSIM, and GoWithGuide
- Amazon Associates: UK, US, Spain, Germany, France, and Italy

The existing Travelpayouts widget account is recorded as `trs=432320` and
`shmarker=493614`. Widget scripts remain placements rather than redirect links;
the older `trs=232507` value is intentionally not used.

World Nomads, SafetyWing, Holafly, Priority Pass, GetTransfer, Bookaway, and
direct Booking.com/Viator/Skyscanner programmes are not activated from ordinary
website URLs or placeholders. Add them only after a real tracked link or public
affiliate identifier has been verified.

## Seed the catalogue

After migrations:

```bash
PYTHONPATH=services/api python services/api/scripts/seed_commercial_catalogue.py
```

The command requires `DATABASE_URL`, is idempotent, and never overwrites an
existing programme. Affiliate passwords and private API credentials do not
belong in the catalogue.

## Link flow

1. The UI reads active programmes from `GET /commercial/programmes`.
2. Disclosure is shown before the traveller chooses a partner.
3. `POST /commercial/outbound-links` requires explicit disclosure acknowledgement.
4. The API validates HTTPS and exact/subdomain allow-lists, then records the click.
5. The returned same-origin redirect path revalidates the stored tracking host
   before redirecting.

The click table contains attribution references and an optional already-hashed
anonymous session value. It contains no email address, IP address, user-agent,
or traveller name.

## Security boundary

- Only active programmes belonging to active partners can create links.
- URLs containing credentials, localhost, IP addresses, non-HTTPS schemes, or
  unapproved hosts are rejected.
- Only `destination_url`, `affiliate_id`, and `sub_id` are allowed as tracking
  template placeholders.
- Campaign and sub-ID values use a restricted character set and maximum length.
- A recommendation remains advisory. The partner owns live inventory, price,
  checkout, refunds, and fulfilment.
