from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Iterable


class SafetyError(ValueError):
    pass


def safe_relative_path(value: str) -> PurePosixPath:
    value = value.replace("\\", "/").strip()
    path = PurePosixPath(value)
    if path.is_absolute() or not value or ".." in path.parts:
        raise SafetyError(f"Unsafe path: {value}")
    if any(part in {"", ".", ".git"} for part in path.parts):
        raise SafetyError(f"Unsafe path: {value}")
    return path


def apply_actions(root: Path, actions: list[dict[str, str]], *, protected_prefixes: Iterable[str], max_files: int, max_bytes: int) -> list[str]:
    if len(actions) > max_files:
        raise SafetyError(f"Too many actions: {len(actions)} > {max_files}")
    total = sum(len(x.get("content", "").encode("utf-8")) for x in actions if x["op"] == "write")
    if total > max_bytes:
        raise SafetyError(f"Generated output too large: {total} > {max_bytes}")
    changed: list[str] = []
    root_resolved = root.resolve()
    for action in actions:
        rel = safe_relative_path(action["path"])
        normalized = rel.as_posix()
        for prefix in protected_prefixes:
            clean = str(prefix).replace("\\", "/")
            if normalized == clean.rstrip("/") or normalized.startswith(clean):
                raise SafetyError(f"Protected path: {normalized}")
        target = (root / normalized).resolve()
        if root_resolved not in target.parents:
            raise SafetyError(f"Path escapes repository: {normalized}")
        if action["op"] == "write":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(action["content"], encoding="utf-8", newline="\n")
        elif target.is_file():
            target.unlink()
        changed.append(normalized)
    return changed
