from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


REPOSITORY = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GITHUB_TOKEN"]
API = "https://api.github.com"
ROOT = Path(".").resolve()

PRIORITY = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
BLOCKING_LABELS = {
    "status:running",
    "status:review",
    "status:blocked",
    "needs-owner-approval",
}
ALLOWED_AGENTS = {
    "analyst",
    "planner",
    "researcher",
    "product",
    "architect",
    "coder",
    "designer",
    "reviewer",
    "growth",
    "operator",
    "security-ethics",
}


def request(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> Any:
    data = (
        json.dumps(payload).encode("utf-8")
        if payload is not None
        else None
    )
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            body = response.read()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(
            f"GitHub API {method} {path} failed: {exc.code} {detail}"
        ) from exc


def labels_of(issue: dict[str, Any]) -> list[str]:
    return [
        str(item.get("name", ""))
        for item in issue.get("labels", [])
        if item.get("name")
    ]


def project_path(body: str) -> Path | None:
    match = re.search(r"`?(tasks/projects/[A-Za-z0-9._-]+)`?", body)
    return ROOT / match.group(1) if match else None


def already_completed(issue: dict[str, Any]) -> bool:
    title = str(issue.get("title", ""))
    body = str(issue.get("body") or "")
    project = project_path(body)
    if not project:
        return False

    if title.startswith("[ANALYSIS]"):
        return (project / ".company" / "AI_ANALYSIS.json").is_file()

    if title.startswith("[PLAN]"):
        return (
            (project / ".company" / "ROADMAP.md").is_file()
            or (project / "roadmap.md").is_file()
        )

    return False


def close_completed(issue: dict[str, Any]) -> None:
    number = int(issue["number"])
    request(
        "PATCH",
        f"/repos/{REPOSITORY}/issues/{number}",
        {"state": "closed", "state_reason": "completed"},
    )
    request(
        "POST",
        f"/repos/{REPOSITORY}/issues/{number}/comments",
        {
            "body": (
                "Kreative Core dispatcher: İlgili çıktı varsayılan dalda "
                "bulunduğu için bu iş otomatik olarak tamamlandı."
            )
        },
    )
    print(f"Closed completed issue #{number}")


def agent_of(labels: list[str]) -> str | None:
    for label in labels:
        if label.startswith("agent:"):
            agent = label.split(":", 1)[1]
            if agent in ALLOWED_AGENTS:
                return agent
    return None


def rank(issue: dict[str, Any]) -> tuple[int, int]:
    labels = labels_of(issue)
    priority = min(
        (PRIORITY[label] for label in labels if label in PRIORITY),
        default=99,
    )
    return priority, int(issue["number"])


def ensure_label(name: str, color: str, description: str) -> None:
    encoded = urllib.parse.quote(name, safe="")
    try:
        request("GET", f"/repos/{REPOSITORY}/labels/{encoded}")
    except RuntimeError as exc:
        if "404" not in str(exc):
            raise
        request(
            "POST",
            f"/repos/{REPOSITORY}/labels",
            {
                "name": name,
                "color": color,
                "description": description,
            },
        )


def set_status(issue: dict[str, Any], status: str) -> None:
    labels = [
        label
        for label in labels_of(issue)
        if not label.startswith("status:")
    ]
    labels.append(status)
    request(
        "PATCH",
        f"/repos/{REPOSITORY}/issues/{issue['number']}",
        {"labels": labels},
    )


def write_env(values: dict[str, str]) -> None:
    env_path = os.environ.get("GITHUB_ENV")
    if not env_path:
        raise RuntimeError("GITHUB_ENV is not available")
    with open(env_path, "a", encoding="utf-8") as stream:
        for key, value in values.items():
            stream.write(f"{key}={value}\n")


def main() -> int:
    ensure_label(
        "status:running",
        "FBCA04",
        "Kreative Core AI is currently executing this issue.",
    )
    ensure_label(
        "status:review",
        "1D76DB",
        "AI output is waiting for human review or merge.",
    )
    ensure_label(
        "status:blocked",
        "B60205",
        "Automatic execution stopped and needs attention.",
    )

    issues = request(
        "GET",
        f"/repos/{REPOSITORY}/issues?state=open&per_page=100",
    )

    candidates: list[dict[str, Any]] = []

    for issue in issues:
        if "pull_request" in issue:
            continue

        labels = labels_of(issue)

        if already_completed(issue):
            close_completed(issue)
            continue

        if "local-ai:ready" not in labels:
            continue
        if BLOCKING_LABELS.intersection(labels):
            continue

        body = str(issue.get("body") or "")
        if "Owner approval required: true" in body:
            continue
        if "Founder approval required before local AI execution" in body:
            # Existing generated issues use this sentence. They remain manual
            # unless explicitly marked with local-ai:auto.
            if "local-ai:auto" not in labels:
                continue

        agent = agent_of(labels)
        if not agent:
            continue

        issue["_agent"] = agent
        candidates.append(issue)

    if not candidates:
        print("No eligible automatic issue found.")
        write_env({"OPERATION": "noop", "TARGET": "", "AGENT": "operator"})
        return 0

    selected = sorted(candidates, key=rank)[0]
    number = str(selected["number"])
    agent = str(selected["_agent"])

    set_status(selected, "status:running")
    request(
        "POST",
        f"/repos/{REPOSITORY}/issues/{number}/comments",
        {
            "body": (
                f"Kreative Core dispatcher bu işi `{agent}` ajanına verdi. "
                "Çıktı ayrı bir pull request olarak gönderilecek."
            )
        },
    )

    write_env(
        {
            "OPERATION": "execute-task",
            "TARGET": number,
            "AGENT": agent,
            "AUTO_DISPATCH": "true",
        }
    )
    print(f"Selected issue #{number} for agent {agent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
