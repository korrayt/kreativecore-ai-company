from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from engine.config import engine_settings


def run_checks(root: Path) -> list[dict[str, Any]]:
    checks = engine_settings(root)["checks"]
    commands: list[str] = list(checks["generic"])
    if (root / "pyproject.toml").is_file() or (root / "pytest.ini").is_file():
        commands.extend(checks["python"])
    if (root / "package.json").is_file():
        commands.extend(checks["node"])
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for command in commands:
        if command in seen:
            continue
        seen.add(command)
        process = subprocess.run(command, cwd=root, shell=True, text=True, capture_output=True, timeout=900)
        results.append({
            "command": command,
            "returncode": process.returncode,
            "stdout": process.stdout[-8000:],
            "stderr": process.stderr[-8000:],
        })
        if process.returncode != 0:
            break
    return results
