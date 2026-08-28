"""Unit/API tests for auth helpers, progress sanitization, mode gating, rate limit."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from itsdangerous import URLSafeTimedSerializer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "tests"))


@pytest.fixture()
def local_client(monkeypatch, tmp_path):
    monkeypatch.setenv("DATAFORGED_MODE", "local")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("RATE_LIMIT_WRITES_PER_MINUTE", "1000")
    # Reload config + app modules with local mode.
    for mod in list(sys.modules):
        if mod in {
            "config", "main", "store", "auth", "ratelimit", "progress_keys",
            "runner", "curriculum",
        } or mod.startswith("curriculum_") or mod.startswith("enrichment"):
            del sys.modules[mod]
    import config  # noqa: F401
    import store as store_mod
    from store import LocalJsonStore

    import main as main_mod

    main_mod.app.state.store = LocalJsonStore(tmp_path / "progress.json")
    main_mod.app.state.limiter = __import__("ratelimit").RateLimiter(
        path=tmp_path / "rl.sqlite3", limit=1000
    )
    with TestClient(main_mod.app) as client:
        yield client


@pytest.fixture()
def hosted_client(monkeypatch, tmp_path):
    monkeypatch.setenv("DATAFORGED_MODE", "hosted")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-unit-tests")
    monkeypatch.setenv("ALLOW_ANONYMOUS", "true")
    monkeypatch.setenv("TRUST_PROXY", "true")
    monkeypatch.setenv("RATE_LIMIT_WRITES_PER_MINUTE", "1000")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("GITHUB_CLIENT_ID", raising=False)
    monkeypatch.delenv("GITHUB_CLIENT_SECRET", raising=False)
    for mod in list(sys.modules):
        if mod in {
            "config", "main", "store", "auth", "ratelimit", "progress_keys",
        } or mod.startswith("curriculum_") or mod.startswith("enrichment") \
                or mod == "curriculum":
            del sys.modules[mod]
    import main as main_mod

    main_mod.app.state.store = None
    main_mod.app.state.limiter = __import__("ratelimit").RateLimiter(
        path=tmp_path / "rl.sqlite3", limit=1000
    )
    with TestClient(main_mod.app) as client:
        yield client, main_mod


def test_healthz_local(local_client):
    r = local_client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["mode"] == "local"
    assert body["projects"] >= 1
    assert "X-Request-Id" in r.headers


def test_run_endpoint_local(local_client):
    # Pick a trivial known exercise if present.
    cur = local_client.get("/api/curriculum").json()
    pid = cur["projects"][0]["id"]
    detail = local_client.get(f"/api/project/{pid}").json()
    ex = detail["project"]["exercises"][0]
    # Starter often fails; just ensure endpoint exists and returns structured result.
    r = local_client.post(
        "/api/run",
        json={"project_id": pid, "exercise_id": ex["id"], "code": ex["starter_code"]},
    )
    assert r.status_code == 200
    assert "passed" in r.json()


def test_run_absent_in_hosted(hosted_client):
    client, _ = hosted_client
    r = client.post("/api/run", json={"project_id": "x", "exercise_id": "y", "code": ""})
    assert r.status_code == 404


def test_curriculum_cache_headers_hosted(hosted_client):
    client, _ = hosted_client
    r = client.get("/api/curriculum")
    assert r.status_code == 200
    assert "max-age" in r.headers.get("Cache-Control", "")
    assert r.json()["progress_honor_system"] is True


def test_sanitize_progress_drops_unknown():
    from progress_keys import KNOWN_EXERCISE_IDS, sanitize_progress

    eid = next(iter(KNOWN_EXERCISE_IDS))
    clean = sanitize_progress({
        "exercises": {eid: True, "totally-fake": True},
        "milestones": {"no-such-project": [0], "task-forge": [0, 999]},
    })
    assert eid in clean["exercises"]
    assert "totally-fake" not in clean["exercises"]
    assert "no-such-project" not in clean["milestones"]
    # 999 is out of range for task-forge milestones
    assert 999 not in clean["milestones"].get("task-forge", [])


def test_atomic_json_store(tmp_path):
    from store import LocalJsonStore

    store = LocalJsonStore(tmp_path / "p.json")
    store.set_exercise(None, "ex-1", True)
    store.set_milestone(None, "proj", 0, True)
    data = store.get_progress()
    assert data["exercises"]["ex-1"] is True
    assert data["milestones"]["proj"] == [0]


def test_rate_limiter_blocks(tmp_path):
    from ratelimit import RateLimiter

    rl = RateLimiter(path=tmp_path / "rl.sqlite3", limit=2)
    assert rl.allow("1.2.3.4")
    assert rl.allow("1.2.3.4")
    assert not rl.allow("1.2.3.4")
    assert rl.allow("9.9.9.9")


def test_session_cookie_roundtrip(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "unit-test-secret")
    for mod in ("config", "auth"):
        sys.modules.pop(mod, None)
    import config
    import auth

    signer = URLSafeTimedSerializer(config.SECRET_KEY, salt="dataforged-session")
    raw = signer.dumps({"uid": 42})

    class FakeReq:
        cookies = {config.SESSION_COOKIE: raw}

    assert auth.current_user_id(FakeReq()) == 42

    class BadReq:
        cookies = {config.SESSION_COOKIE: raw + "tampered"}

    assert auth.current_user_id(BadReq()) is None


def test_allow_anonymous_false_blocks_api(monkeypatch, tmp_path):
    monkeypatch.setenv("DATAFORGED_MODE", "hosted")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-unit-tests")
    monkeypatch.setenv("ALLOW_ANONYMOUS", "false")
    monkeypatch.setenv("RATE_LIMIT_WRITES_PER_MINUTE", "1000")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for mod in list(sys.modules):
        if mod in {"config", "main", "store", "auth", "ratelimit", "progress_keys", "curriculum"} \
                or mod.startswith("curriculum_") or mod.startswith("enrichment"):
            del sys.modules[mod]
    import main as main_mod

    main_mod.app.state.store = None
    main_mod.app.state.limiter = __import__("ratelimit").RateLimiter(
        path=tmp_path / "rl.sqlite3", limit=1000
    )
    with TestClient(main_mod.app, follow_redirects=False) as client:
        r = client.get("/api/curriculum")
        assert r.status_code == 401


def test_curriculum_integrity():
    """Every exercise has enrichment fields; every project has interview Q&A."""
    from curriculum import PROJECTS

    missing_enrich = []
    missing_iv = []
    for p in PROJECTS:
        if not p.get("interview"):
            missing_iv.append(p["id"])
        for ex in p["exercises"]:
            if not ex.get("refresher") or not ex.get("hints") or not ex.get("objectives"):
                missing_enrich.append(ex["id"])
    assert not missing_iv, f"projects missing interview: {missing_iv}"
    assert not missing_enrich, f"exercises missing enrichment: {missing_enrich}"
