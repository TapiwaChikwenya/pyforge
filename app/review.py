"""Spaced review + interview drill queue."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from curriculum import PROJECTS


def _parse_ts(raw: Any) -> datetime | None:
    if not raw:
        return None
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(raw, tz=timezone.utc)
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None


def build_review_queue(
    progress: dict[str, Any],
    review_state: dict[str, Any] | None = None,
    *,
    now: datetime | None = None,
    limit: int = 12,
) -> list[dict[str, Any]]:
    """Return due review items (weak exercises + interview Qs).

    review_state shape (from browser or stored):
      {
        "exercise_passed_at": {ex_id: iso},
        "exercise_fails": {ex_id: n},
        "interview_reviewed_at": {"project_id:idx": iso},
      }
    """
    now = now or datetime.now(timezone.utc)
    state = review_state or {}
    passed_at = state.get("exercise_passed_at") or {}
    fails = state.get("exercise_fails") or {}
    iv_reviewed = state.get("interview_reviewed_at") or {}
    exercises_done = progress.get("exercises") or {}

    items: list[dict[str, Any]] = []

    for p in PROJECTS:
        for ex in p["exercises"]:
            eid = ex["id"]
            n_fail = int(fails.get(eid) or 0)
            if exercises_done.get(eid):
                ts = _parse_ts(passed_at.get(eid))
                age_days = (now - ts).days if ts else 14
                if age_days >= 14:
                    items.append({
                        "kind": "exercise_review",
                        "priority": 20 + min(age_days, 60),
                        "project_id": p["id"],
                        "project_title": p["title"],
                        "exercise_id": eid,
                        "title": ex["title"],
                        "reason": f"Spaced review — last pass ~{age_days}d ago",
                    })
            elif n_fail >= 2:
                items.append({
                    "kind": "weak_exercise",
                    "priority": 80 + n_fail,
                    "project_id": p["id"],
                    "project_title": p["title"],
                    "exercise_id": eid,
                    "title": ex["title"],
                    "reason": f"Struggled here ({n_fail} fails) — revisit",
                })

        for i, q in enumerate(p.get("interview") or []):
            key = f"{p['id']}:{i}"
            ts = _parse_ts(iv_reviewed.get(key))
            age_days = (now - ts).days if ts else 999
            if age_days >= 7:
                items.append({
                    "kind": "interview",
                    "priority": 50 + min(age_days, 40),
                    "project_id": p["id"],
                    "project_title": p["title"],
                    "index": i,
                    "title": f"Interview Q{i + 1}: {(q.get('topics') or ['drill'])[0]}",
                    "difficulty": q.get("difficulty") or "Medium",
                    "question": q.get("question") or "",
                    "answer": q.get("answer") or "",
                    "explanation": q.get("explanation") or "",
                    "reason": (
                        "New interview drill" if ts is None
                        else f"Weekly drill — last review ~{age_days}d ago"
                    ),
                })

    items.sort(key=lambda x: -x["priority"])
    return items[:limit]
