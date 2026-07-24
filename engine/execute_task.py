from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from engine.checks import run_checks
from engine.config import engine_settings, model_config
from engine.github_api import GitHub
from engine.json_protocol import (
    ProtocolError,
    extract_json,
    render_department_markdown,
    validate_code_actions,
    validate_department_json,
)
from engine.runtime import _registry, client, read_agent, repo_context
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


def document_target(
    agent: str,
    project_path: str,
) -> str | None:
    """Return the safe output path for document-style agents."""

    if agent in DOCUMENT_AGENTS:
        return (
            f"{project_path}/.company/"
            f"{DOCUMENT_AGENTS[agent]}"
        )

    if agent.startswith("dept-"):
        slug = re.sub(
            r"[^A-Za-z0-9._-]+",
            "-",
            agent,
        ).strip("-")

        if not slug:
            return None

        return (
            f"{project_path}/.company/"
            f"departments/{slug}.md"
        )

    return None


def resolve(
    root: Path,
    reference: str,
) -> tuple[str, str]:
    if reference.isdigit():
        issue = GitHub().issue(int(reference))

        return (
            str(issue["title"]),
            str(issue.get("body") or ""),
        )

    folder = root / "tasks" / "inbox" / reference

    if folder.is_dir():
        manifest = (
            (folder / "TASK.toml").read_text(
                encoding="utf-8",
                errors="ignore",
            )
            if (folder / "TASK.toml").is_file()
            else ""
        )

        request = (
            (folder / "REQUEST.md").read_text(
                encoding="utf-8",
                errors="ignore",
            )
            if (folder / "REQUEST.md").is_file()
            else ""
        )

        return (
            reference,
            manifest + "\n\n" + request,
        )

    markdown = (
        root
        / "tasks"
        / "inbox"
        / f"{reference}.md"
    )

    if markdown.is_file():
        return (
            reference,
            markdown.read_text(
                encoding="utf-8",
                errors="ignore",
            ),
        )

    raise FileNotFoundError(
        f"Task not found: {reference}"
    )


def project_path_from_request(
    request: str,
) -> str | None:
    matches = re.findall(
        r"`?(tasks/projects/[A-Za-z0-9._-]+)`?",
        request,
    )

    return matches[0] if matches else None


def validate_agent_scope(
    agent: str,
    request: str,
    actions: list[dict[str, Any]],
) -> None:
    """
    Keep every department agent inside its own report file.
    """

    if not agent.startswith("dept-"):
        return

    project_path = project_path_from_request(request)

    if not project_path:
        raise ProtocolError(
            "Could not determine the project path "
            "for department scope validation"
        )

    allowed_path = document_target(
        agent,
        project_path,
    )

    if not allowed_path:
        raise ProtocolError(
            "No safe document target exists for "
            f"department agent: {agent}"
        )

    if len(actions) != 1:
        raise ProtocolError(
            f"Department agent {agent} must produce "
            "exactly one document action"
        )

    action = actions[0]

    if (
        action.get("op") != "write"
        or action.get("path") != allowed_path
    ):
        raise ProtocolError(
            f"Department agent {agent} may write "
            f"only to {allowed_path}"
        )


def strict_payload(
    *,
    llm: Any,
    agent_prompt: str,
    title: str,
    request: str,
    context: str,
    max_tokens: int,
) -> tuple[dict[str, Any] | None, str]:
    protocol = """
Return exactly one compact JSON object:

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

- JSON only.
- No Markdown fence.
- No prose outside JSON.
- Never return shell commands.
- Never edit protected infrastructure paths.
- Use complete file contents.
- Keep the action count small.
"""

    raw = llm.chat(
        system=agent_prompt + "\n\n" + protocol,
        user=f"""
TASK TITLE:

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
            "Repair malformed agent output into one "
            "valid JSON object. Return JSON only. "
            "Never return shell commands."
        ),
        user=f"""
Required schema:

{{
  "summary": "short summary",
  "actions": [
    {{
      "op": "write",
      "path": "relative/path",
      "content": "complete content"
    }}
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

        return (
            payload,
            raw + "\n\n--- REPAIR ---\n\n" + repair,
        )

    except (ProtocolError, ValueError):
        return (
            None,
            raw + "\n\n--- REPAIR ---\n\n" + repair,
        )


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
            "Could not determine the project path "
            "for document fallback"
        )

    target = document_target(
        agent,
        project_path,
    )

    if not target:
        raise ProtocolError(
            "Automatic document mode is not "
            f"allowed for agent: {agent}"
        )

    department_instructions = ""

    if agent.startswith("dept-"):
        department_instructions = """
Focus only on this department's perspective.

The document must include:

- Objective
- Required inputs
- Dependencies
- Acceptance criteria
- Risks
- Smallest next executable task

Do not modify:

- Project state
- Project analysis
- Source code
- Workflows
- Other departments
"""

    markdown = llm.chat(
        system=(
            agent_prompt
            + "\nReturn only the final Markdown document."
            + "\nDo not use a code fence."
            + "\nKeep it concise, concrete and reviewable."
        ),
        user=f"""
Create the requested project document.

{department_instructions}

TASK TITLE:

{title}

TASK REQUEST:

{request}

PROJECT CONTEXT:

{context[:4500]}

The document will be saved only to:

{target}
""",
        max_tokens=700,
        temperature=0.1,
    ).strip()

    if not markdown:
        markdown = f"""
# {title}

## Status

The local model did not return a usable document.

## Required manual review

- Review the source issue.
- Confirm scope and acceptance criteria.
- Retry the task after adjusting the prompt.
""".strip()

    if agent.startswith("dept-"):
        mode_note = (
            "Department agent was restricted "
            "to document-only mode."
        )
    else:
        mode_note = (
            "JSON action protocol required fallback "
            "to Markdown document mode."
        )

    return {
        "summary": (
            f"{agent} produced a reviewable "
            "project document."
        ),
        "actions": [
            {
                "op": "write",
                "path": target,
                "content": markdown.rstrip() + "\n",
            }
        ],
        "notes": [
            mode_note,
            "Human review is required before merge.",
            (
                "Original output length: "
                f"{len(raw_output)} characters."
            ),
        ],
    }


def strict_department_payload(
    *,
    root: Path,
    llm: Any,
    agent: str,
    agent_prompt: str,
    title: str,
    request: str,
    context: str,
    max_tokens: int,
) -> dict[str, Any]:
    project_path = project_path_from_request(request)
    if not project_path:
        raise ProtocolError(
            "Could not determine the project path for department scope validation"
        )

    target = document_target(agent, project_path)
    if not target:
        raise ProtocolError(
            f"No safe document target exists for department agent: {agent}"
        )

    entry = _registry(root).get(agent, {})
    dept_name = str(entry.get("name") or agent)

    schema_instruction = """
Return strictly ONE compact JSON object with no Markdown code fences and no extra prose outside JSON:

{
  "objective": "Detailed department objective (min 15 chars)",
  "required_inputs": [
    "Input 1"
  ],
  "dependencies": [
    "Dependency 1"
  ],
  "acceptance_criteria": [
    "Criterion 1"
  ],
  "risks": [
    "Risk 1"
  ],
  "next_task": {
    "title": "Actionable task title",
    "description": "Clear description of the work",
    "deliverable": "Specific file or report deliverable",
    "done_when": [
      "Completion condition 1"
    ]
  }
}

STRICT CONSTRAINTS:
- JSON format only.
- Do NOT wrap response in ```json code fences.
- Do NOT copy raw repository context or markers like ===== FILE: into text fields.
- Every list must contain at least 1 meaningful item.
- Do not invent facts or leave placeholders like TBD or N/A.
"""

    compact_context = context[:2000]

    raw = llm.chat(
        system=agent_prompt + "\n\n" + schema_instruction,
        user=f"""
TASK TITLE:
{title}

TASK REQUEST:
{request}

SELECTED PROJECT CONTEXT:
{compact_context}
""",
        max_tokens=min(max_tokens, 700),
        temperature=0.1,
    )

    try:
        data = extract_json(raw)
        validated_data = validate_department_json(data)
        markdown_content = render_department_markdown(validated_data, dept_name)

        return {
            "summary": f"{agent} department analysis completed successfully.",
            "actions": [
                {
                    "op": "write",
                    "path": target,
                    "content": markdown_content,
                }
            ],
            "notes": [
                "Department report generated deterministically from verified JSON.",
                "Human review is required before merge.",
            ],
        }
    except (ProtocolError, ValueError) as exc:
        first_error = str(exc)

    repair_raw = llm.chat(
        system=(
            "Repair malformed department output into one valid JSON object. "
            "Return JSON only. No Markdown code fences."
        ),
        user=f"""
Required JSON schema:
{{
  "objective": "...",
  "required_inputs": ["..."],
  "dependencies": ["..."],
  "acceptance_criteria": ["..."],
  "risks": ["..."],
  "next_task": {{
    "title": "...",
    "description": "...",
    "deliverable": "...",
    "done_when": ["..."]
  }}
}}

BROKEN OUTPUT:
{raw[:3000]}
""",
        max_tokens=600,
        temperature=0,
    )

    try:
        data = extract_json(repair_raw)
        validated_data = validate_department_json(data)
        markdown_content = render_department_markdown(validated_data, dept_name)

        return {
            "summary": f"{agent} department analysis completed after automatic JSON repair.",
            "actions": [
                {
                    "op": "write",
                    "path": target,
                    "content": markdown_content,
                }
            ],
            "notes": [
                "Department report generated deterministically after JSON repair.",
                "Human review is required before merge.",
            ],
        }
    except (ProtocolError, ValueError) as exc:
        raise ProtocolError(
            f"Department agent {agent} JSON protocol failed twice. Initial error: {first_error}; Repair error: {exc}"
        ) from exc


def execute(
    root: Path,
    reference: str,
    agent: str,
) -> dict[str, Any]:
    title, request = resolve(
        root,
        reference,
    )

    context = repo_context(
        root,
        title + "\n" + request,
    )

    llm = client(root)
    model = model_config(root)

    baseline_checks = run_checks(root)

    baseline_failures = {
        item["command"]
        for item in baseline_checks
        if item["returncode"] != 0
    }

    if agent.startswith("dept-"):
        payload = strict_department_payload(
            root=root,
            llm=llm,
            agent=agent,
            agent_prompt=read_agent(
                root,
                agent,
            ),
            title=title,
            request=request,
            context=context,
            max_tokens=model.max_tokens_code,
        )

    else:
        payload, raw_output = strict_payload(
            llm=llm,
            agent_prompt=read_agent(
                root,
                agent,
            ),
            title=title,
            request=request,
            context=context,
            max_tokens=model.max_tokens_code,
        )

        if payload is None:
            project_path = (
                project_path_from_request(request)
                or ""
            )

            if (
                document_target(
                    agent,
                    project_path,
                )
                is None
            ):
                raise ProtocolError(
                    "The local model returned invalid "
                    "JSON twice. Automatic document "
                    "fallback is not allowed for "
                    f"agent: {agent}"
                )

            payload = document_fallback(
                llm=llm,
                agent=agent,
                agent_prompt=read_agent(
                    root,
                    agent,
                ),
                title=title,
                request=request,
                context=context,
                raw_output=raw_output,
            )

    actions = validate_code_actions(payload)

    validate_agent_scope(
        agent,
        request,
        actions,
    )

    settings = engine_settings(root)

    changed = apply_actions(
        root,
        actions,
        protected_prefixes=list(
            settings["safety"]["protected_prefixes"]
        ),
        max_files=int(
            settings["engine"]["max_write_files"]
        ),
        max_bytes=int(
            settings["engine"]["max_write_bytes"]
        ),
    )

    checks = run_checks(root)

    new_failures = [
        item
        for item in checks
        if item["returncode"] != 0
        and item["command"] not in baseline_failures
    ]

    passed = not new_failures

    for item in checks:
        status = (
            "PASS"
            if item["returncode"] == 0
            else "FAIL"
        )

        print(
            f"[{status}] {item['command']}"
        )

        if item["stdout"]:
            print(item["stdout"])

        if item["stderr"]:
            print(item["stderr"])

    report = {
        "reference": reference,
        "agent": agent,
        "summary": payload.get(
            "summary",
            "",
        ),
        "changed_files": changed,
        "baseline_checks": baseline_checks,
        "checks": checks,
        "new_failures": new_failures,
        "passed": passed,
        "notes": payload.get(
            "notes",
            [],
        ),
    }

    reports = root / "reports"
    reports.mkdir(exist_ok=True)

    safe_reference = re.sub(
        r"[^A-Za-z0-9._-]+",
        "-",
        reference,
    )

    report_json = (
        reports
        / f"task-{safe_reference}.json"
    )

    report_markdown = (
        reports
        / f"task-{safe_reference}.md"
    )

    report_json.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    changed_markdown = (
        "\n".join(
            f"- `{item}`"
            for item in changed
        )
        or "- No files changed"
    )

    notes_markdown = (
        "\n".join(
            f"- {item}"
            for item in payload.get(
                "notes",
                [],
            )
        )
        or "- None"
    )

    report_markdown.write_text(
        f"""
# AI Task Report — {reference}

- Agent: `{agent}`
- Checks passed: `{passed}`

## Summary

{payload.get("summary", "")}

## Changed files

{changed_markdown}

## Notes

{notes_markdown}

## Checks

~~~json
{json.dumps(checks, ensure_ascii=False, indent=2)}
~~~
""".lstrip(),
        encoding="utf-8",
    )

    if not passed:
        failed_commands = ", ".join(
            item["command"]
            for item in new_failures
        )

        raise RuntimeError(
            "Generated changes introduced new "
            "repository check failures: "
            + failed_commands
        )

    return report


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument("reference")

    parser.add_argument(
        "--agent",
        default="coder",
    )

    parser.add_argument(
        "--root",
        default=".",
    )

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