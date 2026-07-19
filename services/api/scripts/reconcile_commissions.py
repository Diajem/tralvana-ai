"""Validate or apply a provider-neutral canonical commission CSV."""
from __future__ import annotations

import argparse
from pathlib import Path

from app.database.session import create_engine_from_url, create_session_factory, database_url
from app.domains.commercial.reconciliation import (
    CommissionReconciliationService,
    load_canonical_commission_csv,
)
from app.domains.commercial.repository import SqlAlchemyCommercialRepository


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Canonical CSV report")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist the import. Without this flag the transaction is rolled back.",
    )
    args = parser.parse_args()
    url = database_url()
    if not url:
        raise SystemExit("DATABASE_URL is required")

    with args.report.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = load_canonical_commission_csv(stream)

    engine = create_engine_from_url(url)
    factory = create_session_factory(engine)
    try:
        with factory() as session:
            summary = CommissionReconciliationService(
                SqlAlchemyCommercialRepository(session)
            ).reconcile(rows)
            if args.apply and not summary.issues:
                session.commit()
                mode = "applied"
            else:
                session.rollback()
                mode = "dry-run" if not args.apply else "rejected"
        print(
            f"Commission reconciliation {mode}: {summary.successful}/{summary.processed} rows; "
            f"conversions +{summary.conversions_created}/~{summary.conversions_updated}; "
            f"commissions +{summary.commissions_created}/~{summary.commissions_updated}; "
            f"clicks matched {summary.clicks_matched}, unmatched {summary.clicks_unmatched}; "
            f"issues {len(summary.issues)}."
        )
        for issue in summary.issues:
            print(f"Row {issue.row_number}: {issue.message}")
        if summary.issues:
            raise SystemExit(2)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
