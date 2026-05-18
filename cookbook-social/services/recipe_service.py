"""Recipe CRUD, publishing, and listing helpers."""

from __future__ import annotations

import json
import re
import secrets
import sqlite3
from typing import Any, Optional

from models import database as db


def _slugify_title(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (title or "recipe").lower()).strip("-")
    if not s:
        s = "recipe"
    return s[:60]


def generate_recipe_slug(title: str) -> str:
    return f"{_slugify_title(title)}-{secrets.token_urlsafe(6).replace('-', '')[:8]}"


def _dump_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def create_recipe_from_upload(
    creator_id: int,
    structured: dict[str, Any],
    raw_transcript: str,
    visibility: str,
    user_caption: str,
    category_override: str,
    cuisine_override: str,
    audio_filename: str,
    image_filename: Optional[str],
    video_filename: Optional[str],
) -> int:
    now = db.utcnow()
    title = (structured.get("recipe_title") or "Untitled recipe").strip() or "Untitled recipe"
    slug = generate_recipe_slug(title)
    caption = (structured.get("caption") or user_caption or "").strip()
    story = (structured.get("story_note") or "").strip()
    category = (category_override or structured.get("category") or "").strip()
    cuisine = (cuisine_override or structured.get("cuisine") or "").strip()
    difficulty = (structured.get("difficulty") or "").strip()
    serves = str(structured.get("serves") or "").strip()
    prep = structured.get("prep_time_minutes")
    cook = structured.get("cook_time_minutes")
    ingredients = structured.get("ingredients") or []
    method = structured.get("method_steps") or []
    tips = structured.get("creator_tips") or []
    tags = structured.get("tags") or []
    unclear = structured.get("unclear_items_for_review") or []
    alt_names = structured.get("alternate_names") or []
    serving = (structured.get("serving_suggestion") or "").strip()
    storage = (structured.get("storage_notes") or "").strip()

    with db.get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO recipes (
                creator_id, title, slug, caption, story_note, category, cuisine, difficulty,
                serves, prep_time_minutes, cook_time_minutes, visibility, status,
                raw_transcript, alternate_names_json, ingredients_json, method_steps_json,
                tips_json, tags_json, unclear_items_json, serving_suggestion, storage_notes,
                created_at, updated_at, published_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'needs_review', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
            """,
            (
                creator_id,
                title,
                slug,
                caption,
                story,
                category,
                cuisine,
                difficulty,
                serves,
                int(prep) if prep is not None and str(prep).strip() != "" else None,
                int(cook) if cook is not None and str(cook).strip() != "" else None,
                visibility,
                raw_transcript,
                _dump_json(alt_names),
                _dump_json(ingredients),
                _dump_json(method),
                _dump_json(tips),
                _dump_json(tags),
                _dump_json(unclear),
                serving,
                storage,
                now,
                now,
            ),
        )
        recipe_id = int(cur.lastrowid)
        order = 0
        conn.execute(
            """
            INSERT INTO recipe_media (recipe_id, media_type, filename, thumbnail_filename, sort_order, created_at)
            VALUES (?, 'audio', ?, NULL, ?, ?)
            """,
            (recipe_id, audio_filename, order, now),
        )
        order += 1
        if image_filename:
            conn.execute(
                """
                INSERT INTO recipe_media (recipe_id, media_type, filename, thumbnail_filename, sort_order, created_at)
                VALUES (?, 'image', ?, NULL, ?, ?)
                """,
                (recipe_id, image_filename, order, now),
            )
            order += 1
        if video_filename:
            conn.execute(
                """
                INSERT INTO recipe_media (recipe_id, media_type, filename, thumbnail_filename, sort_order, created_at)
                VALUES (?, 'video', ?, NULL, ?, ?)
                """,
                (recipe_id, video_filename, order, now),
            )
        return recipe_id


def _attach_media(conn: sqlite3.Connection, recipe_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM recipe_media WHERE recipe_id = ? ORDER BY sort_order, id",
        (recipe_id,),
    ).fetchall()
    return [db.row_to_dict(r) for r in rows]


def _enrich_recipe(conn: sqlite3.Connection, row: sqlite3.Row, viewer_id: Optional[int]) -> dict:
    r = db.row_to_dict(row)
    if not r:
        return {}
    rid = int(r["id"])
    r["ingredients"] = db.parse_json_field(r.get("ingredients_json"), [])
    r["method_steps"] = db.parse_json_field(r.get("method_steps_json"), [])
    r["tips"] = db.parse_json_field(r.get("tips_json"), [])
    r["tags"] = db.parse_json_field(r.get("tags_json"), [])
    r["unclear_items"] = db.parse_json_field(r.get("unclear_items_json"), [])
    r["alternate_names"] = db.parse_json_field(r.get("alternate_names_json"), [])
    r["media"] = _attach_media(conn, rid)
    lc = conn.execute("SELECT COUNT(*) AS c FROM likes WHERE recipe_id = ?", (rid,)).fetchone()
    r["like_count"] = int(lc["c"]) if lc else 0
    if viewer_id is not None:
        r["liked_by_me"] = db.recipe_has_like(conn, viewer_id, rid)
        r["saved_by_me"] = db.recipe_is_saved(conn, viewer_id, rid)
    else:
        r["liked_by_me"] = False
        r["saved_by_me"] = False
    return r


def get_recipe(recipe_id: int, viewer_id: Optional[int] = None) -> Optional[dict]:
    with db.get_db() as conn:
        row = conn.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
        if row is None:
            return None
        return _enrich_recipe(conn, row, viewer_id)


def get_recipes_by_creator(creator_id: int, viewer_id: Optional[int], include_drafts_for_owner: bool) -> list[dict]:
    owner_sees_all = bool(include_drafts_for_owner and viewer_id is not None and viewer_id == creator_id)
    with db.get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM recipes
            WHERE creator_id = ? AND (? OR status = 'published')
            ORDER BY CASE WHEN published_at IS NULL THEN 1 ELSE 0 END,
                     datetime(COALESCE(published_at, created_at)) DESC
            """,
            (creator_id, 1 if owner_sees_all else 0),
        ).fetchall()
        return [_enrich_recipe(conn, r, viewer_id) for r in rows]


def update_recipe(recipe_id: int, creator_id: int, fields: dict[str, Any]) -> None:
    now = db.utcnow()
    allowed = {
        "title",
        "caption",
        "story_note",
        "category",
        "cuisine",
        "visibility",
        "serves",
        "prep_time_minutes",
        "cook_time_minutes",
        "difficulty",
        "ingredients_json",
        "method_steps_json",
        "tips_json",
        "tags_json",
        "unclear_items_json",
        "serving_suggestion",
        "storage_notes",
        "status",
    }
    sets = []
    values: list[Any] = []
    for k, v in fields.items():
        if k not in allowed:
            continue
        sets.append(f"{k} = ?")
        values.append(v)
    if not sets:
        return
    sets.append("updated_at = ?")
    values.append(now)
    values.extend([recipe_id, creator_id])
    sql = f"UPDATE recipes SET {', '.join(sets)} WHERE id = ? AND creator_id = ?"
    with db.get_db() as conn:
        conn.execute(sql, tuple(values))


def publish_recipe(recipe_id: int, creator_id: int) -> bool:
    now = db.utcnow()
    with db.get_db() as conn:
        cur = conn.execute(
            """
            UPDATE recipes SET status = 'published', published_at = ?, updated_at = ?
            WHERE id = ? AND creator_id = ? AND status IN ('draft', 'needs_review')
            """,
            (now, now, recipe_id, creator_id),
        )
        return cur.rowcount > 0


def get_public_recipes(limit: int = 50, viewer_id: Optional[int] = None) -> list[dict]:
    with db.get_db() as conn:
        rows = conn.execute(
            """
            SELECT r.* FROM recipes r
            WHERE r.status = 'published' AND r.visibility = 'public'
            ORDER BY datetime(r.published_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [_enrich_recipe(conn, r, viewer_id) for r in rows]


def get_following_feed_recipes(user_id: int, limit: int = 50) -> list[dict]:
    with db.get_db() as conn:
        ids = db.get_following_ids(conn, user_id)
        if not ids:
            return get_public_recipes(limit=limit, viewer_id=user_id)
        placeholders = ",".join("?" * len(ids))
        params: list[Any] = [*ids, user_id, limit]
        rows = conn.execute(
            f"""
            SELECT r.* FROM recipes r
            WHERE r.status = 'published'
              AND (r.creator_id IN ({placeholders}) OR r.creator_id = ?)
            ORDER BY datetime(r.published_at) DESC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()
        return [_enrich_recipe(conn, r, user_id) for r in rows]


def toggle_like(user_id: int, recipe_id: int) -> bool:
    """Returns new liked state."""
    now = db.utcnow()
    with db.get_db() as conn:
        if db.recipe_has_like(conn, user_id, recipe_id):
            conn.execute("DELETE FROM likes WHERE user_id = ? AND recipe_id = ?", (user_id, recipe_id))
            return False
        conn.execute(
            "INSERT INTO likes (user_id, recipe_id, created_at) VALUES (?, ?, ?)",
            (user_id, recipe_id, now),
        )
        return True


def toggle_save(user_id: int, recipe_id: int) -> bool:
    now = db.utcnow()
    with db.get_db() as conn:
        if db.recipe_is_saved(conn, user_id, recipe_id):
            conn.execute("DELETE FROM saved_recipes WHERE user_id = ? AND recipe_id = ?", (user_id, recipe_id))
            return False
        conn.execute(
            "INSERT INTO saved_recipes (user_id, recipe_id, created_at) VALUES (?, ?, ?)",
            (user_id, recipe_id, now),
        )
        return True


def get_saved_recipes(user_id: int) -> list[dict]:
    with db.get_db() as conn:
        rows = conn.execute(
            """
            SELECT r.* FROM recipes r
            INNER JOIN saved_recipes s ON s.recipe_id = r.id
            WHERE s.user_id = ?
            ORDER BY datetime(s.created_at) DESC
            """,
            (user_id,),
        ).fetchall()
        return [_enrich_recipe(conn, r, user_id) for r in rows]
