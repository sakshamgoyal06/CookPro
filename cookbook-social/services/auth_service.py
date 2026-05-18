"""Authentication helpers."""

from __future__ import annotations

import re
from typing import Optional

from werkzeug.security import check_password_hash, generate_password_hash

from models import database as db


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def create_user(
    username: str,
    email: str,
    password: str,
    display_name: str,
    is_creator: bool = False,
) -> int:
    now = db.utcnow()
    uname = _normalize_username(username)
    if not re.match(r"^[a-z0-9_]{3,32}$", uname):
        raise ValueError("Username must be 3–32 characters: lowercase letters, numbers, underscore.")
    ph = generate_password_hash(password)
    with db.get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO users (
                username, email, password_hash, display_name, bio,
                profile_photo_filename, is_creator, created_at, updated_at
            ) VALUES (?, ?, ?, ?, '', NULL, ?, ?, ?)
            """,
            (uname, email.strip().lower(), ph, display_name.strip(), 1 if is_creator else 0, now, now),
        )
        return int(cur.lastrowid)


def get_user_by_id(user_id: int) -> Optional[dict]:
    with db.get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return db.row_to_dict(row)


def get_user_by_email(email: str) -> Optional[dict]:
    with db.get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
        return db.row_to_dict(row)


def get_user_by_username(username: str) -> Optional[dict]:
    uname = _normalize_username(username)
    with db.get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (uname,)).fetchone()
        return db.row_to_dict(row)


def verify_password(user: dict, password: str) -> bool:
    return check_password_hash(user["password_hash"], password)


def update_profile(
    user_id: int,
    display_name: str,
    bio: str,
    profile_photo_filename: Optional[str] = None,
) -> None:
    now = db.utcnow()
    with db.get_db() as conn:
        if profile_photo_filename is not None:
            conn.execute(
                """
                UPDATE users SET display_name = ?, bio = ?, profile_photo_filename = ?, updated_at = ?
                WHERE id = ?
                """,
                (display_name.strip(), bio or "", profile_photo_filename, now, user_id),
            )
        else:
            conn.execute(
                """
                UPDATE users SET display_name = ?, bio = ?, updated_at = ?
                WHERE id = ?
                """,
                (display_name.strip(), bio or "", now, user_id),
            )


def set_creator_flag(user_id: int, is_creator: bool) -> None:
    now = db.utcnow()
    with db.get_db() as conn:
        conn.execute(
            "UPDATE users SET is_creator = ?, updated_at = ? WHERE id = ?",
            (1 if is_creator else 0, now, user_id),
        )
