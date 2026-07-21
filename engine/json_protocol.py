from __future__ import annotations

import json
import re
from typing import Any


class ProtocolError(ValueError):
    pass


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