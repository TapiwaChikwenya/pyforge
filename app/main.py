"""
PyForge — project-based Python → data engineering → AI learning app.

Two modes, one codebase (see config.py):

  local  : exercises execute server-side in a sandboxed subprocess, single
           learner, JSON progress file. Used by the docker-compose stack.
  hosted : the server NEVER executes learner code — exercises run in the
           visitor's browser via Pyodide. GitHub sign-in, per-user progress in
           Postgres, anonymous visitors welcome (progress in local storage)
           unless ALLOW_ANONYMOUS=false.

API
  GET  /api/curriculum            projects + stages + progress + mode/user
  GET  /api/project/{pid}         one project with exercises and interview Q&A
  GET  /api/me                    current user (hosted)
  POST /api/progress/exercise     record a pass (hosted: signed-in only; honor system)
  POST /api/milestone             toggle a milestone
  POST /api/progress/merge        fold anonymous progress into an account
  POST /api/run                   LOCAL MODE ONLY — sandboxed execution
  POST /api/lint                  LOCAL MODE ONLY — pyflakes (browser lints itself)
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import config
from curriculum import PROJECTS, PROJECTS_BY_ID, STAGE_LAYOUT
from progress_keys import KNOWN_EXERCISE_IDS, sanitize_progress
from ratelimit import RateLimiter, client_ip
from store import PostgresStore, build_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] req=%(request_id)s %(message)s",
)
# Default filter so non-request log records still format cleanly.
class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


logging.getLogger().addFilter(_RequestIdFilter())
log = logging.getLogger("pyforge")

app = FastAPI(title="PyForge", docs_url="/api/docs")
app.state.store = build_store()
app.state.limiter = RateLimiter()

for _w in config.startup_warnings():
    log.warning("%s", _w)
log.info(
    "mode=%s auth=%s store=%s",
    config.MODE,
    "on" if (config.HOSTED and config.AUTH_ENABLED) else "off",
    type(app.state.store).__name__ if app.state.store else "none",
)

if config.HOSTED:
    import auth

    app.include_router(auth.router)


# --------------------------------------------------------------- middleware
_AUTH_EXEMPT_PREFIXES = (
    "/auth/",
    "/healthz",
    "/static/",
    "/favicon",
)


@app.middleware("http")
async def _guard(request: Request, call_next):
    """Rate-limit writes, enforce ALLOW_ANONYMOUS, attach request id + headers."""
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    request.state.request_id = request_id

    # Require sign-in for everything except auth/health/static when configured.
    if (
        config.HOSTED
        and not config.ALLOW_ANONYMOUS
        and not any(request.url.path.startswith(p) for p in _AUTH_EXEMPT_PREFIXES)
    ):
        import auth as auth_mod

        if auth_mod.current_user_id(request) is None:
            if request.url.path.startswith("/api/"):
                return JSONResponse(
                    {"detail": "sign in required"},
                    status_code=401,
                    headers={"X-Request-Id": request_id},
                )
            from fastapi.responses import RedirectResponse

            nxt = request.url.path if request.url.path.startswith("/") else "/"
            return RedirectResponse(f"/auth/login?next={nxt}", status_code=303)

    if request.method == "POST":
        ip = client_ip(request)
        if not app.state.limiter.allow(ip):
            log.warning("rate limited ip=%s", ip, extra={"request_id": request_id})
            return JSONResponse(
                {"detail": "slow down"},
                status_code=429,
                headers={"X-Request-Id": request_id},
            )

    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    if config.COOKIE_SECURE:
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    # Baseline CSP when not behind Caddy (ALB / direct expose).
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob: https://cdn.jsdelivr.net "
        "https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://cdn.jsdelivr.net; "
        "worker-src 'self' blob:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'",
    )
    return response


# ------------------------------------------------------------------ helpers
def _user_id(request: Request) -> int | None:
    if not config.HOSTED:
        return None
    import auth

    return auth.current_user_id(request)


def _progress_for(request: Request) -> dict[str, Any]:
    store = request.app.state.store
    if store is None:
        return {"exercises": {}, "milestones": {}}
    if config.HOSTED:
        uid = _user_id(request)
        return store.get_progress(uid) if uid else {"exercises": {}, "milestones": {}}
    return store.get_progress()


def _require_user(request: Request) -> int:
    uid = _user_id(request)
    if uid is None:
        raise HTTPException(401, "sign in to save progress across devices")
    return uid


def _auth_usable(request: Request) -> bool:
    return bool(
        config.HOSTED
        and config.AUTH_ENABLED
        and request.app.state.store is not None
    )


def _current_user(request: Request) -> dict[str, Any] | None:
    store = request.app.state.store
    uid = _user_id(request)
    if uid is None or store is None or not hasattr(store, "get_user"):
        return None
    return store.get_user(uid)


# ------------------------------------------------------------------- models
class RunRequest(BaseModel):
    project_id: str
    exercise_id: str
    code: str


class LintRequest(BaseModel):
    code: str


class ExerciseProgress(BaseModel):
    exercise_id: str
    passed: bool = True


class MilestoneRequest(BaseModel):
    project_id: str
    index: int
    done: bool


class MergeRequest(BaseModel):
    progress: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------- endpoints
@app.get("/api/curriculum")
def get_curriculum(request: Request) -> JSONResponse:
    progress = _progress_for(request)
    out = []
    for p in PROJECTS:
        ex_done = sum(1 for e in p["exercises"] if progress["exercises"].get(e["id"]))
        out.append({
            "id": p["id"], "num": p["num"], "title": p["title"],
            "tagline": p["tagline"], "level": p["level"], "tech": p["tech"],
            "est_hours": p["est_hours"],
            "exercises_done": ex_done, "exercises_total": len(p["exercises"]),
            "exercise_ids": [e["id"] for e in p["exercises"]],
            "milestones_done": len(progress["milestones"].get(p["id"], [])),
            "milestones_total": len(p["milestones"]),
            "interview_total": len(p.get("interview", [])),
        })
    body = {
        "projects": out,
        "progress": progress,
        "stages": STAGE_LAYOUT,
        "mode": "hosted" if config.HOSTED else "local",
        "auth_enabled": _auth_usable(request),
        "user": _current_user(request),
        "pyodide_index_url": config.PYODIDE_INDEX_URL,
        "allow_anonymous": config.ALLOW_ANONYMOUS,
        # Hosted checkmarks are browser-verified; do not treat as proctored proof.
        "progress_honor_system": bool(config.HOSTED and config.PROGRESS_HONOR_SYSTEM),
    }
    response = JSONResponse(body)
    # Progress is user-specific; only cache the anonymous case lightly.
    if config.HOSTED and _user_id(request) is None:
        response.headers["Cache-Control"] = (
            f"public, max-age={config.CURRICULUM_CACHE_SECONDS}"
        )
    else:
        response.headers["Cache-Control"] = "private, no-store"
    return response


@app.get("/api/project/{pid}")
def get_project(pid: str, request: Request) -> dict[str, Any]:
    p = PROJECTS_BY_ID.get(pid)
    if not p:
        raise HTTPException(404, "unknown project")
    progress = _progress_for(request)
    return {
        "project": p,
        "exercises_passed": {
            e["id"]: bool(progress["exercises"].get(e["id"])) for e in p["exercises"]
        },
        "milestones_done": progress["milestones"].get(pid, []),
    }


@app.get("/api/me")
def me(request: Request) -> dict[str, Any]:
    return {"user": _current_user(request), "auth_enabled": _auth_usable(request)}


@app.post("/api/progress/exercise")
def record_exercise(req: ExerciseProgress, request: Request) -> dict[str, Any]:
    """Record a browser-verified pass (hosted honor system).

    The server validates that the exercise id is known and that the caller is
    signed in; it does not re-execute the check. Anonymous visitors keep
    progress in local storage instead.
    """
    if req.exercise_id not in KNOWN_EXERCISE_IDS:
        raise HTTPException(404, "unknown exercise")
    store = request.app.state.store
    if store is None:
        raise HTTPException(503, "no progress storage configured")
    if config.HOSTED:
        store.set_exercise(_require_user(request), req.exercise_id, req.passed)
    else:
        store.set_exercise(None, req.exercise_id, req.passed)
    return {"ok": True}


@app.post("/api/milestone")
def set_milestone(req: MilestoneRequest, request: Request) -> dict[str, Any]:
    p = PROJECTS_BY_ID.get(req.project_id)
    if not p:
        raise HTTPException(404, "unknown project")
    if not (0 <= req.index < len(p["milestones"])):
        raise HTTPException(400, "bad milestone index")
    store = request.app.state.store
    if store is None:
        raise HTTPException(503, "no progress storage configured")
    uid = _require_user(request) if config.HOSTED else None
    done = store.set_milestone(uid, req.project_id, req.index, req.done)
    return {"ok": True, "milestones_done": done}


@app.post("/api/progress/merge")
def merge_progress(req: MergeRequest, request: Request) -> dict[str, Any]:
    """Fold a visitor's anonymous local-storage progress into their account."""
    if not config.HOSTED:
        raise HTTPException(400, "merge is a hosted-mode feature")
    store = request.app.state.store
    if store is None:
        raise HTTPException(503, "no progress storage configured")
    clean = sanitize_progress(req.progress)
    store.merge(_require_user(request), clean)
    return {"ok": True, "progress": _progress_for(request)}


@app.get("/api/progress")
def get_progress(request: Request) -> dict[str, Any]:
    return _progress_for(request)


# ------------------------------------------ local-only execution endpoints
if not config.HOSTED:
    from runner import run_exercise, run_scratch

    class ScratchRequest(BaseModel):
        code: str
        heavy: bool = False

    @app.post("/api/run")
    def run_code(req: RunRequest, request: Request) -> dict[str, Any]:
        p = PROJECTS_BY_ID.get(req.project_id)
        if not p:
            raise HTTPException(404, "unknown project")
        exercise = next((e for e in p["exercises"] if e["id"] == req.exercise_id), None)
        if not exercise:
            raise HTTPException(404, "unknown exercise")

        result = run_exercise(
            req.code, exercise["check_code"], heavy=exercise.get("heavy", False)
        )
        if result["passed"]:
            request.app.state.store.set_exercise(None, req.exercise_id, True)
        return result

    @app.post("/api/scratch")
    def scratch(req: ScratchRequest) -> dict[str, Any]:
        return run_scratch(req.code, heavy=req.heavy)

    @app.post("/api/lint")
    def lint(req: LintRequest) -> dict[str, Any]:
        problems: list[dict[str, Any]] = []
        if len(req.code) > 200_000:
            return {
                "problems": [{
                    "line": 1, "col": 1, "severity": "error",
                    "message": "file too large to lint",
                }]
            }
        try:
            compile(req.code, "<exercise>", "exec")
        except SyntaxError as e:
            return {
                "problems": [{
                    "line": e.lineno or 1, "col": e.offset or 1,
                    "message": f"SyntaxError: {e.msg}", "severity": "error",
                }]
            }
        try:
            import io
            import re as _re

            from pyflakes.api import check
            from pyflakes.reporter import Reporter

            out, err = io.StringIO(), io.StringIO()
            check(req.code, "<exercise>", Reporter(out, err))
            for line in out.getvalue().splitlines():
                m = _re.match(r"^<exercise>:(\d+):(\d+):?\s*(.*)$", line)
                if m:
                    problems.append({
                        "line": int(m.group(1)), "col": int(m.group(2)),
                        "message": m.group(3), "severity": "warning",
                    })
        except ImportError:
            pass
        return {"problems": problems}


# ------------------------------------------------------------------- static
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/healthz")
def healthz(request: Request) -> Response:
    """Liveness always 200; readiness fails (503) when hosted DB is down."""
    payload: dict[str, Any] = {
        "ok": True,
        "mode": config.MODE,
        "projects": len(PROJECTS),
    }
    store = request.app.state.store
    if config.HOSTED and isinstance(store, PostgresStore):
        ready = store.ping()
        payload["db"] = "ok" if ready else "down"
        if not ready:
            payload["ok"] = False
            return JSONResponse(payload, status_code=503)
    elif config.HOSTED and store is None:
        payload["db"] = "unconfigured"
    return JSONResponse(payload)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")
