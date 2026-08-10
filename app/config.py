"""
Runtime configuration — one switch decides how PyForge behaves.

PYFORGE_MODE=local  (default)
    Your own machine. Exercises execute server-side in a sandboxed subprocess,
    there is no login, and progress lives in a JSON file. This is the mode the
    docker-compose stack uses.

PYFORGE_MODE=hosted
    Public deployment. The server NEVER executes learner code — exercises run
    in the visitor's browser via Pyodide. Sign-in is GitHub OAuth and progress
    is stored per user in Postgres. Anonymous visitors get the full curriculum
    with progress kept in their browser's local storage (unless
    ALLOW_ANONYMOUS=false).
"""

from __future__ import annotations

import os
import secrets


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


MODE = os.environ.get("PYFORGE_MODE", "local").strip().lower()
HOSTED = MODE == "hosted"

# --- hosted-only settings -------------------------------------------------
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
AUTH_ENABLED = bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)

SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32)
SECRET_KEY_PROVIDED = bool(os.environ.get("SECRET_KEY"))

DATABASE_URL = os.environ.get("DATABASE_URL", "")

SESSION_COOKIE = "pyforge_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30          # 30 days
COOKIE_SECURE = _bool("COOKIE_SECURE", BASE_URL.startswith("https://"))

# Anonymous visitors can browse and run everything; only cross-device progress
# needs an account. Set ALLOW_ANONYMOUS=false to require sign-in for the API/UI.
ALLOW_ANONYMOUS = _bool("ALLOW_ANONYMOUS", True)

# Hosted progress is browser-verified (honor system). Certificates/leaderboards
# must not rely on these checkmarks without an independent proctoring layer.
PROGRESS_HONOR_SYSTEM = True

RATE_LIMIT_WRITES_PER_MINUTE = int(os.environ.get("RATE_LIMIT_WRITES_PER_MINUTE", "120"))
RATE_LIMIT_DB = os.environ.get("RATE_LIMIT_DB", "")

# When true (typical behind Caddy), trust X-Forwarded-For / X-Real-IP for the
# client address used by the rate limiter.
TRUST_PROXY = _bool("TRUST_PROXY", HOSTED)

PYODIDE_INDEX_URL = os.environ.get(
    "PYODIDE_INDEX_URL", "https://cdn.jsdelivr.net/pyodide/v0.28.3/full/"
)

# Curriculum list responses are identical for anonymous users; cache briefly.
CURRICULUM_CACHE_SECONDS = int(os.environ.get("CURRICULUM_CACHE_SECONDS", "60"))


def startup_warnings() -> list[str]:
    """Problems worth shouting about at boot rather than discovering later."""
    warns: list[str] = []
    if HOSTED:
        if not DATABASE_URL:
            warns.append(
                "DATABASE_URL is not set — progress cannot be saved for signed-in users."
            )
        if not AUTH_ENABLED:
            warns.append(
                "GITHUB_CLIENT_ID/SECRET not set — sign-in is disabled, "
                "visitors keep progress in their browser only."
            )
            if not ALLOW_ANONYMOUS:
                warns.append(
                    "ALLOW_ANONYMOUS=false but sign-in is not configured — "
                    "the site will reject every request."
                )
        if not SECRET_KEY_PROVIDED:
            warns.append(
                "SECRET_KEY not set — a random one was generated, so every "
                "restart signs everybody out."
            )
        if not COOKIE_SECURE and BASE_URL.startswith("https://"):
            warns.append(
                "COOKIE_SECURE is off while BASE_URL is https — cookies will "
                "be sent over plain HTTP too."
            )
    return warns
