from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace

from evidencebound.integrity import verify_snapshot
from evidencebound.repository import connect, load_snapshot, similar_incidents


def _run_json(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        print(completed.stdout, file=sys.stderr, end="")
        print(completed.stderr, file=sys.stderr, end="")
        raise SystemExit(completed.returncode)
    return json.loads(completed.stdout.strip().splitlines()[-1])


def run() -> None:
    t0 = _run_json([sys.executable, "scripts/session_a_save.py"])
    memory_id = str(t0["memory_id"])
    t1 = _run_json([sys.executable, "scripts/session_b_reopen.py", memory_id])
    assert t0["decision"] == "VERIFIED"
    assert t1["historical_integrity"] == "VERIFIED"
    assert t1["current_applicability"] == "REVIEW_REQUIRED"
    states = {d["state"] for d in t1["diffs"]}
    assert {"UNCHANGED", "CHANGED", "STALE", "NEW"}.issubset(states)

    stored_snapshot, stored_hash = load_snapshot(memory_id)
    altered_snapshot = replace(stored_snapshot, decision_reason="altered historical payload")
    altered_integrity = verify_snapshot(altered_snapshot, stored_hash)
    assert altered_integrity == "FAIL_CLOSED"

    recalled = similar_incidents(["changed", "stale"], limit=50)
    assert recalled and any(item["memory_id"] == memory_id for item in recalled)
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SHOW CREATE TABLE verification_incidents")
        assert "VECTOR" in "\n".join(str(row) for row in cur.fetchall()).upper()
        cur.execute("SHOW INDEXES FROM verification_incidents")
        assert any("verification_incidents_signature_idx" in str(row) for row in cur.fetchall())
    print(
        json.dumps(
            {
                "cockroach_live_acceptance": "PASS",
                "memory_id": memory_id,
                "session_a_ended_before_b": True,
                "historical_integrity": t1["historical_integrity"],
                "current_applicability": t1["current_applicability"],
                "diff_states": sorted(states),
                "db_backed_altered_snapshot_integrity": altered_integrity,
                "vector_recall_count": len(recalled),
                "vector_index": "verification_incidents_signature_idx",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    run()
