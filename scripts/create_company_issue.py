#!/usr/bin/env python3
"""Create safe issue title/body files for Mobile Company Control."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

def clean(value: str, limit: int = 5000) -> str:
    return value.replace("\x00", "").strip()[:limit]

def weekly(today: str, notes: str) -> tuple[str, str]:
    title = f"[WEEKLY] Kreative Core Company Review — {today}"
    body = f"""# Weekly Company Review

## Wins

-

## Product movement

| Product | What changed? | Evidence | Next decision |
|---|---|---|---|
| Vision | | | |
| CutMate | | | |
| Transcribe TR | | | |
| Store | | | |

## Blockers

-

## Risks

-

## Stop / pause

-

## This week's three outcomes

- [ ]
- [ ]
- [ ]

## Decisions needed

-

## Starting notes

{notes or "—"}

---
Created by Mobile Company Control.
"""
    return title, body

def product(today: str, product_name: str, notes: str, priority: str) -> tuple[str, str]:
    name = product_name or "TBD Product"
    title = f"[PRODUCT] {name} — proposal"
    body = f"""# Product Proposal

- Date: {today}
- Product: {name}
- Priority: {priority}
- Status: PROPOSED
- Owner: @korrayt

## Target user

TBD

## Problem

TBD

## Promise

TBD

## Smallest proof

TBD

## Success signal

TBD

## Risks

TBD

## Starting notes

{notes or "—"}

---
Created by Mobile Company Control.
"""
    return title, body

def release(today: str, product_name: str, notes: str) -> tuple[str, str]:
    name = product_name or "TBD Product"
    title = f"[RELEASE] {name} — readiness"
    body = f"""# Release Readiness

- Date: {today}
- Product: {name}
- Owner: @korrayt

## Product

- [ ] Promise and scope are current
- [ ] Acceptance criteria pass
- [ ] Known limitations are documented

## Engineering

- [ ] Build succeeds
- [ ] Tests succeed
- [ ] Installation/update succeeds
- [ ] Rollback is verified
- [ ] Dependencies and licenses are reviewed

## Security and privacy

- [ ] No secrets are present
- [ ] Permissions are minimal
- [ ] Data flow matches privacy claims
- [ ] Critical risks have mitigation

## Marketing and support

- [ ] Product page matches the release
- [ ] Screenshots are current
- [ ] Release notes exist
- [ ] Support path exists

## Starting notes

{notes or "—"}

---
Created by Mobile Company Control.
"""
    return title, body

def risk(today: str, notes: str, priority: str) -> tuple[str, str]:
    title = f"[RISK] Company risk review — {today}"
    body = f"""# Risk Review

- Date: {today}
- Priority: {priority}
- Owner: @korrayt
- Status: ACTIVE

## Risk

TBD

## Area

TBD

## Likelihood

TBD

## Impact

TBD

## Mitigation

TBD

## Review date

TBD

## Starting notes

{notes or "—"}

---
Created by Mobile Company Control.
"""
    return title, body

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operation", required=True)
    parser.add_argument("--product", default="")
    parser.add_argument("--priority", default="P2")
    parser.add_argument("--notes", default="")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    today = dt.date.today().isoformat()
    notes = clean(args.notes)
    product_name = clean(args.product, 150)
    priority = clean(args.priority, 10)

    if args.operation == "weekly-review":
        title, body = weekly(today, notes)
        labels = ["weekly-review", "company"]
    elif args.operation == "product-proposal":
        title, body = product(today, product_name, notes, priority)
        labels = ["product", "needs-triage", priority.lower()]
    elif args.operation == "release-checklist":
        title, body = release(today, product_name, notes)
        labels = ["release", "needs-triage"]
    elif args.operation == "risk-review":
        title, body = risk(today, notes, priority)
        labels = ["risk", "security", priority.lower()]
    else:
        raise SystemExit(f"Unsupported issue operation: {args.operation}")

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "title.txt").write_text(title + "\n", encoding="utf-8")
    (out / "body.md").write_text(body, encoding="utf-8")
    (out / "labels.txt").write_text(",".join(labels) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
