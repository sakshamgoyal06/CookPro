"""OpenAI speech-to-text transcription."""

from __future__ import annotations

from openai import OpenAI

import config


class OpenAIServiceError(Exception):
    """User-friendly OpenAI transcription failures."""

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
