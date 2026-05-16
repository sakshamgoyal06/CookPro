"""OpenAI transcription and recipe structuring."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from openai import OpenAI

import config

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "recipe_editor_prompt.txt"


class OpenAIServiceError(Exception):
    """User-friendly OpenAI or parsing failures."""

    pass


class RecipeJSONError(OpenAIServiceError):
    pass


def _client() -> OpenAI:
    if not config.OPENAI_API_KEY:
        raise OpenAIServiceError("OpenAI API key is not configured. Set OPENAI_API_KEY in your environment.")
    return OpenAI(api_key=config.OPENAI_API_KEY)


def transcribe_audio(file_path: str) -> str:
    client = _client()
    try:
        with open(file_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model=config.OPENAI_TRANSCRIBE_MODEL,
                file=audio_file,
            )
        text = (result.text or "").strip()
        return text
    except Exception as exc:
        raise OpenAIServiceError(f"Transcription failed: {exc}") from exc


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


def structure_recipe(transcript: str) -> dict[str, Any]:
    if not PROMPT_PATH.is_file():
        raise OpenAIServiceError("Recipe prompt file is missing.")
    template = PROMPT_PATH.read_text(encoding="utf-8")
    if "{{TRANSCRIPT}}" not in template:
        prompt = template + "\n\nTranscript:\n" + transcript
    else:
        prompt = template.replace("{{TRANSCRIPT}}", transcript)

    client = _client()
    try:
        completion = client.chat.completions.create(
            model=config.OPENAI_RECIPE_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You output only valid JSON for recipes. No markdown fences.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        raw = completion.choices[0].message.content or ""
    except Exception as exc:
        raise OpenAIServiceError(f"Recipe structuring failed: {exc}") from exc

    try:
        return _safe_parse_json(raw)
    except RecipeJSONError as exc:
        raise OpenAIServiceError(str(exc)) from exc
