"""Lightweight learning analytics — friction / drop-off signals."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("dataforged.analytics")

ALLOWED_EVENTS = frozenset({
    "exercise_open", "exercise_run", "exercise_fail", "exercise_pass",
    "project_open", "onboarding_start", "onboarding_complete",
    "review_open", "review_complete", "portfolio_export",
    "mentor_unlock", "solution_view", "resume_open",
})

_MAX_META_BYTES = 8192
_MAX_META_KEYS = 8
_MAX_META_STR = 200
_MAX_STORED_META = 1024


def meta_too_large(meta: dict[str, Any] | None) -> bool:
    """Reject payloads that are not a small JSON object."""
    if not meta:
        return False
    try:
        raw = json.dumps(meta, separators=(",", ":"))
    except (TypeError, ValueError):
        return True
    return len(raw.encode("utf-8")) > _MAX_META_BYTES


def _bound_meta(meta: dict[str, Any] | None) -> dict[str, Any]:
    """Keep scalars only, and cap key count plus stored size."""
    if not isinstance(meta, dict):
        return {}
    clean: dict[str, Any] = {}
    for key, value in meta.items():
        if len(clean) >= _MAX_META_KEYS:
            break
        name = str(key)[:64]
        if isinstance(value, bool) or value is None or isinstance(value, int):
            clean[name] = value
        elif isinstance(value, float):
            if value != value or value in (float("inf"), float("-inf")):
                continue
            clean[name] = value
        elif isinstance(value, str):
            clean[name] = value[:_MAX_META_STR]
    raw = json.dumps(clean, separators=(",", ":"))
    if len(raw.encode("utf-8")) > _MAX_STORED_META:
        return {"truncated": True}
    return clean


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
        """Atomic replace so a crash cannot leave a half-written file."""
        payload = json.dumps(rows[-5000:], indent=2)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            dir=self.path.parent, prefix=".analytics-", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, self.path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

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
            "meta": _bound_meta(meta),
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
