"""Whitelist known progress keys so merge/write endpoints cannot pollute storage."""

from __future__ import annotations

from typing import Any

from curriculum import PROJECTS, PROJECTS_BY_ID

KNOWN_EXERCISE_IDS: frozenset[str] = frozenset(
    e["id"] for p in PROJECTS for e in p["exercises"]
)


def known_milestone_key(project_id: str, index: int) -> bool:
    p = PROJECTS_BY_ID.get(project_id)
    if not p:
        return False
    return 0 <= index < len(p["milestones"])


def sanitize_progress(progress: dict[str, Any] | None) -> dict[str, Any]:
    """Keep only known exercise ids and valid milestone indices."""
    progress = progress or {}
    exercises_in = progress.get("exercises") or {}
    milestones_in = progress.get("milestones") or {}

    exercises = {
        eid: True
        for eid, val in exercises_in.items()
        if eid in KNOWN_EXERCISE_IDS and val
    }

    milestones: dict[str, list[int]] = {}
    if isinstance(milestones_in, dict):
        for pid, idxs in milestones_in.items():
            if pid not in PROJECTS_BY_ID:
                continue
            clean: list[int] = []
            for i in idxs or []:
                try:
                    ii = int(i)
                except (TypeError, ValueError):
                    continue
                if known_milestone_key(pid, ii):
                    clean.append(ii)
            if clean:
                milestones[pid] = sorted(set(clean))

    return {"exercises": exercises, "milestones": milestones}
