"""One thin wrapper around any OpenAI-compatible /chat/completions endpoint.

This is the only file that knows how to talk to a model. To use a provider that
isn't OpenAI-compatible (check what Alan AI exposes), edit `chat()` only.
"""
from __future__ import annotations

import json
import re

import httpx

from ..config import Settings, get_settings


class LLMError(RuntimeError):
    pass


class LLMFormatError(ValueError):
    def __init__(self, raw: str):
        super().__init__("Model did not return valid JSON")
        self.raw = raw


def chat(messages: list[dict], *, json_mode: bool = False, temperature: float = 0.1, settings: Settings | None = None) -> str:
    s = settings or get_settings()
    body: dict = {"model": s.llm_model, "messages": messages, "temperature": temperature}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    headers = {"Authorization": f"Bearer {s.llm_api_key}"}
    url = f"{s.llm_base_url}/chat/completions"
    try:
        r = httpx.post(url, json=body, headers=headers, timeout=180)
        if r.status_code == 400 and json_mode:  # some servers reject response_format
            body.pop("response_format")
            r = httpx.post(url, json=body, headers=headers, timeout=180)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"] or ""
    except httpx.HTTPError as e:
        raise LLMError(f"LLM request to {url} failed: {e}") from e
    except (KeyError, IndexError, ValueError) as e:
        raise LLMError(f"Unexpected LLM response shape: {e}") from e


def parse_json(text: str) -> dict:
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.M).strip()
    try:
        out = json.loads(t)
    except json.JSONDecodeError:
        s, e = t.find("{"), t.rfind("}")
        if s == -1 or e <= s:
            raise ValueError("no JSON object found")
        out = json.loads(t[s : e + 1])
    if not isinstance(out, dict):
        raise ValueError("JSON is not an object")
    return out


def chat_json(messages: list[dict], *, retries: int = 1, settings: Settings | None = None) -> dict:
    """Ask for JSON; on a parse failure show the model its mistake and retry."""
    msgs = list(messages)
    raw = ""
    for attempt in range(retries + 1):
        raw = chat(msgs, json_mode=True, settings=settings)
        try:
            return parse_json(raw)
        except ValueError:
            if attempt == retries:
                break
            msgs = msgs + [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": "That was not valid JSON. Reply again with ONLY the JSON object, no prose, no code fences."},
            ]
    raise LLMFormatError(raw)
