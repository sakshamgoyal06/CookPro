"""Cookbook Social — Flask application entrypoint."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from typing import Any, Optional

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

import config  # noqa: E402
from models import database as db  # noqa: E402
from services import (  # noqa: E402
    access_service,
    auth_service,
    feed_service,
    media_service,
    recipe_service,
)
from services.anthropic_service import AnthropicServiceError  # noqa: E402
from services.openai_service import OpenAIServiceError  # noqa: E402

config.ensure_directories()

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

login_manager = LoginManager(app)
login_manager.login_view = "login"


@app.context_processor
def template_helpers():
    def media_url(media_type: str, filename: str | None):
        return media_service.media_url(media_type, filename)

    def profile_photo_url(user: dict | None):
        if not user:
            return None
        fn = user.get("profile_photo_filename")
        return f"/files/images/{fn}" if fn else None

    return dict(media_url=media_url, profile_photo_url=profile_photo_url)


class WebUser(UserMixin):
    def __init__(self, row: dict[str, Any]):
        self._row = row

    def get_id(self) -> str:
        return str(self._row["id"])

    @property
    def raw(self) -> dict[str, Any]:
        return self._row

    @property
    def id(self) -> int:  # type: ignore[override]
        return int(self._row["id"])

    @property
    def username(self) -> str:
        return self._row["username"]

    @property
    def display_name(self) -> str:
        return self._row["display_name"]

    @property
    def is_creator(self) -> bool:
        return bool(self._row.get("is_creator"))


@login_manager.user_loader
def load_user(user_id: str) -> Optional[WebUser]:
    row = auth_service.get_user_by_id(int(user_id))
    return WebUser(row) if row else None


@app.route("/files/<folder>/<path:filename>")
def serve_upload(folder: str, filename: str):
    safe = secure_filename(os.path.basename(filename))
    if not safe or safe != os.path.basename(filename):
        abort(404)
    mapping = {
        "images": config.IMAGES_DIR,
        "videos": config.VIDEOS_DIR,
        "audio": config.AUDIO_DIR,
    }
    if folder not in mapping:
        abort(404)
    directory = mapping[folder]
    path = directory / safe
    if not path.is_file():
        abort(404)
    return send_from_directory(directory, safe)


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("feed"))
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("feed"))
    if request.method == "POST":
        username = request.form.get("username", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        display_name = request.form.get("display_name", username)
        is_creator = request.form.get("is_creator") == "on"
        try:
            uid = auth_service.create_user(username, email, password, display_name, is_creator=is_creator)
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("signup.html"), 400
        except sqlite3.IntegrityError:
            flash("That username or email is already registered.", "error")
            return render_template("signup.html"), 400
        user = auth_service.get_user_by_id(uid)
        if user:
            login_user(WebUser(user))
        flash("Welcome to Cookbook Social.", "success")
        return redirect(url_for("feed"))
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("feed"))
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        user = auth_service.get_user_by_email(email)
        if not user or not auth_service.verify_password(user, password):
            flash("Invalid email or password.", "error")
            return render_template("login.html"), 401
        login_user(WebUser(user))
        return redirect(request.args.get("next") or url_for("feed"))
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/feed")
@login_required
def feed():
    items = feed_service.get_feed_for_user(current_user.raw)
    return render_template("feed.html", items=items)


@app.route("/saved")
@login_required
def saved_recipes():
    recipes = recipe_service.get_saved_recipes(current_user.id)
    decorated = []
    for r in recipes:
        lvl = access_service.can_view_recipe(current_user.raw, r)
        creator = auth_service.get_user_by_id(int(r["creator_id"]))
        cdict = None
        if creator:
            cdict = {
                "id": creator["id"],
                "username": creator["username"],
                "display_name": creator["display_name"],
                "profile_photo_filename": creator.get("profile_photo_filename"),
            }
        decorated.append({**r, "access_level": lvl, "creator": cdict})
    return render_template("saved_recipes.html", recipes=decorated)


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        display_name = request.form.get("display_name", "")
        bio = request.form.get("bio", "")
        is_creator = request.form.get("is_creator") == "on"
        photo = request.files.get("profile_photo")
        photo_name = None
        if photo and photo.filename:
            try:
                photo_name = media_service.save_uploaded_file(photo, "image")
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template("edit_profile.html", user=current_user.raw), 400
        if photo_name:
            auth_service.update_profile(current_user.id, display_name, bio, profile_photo_filename=photo_name)
        else:
            auth_service.update_profile(current_user.id, display_name, bio)
        auth_service.set_creator_flag(current_user.id, is_creator)
        flash("Profile updated.", "success")
        return redirect(url_for("profile", username=current_user.username))
    return render_template("edit_profile.html", user=current_user.raw)


@app.route("/u/<username>")
def profile(username: str):
    target = auth_service.get_user_by_username(username)
    if not target:
        flash("User not found.", "error")
        return redirect(url_for("index"))
    viewer = current_user.raw if current_user.is_authenticated else None
    viewer_id = viewer["id"] if viewer else None
    is_self = bool(viewer and viewer["id"] == target["id"])
    recipes = recipe_service.get_recipes_by_creator(
        int(target["id"]),
        viewer_id,
        include_drafts_for_owner=is_self,
    )
    following = False
    subscribed = False
    if viewer and not is_self:
        with db.get_db() as conn:
            following = db.user_is_following(conn, int(viewer["id"]), int(target["id"]))
        subscribed = access_service.is_subscribed_to_creator(int(viewer["id"]), int(target["id"]))
    return render_template(
        "profile.html",
        target=target,
        recipes=recipes,
        is_self=is_self,
        following=following,
        subscribed=subscribed,
        viewer=viewer,
    )


@app.route("/u/<username>/follow", methods=["POST"])
@login_required
def follow_user(username: str):
    target = auth_service.get_user_by_username(username)
    if not target or target["id"] == current_user.id:
        flash("Cannot follow that user.", "error")
        return redirect(url_for("index"))
    now = db.utcnow()
    try:
        with db.get_db() as conn:
            conn.execute(
                """
                INSERT INTO follows (follower_id, following_id, created_at)
                VALUES (?, ?, ?)
                """,
                (current_user.id, int(target["id"]), now),
            )
    except sqlite3.IntegrityError:
        flash("Already following.", "info")
    else:
        flash("You are now following this cook.", "success")
    return redirect(url_for("profile", username=target["username"]))


@app.route("/u/<username>/unfollow", methods=["POST"])
@login_required
def unfollow_user(username: str):
    target = auth_service.get_user_by_username(username)
    if not target:
        flash("User not found.", "error")
        return redirect(url_for("index"))
    with db.get_db() as conn:
        conn.execute(
            "DELETE FROM follows WHERE follower_id = ? AND following_id = ?",
            (current_user.id, int(target["id"])),
        )
    flash("Unfollowed.", "success")
    return redirect(url_for("profile", username=target["username"]))


@app.route("/u/<username>/subscribe", methods=["POST"])
@login_required
def subscribe_creator(username: str):
    target = auth_service.get_user_by_username(username)
    if not target or not target.get("is_creator"):
        flash("Subscriptions are only available for creators.", "error")
        return redirect(url_for("index"))
    if target["id"] == current_user.id:
        flash("You cannot subscribe to yourself.", "error")
        return redirect(url_for("profile", username=username))
    now = db.utcnow()
    with db.get_db() as conn:
        row = conn.execute(
            """
            SELECT id FROM creator_subscriptions WHERE subscriber_id = ? AND creator_id = ?
            """,
            (current_user.id, int(target["id"])),
        ).fetchone()
        if row:
            conn.execute(
                """
                UPDATE creator_subscriptions
                SET status = 'active', started_at = ?, expires_at = NULL, created_at = ?
                WHERE id = ?
                """,
                (now, now, int(row["id"])),
            )
        else:
            conn.execute(
                """
                INSERT INTO creator_subscriptions (subscriber_id, creator_id, status, started_at, expires_at, created_at)
                VALUES (?, ?, 'active', ?, NULL, ?)
                """,
                (current_user.id, int(target["id"]), now, now),
            )
    flash("Simulated subscription activated. Premium recipes are unlocked.", "success")
    return redirect(url_for("profile", username=target["username"]))


@app.route("/u/<username>/unsubscribe", methods=["POST"])
@login_required
def unsubscribe_creator(username: str):
    target = auth_service.get_user_by_username(username)
    if not target:
        flash("User not found.", "error")
        return redirect(url_for("index"))
    with db.get_db() as conn:
        conn.execute(
            "DELETE FROM creator_subscriptions WHERE subscriber_id = ? AND creator_id = ?",
            (current_user.id, int(target["id"])),
        )
    flash("Subscription removed (simulated).", "success")
    return redirect(url_for("profile", username=target["username"]))


@app.route("/recipes/upload", methods=["GET", "POST"])
@login_required
def upload_recipe():
    if request.method == "POST":
        audio = request.files.get("audio")
        if not audio or not audio.filename:
            flash("A voice note audio file is required.", "error")
            return render_template("upload_recipe.html"), 400
        image = request.files.get("photo")
        video = request.files.get("video")
        caption = request.form.get("caption", "")
        visibility = request.form.get("visibility", "public")
        if visibility not in ("public", "premium"):
            visibility = "public"
        category = request.form.get("category", "")
        cuisine = request.form.get("cuisine", "")
        try:
            audio_name = media_service.save_uploaded_file(audio, "audio")
            image_name = None
            video_name = None
            if image and image.filename:
                image_name = media_service.save_uploaded_file(image, "image")
            if video and video.filename:
                video_name = media_service.save_uploaded_file(video, "video")
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("upload_recipe.html"), 400
        audio_path = str(config.AUDIO_DIR / audio_name)
        try:
            from services import anthropic_service, openai_service

            transcript = openai_service.transcribe_audio(audio_path)
            if not transcript.strip():
                flash("We could not detect speech in that recording. Try a clearer voice note.", "error")
                return render_template("upload_recipe.html"), 400
            structured = anthropic_service.structure_recipe(transcript)
        except (OpenAIServiceError, AnthropicServiceError) as exc:
            flash(str(exc), "error")
            return render_template("upload_recipe.html"), 502
        rid = recipe_service.create_recipe_from_upload(
            current_user.id,
            structured,
            transcript,
            visibility,
            caption,
            category,
            cuisine,
            audio_name,
            image_name,
            video_name,
        )
        flash("Recipe drafted from your voice note. Review before publishing.", "success")
        return redirect(url_for("recipe_review", recipe_id=rid))
    return render_template("upload_recipe.html")


@app.route("/recipes/<int:recipe_id>/review")
@login_required
def recipe_review(recipe_id: int):
    recipe = recipe_service.get_recipe(recipe_id, current_user.id)
    if not recipe or int(recipe["creator_id"]) != current_user.id:
        flash("You cannot review that recipe.", "error")
        return redirect(url_for("feed")), 403
    if recipe["status"] not in ("draft", "needs_review"):
        return redirect(url_for("recipe_detail", recipe_id=recipe_id))
    return render_template("recipe_review.html", recipe=recipe)


@app.route("/recipes/<int:recipe_id>/edit", methods=["GET", "POST"])
@login_required
def recipe_edit(recipe_id: int):
    recipe = recipe_service.get_recipe(recipe_id, current_user.id)
    if not recipe or int(recipe["creator_id"]) != current_user.id:
        flash("You cannot edit that recipe.", "error")
        return redirect(url_for("feed")), 403
    if request.method == "POST":
        try:
            ingredients_json = request.form.get("ingredients_json", "[]")
            method_json = request.form.get("method_steps_json", "[]")
            tips_json = request.form.get("tips_json", "[]")
            tags_json = request.form.get("tags_json", "[]")
            unclear_json = request.form.get("unclear_items_json", "[]")
            json.loads(ingredients_json)
            json.loads(method_json)
            json.loads(tips_json)
            json.loads(tags_json)
            json.loads(unclear_json)
        except json.JSONDecodeError:
            flash("JSON fields must contain valid JSON arrays.", "error")
            return render_template("recipe_edit.html", recipe=recipe), 400
        prep = request.form.get("prep_time_minutes") or None
        cook = request.form.get("cook_time_minutes") or None
        try:
            prep_val = int(prep) if prep else None
            cook_val = int(cook) if cook else None
        except ValueError:
            flash("Prep and cook times must be whole numbers.", "error")
            return render_template("recipe_edit.html", recipe=recipe), 400
        fields = {
            "title": request.form.get("title", recipe["title"]),
            "caption": request.form.get("caption", ""),
            "story_note": request.form.get("story_note", ""),
            "category": request.form.get("category", ""),
            "cuisine": request.form.get("cuisine", ""),
            "visibility": request.form.get("visibility", recipe["visibility"]),
            "serves": request.form.get("serves", ""),
            "prep_time_minutes": prep_val,
            "cook_time_minutes": cook_val,
            "difficulty": request.form.get("difficulty", ""),
            "ingredients_json": ingredients_json,
            "method_steps_json": method_json,
            "tips_json": tips_json,
            "tags_json": tags_json,
            "unclear_items_json": unclear_json,
            "serving_suggestion": request.form.get("serving_suggestion", ""),
            "storage_notes": request.form.get("storage_notes", ""),
        }
        if fields["visibility"] not in ("public", "premium"):
            fields["visibility"] = recipe["visibility"]
        recipe_service.update_recipe(recipe_id, current_user.id, fields)
        flash("Recipe updated.", "success")
        return redirect(url_for("recipe_review", recipe_id=recipe_id))
    return render_template("recipe_edit.html", recipe=recipe)


@app.route("/recipes/<int:recipe_id>/publish", methods=["POST"])
@login_required
def recipe_publish(recipe_id: int):
    ok = recipe_service.publish_recipe(recipe_id, current_user.id)
    if not ok:
        flash("Unable to publish. Check that you own the recipe and it is still a draft.", "error")
        return redirect(url_for("recipe_review", recipe_id=recipe_id)), 400
    flash("Recipe published.", "success")
    return redirect(url_for("recipe_detail", recipe_id=recipe_id))


@app.route("/recipes/<int:recipe_id>/draft", methods=["POST"])
@login_required
def recipe_mark_draft(recipe_id: int):
    recipe = recipe_service.get_recipe(recipe_id, current_user.id)
    if not recipe or int(recipe["creator_id"]) != current_user.id:
        flash("Unauthorized.", "error")
        return redirect(url_for("feed")), 403
    recipe_service.update_recipe(recipe_id, current_user.id, {"status": "draft"})
    flash("Kept as draft.", "success")
    return redirect(url_for("recipe_edit", recipe_id=recipe_id))


@app.route("/recipes/<int:recipe_id>")
@login_required
def recipe_detail(recipe_id: int):
    recipe = recipe_service.get_recipe(recipe_id, current_user.id)
    if not recipe:
        flash("Recipe not found.", "error")
        return redirect(url_for("feed")), 404
    level = access_service.can_view_recipe(current_user.raw, recipe)
    if level == "hidden":
        flash("That recipe is not available.", "error")
        return redirect(url_for("feed")), 404
    creator = auth_service.get_user_by_id(int(recipe["creator_id"]))
    return render_template("recipe_detail.html", recipe=recipe, access_level=level, creator=creator)


@app.route("/recipes/<int:recipe_id>/like", methods=["POST"])
@login_required
def recipe_like(recipe_id: int):
    recipe = recipe_service.get_recipe(recipe_id, current_user.id)
    if not recipe:
        abort(404)
    recipe_service.toggle_like(current_user.id, recipe_id)
    return redirect(request.referrer or url_for("feed"))


@app.route("/recipes/<int:recipe_id>/save", methods=["POST"])
@login_required
def recipe_save(recipe_id: int):
    recipe = recipe_service.get_recipe(recipe_id, current_user.id)
    if not recipe:
        abort(404)
    recipe_service.toggle_save(current_user.id, recipe_id)
    return redirect(request.referrer or url_for("feed"))


@app.route("/collections")
@login_required
def collections_list():
    with db.get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM collections WHERE creator_id = ?
            ORDER BY datetime(updated_at) DESC
            """,
            (current_user.id,),
        ).fetchall()
        items = [db.row_to_dict(r) for r in rows]
    return render_template("collections.html", collections=items, create_mode=False)


@app.route("/collections/create", methods=["GET", "POST"])
@login_required
def collections_create():
    if request.method == "POST":
        title = request.form.get("title", "").strip() or "Untitled collection"
        description = request.form.get("description", "")
        visibility = request.form.get("visibility", "public")
        if visibility not in ("public", "premium"):
            visibility = "public"
        now = db.utcnow()
        with db.get_db() as conn:
            cur = conn.execute(
                """
                INSERT INTO collections (creator_id, title, description, visibility, cover_image_filename, created_at, updated_at)
                VALUES (?, ?, ?, ?, NULL, ?, ?)
                """,
                (current_user.id, title, description, visibility, now, now),
            )
            cid = int(cur.lastrowid)
        flash("Collection created.", "success")
        return redirect(url_for("collection_detail", collection_id=cid))
    return render_template("collections.html", collections=[], create_mode=True)


@app.route("/collections/<int:collection_id>", methods=["GET", "POST"])
@login_required
def collection_detail(collection_id: int):
    with db.get_db() as conn:
        col = conn.execute(
            "SELECT * FROM collections WHERE id = ? AND creator_id = ?",
            (collection_id, current_user.id),
        ).fetchone()
        if not col:
            flash("Collection not found.", "error")
            return redirect(url_for("collections_list")), 404
        collection = db.row_to_dict(col)
        if request.method == "POST":
            recipe_id = int(request.form.get("recipe_id", "0"))
            rec = conn.execute(
                "SELECT id, creator_id FROM recipes WHERE id = ?",
                (recipe_id,),
            ).fetchone()
            if not rec or int(rec["creator_id"]) != current_user.id:
                flash("You can only add your own recipes.", "error")
            else:
                try:
                    max_sort = conn.execute(
                        "SELECT COALESCE(MAX(sort_order), -1) AS m FROM collection_recipes WHERE collection_id = ?",
                        (collection_id,),
                    ).fetchone()
                    nxt = int(max_sort["m"]) + 1 if max_sort else 0
                    conn.execute(
                        """
                        INSERT INTO collection_recipes (collection_id, recipe_id, sort_order, created_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (collection_id, recipe_id, nxt, db.utcnow()),
                    )
                    conn.execute(
                        "UPDATE collections SET updated_at = ? WHERE id = ?",
                        (db.utcnow(), collection_id),
                    )
                    flash("Recipe added to collection.", "success")
                except sqlite3.IntegrityError:
                    flash("That recipe is already in this collection.", "info")
            return redirect(url_for("collection_detail", collection_id=collection_id))
        rows = conn.execute(
            """
            SELECT r.*, cr.sort_order
            FROM collection_recipes cr
            INNER JOIN recipes r ON r.id = cr.recipe_id
            WHERE cr.collection_id = ?
            ORDER BY cr.sort_order, cr.id
            """,
            (collection_id,),
        ).fetchall()
        recipes = [x for x in (recipe_service.get_recipe(int(r["id"]), current_user.id) for r in rows) if x]
        own = conn.execute(
            "SELECT id, title, status FROM recipes WHERE creator_id = ? ORDER BY datetime(created_at) DESC LIMIT 100",
            (current_user.id,),
        ).fetchall()
        own_recipes = [dict(r) for r in own]
    return render_template(
        "collection_detail.html",
        collection=collection,
        recipes=recipes,
        own_recipes=own_recipes,
    )


@app.route("/cookbook/themes")
@login_required
def cookbook_themes():
    with db.get_db() as conn:
        rows = conn.execute("SELECT * FROM cookbook_themes ORDER BY id").fetchall()
        themes = [db.row_to_dict(r) for r in rows]
    return render_template("cookbook_themes.html", themes=themes)


def _startup():
    db.init_db()
    db.seed_cookbook_themes_if_empty()


if __name__ == "__main__":
    _startup()
    app.run(host="127.0.0.1", port=5000, debug=True)
