from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from engine.config import engine_settings, model_config
from engine.context import select_context
from engine.llm_client import LLMClient


CORE_PROMPTS: dict[str, str] = {
    "orchestrator": "Coordinate the company workflow. Route work to the smallest relevant set of agents and preserve approval gates.",
    "executive": "Act as the executive decision agent. Clarify priorities, trade-offs, founder decisions and measurable outcomes.",
    "planner": "Turn the approved objective into a realistic staged roadmap with dependencies, acceptance criteria, risks and one next action.",
    "analyst": "Analyze the complete project context. Identify the real problem, opportunities, unknowns, risks, required departments and the first decision. Do not invent facts.",
    "researcher": "Plan and perform evidence-oriented technical, user and market research. Separate verified facts, assumptions and open questions.",
    "product": "Define the user problem, value proposition, MVP scope, exclusions, success signals and acceptance criteria.",
    "architect": "Design a small, secure and testable architecture. Explain components, boundaries, data flow, dependencies, risks and validation steps.",
    "coder": "Implement only the approved task as small, reversible and testable repository changes. Respect protected paths and never invent successful tests.",
    "designer": "Design the user experience, interface structure and creative output around explicit user needs, accessibility and implementation constraints.",
    "reviewer": "Independently review correctness, scope, security, regressions, usability and test evidence. State uncertainty and request changes when needed.",
    "operator": "Manage queues, workflow health, blockers, status and company memory. Prefer deterministic and idempotent operations.",
    "growth": "Define measurable distribution, adoption, retention, learning and revenue experiments without dark patterns.",
    "security-ethics": "Protect security, privacy, consent, legal boundaries and human safety. Require explicit approval for consequential actions.",
}

BASE_RULES = """
You are an agent inside Kreative Core AI Company.
- Read the supplied task and repository context carefully.
- Do not invent facts, users, metrics, legal conclusions or successful tests.
- Keep work strictly inside scope.
- State uncertainty explicitly.
- Protect secrets, personal data and user control.
- Prefer small, reversible and testable steps.
- Return only the output format requested by the caller.
""".strip()


def _registry(root: Path) -> dict[str, dict[str, Any]]:
    path = root / "company" / "AGENT_REGISTRY.toml"
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as stream:
            data = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return {
        str(item.get("id")): item
        for item in data.get("agents", [])
        if item.get("id")
    }


def _candidate_paths(root: Path, agent: str) -> list[Path]:
    return [
        root / ".github" / "agents" / f"{agent}.agent.md",
        root / "company" / "agents" / "core" / f"{agent}.md",
        root / "company" / "agents" / "departments" / f"{agent}.md",
    ]


def read_agent(root: Path, agent: str) -> str:
    for path in _candidate_paths(root, agent):
        if path.is_file():
            return path.read_text(encoding="utf-8", errors="ignore")

    agents_dir = root / ".github" / "agents"
    if agents_dir.is_dir():
        matches = sorted(agents_dir.glob(f"*{agent}*.agent.md"))
        if matches:
            return matches[0].read_text(encoding="utf-8", errors="ignore")

    entry = _registry(root).get(agent, {})
    role = CORE_PROMPTS.get(agent)

    if role is None and entry:
        name = str(entry.get("name") or agent)
        description = str(
            entry.get("description")
            or "Perform the assigned department work."
        )
        department = str(entry.get("department") or "company")
        role = (
            f"Act as the {name} agent for department '{department}'. "
            f"{description} Produce only department-specific, actionable work; "
            "make dependencies on other departments explicit."
        )

    if role is None:
        role = (
            f"Act as the '{agent}' company agent. Complete only the assigned "
            "scope, make assumptions explicit and preserve all safety and "
            "approval gates."
        )

    return f"{role}\n\n{BASE_RULES}"


def client(root: Path) -> LLMClient:
    config = model_config(root)
    return LLMClient(
        f"http://{config.host}:{config.port}",
        config.name,
        config.temperature,
    )


def repo_context(root: Path, query: str) -> str:
    settings = engine_settings(root)["engine"]
    return select_context(
        root,
        query,
        max_files=int(settings["max_context_files"]),
        max_chars_per_file=int(settings["max_chars_per_file"]),
        max_total_chars=int(settings["max_total_context_chars"]),
    )
