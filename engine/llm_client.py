from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class LLMError(RuntimeError):
    pass


def _compact(text: str, limit: int) -> str:
    """Keep useful beginning and ending context inside a conservative char budget."""
    text = text.strip()
    if len(text) <= limit:
        return text
    marker = "\n\n[... context shortened to fit local model ...]\n\n"
    head = max(1, int(limit * 0.72))
    tail = max(1, limit - head - len(marker))
    return text[:head] + marker + text[-tail:]


@dataclass
class LLMClient:
    base_url: str
    model: str
    temperature: float = 0.15

    def _request(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        request = urllib.request.Request(
            self.base_url.rstrip("/") + "/v1/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=1200) as response:
                data: dict[str, Any] = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise LLMError(
                f"Local model HTTP {exc.code}: {detail or exc.reason}"
            ) from exc
        except urllib.error.URLError as exc:
            raise LLMError(f"Local model connection failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise LLMError(f"Local model returned invalid JSON envelope: {exc}") from exc

        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected local model response: {data}") from exc

    def chat(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        temperature: float | None = None,
    ) -> str:
        temp = self.temperature if temperature is None else temperature

        # Qwen server is currently launched with a 4096-token context.
        # Keep enough room for the requested completion.
        first_system = _compact(system, 2400)
        first_user = _compact(user, 6200)

        try:
            return self._request(
                system=first_system,
                user=first_user,
                max_tokens=max_tokens,
                temperature=temp,
            )
        except LLMError as first_error:
            # Context-size failures commonly arrive as HTTP 400. Retry once with
            # a much smaller prompt instead of failing the entire company run.
            if "HTTP 400" not in str(first_error):
                raise

            retry_system = _compact(system, 1500)
            retry_user = _compact(user, 3600)
            retry_tokens = min(max_tokens, 700)

            try:
                return self._request(
                    system=retry_system,
                    user=retry_user,
                    max_tokens=retry_tokens,
                    temperature=temp,
                )
            except LLMError as retry_error:
                raise LLMError(
                    "Local model request failed after automatic context reduction. "
                    f"First error: {first_error}; retry error: {retry_error}"
                ) from retry_error
