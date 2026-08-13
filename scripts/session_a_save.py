from __future__ import annotations

import json
from demo_data import t0_snapshot
from evidencebound.repository import apply_migrations, connect, save_snapshot

if __name__ == "__main__":
    with connect() as conn:
        apply_migrations(conn)
    memory_id = save_snapshot(t0_snapshot())
    print(json.dumps({"session": "A", "memory_id": memory_id, "decision": "VERIFIED"}))
