from __future__ import annotations

import os
from pathlib import Path

MIGRATION_VERSION = "001_verified_memory_vector"


def migrate(database_url: str | None = None) -> str:
    import psycopg
    url = database_url or os.environ["COCKROACH_DATABASE_URL"]
    root = Path(__file__).resolve().parents[1]
    statements = (root / "migrations" / "001_init.sql").read_text(encoding="utf-8").split("-- statement-break")
    with psycopg.connect(url, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version STRING PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
        cur.execute("SELECT 1 FROM schema_migrations WHERE version = %s", (MIGRATION_VERSION,))
        if cur.fetchone():
            return "already_applied"
        for statement in statements:
            if statement.strip():
                cur.execute(statement.strip())
        cur.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (MIGRATION_VERSION,))
    return "applied"


if __name__ == "__main__":
    print(migrate())
