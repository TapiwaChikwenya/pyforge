"""Versioned SQL migrations for PostgresStore.

Apply order is the numeric prefix of each *.sql file. Each version is recorded
in schema_migrations so re-applies are no-ops. Rollback: restore a DB snapshot
(or restore from the automated backup) — forward-only migrations by design.
"""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger("dataforged.migrations")

MIGRATIONS_DIR = Path(__file__).parent


def apply_migrations(conn) -> list[str]:
    """Run pending *.sql migrations. Returns list of newly applied versions."""
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version     TEXT PRIMARY KEY,
                applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        conn.commit()
        cur.execute("SELECT version FROM schema_migrations")
        applied = {row[0] for row in cur.fetchall()}

    newly: list[str] = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        version = path.stem  # e.g. 001_initial
        if version in applied:
            continue
        sql = path.read_text(encoding="utf-8")
        log.info("applying migration %s", version)
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)", (version,)
            )
            conn.commit()
        newly.append(version)
    return newly
