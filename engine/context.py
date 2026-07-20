from __future__ import annotations

import re
from pathlib import Path

TEXT_EXTENSIONS = {".md", ".txt", ".toml", ".json", ".yaml", ".yml", ".py", ".js", ".jsx", ".ts", ".tsx", ".rs", ".html", ".css", ".scss", ".sql", ".sh", ".java", ".go", ".cs", ".cpp", ".c", ".h"}
IGNORE = {".git", ".engine-cache", ".engine-runtime", "node_modules", ".venv", "__pycache__", "dist", "build", "coverage"}


def read_text(path: Path, limit: int) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def select_context(root: Path, query: str, *, max_files: int, max_chars_per_file: int, max_total_chars: int) -> str:
    terms = set(re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü0-9_-]{3,}", query.lower()))
    candidates: list[tuple[int, str, Path]] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS or path.stat().st_size > 500_000:
            continue
        rel = path.relative_to(root)
        if any(part in IGNORE for part in rel.parts):
            continue
        rel_text = rel.as_posix().lower()
        preview = read_text(path, min(2500, max_chars_per_file)).lower()
        score = sum(4 for term in terms if term in rel_text) + sum(1 for term in terms if term in preview)
        if rel.as_posix() in {"README.md", "AGENTS.md", "pyproject.toml", "package.json"}:
            score += 3
        candidates.append((score, rel.as_posix(), path))
    candidates.sort(key=lambda x: (-x[0], x[1]))
    blocks: list[str] = []
    total = 0
    for _, rel, path in candidates[:max_files]:
        block = f"\n===== FILE: {rel} =====\n{read_text(path, max_chars_per_file)}\n"
        if total + len(block) > max_total_chars:
            break
        blocks.append(block)
        total += len(block)
    return "".join(blocks)
