#!/usr/bin/env python3
"""Read-only RateHawk sandbox verification.

Uses RateHawk's published certification properties and never starts a booking.
Secrets are read only from RATEHAWK_SANDBOX_KEY_ID and
RATEHAWK_SANDBOX_API_KEY and are never printed.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelos.intelligence_gateway.secret_reference import SecretReference  # noqa: E402
from travelos.live_providers.auth.basic_auth import BasicAuthStrategy  # noqa: E402

BASE_URL = "https://api-sandbox.ratehawk.com/api/b2b/v3"
CERTIFICATION_HOTELS = [10004834, 8819557]


def _search_payload(checkin: str, checkout: str) -> dict[str, object]:
    return {
        "checkin": checkin,
        "checkout": checkout,
        "residency": "gb",
        "language": "en",
        "guests": [{"adults": 2, "children": [7, 10]}],
        "hids": CERTIFICATION_HOTELS,
        "currency": "USD",
        "timeout": 20,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify RateHawk sandbox search without booking")
    parser.add_argument("--checkin", help="YYYY-MM-DD; defaults to 45 days from today")
    args = parser.parse_args()

    auth = BasicAuthStrategy(
        username=SecretReference("RATEHAWK_SANDBOX_KEY_ID", required=True),
        password=SecretReference("RATEHAWK_SANDBOX_API_KEY", required=True),
    )
    if not auth.is_configured():
        print("RateHawk sandbox credentials are not configured.")
        return 2

    checkin_date = date.fromisoformat(args.checkin) if args.checkin else date.today() + timedelta(days=45)
    checkout_date = checkin_date + timedelta(days=2)
    body = json.dumps(_search_payload(checkin_date.isoformat(), checkout_date.isoformat())).encode("utf-8")
    headers = {"Accept": "application/json", "Content-Type": "application/json", **auth.headers()}
    outbound = request.Request(
        f"{BASE_URL}/search/serp/hotels/",
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(outbound, timeout=30) as response:
            payload = json.load(response)
    except error.HTTPError as exc:
        print(f"RateHawk sandbox returned HTTP {exc.code}; no booking was attempted.")
        return 1
    except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"RateHawk sandbox verification failed safely: {type(exc).__name__}")
        return 1

    hotels = payload.get("data", {}).get("hotels", []) if isinstance(payload, dict) else []
    print("authentication: accepted")
    print("booking_attempted: false")
    print(f"certification_hotels_requested: {len(CERTIFICATION_HOTELS)}")
    print(f"hotels_returned: {len(hotels) if isinstance(hotels, list) else 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
