import os

from evidencebound.migrate import migrate
from evidencebound.repository import CockroachRepository, INCIDENT_TABLE, MEMORY_TABLE, VECTOR_INDEX
from evidencebound.service import EvidenceBoundService

AGENT_SKILL = "cockroachlabs/cockroachdb-skills/skills/cockroachdb-query-and-schema-design/cockroachdb-sql/SKILL.md"
AGENT_SKILL_BLOB_SHA = "2690e972a99fe632818f0fc1a434080bc7acd917"


class AcceptanceModel:
    def embed(self, text):
        return [1.0] + [0.0] * 1023

    def explain(self, result):
        return "Acceptance stub; Bedrock is verified separately."


def _vector(values):
    return "[" + ",".join(f"{value:.9g}" for value in values) + "]"


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

        # CockroachDB Agent Skill cockroachdb-sql requires EXPLAIN validation
        # for generated SQL when a live connection is available.
        cur.execute(
            sql.SQL(
                "EXPLAIN SELECT snapshot FROM {} WHERE memory_id = gen_random_uuid() "
                "ORDER BY created_at DESC, id DESC LIMIT 1"
            ).format(sql.Identifier(MEMORY_TABLE))
        )
        memory_plan = cur.fetchall()
        assert memory_plan

        probe_vector = _vector(AcceptanceModel().embed("vector-plan-probe"))
        cur.execute(
            sql.SQL(
                "EXPLAIN SELECT incident_text FROM {} "
                "ORDER BY embedding <-> %s::VECTOR LIMIT 3"
            ).format(sql.Identifier(INCIDENT_TABLE)),
            (probe_vector,),
        )
        vector_plan = cur.fetchall()
        assert vector_plan

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
        "COCKROACH_AGENT_SKILL_ACCEPTANCE=PASS "
        f"skill={AGENT_SKILL} blob_sha={AGENT_SKILL_BLOB_SHA} "
        "memory_explain=true vector_explain=true"
    )
    print(
        "COCKROACH_BEHAVIORAL_ACCEPTANCE=PASS "
        f"migration={migration} integrity={reopened['historical_integrity']} "
        f"applicability={reopened['current_applicability']} "
        f"changes={','.join(sorted(changes))} vector_index={VECTOR_INDEX} "
        "bedrock=separate_gate"
    )


if __name__ == "__main__":
    main()
