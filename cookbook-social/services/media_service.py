"""File upload validation and storage."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional, Tuple

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

import config

ALLOWED_AUDIO = {".mp3", ".m4a", ".wav", ".ogg", ".webm"}
ALLOWED_IMAGES = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEOS = {".mp4", ".mov", ".webm"}

FOLDER_FOR_TYPE = {
    "audio": config.AUDIO_DIR,
    "images": config.IMAGES_DIR,
    "videos": config.VIDEOS_DIR,
}


def _ext(name: str) -> str:
    return Path(name).suffix.lower()


def validate_file_type(filename: str, category: str) -> Tuple[bool, str]:
    ext = _ext(filename)
    if category == "audio":
        if ext not in ALLOWED_AUDIO:
            return False, f"Unsupported audio type {ext or '(none)'}. Allowed: {', '.join(sorted(ALLOWED_AUDIO))}."
        return True, ""
    if category == "image":
        if ext not in ALLOWED_IMAGES:
            return False, f"Unsupported image type {ext or '(none)'}. Allowed: {', '.join(sorted(ALLOWED_IMAGES))}."
        return True, ""
    if category == "video":
        if ext not in ALLOWED_VIDEOS:
            return False, f"Unsupported video type {ext or '(none)'}. Allowed: {', '.join(sorted(ALLOWED_VIDEOS))}."
        return True, ""
    return False, "Unknown media category."


def save_uploaded_file(storage: FileStorage, category: str) -> str:
    """Save file to uploads/{audio|images|videos}. Returns stored filename (unique prefix + secure base)."""
    if not storage or not storage.filename:
        raise ValueError("No file provided.")
    ok, err = validate_file_type(storage.filename, category)
    if not ok:
        raise ValueError(err)
    base = secure_filename(storage.filename) or "file"
    unique = f"{uuid.uuid4().hex[:12]}_{base}"
    dest_dir = FOLDER_FOR_TYPE.get(
        "audio" if category == "audio" else "images" if category == "image" else "videos"
    )
    if dest_dir is None:
        raise ValueError("Invalid category.")
    dest_path = dest_dir / unique
    storage.save(str(dest_path))
    if not os.path.isfile(dest_path):
        raise RuntimeError("Failed to save upload.")
    return unique


def media_url(media_type: str, filename: Optional[str]) -> Optional[str]:
    if not filename:
        return None
    if media_type == "image":
        return f"/files/images/{filename}"
    if media_type == "video":
        return f"/files/videos/{filename}"
    if media_type == "audio":
        return f"/files/audio/{filename}"
    return None
