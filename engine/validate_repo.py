from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

REQUIRED = [
    "README.md", "QUICKSTART.md", "company/DEPARTMENTS.toml", "company/ENGINE_SETTINGS.toml",
    "models/model.toml", "engine/analyze_project.py", "engine/execute_task.py",
    ".github/workflows/bootstrap-engine.yml", ".github/workflows/daily-intake.yml",
    ".github/workflows/ai-analyze-project.yml", ".github/workflows/ai-execute-task.yml",
]
PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


def validate(root: Path) -> list[str]:
    errors = [f"Missing: {rel}" for rel in REQUIRED if not (root / rel).is_file()]
    for path in root.rglob("*.toml"):
        try:
            with path.open("rb") as stream:
                tomllib.load(stream)
        except tomllib.TOMLDecodeError as exc:
            errors.append(f"Invalid TOML {path.relative_to(root)}: {exc}")
    for path in root.rglob("*"):
        if not path.is_file() or path.stat().st_size > 2_000_000 or any(x in path.parts for x in {".git", ".engine-cache", ".engine-runtime"}):
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in PATTERNS:
            if pattern.search(content):
                errors.append(f"Possible secret in {path.relative_to(root)}")
    agents = list((root / ".github" / "agents").glob("*.agent.md"))
    if len(agents) < 33:
        errors.append(f"Expected at least 33 agents, found {len(agents)}")
    return sorted(set(errors))


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
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
