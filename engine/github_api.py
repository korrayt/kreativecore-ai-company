from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class GitHub:
    def __init__(self) -> None:
        self.repo = os.environ.get("GITHUB_REPOSITORY", "")
        self.token = os.environ.get("GITHUB_TOKEN", "")
        if not self.repo or not self.token:
            raise RuntimeError("GITHUB_REPOSITORY and GITHUB_TOKEN are required")

    def request(self, method: str, path: str, data: Any = None) -> Any:
        body = None if data is None else json.dumps(data).encode("utf-8")
        request = urllib.request.Request("https://api.github.com" + path, method=method, data=body)
        request.add_header("Authorization", f"Bearer {self.token}")
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        request.add_header("User-Agent", "kreativecore-github-ai")
        if body is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"GitHub API error {exc.code}: {detail}") from exc

    def issue(self, number: int) -> dict[str, Any]:
        return self.request("GET", f"/repos/{self.repo}/issues/{number}")

    def pull(self, number: int) -> dict[str, Any]:
        return self.request("GET", f"/repos/{self.repo}/pulls/{number}")

    def pull_files(self, number: int) -> list[dict[str, Any]]:
        return self.request("GET", f"/repos/{self.repo}/pulls/{number}/files?per_page=100")

    def comment(self, number: int, body: str) -> None:
        self.request("POST", f"/repos/{self.repo}/issues/{number}/comments", {"body": body})
