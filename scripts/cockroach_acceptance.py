import os

from evidencebound.migrate import migrate
from evidencebound.repository import CockroachRepository


def main():
    import psycopg
    url = os.environ["COCKROACH_DATABASE_URL"]
    migration = migrate(url)
    repo = CockroachRepository(url)
    with psycopg.connect(url, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute("SHOW TABLES")
        tables = {row[0] for row in cur.fetchall()}
        assert {"verified_memories", "verification_incidents"}.issubset(tables)
        cur.execute("SHOW CREATE TABLE verification_incidents")
        schema = "\n".join(str(part) for row in cur.fetchall() for part in row)
        assert "VECTOR(1024)" in schema.upper()
        cur.execute("EXPLAIN SELECT snapshot FROM verified_memories WHERE memory_id = gen_random_uuid() ORDER BY created_at DESC, id DESC LIMIT 1")
        assert cur.fetchall()
    tooling = repo.tooling_evidence()
    assert tooling["vector_index"] == "verification_incidents_embedding_idx"
    print(f"COCKROACH_ACCEPTANCE=PASS migration={migration} vector_index={tooling['vector_index']}")


if __name__ == "__main__":
    main()
