# Cookbook Social

Cookbook Social is a small, production-minded MVP for a cooking-focused social network. Creators record a mandatory voice note when uploading a recipe. The audio is transcribed with OpenAI speech-to-text, then structured into a polished recipe JSON with a dedicated prompt. Other cooks can follow each other, browse a feed, save dishes, curate collections, and simulate premium subscriptions to unlock subscriber-only recipes.

## Features

- Email/username authentication with Flask-Login and Werkzeug password hashing.
- Rich profiles with optional profile photo, bio, and creator flag.
- Follow graph with a feed that prefers followed creators, falling back to global public recipes when you follow nobody.
- Voice-first recipe upload with optional photo/video, visibility (public/premium), and AI-assisted structuring.
- Review, edit, publish, and draft flows with guarded access.
- Likes and saves with simple toggles.
- Collections for organizing your own recipes.
- Simulated creator subscriptions for premium access (no payments in this MVP).
- Cookbook theme seeds and a themes gallery page as a foundation for future PDF/print export.

## Tech stack

- Python 3 and Flask with server-rendered HTML templates.
- SQLite via lightweight SQL helpers (easy to swap for PostgreSQL later by changing connection code and SQL dialect where needed).
- Flask-Login for sessions.
- OpenAI APIs for transcription and JSON recipe structuring.
- Local disk storage under `uploads/` and `outputs/` for MVP media.

## Setup

```bash
cd cookbook-social
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set at least:

- `SECRET_KEY` — random string for signing session cookies.
- `OPENAI_API_KEY` — required for transcription and structuring during upload.

Optional:

- `OPENAI_TRANSCRIBE_MODEL` (defaults to `gpt-4o-transcribe`).
- `OPENAI_RECIPE_MODEL` (defaults to `gpt-4.1`).
- `DATABASE_PATH` — override SQLite file location.

## Run the app

```bash
cd cookbook-social
python3 app.py
```

Then open `http://127.0.0.1:5000` in your browser.

On startup the app ensures upload directories exist, initializes the SQLite schema if needed, and seeds placeholder cookbook themes when the table is empty.

## Suggested end-to-end test flow

1. Sign up as a new user and mark yourself as a creator.
2. Upload a short voice note describing a simple dish, plus optional photo fields.
3. Review the AI draft on the review screen, tweak details on the edit page if needed.
4. Publish the recipe.
5. Sign up as a second user, follow the first creator, and confirm the recipe appears on `/feed`.
6. Save the recipe from the feed or detail page and confirm it appears under `/saved`.
7. As the second user, open the creator profile and use the simulated subscribe button, then confirm premium recipes unlock accordingly.

## Roadmap ideas

- Real payments and entitlements for premium recipes.
- Twilio or WhatsApp ingestion for voice notes captured off-web.
- Native mobile clients and push notifications.
- Comments, mentions, and richer notifications.
- Recommendation and ranking experiments tuned for home cooking.
- Full cookbook PDF layout engine using the `cookbook_themes` metadata.
- Physical print partner integrations and fulfillment APIs.
- Creator payouts, analytics, and moderation tooling.

## Project layout

See the repository tree under `cookbook-social/` for `app.py`, `config.py`, `models/`, `services/`, `templates/`, `static/`, `prompts/`, and media folders.
