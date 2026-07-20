from __future__ import annotations

from pathlib import Path

from engine.config import engine_settings, model_config
from engine.context import select_context
from engine.llm_client import LLMClient


def read_agent(root: Path, agent: str) -> str:
    direct = root / ".github" / "agents" / f"{agent}.agent.md"
    if direct.is_file():
        return direct.read_text(encoding="utf-8", errors="ignore")
    matches = list((root / ".github" / "agents").glob(f"*{agent}*.agent.md"))
    if not matches:
        raise FileNotFoundError(f"Unknown agent: {agent}")
    return matches[0].read_text(encoding="utf-8", errors="ignore")


def client(root: Path) -> LLMClient:
    config = model_config(root)
    return LLMClient(f"http://{config.host}:{config.port}", config.name, config.temperature)


def repo_context(root: Path, query: str) -> str:
    settings = engine_settings(root)["engine"]
    return select_context(
        root,
        query,
        max_files=int(settings["max_context_files"]),
        max_chars_per_file=int(settings["max_chars_per_file"]),
        max_total_chars=int(settings["max_total_context_chars"]),
    )
