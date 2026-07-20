#!/usr/bin/env python3
"""Read-only smoke test for a deployed Tralvana web/API pair."""
from __future__ import annotations

import argparse
import json
from urllib.request import Request, urlopen


def fetch(url: str, *, timeout: float) -> tuple[int, str]:
    request = Request(url, headers={"User-Agent": "tralvana-deployment-smoke/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.status, response.read().decode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web-url", default="https://app.tralvana.com")
    parser.add_argument("--api-url", default="https://api.tralvana.com")
    parser.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args()

    web_url = args.web_url.rstrip("/")
    api_url = args.api_url.rstrip("/")

    _, homepage = fetch(web_url, timeout=args.timeout)
    if "Tralvana" not in homepage:
        raise SystemExit("Web smoke failed: Tralvana marker missing")

    _, health_text = fetch(f"{api_url}/health", timeout=args.timeout)
    if json.loads(health_text).get("status") != "ok":
        raise SystemExit("API liveness smoke failed")

    _, ready_text = fetch(f"{api_url}/health/ready", timeout=args.timeout)
    readiness = json.loads(ready_text)
    if readiness.get("status") != "ok" or readiness.get("affiliate_programmes", 0) < 1:
        raise SystemExit("API readiness smoke failed")

    _, programmes_text = fetch(f"{api_url}/commercial/programmes", timeout=args.timeout)
    programmes = json.loads(programmes_text)
    if not programmes or any("disclosure_text" not in item for item in programmes):
        raise SystemExit("Affiliate catalogue smoke failed")

    print(
        "Production smoke passed: web, API, database schema, and "
        f"{len(programmes)} disclosed affiliate programmes are ready."
    )


if __name__ == "__main__":
    main()
