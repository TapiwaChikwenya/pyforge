"""Lightweight learning analytics — friction / drop-off signals."""

from __future__ import annotations

import json
import logging
import threading
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import config

log = logging.getLogger("dataforged.analytics")

ALLOWED_EVENTS = frozenset({
    "exercise_open", "exercise_run", "exercise_fail", "exercise_pass",
    "project_open", "onboarding_start", "onboarding_complete",
    "review_open", "review_complete", "portfolio_export",
    "mentor_unlock", "solution_view",
})


class AnalyticsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(__file__).parent / "data" / "analytics.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log.warning("corrupt analytics file — resetting")
            return []

    def _write(self, rows: list[dict[str, Any]]) -> None:
        self.path.write_text(json.dumps(rows[-5000:], indent=2), encoding="utf-8")

    def record(
        self,
        event: str,
        *,
        exercise_id: str | None = None,
        project_id: str | None = None,
        user_id: int | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        if event not in ALLOWED_EVENTS:
            raise ValueError(f"unknown event: {event}")
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "exercise_id": exercise_id,
            "project_id": project_id,
            "user_id": user_id,
            "meta": meta or {},
        }
        with self._lock:
            rows = self._read()
            rows.append(row)
            self._write(rows)

    def friction_report(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._read()
        opens: dict[str, int] = defaultdict(int)
        fails: dict[str, int] = defaultdict(int)
        passes: dict[str, int] = defaultdict(int)
        for r in rows:
            eid = r.get("exercise_id")
            if not eid:
                continue
            if r["event"] == "exercise_open":
                opens[eid] += 1
            elif r["event"] == "exercise_fail":
                fails[eid] += 1
            elif r["event"] == "exercise_pass":
                passes[eid] += 1
        scored = []
        for eid in set(opens) | set(fails) | set(passes):
            o, f, p = opens[eid], fails[eid], passes[eid]
            # Drop-off: attempts that fail without a corresponding pass weight.
            drop = max(0, f - p) + max(0, o - p - f)
            if o + f + p == 0:
                continue
            fail_rate = f / max(1, f + p)
            scored.append({
                "exercise_id": eid,
                "opens": o,
                "fails": f,
                "passes": p,
                "fail_rate": round(fail_rate, 3),
                "drop_score": drop + f,
            })
        scored.sort(key=lambda x: (-x["drop_score"], -x["fail_rate"]))
        return scored[:limit]


_store: AnalyticsStore | None = None


def get_analytics() -> AnalyticsStore:
    global _store
    if _store is None:
        _store = AnalyticsStore()
    return _store
