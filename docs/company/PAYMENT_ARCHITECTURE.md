# Payment Architecture

Status: `PROPOSED`

This document defines principles only. It contains no banking data, API keys, customer data,
or provider credentials.

## Goals

- Sell Kreative Core products from a clear public store.
- Support transparent pricing and invoices.
- Separate payment processing from product licensing.
- Keep sensitive payment data outside Kreative Core systems wherever possible.
- Provide a recoverable purchase and license history.

## Logical components

1. Storefront
2. Payment provider
3. Order record
4. License service
5. Download/update service
6. Support and refund workflow
7. Accounting export

## Security boundaries

- Card data must be handled by the payment provider.
- Secrets must live in protected environment or repository secrets, never files.
- Webhooks require signature verification.
- License checks must fail safely without locking legitimate users out permanently.
- Refund and manual recovery paths must exist.

## Decisions still required

- Payment provider: `TBD`
- Legal seller entity: `TBD`
- Invoice integration: `TBD`
- License model: `TBD`
- Offline grace period: `TBD`
- Refund policy: `TBD`

Record approved decisions in `DECISION_LOG.md`.
