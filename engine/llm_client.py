from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class LLMError(RuntimeError):
    pass


@dataclass
class LLMClient:
    base_url: str
    model: str
    temperature: float = 0.15

    def chat(self, *, system: str, user: str, max_tokens: int, temperature: float | None = None) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        request = urllib.request.Request(
            self.base_url.rstrip("/") + "/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=1200) as response:
                data: dict[str, Any] = json.loads(response.read())
            return str(data["choices"][0]["message"]["content"])
        except (urllib.error.URLError, json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Local model request failed: {exc}") from exc
