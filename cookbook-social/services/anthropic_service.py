"""Anthropic Claude for structured recipe JSON from transcripts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import anthropic

import config

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "recipe_editor_prompt.txt"


class AnthropicServiceError(Exception):
    """User-friendly Anthropic API or parsing failures."""

    pass


class RecipeJSONError(AnthropicServiceError):
    pass


def _client() -> anthropic.Anthropic:
    if not config.ANTHROPIC_API_KEY:
        raise AnthropicServiceError(
            "Anthropic API key is not configured. Set ANTHROPIC_API_KEY in your environment."
        )
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def _extract_json_object(text: str) -> str:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    fence = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
    if fence:
        return fence.group(1).strip()
    brace = re.search(r"(\{[\s\S]*\})", text)
    if brace:
        return brace.group(1).strip()
    return text


def _safe_parse_json(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
        raise RecipeJSONError("Model output was not a JSON object.")
    except json.JSONDecodeError:
        extracted = _extract_json_object(text)
        try:
            data = json.loads(extracted)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        raise RecipeJSONError("Could not parse recipe JSON from the model response.")


def _response_text(message: Any) -> str:
    parts: list[str] = []
    for block in message.content:
        if getattr(block, "type", None) == "text":
            t = getattr(block, "text", None)
            if t:
                parts.append(t)
    return "".join(parts).strip()


def structure_recipe(transcript: str) -> dict[str, Any]:
    if not PROMPT_PATH.is_file():
        raise AnthropicServiceError("Recipe prompt file is missing.")
    template = PROMPT_PATH.read_text(encoding="utf-8")
    if "{{TRANSCRIPT}}" not in template:
        prompt = template + "\n\nTranscript:\n" + transcript
    else:
        prompt = template.replace("{{TRANSCRIPT}}", transcript)

    client = _client()
    try:
        message = client.messages.create(
            model=config.ANTHROPIC_RECIPE_MODEL,
            max_tokens=8192,
            temperature=0.3,
            system="You output only valid JSON for recipes. No markdown fences or commentary outside JSON.",
            messages=[{"role": "user", "content": prompt}],
        )
        raw = _response_text(message)
    except Exception as exc:
        raise AnthropicServiceError(f"Recipe structuring failed: {exc}") from exc

    if not raw:
        raise AnthropicServiceError("The model returned an empty response.")

    try:
        return _safe_parse_json(raw)
    except RecipeJSONError as exc:
        raise AnthropicServiceError(str(exc)) from exc
