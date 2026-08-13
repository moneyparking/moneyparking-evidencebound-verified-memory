import os

from evidencebound.migrate import migrate
from evidencebound.repository import CockroachRepository, INCIDENT_TABLE, MEMORY_TABLE, VECTOR_INDEX
from evidencebound.service import EvidenceBoundService


class AcceptanceModel:
    def embed(self, text):
        return [1.0] + [0.0] * 1023

    def explain(self, result):
        return "Acceptance stub; Bedrock is verified separately."


def main():
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import make_conninfo

    url = make_conninfo(
        os.environ["COCKROACH_DATABASE_URL"],
        sslmode="verify-full",
        sslrootcert=os.environ["PGSSLROOTCERT"],
    )
    migration = migrate(url)
    with psycopg.connect(url, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = current_schema() AND table_type = 'BASE TABLE'"
        )
        tables = {row[0] for row in cur.fetchall()}
        assert {MEMORY_TABLE, INCIDENT_TABLE}.issubset(tables)
        cur.execute(sql.SQL("SHOW CREATE TABLE {}").format(sql.Identifier(INCIDENT_TABLE)))
        schema = "\n".join(str(part) for row in cur.fetchall() for part in row)
        assert "VECTOR(1024)" in schema.upper()

    session_a = EvidenceBoundService(CockroachRepository(url), AcceptanceModel())
    saved = session_a.save_t0()
    assert saved["session_a_ended"] is True
    memory_id = saved["memory_id"]
    del session_a

    session_b = EvidenceBoundService(CockroachRepository(url), AcceptanceModel())
    reopened = session_b.reopen_t1(memory_id)
    assert reopened["fresh_session"] is True
    assert reopened["session_a_id"] != reopened["session_b_id"]
    assert reopened["historical_integrity"] == "VERIFIED"
    assert reopened["historical_decision"] == "VERIFIED"
    assert reopened["current_applicability"] == "REVIEW_REQUIRED"
    changes = {item["change"] for item in reopened["changes"]}
    assert {"UNCHANGED", "CHANGED", "STALE", "NEW"}.issubset(changes)
    assert reopened["recalled_incidents"]
    assert reopened["tooling"]["vector_index"] == VECTOR_INDEX

    print(
        "COCKROACH_BEHAVIORAL_ACCEPTANCE=PASS "
        f"migration={migration} integrity={reopened['historical_integrity']} "
        f"applicability={reopened['current_applicability']} "
        f"changes={','.join(sorted(changes))} vector_index={VECTOR_INDEX} "
        "bedrock=separate_gate"
    )


if __name__ == "__main__":
    main()
