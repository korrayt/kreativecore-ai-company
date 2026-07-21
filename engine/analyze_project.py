from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from engine.config import model_config
from engine.json_protocol import ProtocolError, extract_json
from engine.runtime import client, read_agent, repo_context


def text(path: Path) -> str:
    return (
        path.read_text(encoding="utf-8", errors="ignore")
        if path.is_file()
        else ""
    )


def call_json(
    *,
    llm: Any,
    system: str,
    user: str,
    max_tokens: int,
    fallback: dict[str, Any],
) -> dict[str, Any]:
    """Ask for concise JSON, repair once, then return a safe explicit fallback."""
    raw = llm.chat(
        system=(
            system
            + "\nReturn ONE compact valid JSON object only."
            + "\nNo markdown. No code fence. No prose outside JSON."
            + "\nKeep every string concise and every list short."
        ),
        user=user,
        max_tokens=min(max_tokens, 650),
        temperature=0.1,
    )

    try:
        return extract_json(raw)
    except ProtocolError as first_error:
        repair_prompt = f"""Repair the following malformed or incomplete JSON.

RULES:
- Return one valid JSON object only.
- Preserve useful information when possible.
- Remove unfinished fragments.
- Keep the result concise.
- Do not use markdown.

BROKEN OUTPUT:
{raw[:5000]}
"""
        repaired = llm.chat(
            system="You repair JSON. Return valid JSON only.",
            user=repair_prompt,
            max_tokens=500,
            temperature=0,
        )
        try:
            return extract_json(repaired)
        except ProtocolError as second_error:
            result = dict(fallback)
            result["_warning"] = (
                "Local model produced invalid JSON twice; safe fallback used."
            )
            result["_parse_errors"] = [
                str(first_error)[:500],
                str(second_error)[:500],
            ]
            return result


def analyze(root: Path, slug: str) -> None:
    project = root / "tasks" / "projects" / slug
    if not project.is_dir():
        raise FileNotFoundError(f"Project not found: {slug}")

    manifest = text(project / "PROJECT.toml")
    brief = text(project / "BRIEF.md")
    context = repo_context(root, f"{slug}\n{manifest}\n{brief}")
    llm = client(root)
    model = model_config(root)

    analyst = call_json(
        llm=llm,
        system=read_agent(root, "analyst"),
        user=f"""Analyze project `{slug}`.

Return keys:
analysis, opportunities, unknowns, departments, first_decision, success_signal.

PROJECT TOML:
{manifest}

BRIEF:
{brief}

SELECTED CONTEXT:
{context}
""",
        max_tokens=model.max_tokens_analysis,
        fallback={
            "analysis": "Automatic deep analysis could not be parsed.",
            "opportunities": [],
            "unknowns": ["Review the project brief manually."],
            "departments": [],
            "first_decision": "Review project scope and retry analysis.",
            "success_signal": "A valid reviewed analysis is available.",
        },
    )

    planner = call_json(
        llm=llm,
        system=read_agent(root, "planner"),
        user=f"""Create a concise roadmap for `{slug}`.

Return keys:
objective, milestones, dependencies, acceptance_criteria, risks, next_action.

Use at most 5 milestones. Keep each item short.

ANALYSIS:
{json.dumps(analyst, ensure_ascii=False)}

BRIEF:
{brief[:5000]}
""",
        max_tokens=model.max_tokens_analysis,
        fallback={
            "objective": "Convert the approved project brief into a working MVP.",
            "milestones": [
                "Confirm scope",
                "Approve architecture",
                "Build smallest prototype",
                "Test and review",
            ],
            "dependencies": ["Founder scope approval"],
            "acceptance_criteria": [
                "A reviewed roadmap exists",
                "The first executable task is defined",
            ],
            "risks": ["Local model output required fallback"],
            "next_action": "Review and approve the MVP scope.",
        },
    )

    architect = call_json(
        llm=llm,
        system=read_agent(root, "architect"),
        user=f"""Create a concise architecture note for `{slug}`.

Return keys:
architecture, components, data_flow, technical_risks, validation.

Use at most 6 components and short strings.

ANALYSIS:
{json.dumps(analyst, ensure_ascii=False)}

ROADMAP:
{json.dumps(planner, ensure_ascii=False)}

REPOSITORY CONTEXT:
{context[:5000]}
""",
        max_tokens=model.max_tokens_analysis,
        fallback={
            "architecture": "Small modular local-first desktop architecture.",
            "components": [
                "Desktop shell",
                "Local model adapter",
                "Project memory",
                "Permission manager",
                "Diagnostics",
            ],
            "data_flow": "User input -> permission check -> local service -> local storage.",
            "technical_risks": [
                "Model context limits",
                "Platform packaging",
                "File permission safety",
            ],
            "validation": [
                "Run local model health check",
                "Test project creation",
                "Test permission gates",
            ],
        },
    )

    company = project / ".company"
    company.mkdir(parents=True, exist_ok=True)

    outputs = [
        ("AI_ANALYSIS", analyst),
        ("AI_ROADMAP", planner),
        ("AI_ARCHITECTURE", architect),
    ]
    for name, value in outputs:
        (company / f"{name}.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    (company / "AI_REPORT.md").write_text(
        f"""# {slug} — Local AI Company Report

## Analysis

```json
{json.dumps(analyst, ensure_ascii=False, indent=2)}
```

## Roadmap

```json
{json.dumps(planner, ensure_ascii=False, indent=2)}
```

## Architecture

```json
{json.dumps(architect, ensure_ascii=False, indent=2)}
```
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("slug")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    analyze(Path(args.root).resolve(), args.slug)
    print(f"AI analysis completed for {args.slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
