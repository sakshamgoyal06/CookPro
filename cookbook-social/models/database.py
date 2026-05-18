"""SQLite database initialization and helpers. Designed for easy PostgreSQL migration later."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator, Optional

import config


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                bio TEXT DEFAULT '',
                profile_photo_filename TEXT,
                is_creator INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                caption TEXT DEFAULT '',
                story_note TEXT DEFAULT '',
                category TEXT DEFAULT '',
                cuisine TEXT DEFAULT '',
                difficulty TEXT DEFAULT '',
                serves TEXT DEFAULT '',
                prep_time_minutes INTEGER,
                cook_time_minutes INTEGER,
                visibility TEXT NOT NULL DEFAULT 'public',
                status TEXT NOT NULL DEFAULT 'draft',
                raw_transcript TEXT DEFAULT '',
                alternate_names_json TEXT DEFAULT '[]',
                ingredients_json TEXT DEFAULT '[]',
                method_steps_json TEXT DEFAULT '[]',
                tips_json TEXT DEFAULT '[]',
                tags_json TEXT DEFAULT '[]',
                unclear_items_json TEXT DEFAULT '[]',
                serving_suggestion TEXT DEFAULT '',
                storage_notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                published_at TEXT
            );

            CREATE TABLE IF NOT EXISTS recipe_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
                media_type TEXT NOT NULL,
                filename TEXT NOT NULL,
                thumbnail_filename TEXT,
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS follows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                follower_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                following_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                UNIQUE(follower_id, following_id)
            );

            CREATE TABLE IF NOT EXISTS saved_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                UNIQUE(user_id, recipe_id)
            );

            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                UNIQUE(user_id, recipe_id)
            );

            CREATE TABLE IF NOT EXISTS creator_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscriber_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                creator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                status TEXT NOT NULL DEFAULT 'active',
                started_at TEXT NOT NULL,
                expires_at TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(subscriber_id, creator_id)
            );

            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                visibility TEXT NOT NULL DEFAULT 'public',
                cover_image_filename TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS collection_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
                recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                UNIQUE(collection_id, recipe_id)
            );

            CREATE TABLE IF NOT EXISTS cookbook_themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                preview_image_filename TEXT,
                page_size TEXT DEFAULT 'A4',
                theme_config_json TEXT DEFAULT '{}',
                template_html_path TEXT,
                template_css_path TEXT,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_recipes_creator ON recipes(creator_id);
            CREATE INDEX IF NOT EXISTS idx_recipes_status_pub ON recipes(status, visibility, published_at);
            CREATE INDEX IF NOT EXISTS idx_follows_follower ON follows(follower_id);
            """
        )


def seed_cookbook_themes_if_empty() -> None:
    with get_db() as db:
        row = db.execute("SELECT COUNT(*) AS c FROM cookbook_themes").fetchone()
        if row and row["c"] > 0:
            return
        now = utcnow()
        themes = [
            (
                "Classic Indian Home",
                "Warm layouts inspired by traditional home kitchens and handwritten notes.",
                "A4",
                json.dumps({"accent": "maroon", "paper": "cream"}),
                None,
                None,
                now,
            ),
            (
                "Modern Minimal",
                "Clean typography and generous whitespace for a contemporary cookbook feel.",
                "A4",
                json.dumps({"accent": "charcoal", "paper": "white"}),
                None,
                None,
                now,
            ),
            (
                "Festive Heritage",
                "Rich borders and festive motifs suited for celebrations and family gatherings.",
                "Letter",
                json.dumps({"accent": "gold", "paper": "ivory"}),
                None,
                None,
                now,
            ),
        ]
        db.executemany(
            """
            INSERT INTO cookbook_themes (
                name, description, page_size, theme_config_json,
                template_html_path, template_css_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            themes,
        )


def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}


def parse_json_field(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def user_is_following(conn: sqlite3.Connection, follower_id: int, following_id: int) -> bool:
    r = conn.execute(
        "SELECT 1 FROM follows WHERE follower_id = ? AND following_id = ?",
        (follower_id, following_id),
    ).fetchone()
    return r is not None


def get_following_ids(conn: sqlite3.Connection, user_id: int) -> list[int]:
    rows = conn.execute(
        "SELECT following_id FROM follows WHERE follower_id = ?",
        (user_id,),
    ).fetchall()
    return [int(r["following_id"]) for r in rows]


def recipe_has_like(conn: sqlite3.Connection, user_id: int, recipe_id: int) -> bool:
    r = conn.execute(
        "SELECT 1 FROM likes WHERE user_id = ? AND recipe_id = ?",
        (user_id, recipe_id),
    ).fetchone()
    return r is not None


def recipe_is_saved(conn: sqlite3.Connection, user_id: int, recipe_id: int) -> bool:
    r = conn.execute(
        "SELECT 1 FROM saved_recipes WHERE user_id = ? AND recipe_id = ?",
        (user_id, recipe_id),
    ).fetchone()
    return r is not None
