"""Application configuration. Paths are absolute for predictable behavior."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
# Load project .env even when the app is started from a different working directory.
load_dotenv(BASE_DIR / ".env")

INSTANCE_DIR = BASE_DIR / "instance"
UPLOADS_DIR = BASE_DIR / "uploads"
AUDIO_DIR = UPLOADS_DIR / "audio"
IMAGES_DIR = UPLOADS_DIR / "images"
VIDEOS_DIR = UPLOADS_DIR / "videos"
OUTPUTS_DIR = BASE_DIR / "outputs"
PROMPTS_DIR = BASE_DIR / "prompts"

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me-in-production")
DATABASE_PATH = os.environ.get("DATABASE_PATH", str(INSTANCE_DIR / "cookbook_social.db"))

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_TRANSCRIBE_MODEL = os.environ.get("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe")
OPENAI_RECIPE_MODEL = os.environ.get("OPENAI_RECIPE_MODEL", "gpt-4.1")

MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB uploads


def ensure_directories() -> None:
    for d in (
        INSTANCE_DIR,
        UPLOADS_DIR,
        AUDIO_DIR,
        IMAGES_DIR,
        VIDEOS_DIR,
        OUTPUTS_DIR,
    ):
        d.mkdir(parents=True, exist_ok=True)
