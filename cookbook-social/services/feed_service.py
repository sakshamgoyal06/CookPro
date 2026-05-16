"""Feed assembly with per-recipe access hints."""

from __future__ import annotations

from typing import Any

from services import access_service, auth_service, recipe_service


def get_feed_for_user(viewer: dict[str, Any]) -> list[dict[str, Any]]:
    recipes = recipe_service.get_following_feed_recipes(int(viewer["id"]))
    out: list[dict[str, Any]] = []
    for r in recipes:
        creator = auth_service.get_user_by_id(int(r["creator_id"]))
        item = dict(r)
        if creator:
            item["creator"] = {
                "id": creator["id"],
                "username": creator["username"],
                "display_name": creator["display_name"],
                "profile_photo_filename": creator.get("profile_photo_filename"),
            }
        else:
            item["creator"] = None
        item["access_level"] = access_service.can_view_recipe(viewer, r)
        out.append(item)
    return out
