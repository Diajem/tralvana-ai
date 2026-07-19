# ADR-030: Provider-neutral commission reconciliation

**Date**: 2026-07-19

**Status**: Accepted

**Task**: T-044

## Context

T-042 created the commercial ledger and T-043 created attributed outbound
clicks. Tralvana still needed a safe way to ingest partner-reported sales and
commission states. Real Awin, Expedia, Amazon, and Travelpayouts export schemas
have not yet been supplied, so implementing named adapters would fabricate
contracts that may not match the networks' actual reports.

## Decision

1. Define one strict canonical CSV contract and an operator-only CLI.
2. Require a dry run by default and explicit `--apply` for persistence.
3. Reject unknown columns and do not retain raw report rows.
4. Reconcile idempotently by programme plus transaction reference and by a
   stable commission reference.
5. Match the most recent click by programme and sub-ID when supplied, while
   retaining and counting legitimate unmatched sales.
6. Prevent stale reports from regressing terminal states.
7. Add provider adapters only after verified documentation or anonymised sample
   reports are available.

## Consequences

Tralvana can operate and audit commissions before network-specific automation is
available. The next integration task is factual mapping—not a redesign of the
ledger or reconciliation rules.
