"""
Progress storage — two backends behind one small interface.

LocalJsonStore : single learner, one JSON file (the local Docker stack).
PostgresStore  : many learners, one row per (user, item), for hosted mode.

Progress shape returned by both:
    {"exercises": {exercise_id: True}, "milestones": {project_id: [idx, ...]}}
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

import config

log = logging.getLogger("dataforged.store")


class LocalJsonStore:
    """File-backed store for single-user local mode."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _read_unlocked(self) -> dict[str, Any]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                log.warning("corrupt progress file at %s — starting fresh", self.path)
        return {"exercises": {}, "milestones": {}}

    def _write_unlocked(self, data: dict[str, Any]) -> None:
        """Atomic replace so a crash mid-write cannot leave empty/partial JSON."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            dir=str(self.path.parent), prefix=".progress-", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, self.path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    def get_progress(self, user_id: int | None = None) -> dict[str, Any]:
        with self._lock:
            return self._read_unlocked()

    def set_exercise(
        self, user_id: int | None, exercise_id: str, passed: bool = True
    ) -> None:
        with self._lock:
            data = self._read_unlocked()
            if passed:
                data["exercises"][exercise_id] = True
            else:
                data["exercises"].pop(exercise_id, None)
            self._write_unlocked(data)

    def set_milestone(
        self, user_id: int | None, project_id: str, index: int, done: bool
    ) -> list[int]:
        with self._lock:
            data = self._read_unlocked()
            current = set(data["milestones"].get(project_id, []))
            (current.add if done else current.discard)(index)
            data["milestones"][project_id] = sorted(current)
            self._write_unlocked(data)
            return data["milestones"][project_id]


class PostgresStore:
    """Per-user store for hosted mode.

    Uses a small psycopg2 connection pool. Every endpoint that touches it is a
    plain `def` (not `async def`) so FastAPI runs it in its threadpool.
    """

    def __init__(self, dsn: str) -> None:
        from psycopg2.pool import ThreadedConnectionPool

        from migrations import apply_migrations

        self.pool = ThreadedConnectionPool(1, 10, dsn)
        with self._conn() as conn:
            applied = apply_migrations(conn)
            if applied:
                log.info("applied migrations: %s", ", ".join(applied))

    class _ConnCtx:
        def __init__(self, pool: Any) -> None:
            self.pool, self.conn = pool, None

        def __enter__(self) -> Any:
            self.conn = self.pool.getconn()
            return self.conn

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            if exc_type:
                self.conn.rollback()
            self.pool.putconn(self.conn)

    def _conn(self) -> PostgresStore._ConnCtx:
        return self._ConnCtx(self.pool)

    def ping(self) -> bool:
        """Return True if the database answers a trivial query."""
        try:
            with self._conn() as conn, conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            return True
        except Exception as exc:  # noqa: BLE001 — readiness must never raise
            log.warning("postgres ping failed: %s", exc)
            return False

    def consume_oauth_nonce(self, nonce: str) -> bool:
        """Mark an OAuth state nonce as used. Returns False if already consumed."""
        with self._conn() as conn, conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO oauth_consumed (nonce) VALUES (%s) ON CONFLICT DO NOTHING",
                    (nonce,),
                )
                inserted = cur.rowcount == 1
                # Opportunistic cleanup of nonces older than 1 day.
                cur.execute(
                    "DELETE FROM oauth_consumed WHERE consumed_at < now() - interval '1 day'"
                )
                conn.commit()
                return inserted
            except Exception:
                conn.rollback()
                raise

    def upsert_user(
        self,
        github_id: int,
        login: str,
        name: str | None,
        avatar_url: str | None,
    ) -> dict[str, Any]:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (github_id, login, name, avatar_url)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (github_id) DO UPDATE
                   SET login = EXCLUDED.login,
                       name = EXCLUDED.name,
                       avatar_url = EXCLUDED.avatar_url,
                       last_seen_at = now()
                RETURNING id, login, name, avatar_url
                """,
                (github_id, login, name, avatar_url),
            )
            row = cur.fetchone()
            conn.commit()
        return {"id": row[0], "login": row[1], "name": row[2], "avatar_url": row[3]}

    def get_user(self, user_id: int) -> dict[str, Any] | None:
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id, login, name, avatar_url FROM users WHERE id = %s",
                (user_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "login": row[1], "name": row[2], "avatar_url": row[3]}

    def get_progress(self, user_id: int | None) -> dict[str, Any]:
        out: dict[str, Any] = {"exercises": {}, "milestones": {}}
        if user_id is None:
            return out
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT kind, item_key FROM progress WHERE user_id = %s", (user_id,)
            )
            for kind, key in cur.fetchall():
                if kind == "exercise":
                    out["exercises"][key] = True
                else:
                    project_id, _, idx = key.rpartition(":")
                    out["milestones"].setdefault(project_id, []).append(int(idx))
        for pid in out["milestones"]:
            out["milestones"][pid].sort()
        return out

    def set_exercise(
        self, user_id: int, exercise_id: str, passed: bool = True
    ) -> None:
        with self._conn() as conn, conn.cursor() as cur:
            if passed:
                cur.execute(
                    """INSERT INTO progress (user_id, kind, item_key)
                       VALUES (%s, 'exercise', %s)
                       ON CONFLICT (user_id, kind, item_key)
                       DO UPDATE SET updated_at = now()""",
                    (user_id, exercise_id),
                )
            else:
                cur.execute(
                    "DELETE FROM progress WHERE user_id=%s AND kind='exercise' AND item_key=%s",
                    (user_id, exercise_id),
                )
            conn.commit()

    def set_milestone(
        self, user_id: int, project_id: str, index: int, done: bool
    ) -> list[int]:
        key = f"{project_id}:{index}"
        with self._conn() as conn, conn.cursor() as cur:
            if done:
                cur.execute(
                    """INSERT INTO progress (user_id, kind, item_key)
                       VALUES (%s, 'milestone', %s)
                       ON CONFLICT (user_id, kind, item_key)
                       DO UPDATE SET updated_at = now()""",
                    (user_id, key),
                )
            else:
                cur.execute(
                    "DELETE FROM progress WHERE user_id=%s AND kind='milestone' AND item_key=%s",
                    (user_id, key),
                )
            conn.commit()
            cur.execute(
                """SELECT item_key FROM progress
                   WHERE user_id=%s AND kind='milestone' AND item_key LIKE %s""",
                (user_id, f"{project_id}:%"),
            )
            done_idx = sorted(int(k.rpartition(":")[2]) for (k,) in cur.fetchall())
        return done_idx

    def merge(self, user_id: int, progress: dict[str, Any]) -> None:
        """Fold sanitized anonymous progress into the account (union semantics)."""
        from progress_keys import sanitize_progress

        clean = sanitize_progress(progress)
        exercises = list(clean["exercises"].keys())
        milestones = [
            f"{pid}:{i}"
            for pid, idxs in clean["milestones"].items()
            for i in idxs
        ]
        if not exercises and not milestones:
            return
        with self._conn() as conn, conn.cursor() as cur:
            for key in exercises:
                cur.execute(
                    """INSERT INTO progress (user_id, kind, item_key) VALUES (%s,'exercise',%s)
                       ON CONFLICT DO NOTHING""",
                    (user_id, key),
                )
            for key in milestones:
                cur.execute(
                    """INSERT INTO progress (user_id, kind, item_key) VALUES (%s,'milestone',%s)
                       ON CONFLICT DO NOTHING""",
                    (user_id, key),
                )
            conn.commit()


def build_store() -> LocalJsonStore | PostgresStore | None:
    """Pick the backend for the current mode."""
    if config.HOSTED and config.DATABASE_URL:
        return PostgresStore(config.DATABASE_URL)
    if config.HOSTED:
        return None
    return LocalJsonStore(Path(__file__).parent / "data" / "progress.json")
