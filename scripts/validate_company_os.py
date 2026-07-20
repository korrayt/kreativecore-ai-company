#!/usr/bin/env python3
"""Validate Kreative Core Company OS structure without third-party packages."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REQUIRED_FILES = ['README.md', 'AGENTS.md', 'AUTONOMOUS_COMPANY.md', 'PROPRIETARY_NOTICE.md', '.gitignore', '.coderabbit.yaml', '.github/copilot-instructions.md', '.github/workflows/company-os-ci.yml', '.github/workflows/mobile-company-control.yml', '.github/workflows/company-daily-orchestrator.yml', '.github/workflows/company-copilot-dispatch.yml', '.github/workflows/copilot-setup-steps.yml', 'company/DEPARTMENTS.toml', 'company/AGENT_REGISTRY.toml', 'company/POLICIES.toml', 'company/ORCHESTRATION.md', 'tasks/README.md', 'tasks/projects/_template/PROJECT.toml', 'tasks/inbox/_template/TASK.toml', 'scripts/company_orchestrator.py', 'scripts/sync_company_issues.py', 'docs/company/KREATIVE_CORE_COMPANY_OS.md', 'docs/company/ORGANIZATION.md', 'docs/company/PRODUCT_PORTFOLIO.md', 'docs/company/COMPANY_ROADMAP.md', 'docs/company/PAYMENT_ARCHITECTURE.md', 'docs/company/WORKFLOW.md', 'docs/company/RISK_REGISTER.md', 'docs/company/DECISION_LOG.md', 'products/README.md', 'security/SECURITY_POLICY.md', 'releases/RELEASE_CHECKLIST.md']

FORBIDDEN_TRACKED_PARTS = {
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "finance/private",
    "security/private",
    "operations/private",
    "contracts/private",
}

SECRET_PATTERNS = [
    ("GitHub token", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("classic GitHub token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("OpenAI key", re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
]

MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

def tracked_files(root: Path) -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "ls-files"], cwd=root, text=True, stderr=subprocess.DEVNULL
        )
        return [line.strip() for line in output.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return [
            str(path.relative_to(root)).replace("\\", "/")
            for path in root.rglob("*")
            if path.is_file() and ".git" not in path.parts
        ]

def validate(root: Path) -> list[str]:
    errors: list[str] = []
    files = tracked_files(root)

    for rel in REQUIRED_FILES:
        path = root / rel
        if not path.is_file():
            errors.append(f"Missing required file: {rel}")
        elif not path.read_text(encoding="utf-8", errors="ignore").strip():
            errors.append(f"Required file is empty: {rel}")

    for rel in files:
        normalized = rel.replace("\\", "/")
        parts = set(Path(normalized).parts)
        if any(item in parts or normalized.startswith(item + "/") for item in FORBIDDEN_TRACKED_PARTS):
            errors.append(f"Forbidden tracked path: {normalized}")

        path = root / rel
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"Possible {name} in: {normalized}")

        if path.suffix.lower() == ".md":
            for target in MARKDOWN_LINK.findall(text):
                target = target.strip().split("#", 1)[0]
                if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                if target.startswith("/"):
                    candidate = root / target.lstrip("/")
                else:
                    candidate = path.parent / target
                if not candidate.resolve().exists():
                    errors.append(f"Broken local link in {normalized}: {target}")


    agents_dir = root / ".github" / "agents"
    agent_files = list(agents_dir.glob("*.agent.md")) if agents_dir.is_dir() else []
    if len(agent_files) < 33:
        errors.append(f"Expected at least 33 custom agents, found {len(agent_files)}")
    for agent_file in agent_files:
        text = agent_file.read_text(encoding="utf-8", errors="ignore")
        if not text.startswith("---\n"):
            errors.append(f"Agent missing YAML frontmatter: {agent_file.relative_to(root)}")
        if "description:" not in text.split("---", 2)[1]:
            errors.append(f"Agent missing description: {agent_file.relative_to(root)}")

    return sorted(set(errors))

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    errors = validate(root)
    if errors:
        print("Kreative Core Company OS validation failed:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("Kreative Core Company OS validation passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
