from __future__ import annotations

import json
import re
from typing import Any


class ProtocolError(ValueError):
    pass


FORBIDDEN_MARKERS = (
    "===== FILE:",
    "SELECTED REPOSITORY CONTEXT:",
    "PROJECT CONTEXT:",
    '"kind": "project"',
    '"departments": [',
)


def _check_string(val: Any, name: str, min_len: int = 1) -> str:
    if not isinstance(val, str):
        raise ProtocolError(f"Department JSON field '{name}' must be a string")
    cleaned = val.strip()
    if len(cleaned) < min_len:
        raise ProtocolError(f"Department JSON field '{name}' is too short (min {min_len} chars)")
    if "```" in cleaned or "~~~" in cleaned:
        raise ProtocolError(f"Department JSON field '{name}' must not contain Markdown code fences")
    for marker in FORBIDDEN_MARKERS:
        if marker in cleaned:
            raise ProtocolError(f"Department JSON field '{name}' contains copied repository context: {marker}")
    return cleaned


def _check_string_list(val: Any, name: str, min_items: int = 1) -> list[str]:
    if not isinstance(val, list):
        raise ProtocolError(f"Department JSON field '{name}' must be a list")
    items: list[str] = []
    for idx, item in enumerate(val):
        item_str = _check_string(item, f"{name}[{idx}]", min_len=3)
        items.append(item_str)
    if len(items) < min_items:
        raise ProtocolError(f"Department JSON field '{name}' must contain at least {min_items} item(s)")
    return items


def validate_department_json(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ProtocolError("Department payload must be a JSON object")

    objective = _check_string(payload.get("objective"), "objective", min_len=15)
    required_inputs = _check_string_list(payload.get("required_inputs"), "required_inputs", min_items=1)
    dependencies = _check_string_list(payload.get("dependencies"), "dependencies", min_items=1)
    acceptance_criteria = _check_string_list(payload.get("acceptance_criteria"), "acceptance_criteria", min_items=1)
    risks = _check_string_list(payload.get("risks"), "risks", min_items=1)

    next_task = payload.get("next_task")
    if not isinstance(next_task, dict):
        raise ProtocolError("Department JSON field 'next_task' must be an object")

    task_title = _check_string(next_task.get("title"), "next_task.title", min_len=5)
    task_desc = _check_string(next_task.get("description"), "next_task.description", min_len=15)
    task_deliverable = _check_string(next_task.get("deliverable"), "next_task.deliverable", min_len=5)
    task_done_when = _check_string_list(next_task.get("done_when"), "next_task.done_when", min_items=1)

    return {
        "objective": objective,
        "required_inputs": required_inputs,
        "dependencies": dependencies,
        "acceptance_criteria": acceptance_criteria,
        "risks": risks,
        "next_task": {
            "title": task_title,
            "description": task_desc,
            "deliverable": task_deliverable,
            "done_when": task_done_when,
        },
    }


def render_department_markdown(data: dict[str, Any], department_name: str) -> str:
    obj = data["objective"]
    inputs_md = "\n".join(f"- {item}" for item in data["required_inputs"])
    deps_md = "\n".join(f"- {item}" for item in data["dependencies"])
    criteria_md = "\n".join(f"- {item}" for item in data["acceptance_criteria"])
    risks_md = "\n".join(f"- {item}" for item in data["risks"])

    next_task = data["next_task"]
    task_title = next_task["title"]
    task_desc = next_task["description"]
    task_deliv = next_task["deliverable"]
    done_md = "\n".join(f"- {item}" for item in next_task["done_when"])

    return f"""# {department_name} Raporu

## Amaç

{obj}

## Gerekli Girdiler

{inputs_md}

## Bağımlılıklar

{deps_md}

## Kabul Kriterleri

{criteria_md}

## Riskler

{risks_md}

## Sonraki Uygulanabilir Görev

### Görev

{task_title}

### Açıklama

{task_desc}

### Teslimat

{task_deliv}

### Tamamlanma Koşulları

{done_md}
""".strip() + "\n"



def extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    candidates = [stripped]

    candidates += re.findall(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        stripped,
        flags=re.S,
    )

    start = stripped.find("{")
    end = stripped.rfind("}")

    if start >= 0 and end > start:
        candidates.append(
            stripped[start:end + 1]
        )

    errors: list[str] = []

    for candidate in candidates:
        versions = (
            candidate,
            re.sub(
                r",\s*([}\]])",
                r"\1",
                candidate,
            ),
        )

        for version in versions:
            try:
                value = json.loads(version)

                if not isinstance(value, dict):
                    raise ProtocolError(
                        "Root JSON must be an object"
                    )

                return value

            except (
                json.JSONDecodeError,
                ProtocolError,
            ) as exc:
                errors.append(str(exc))

    raise ProtocolError(
        "Could not parse model JSON: "
        + " | ".join(errors[:4])
    )


def normalized_heading(text: str) -> str:
    value = text.casefold()

    value = (
        value.replace("ı", "i")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ş", "s")
        .replace("ö", "o")
        .replace("ç", "c")
    )

    return re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    ).strip()


def has_heading(
    content: str,
    alternatives: tuple[str, ...],
) -> bool:
    headings = re.findall(
        r"(?m)^\s{0,3}#{1,6}\s+(.+?)\s*$",
        content,
    )

    normalized = {
        normalized_heading(heading)
        for heading in headings
    }

    expected = {
        normalized_heading(item)
        for item in alternatives
    }

    return bool(
        normalized.intersection(expected)
    )


def validate_department_document(
    path: str,
    content: str,
) -> None:
    normalized_path = path.replace("\\", "/")

    if "/.company/departments/" not in normalized_path:
        return

    if not normalized_path.endswith(".md"):
        raise ProtocolError(
            "Department output must be a Markdown file"
        )

    document = content.strip()

    if len(document) < 500:
        raise ProtocolError(
            "Department document is too short"
        )

    if len(document) > 18000:
        raise ProtocolError(
            "Department document is too large"
        )

    if "```" in document or "~~~" in document:
        raise ProtocolError(
            "Department document must not contain "
            "Markdown code fences"
        )

    forbidden_markers = (
        "===== FILE:",
        "SELECTED REPOSITORY CONTEXT:",
        "PROJECT CONTEXT:",
        '"kind": "project"',
        '"departments": [',
    )

    for marker in forbidden_markers:
        if marker in document:
            raise ProtocolError(
                "Department document contains copied "
                f"repository context: {marker}"
            )

    required_sections = {
        "objective": (
            "Objective",
            "Amaç",
            "Hedef",
        ),
        "required inputs": (
            "Required inputs",
            "Gerekli girdiler",
            "Girdiler",
        ),
        "dependencies": (
            "Dependencies",
            "Bağımlılıklar",
        ),
        "acceptance criteria": (
            "Acceptance criteria",
            "Kabul kriterleri",
        ),
        "risks": (
            "Risks",
            "Riskler",
        ),
        "smallest next executable task": (
            "Smallest next executable task",
            "En küçük sonraki uygulanabilir görev",
            "Sonraki uygulanabilir görev",
            "Sonraki görev",
        ),
    }

    missing = [
        name
        for name, alternatives
        in required_sections.items()
        if not has_heading(
            document,
            alternatives,
        )
    ]

    if missing:
        raise ProtocolError(
            "Department document is missing required "
            "sections: "
            + ", ".join(missing)
        )

    meaningful_lines = [
        line.strip()
        for line in document.splitlines()
        if line.strip()
        and not line.lstrip().startswith("#")
    ]

    if len(meaningful_lines) < 12:
        raise ProtocolError(
            "Department document does not contain "
            "enough substantive content"
        )

    if document.endswith(
        (
            ":",
            ",",
            "{",
            "[",
            '"',
            "`",
        )
    ):
        raise ProtocolError(
            "Department document appears truncated"
        )


def validate_code_actions(
    payload: dict[str, Any],
) -> list[dict[str, str]]:
    actions = payload.get("actions")

    if not isinstance(actions, list):
        raise ProtocolError(
            "actions must be a list"
        )

    output: list[dict[str, str]] = []

    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            raise ProtocolError(
                f"Action {index} must be an object"
            )

        op = action.get("op")
        path = action.get("path")

        if op not in {"write", "delete"}:
            raise ProtocolError(
                f"Invalid action op at {index}"
            )

        if (
            not isinstance(path, str)
            or not path.strip()
        ):
            raise ProtocolError(
                f"Invalid path at {index}"
            )

        clean_path = path.strip()

        item = {
            "op": op,
            "path": clean_path,
        }

        if op == "write":
            content = action.get("content")

            if not isinstance(content, str):
                raise ProtocolError(
                    "Write content must be text "
                    f"at {index}"
                )

            validate_department_document(
                clean_path,
                content,
            )

            item["content"] = content

        output.append(item)

    return output