"""Tests for portfolio, mentor, review, analytics, community solutions."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "tests"))


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("PYFORGE_MODE", "local")
    monkeypatch.setenv("RATE_LIMIT_WRITES_PER_MINUTE", "1000")
    for mod in list(sys.modules):
        if mod in {
            "config", "main", "store", "ratelimit", "progress_keys",
            "portfolio", "mentor", "review", "analytics_store",
            "community_solutions", "curriculum",
        } or mod.startswith("curriculum_") or mod.startswith("enrichment"):
            del sys.modules[mod]
    import main as main_mod
    from store import LocalJsonStore

    main_mod.app.state.store = LocalJsonStore(tmp_path / "progress.json")
    main_mod.app.state.limiter = __import__("ratelimit").RateLimiter(
        path=tmp_path / "rl.sqlite3", limit=1000
    )
    # Point analytics at a temp file
    import analytics_store
    analytics_store._store = analytics_store.AnalyticsStore(tmp_path / "analytics.json")
    with TestClient(main_mod.app) as c:
        yield c


def test_onboarding_and_first_hour(client):
    r = client.get("/api/onboarding")
    assert r.status_code == 200
    body = r.json()
    assert body["project_id"] == "task-forge"
    assert body["exercise_id"] == "tf-1"
    cur = client.get("/api/curriculum").json()
    assert cur["first_hour"]["project_id"] == "task-forge"
    assert cur["projects"][0]["stack_tier"] == "light"


def test_portfolio_and_certificate(client):
    client.post("/api/progress/exercise", json={"exercise_id": "tf-1", "passed": True})
    r = client.get("/api/portfolio")
    assert r.status_code == 200
    assert "Task Forge" in r.json()["markdown"]
    assert r.json()["stats"]["exercises_done"] >= 1
    cert = client.get("/api/certificate")
    assert cert.status_code == 200
    assert "CERTIFICATE" in cert.text
    assert "Honor system" in cert.text


def test_mentor_debrief_on_project(client):
    p = client.get("/api/project/task-forge").json()["project"]
    ex = p["exercises"][0]
    assert "mentor_debrief" in ex
    assert ex["mentor_debrief"]["fails_before_unlock"] == 3
    assert ex["mentor_debrief"]["steps"]


def test_community_solutions_gated(client):
    r = client.get("/api/solutions/tf-1")
    assert r.status_code == 403
    client.post("/api/progress/exercise", json={"exercise_id": "tf-1", "passed": True})
    r = client.get("/api/solutions/tf-1")
    assert r.status_code == 200
    assert len(r.json()["solutions"]) >= 1


def test_analytics_friction(client):
    for ev in ("exercise_open", "exercise_fail", "exercise_fail", "exercise_pass"):
        assert client.post("/api/analytics/event", json={
            "event": ev, "exercise_id": "tf-1", "project_id": "task-forge",
        }).status_code == 200
    r = client.get("/api/analytics/friction")
    assert r.status_code == 200
    items = r.json()["items"]
    assert items and items[0]["exercise_id"] == "tf-1"


def test_review_queue(client):
    r = client.post("/api/review", json={
        "review_state": {
            "exercise_fails": {"tf-2": 3},
            "exercise_passed_at": {},
            "interview_reviewed_at": {},
        }
    })
    assert r.status_code == 200
    kinds = {i["kind"] for i in r.json()["items"]}
    assert "weak_exercise" in kinds or "interview" in kinds


def test_stack_tiers_present(client):
    cur = client.get("/api/curriculum").json()
    tiers = {p["stack_tier"] for p in cur["projects"]}
    assert "light" in tiers
    assert "db" in tiers or "spark" in tiers or "full" in tiers
