from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from engine.checks import run_checks
from engine.config import engine_settings, model_config
from engine.github_api import GitHub
from engine.json_protocol import ProtocolError, extract_json, validate_code_actions
from engine.runtime import client, read_agent, repo_context
from engine.safety import apply_actions


DOCUMENT_AGENTS = {
    "planner": "ROADMAP.md",
    "analyst": "ANALYSIS.md",
    "researcher": "RESEARCH.md",
    "product": "PRODUCT.md",
    "architect": "ARCHITECTURE.md",
    "designer": "DESIGN.md",
    "growth": "GROWTH.md",
    "reviewer": "REVIEW.md",
}


def resolve(root: Path, reference: str) -> tuple[str, str]:
    if reference.isdigit():
        issue = GitHub().issue(int(reference))
        return str(issue["title"]), str(issue.get("body") or "")

    folder = root / "tasks" / "inbox" / reference
    if folder.is_dir():
        manifest = (
            (folder / "TASK.toml").read_text(encoding="utf-8", errors="ignore")
            if (folder / "TASK.toml").is_file()
            else ""
        )
        request = (
            (folder / "REQUEST.md").read_text(encoding="utf-8", errors="ignore")
            if (folder / "REQUEST.md").is_file()
            else ""
        )
        return reference, manifest + "\n\n" + request

    markdown = root / "tasks" / "inbox" / f"{reference}.md"
    if markdown.is_file():
        return reference, markdown.read_text(encoding="utf-8", errors="ignore")

    raise FileNotFoundError(f"Task not found: {reference}")


def project_path_from_request(request: str) -> str | None:
    matches = re.findall(
        r"`?(tasks/projects/[A-Za-z0-9._-]+)`?",
        request,
    )
    return matches[0] if matches else None


def strict_payload(
    *,
    llm: Any,
    agent_prompt: str,
    title: str,
    request: str,
    context: str,
    max_tokens: int,
) -> tuple[dict[str, Any] | None, str]:
    protocol = """Return exactly one compact JSON object:
{
  "summary": "short summary",
  "actions": [
    {
      "op": "write",
      "path": "relative/path",
      "content": "complete file content"
    }
  ],
  "notes": []
}

Rules:
- JSON only. No markdown fence. No prose outside JSON.
- Never return shell commands.
- Never edit protected infrastructure paths.
- Use complete file contents.
- Keep the action count small.
"""

    raw = llm.chat(
        system=agent_prompt + "\n\n" + protocol,
        user=f"""TASK TITLE:
{title}

TASK REQUEST:
{request}

SELECTED REPOSITORY CONTEXT:
{context}
""",
        max_tokens=min(max_tokens, 700),
        temperature=0.1,
    )

    try:
        payload = extract_json(raw)
        validate_code_actions(payload)
        return payload, raw
    except (ProtocolError, ValueError):
        pass

    repair = llm.chat(
        system=(
            "Repair malformed agent output into one valid JSON object. "
            "Return JSON only. Never return shell commands."
        ),
        user=f"""Required schema:
{{
  "summary": "short summary",
  "actions": [
    {{"op": "write", "path": "relative/path", "content": "complete content"}}
  ],
  "notes": []
}}

TASK:
{title}

BROKEN OUTPUT:
{raw[:5000]}
""",
        max_tokens=600,
        temperature=0,
    )

    try:
        payload = extract_json(repair)
        validate_code_actions(payload)
        return payload, raw + "\n\n--- REPAIR ---\n\n" + repair
    except (ProtocolError, ValueError):
        return None, raw + "\n\n--- REPAIR ---\n\n" + repair


def document_fallback(
    *,
    llm: Any,
    agent: str,
    agent_prompt: str,
    title: str,
    request: str,
    context: str,
    raw_output: str,
) -> dict[str, Any]:
    project_path = project_path_from_request(request)
    if not project_path:
        raise ProtocolError(
            "Could not determine the project path for document fallback"
        )

    filename = DOCUMENT_AGENTS[agent]
    target = f"{project_path}/.company/{filename}"

    markdown = llm.chat(
        system=(
            agent_prompt
            + "\nReturn only the final Markdown document."
            + "\nDo not use a code fence."
            + "\nKeep it concise, concrete and reviewable."
        ),
        user=f"""Create the requested project document.

TASK TITLE:
{title}

TASK REQUEST:
{request}

PROJECT CONTEXT:
{context[:4500]}

The document will be saved to:
{target}
""",
        max_tokens=700,
        temperature=0.1,
    ).strip()

    if not markdown:
        markdown = f"""# {title}

## Status

The local model did not return a usable document.

## Required manual review

- Review the source issue.
- Confirm scope and acceptance criteria.
- Retry the task after adjusting the prompt.
"""

    return {
        "summary": (
            f"{agent} output was converted to a project document after "
            "the model failed the JSON action protocol."
        ),
        "actions": [
            {
                "op": "write",
                "path": target,
                "content": markdown.rstrip() + "\n",
            }
        ],
        "notes": [
            "JSON action protocol required fallback to Markdown document mode.",
            "Human review is required before merge.",
            f"Original malformed output length: {len(raw_output)} characters.",
        ],
    }


def execute(root: Path, reference: str, agent: str) -> dict[str, Any]:
    title, request = resolve(root, reference)
    context = repo_context(root, title + "\n" + request)
    llm = client(root)
    model = model_config(root)

    # Capture existing repository health before the AI changes anything.
    baseline_checks = run_checks(root)
    baseline_failures = {
        item["command"] for item in baseline_checks
        if item["returncode"] != 0
    }

    payload, raw_output = strict_payload(
        llm=llm,
        agent_prompt=read_agent(root, agent),
        title=title,
        request=request,
        context=context,
        max_tokens=model.max_tokens_code,
    )

    if payload is None:
        if agent not in DOCUMENT_AGENTS:
            raise ProtocolError(
                "The local model returned invalid JSON twice. "
                "Automatic document fallback is not allowed for this agent."
            )
        payload = document_fallback(
            llm=llm,
            agent=agent,
            agent_prompt=read_agent(root, agent),
            title=title,
            request=request,
            context=context,
            raw_output=raw_output,
        )

    actions = validate_code_actions(payload)
    settings = engine_settings(root)

    changed = apply_actions(
        root,
        actions,
        protected_prefixes=list(settings["safety"]["protected_prefixes"]),
        max_files=int(settings["engine"]["max_write_files"]),
        max_bytes=int(settings["engine"]["max_write_bytes"]),
    )

    checks = run_checks(root)
    new_failures = [
        item for item in checks
        if item["returncode"] != 0
        and item["command"] not in baseline_failures
    ]
    passed = not new_failures

    for item in checks:
        status = "PASS" if item["returncode"] == 0 else "FAIL"
        print(f"[{status}] {item['command']}")
        if item["stdout"]:
            print(item["stdout"])
        if item["stderr"]:
            print(item["stderr"])

    report = {
        "reference": reference,
        "agent": agent,
        "summary": payload.get("summary", ""),
        "changed_files": changed,
        "baseline_checks": baseline_checks,
        "checks": checks,
        "new_failures": new_failures,
        "passed": passed,
        "notes": payload.get("notes", []),
    }

    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", reference)

    (reports / f"task-{safe}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    (reports / f"task-{safe}.md").write_text(
        f"""# AI Task Report — {reference}

- Agent: `{agent}`
- Checks passed: `{passed}`

## Summary

{payload.get("summary", "")}

## Changed files

{chr(10).join(f"- `{item}`" for item in changed) or "- No files changed"}

## Notes

{chr(10).join(f"- {item}" for item in payload.get("notes", [])) or "- None"}

## Checks

```json
{json.dumps(checks, ensure_ascii=False, indent=2)}
```
""",
        encoding="utf-8",
    )

    if not passed:
        failed_commands = ", ".join(
            item["command"] for item in new_failures
        )
        raise RuntimeError(
            "Generated changes introduced new repository check failures: "
            + failed_commands
        )

    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("--agent", default="coder")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    print(
        json.dumps(
            execute(
                Path(args.root).resolve(),
                args.reference,
                args.agent,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
