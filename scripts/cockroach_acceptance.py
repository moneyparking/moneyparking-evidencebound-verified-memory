import os

from evidencebound.migrate import migrate
from evidencebound.repository import CockroachRepository, INCIDENT_TABLE, MEMORY_TABLE, VECTOR_INDEX


def main():
    import psycopg
    from psycopg.conninfo import make_conninfo

    url = make_conninfo(
        os.environ["COCKROACH_DATABASE_URL"],
        sslmode="verify-full",
        sslrootcert=os.environ["PGSSLROOTCERT"],
    )
    migration = migrate(url)
    repo = CockroachRepository(url)
    with psycopg.connect(url, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = current_schema() AND table_type = 'BASE TABLE'"
        )
        tables = {row[0] for row in cur.fetchall()}
        assert {MEMORY_TABLE, INCIDENT_TABLE}.issubset(tables)
        cur.execute(f"SHOW CREATE TABLE {INCIDENT_TABLE}")
        schema = "\n".join(str(part) for row in cur.fetchall() for part in row)
        assert "VECTOR(1024)" in schema.upper()
        cur.execute(
            f"EXPLAIN SELECT snapshot FROM {MEMORY_TABLE} "
            "WHERE memory_id = gen_random_uuid() ORDER BY created_at DESC, id DESC LIMIT 1"
        )
        assert cur.fetchall()
    tooling = repo.tooling_evidence()
    assert tooling["vector_index"] == VECTOR_INDEX
    print(f"COCKROACH_ACCEPTANCE=PASS migration={migration} vector_index={tooling['vector_index']}")


if __name__ == "__main__":
    main()
