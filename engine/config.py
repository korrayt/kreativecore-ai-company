from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        return tomllib.load(stream)


@dataclass(frozen=True)
class ModelConfig:
    name: str
    release_tag: str
    release_asset: str
    context_size: int
    threads: int
    temperature: float
    max_tokens_analysis: int
    max_tokens_code: int
    max_tokens_review: int
    host: str
    port: int


def model_config(root: Path) -> ModelConfig:
    data = load_toml(root / "models" / "model.toml")
    model = data["model"]
    runtime = data["runtime"]
    return ModelConfig(
        name=str(model["name"]),
        release_tag=str(model["release_tag"]),
        release_asset=str(model["release_asset"]),
        context_size=int(model["context_size"]),
        threads=int(model["threads"]),
        temperature=float(model["temperature"]),
        max_tokens_analysis=int(model["max_tokens_analysis"]),
        max_tokens_code=int(model["max_tokens_code"]),
        max_tokens_review=int(model["max_tokens_review"]),
        host=str(runtime["server_host"]),
        port=int(runtime["server_port"]),
    )


def engine_settings(root: Path) -> dict[str, Any]:
    return load_toml(root / "company" / "ENGINE_SETTINGS.toml")
