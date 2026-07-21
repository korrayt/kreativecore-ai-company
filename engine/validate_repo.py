import re
import sys
import tomllib
from pathlib import Path
from typing import Any


REQUIRED = [
    "README.md",
    "QUICKSTART.md",
    "company/DEPARTMENTS.toml",
    "company/ENGINE_SETTINGS.toml",
    "company/AGENT_REGISTRY.toml",
    "models/model.toml",
    "engine/analyze_project.py",
    "engine/execute_task.py",
    "engine/runtime.py",
    "engine/llm_client.py",
    ".github/workflows/company-control.yml",
]

PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]

IGNORED_PARTS = {
    ".git",
    ".engine-cache",
    ".engine-runtime",
    "__pycache__",
    ".pytest_cache",
}


def load_toml(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except FileNotFoundError:
        return {}
    except tomllib.TOMLDecodeError as exc:
        errors.append(f"Invalid TOML {path}: {exc}")
        return {}


def validate_agents(root: Path, errors: list[str]) -> None:
    """Accept real prompt files or the registry-backed built-in prompt system."""
    prompt_files = list(
        (root / ".github" / "agents").glob("*.agent.md")
    )

    registry_path = root / "company" / "AGENT_REGISTRY.toml"
    registry = load_toml(registry_path, errors)
    registry_agents = registry.get("agents", [])

    if not isinstance(registry_agents, list):
        errors.append("AGENT_REGISTRY.toml: agents must be a list")
        registry_agents = []

    valid_entries = [
        item
        for item in registry_agents
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and item["id"].strip()
    ]

    ids = [str(item["id"]).strip() for item in valid_entries]
    duplicate_ids = sorted(
        {agent_id for agent_id in ids if ids.count(agent_id) > 1}
    )
    if duplicate_ids:
        errors.append(
            "Duplicate agent ids: " + ", ".join(duplicate_ids)
        )

    # The runtime supports registry-defined agents with built-in safe prompts.
    # Require the complete company registry even when individual prompt files
    # are intentionally absent.
    available_count = max(len(prompt_files), len(valid_entries))
    if available_count < 33:
        errors.append(
            "Expected at least 33 agents from prompt files or registry, "
            f"found {available_count}"
        )

    required_core = {
        "orchestrator",
        "executive",
        "planner",
        "analyst",
        "researcher",
        "product",
        "architect",
        "coder",
        "designer",
        "reviewer",
        "operator",
        "growth",
        "security-ethics",
    }
    missing_core = sorted(required_core - set(ids))
    if missing_core:
        errors.append(
            "Missing core agents in registry: " + ", ".join(missing_core)
        )


def validate_workflow(root: Path, errors: list[str]) -> None:
    workflow = root / ".github" / "workflows" / "company-control.yml"
    if not workflow.is_file():
        return

    content = workflow.read_text(encoding="utf-8", errors="ignore")
    required_operations = {
        "bootstrap-engine",
        "engine-health",
        "scan-intake",
        "analyze-project",
        "execute-task",
        "review-pr",
    }
    missing = sorted(
        operation
        for operation in required_operations
        if operation not in content
    )
    if missing:
        errors.append(
            "Unified workflow missing operations: " + ", ".join(missing)
        )


def validate(root: Path) -> list[str]:
    errors: list[str] = [
        f"Missing: {relative}"
        for relative in REQUIRED
        if not (root / relative).is_file()
    ]

    for path in root.rglob("*.toml"):
        if any(part in IGNORED_PARTS for part in path.parts):
            continue
        try:
            with path.open("rb") as stream:
                tomllib.load(stream)
        except tomllib.TOMLDecodeError as exc:
            errors.append(
                f"Invalid TOML {path.relative_to(root)}: {exc}"
            )

    for path in root.rglob("*"):
        if (
            not path.is_file()
            or path.stat().st_size > 2_000_000
            or any(part in IGNORED_PARTS for part in path.parts)
        ):
            continue

        content = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in PATTERNS:
            if pattern.search(content):
                errors.append(
                    f"Possible secret in {path.relative_to(root)}"
                )

    validate_agents(root, errors)
    validate_workflow(root, errors)

    return sorted(set(errors))


def main() -> int:
    root = Path(
        sys.argv[1] if len(sys.argv) > 1 else "."
    ).resolve()
    errors = validate(root)

    if errors:
        print("Repository validation failed:")
        for error in errors:
            print(" -", error)
        return 1

    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
