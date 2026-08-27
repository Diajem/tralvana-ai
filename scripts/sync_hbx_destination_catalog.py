"""Manually load HBX destination codes into Tralvana's local database.

Usage (sandbox credentials only unless --production is deliberately used):

    python scripts/sync_hbx_destination_catalog.py

This is an explicit operational command, never an application-startup task
and never part of pytest/CI. It prints counts only, never credentials or raw
supplier payloads.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=_REPO_ROOT / ".env", override=True)
sys.path.insert(0, str(_REPO_ROOT))

from travelos.live_providers.hbx_content_sync import HbxDestinationContentSync  # noqa: E402
from travelos.live_providers.hbx_destination_catalog import build_hbx_destination_catalog  # noqa: E402
from travelos.live_providers.httpx_transport import HttpxTransport  # noqa: E402
from travelos.persistence.session import database_url  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync HBX destination content into Tralvana")
    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=1000)
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument("--production", action="store_true")
    args = parser.parse_args()

    if not database_url():
        print("DATABASE_URL is required; refusing to sync into an in-memory catalogue.")
        return 1

    transport = HttpxTransport()
    try:
        result = HbxDestinationContentSync(
            transport=transport,
            catalog=build_hbx_destination_catalog(),
            production=args.production,
        ).sync(
            start_index=args.start_index,
            page_size=args.page_size,
            max_pages=args.max_pages,
        )
    except Exception as exc:  # noqa: BLE001 - bounded manual diagnostic command
        print("sync_success: False")
        print("error_type:", type(exc).__name__)
        print("error:", str(exc))
        return 1
    finally:
        transport.close()

    print("sync_success: True")
    print("pages_requested:", result.pages_requested)
    print("destinations_received:", result.destinations_received)
    print("destinations_upserted:", result.destinations_upserted)
    print("next_index:", result.next_index)
    print("complete:", result.complete)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
