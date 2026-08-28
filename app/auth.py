"""
GitHub OAuth sign-in for hosted mode.

Flow:
  /auth/login     -> redirect to GitHub with a signed, single-use `state`
  /auth/callback  -> verify state, consume nonce, swap code for a token,
                     upsert the user, set a signed session cookie
  /auth/logout    -> clear the cookie

The session cookie holds only the user id, signed (not encrypted) with
SECRET_KEY and time-limited — nothing secret lives in the browser, and a
tampered cookie fails signature verification.
"""

from __future__ import annotations

import logging
import secrets
import sqlite3
import threading
import time
from pathlib import Path
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

import config

log = logging.getLogger("dataforged.auth")
router = APIRouter()

_signer = URLSafeTimedSerializer(config.SECRET_KEY, salt="dataforged-session")
_state_signer = URLSafeTimedSerializer(config.SECRET_KEY, salt="dataforged-oauth-state")

GITHUB_AUTHORIZE = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN = "https://github.com/login/oauth/access_token"
GITHUB_USER = "https://api.github.com/user"

_FALLBACK_DB = Path(__file__).parent / "data" / "oauth_state.sqlite3"
_fallback_lock = threading.Lock()


def current_user_id(request: Request) -> int | None:
    """User id from the session cookie, or None. Never raises on bad input."""
    raw = request.cookies.get(config.SESSION_COOKIE)
    if not raw:
        return None
    try:
        data = _signer.loads(raw, max_age=config.SESSION_MAX_AGE)
        return int(data["uid"])
    except (BadSignature, SignatureExpired, KeyError, ValueError, TypeError):
        return None


def _set_session(response: RedirectResponse, user_id: int) -> None:
    response.set_cookie(
        config.SESSION_COOKIE,
        _signer.dumps({"uid": int(user_id)}),
        max_age=config.SESSION_MAX_AGE,
        httponly=True,
        secure=config.COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def _consume_nonce_fallback(nonce: str) -> bool:
    """SQLite fallback when Postgres is unavailable."""
    _FALLBACK_DB.parent.mkdir(parents=True, exist_ok=True)
    with _fallback_lock:
        conn = sqlite3.connect(_FALLBACK_DB, timeout=5)
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS oauth_consumed "
                "(nonce TEXT PRIMARY KEY, consumed_at REAL NOT NULL)"
            )
            cur = conn.execute(
                "INSERT OR IGNORE INTO oauth_consumed (nonce, consumed_at) VALUES (?, ?)",
                (nonce, time.time()),
            )
            inserted = cur.rowcount == 1
            conn.execute(
                "DELETE FROM oauth_consumed WHERE consumed_at < ?",
                (time.time() - 86400,),
            )
            conn.commit()
            return inserted
        finally:
            conn.close()


def _consume_oauth_nonce(request: Request, nonce: str) -> bool:
    store = request.app.state.store
    if store is not None and hasattr(store, "consume_oauth_nonce"):
        return store.consume_oauth_nonce(nonce)
    return _consume_nonce_fallback(nonce)


@router.get("/auth/login")
def login(request: Request, next: str = "/") -> RedirectResponse:
    if not config.AUTH_ENABLED:
        raise HTTPException(503, "sign-in is not configured on this deployment")
    nonce = secrets.token_urlsafe(16)
    state = _state_signer.dumps(
        {"n": nonce, "next": next if next.startswith("/") else "/"}
    )
    params = {
        "client_id": config.GITHUB_CLIENT_ID,
        "redirect_uri": f"{config.BASE_URL}/auth/callback",
        "scope": "read:user",
        "state": state,
        "allow_signup": "true",
    }
    return RedirectResponse(f"{GITHUB_AUTHORIZE}?{urlencode(params)}", status_code=307)


@router.get("/auth/callback")
def callback(request: Request, code: str = "", state: str = "") -> RedirectResponse:
    if not config.AUTH_ENABLED:
        raise HTTPException(503, "sign-in is not configured on this deployment")
    if not code:
        raise HTTPException(400, "missing code")
    try:
        payload = _state_signer.loads(state, max_age=600)
    except (BadSignature, SignatureExpired):
        raise HTTPException(400, "invalid or expired state — start sign-in again")

    nonce = payload.get("n")
    if not nonce or not _consume_oauth_nonce(request, str(nonce)):
        log.warning("oauth state replay rejected")
        raise HTTPException(400, "state already used — start sign-in again")

    with httpx.Client(timeout=10) as client:
        token_resp = client.post(
            GITHUB_TOKEN,
            headers={"Accept": "application/json"},
            data={
                "client_id": config.GITHUB_CLIENT_ID,
                "client_secret": config.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": f"{config.BASE_URL}/auth/callback",
            },
        )
        token = token_resp.json().get("access_token")
        if not token:
            log.warning("oauth token exchange failed status=%s", token_resp.status_code)
            raise HTTPException(400, "GitHub did not return an access token")

        profile = client.get(
            GITHUB_USER,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        ).json()

    if "id" not in profile:
        log.warning("oauth profile missing id")
        raise HTTPException(400, "could not read the GitHub profile")

    store = request.app.state.store
    if store is None:
        raise HTTPException(503, "no database configured — cannot create accounts")
    user = store.upsert_user(
        github_id=profile["id"],
        login=profile.get("login", "unknown"),
        name=profile.get("name"),
        avatar_url=profile.get("avatar_url"),
    )
    log.info("user signed in login=%s", user.get("login"))

    response = RedirectResponse(payload.get("next", "/"), status_code=303)
    _set_session(response, user["id"])
    return response


@router.get("/auth/logout")
@router.post("/auth/logout")
def logout() -> RedirectResponse:
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(config.SESSION_COOKIE, path="/")
    return response
