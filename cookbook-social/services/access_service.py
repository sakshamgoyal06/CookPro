"""Premium and recipe visibility rules."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from models import database as db


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def is_subscribed_to_creator(subscriber_id: int, creator_id: int) -> bool:
    if subscriber_id == creator_id:
        return True
    now = datetime.now(timezone.utc)
    with db.get_db() as conn:
        row = conn.execute(
            """
            SELECT status, expires_at FROM creator_subscriptions
            WHERE subscriber_id = ? AND creator_id = ?
            """,
            (subscriber_id, creator_id),
        ).fetchone()
        if row is None or row["status"] != "active":
            return False
        exp = _parse_dt(row["expires_at"])
        if exp is not None and exp < now:
            return False
        return True


def can_view_recipe(viewer: Optional[dict], recipe: dict) -> str:
    """
    Returns:
      'full' — complete recipe content
      'locked' — premium teaser only (published premium, no access)
      'hidden' — treat as not found / unauthorized
    """
    status = recipe.get("status") or "draft"
    creator_id = int(recipe["creator_id"])
    visibility = recipe.get("visibility") or "public"

    viewer_id = int(viewer["id"]) if viewer else None

    if status in ("draft", "needs_review"):
        if viewer_id is None or viewer_id != creator_id:
            return "hidden"
        return "full"

    if status != "published":
        return "hidden"

    if visibility == "public":
        return "full"

    if visibility == "premium":
        if viewer_id is None:
            return "locked"
        if viewer_id == creator_id:
            return "full"
        if is_subscribed_to_creator(viewer_id, creator_id):
            return "full"
        return "locked"

    return "full"
