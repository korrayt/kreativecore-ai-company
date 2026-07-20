from __future__ import annotations

import json
import re
from typing import Any


class ProtocolError(ValueError):
    pass


def extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    candidates = [stripped]
    candidates += re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.S)
    start, end = stripped.find("{"), stripped.rfind("}")
    if start >= 0 and end > start:
        candidates.append(stripped[start:end + 1])
    errors: list[str] = []
    for candidate in candidates:
        for version in (candidate, re.sub(r",\s*([}\]])", r"\1", candidate)):
            try:
                value = json.loads(version)
                if not isinstance(value, dict):
                    raise ProtocolError("Root JSON must be an object")
                return value
            except (json.JSONDecodeError, ProtocolError) as exc:
                errors.append(str(exc))
    raise ProtocolError("Could not parse model JSON: " + " | ".join(errors[:4]))


def validate_code_actions(payload: dict[str, Any]) -> list[dict[str, str]]:
    actions = payload.get("actions")
    if not isinstance(actions, list):
        raise ProtocolError("actions must be a list")
    output: list[dict[str, str]] = []
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            raise ProtocolError(f"Action {index} must be an object")
        op, path = action.get("op"), action.get("path")
        if op not in {"write", "delete"}:
            raise ProtocolError(f"Invalid action op at {index}")
        if not isinstance(path, str) or not path.strip():
            raise ProtocolError(f"Invalid path at {index}")
        item = {"op": op, "path": path.strip()}
        if op == "write":
            content = action.get("content")
            if not isinstance(content, str):
                raise ProtocolError(f"Write content must be text at {index}")
            item["content"] = content
        output.append(item)
    return output
