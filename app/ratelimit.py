"""Shared write rate limiter for multi-worker uvicorn.

Uses a small SQLite database so all workers on one host share the same budget.
Idle IP rows are pruned periodically to bound memory/disk growth.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

import config


class RateLimiter:
    def __init__(self, path: Path | None = None, limit: int | None = None) -> None:
        self.limit = limit if limit is not None else config.RATE_LIMIT_WRITES_PER_MINUTE
        self.path = path or Path(
            config.RATE_LIMIT_DB
            if getattr(config, "RATE_LIMIT_DB", "")
            else Path(__file__).parent / "data" / "ratelimit.sqlite3"
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._last_prune = 0.0
        self._db: sqlite3.Connection | None = None
        with self._lock:
            conn = self._db_conn()
            conn.execute(
                """CREATE TABLE IF NOT EXISTS hits (
                       ip TEXT NOT NULL,
                       ts REAL NOT NULL
                   )"""
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS hits_ip_ts ON hits(ip, ts)"
            )
            conn.commit()

    def _db_conn(self) -> sqlite3.Connection:
        """One connection per process. Callers must hold ``self._lock``."""
        if self._db is None:
            conn = sqlite3.connect(self.path, timeout=5, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL").fetchone()
            self._db = conn
        return self._db

    def close(self) -> None:
        with self._lock:
            if self._db is not None:
                self._db.close()
                self._db = None

    def allow(self, ip: str) -> bool:
        """Return True if the request is allowed; record the hit when allowed."""
        now = time.time()
        cutoff = now - 60.0
        with self._lock:
            conn = self._db_conn()
            try:
                conn.execute("DELETE FROM hits WHERE ip = ? AND ts < ?", (ip, cutoff))
                (count,) = conn.execute(
                    "SELECT COUNT(*) FROM hits WHERE ip = ? AND ts >= ?", (ip, cutoff)
                ).fetchone()
                if count >= self.limit:
                    conn.commit()
                    return False
                conn.execute("INSERT INTO hits (ip, ts) VALUES (?, ?)", (ip, now))
                if now - self._last_prune > 300:
                    # Drop stale rows for idle IPs so the table cannot grow forever.
                    conn.execute("DELETE FROM hits WHERE ts < ?", (cutoff,))
                    self._last_prune = now
                conn.commit()
                return True
            except Exception:
                conn.rollback()
                raise


def client_ip(request) -> str:
    """Best-effort client IP. Trust X-Forwarded-For only when configured."""
    if config.TRUST_PROXY:
        xff = request.headers.get("x-forwarded-for") or ""
        first = xff.split(",")[0].strip()
        if first:
            return first
        real = (request.headers.get("x-real-ip") or "").strip()
        if real:
            return real
    if request.client and request.client.host:
        return request.client.host
    return "?"
