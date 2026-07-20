#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

MARKER = re.compile(r"<!-- kc-work-id:([^>]+) -->")
COLORS = {"kc:company": "6C5CE7", "kc:project": "1D76DB", "kc:task": "0E8A16", "local-ai:ready": "A2EEEF", "local-ai:auto": "7057FF", "needs-owner-approval": "D876E3", "P0": "B60205", "P1": "D93F0B", "P2": "FBCA04", "P3": "C2E0C6"}


class GitHub:
    def __init__(self, repo: str, token: str) -> None:
        self.repo, self.token = repo, token

    def call(self, method: str, path: str, data: Any = None) -> Any:
        body = None if data is None else json.dumps(data).encode("utf-8")
        request = urllib.request.Request("https://api.github.com" + path, method=method, data=body)
        request.add_header("Authorization", f"Bearer {self.token}")
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        request.add_header("User-Agent", "kreativecore-local-ai")
        if body is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"GitHub API error {exc.code}: {detail}") from exc

    def issues(self) -> list[dict[str, Any]]:
        result = []
        page = 1
        while True:
            items = self.call("GET", f"/repos/{self.repo}/issues?state=all&per_page=100&page={page}")
            if not items:
                break
            result.extend(x for x in items if "pull_request" not in x)
            if len(items) < 100:
                break
            page += 1
        return result

    def label(self, name: str) -> None:
        encoded = urllib.parse.quote(name, safe="")
        try:
            self.call("PATCH", f"/repos/{self.repo}/labels/{encoded}", {"new_name": name, "color": COLORS.get(name, "C5DEF5")})
        except RuntimeError as exc:
            if "404" not in str(exc):
                raise
            self.call("POST", f"/repos/{self.repo}/labels", {"name": name, "color": COLORS.get(name, "C5DEF5")})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    items = json.loads((root / "tasks/.company/dispatch.json").read_text(encoding="utf-8")).get("items", [])
    if args.dry_run:
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return 0
    repo, token = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", "")
    if not repo or not token:
        raise SystemExit("GITHUB_REPOSITORY and GITHUB_TOKEN are required")
    github = GitHub(repo, token)
    existing = {}
    for issue in github.issues():
        match = MARKER.search(issue.get("body") or "")
        if match:
            existing[match.group(1)] = issue
    created = 0
    for item in items:
        if item["work_id"] in existing:
            continue
        labels = [x.replace("copilot-ready", "local-ai:ready").replace("copilot:auto", "local-ai:auto") for x in item["labels"]]
        for label in labels:
            github.label(label)
        github.call("POST", f"/repos/{repo}/issues", {"title": item["title"], "body": item["body"], "labels": labels})
        created += 1
    print(f"Issue sync complete: {created} created for local AI workflows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
