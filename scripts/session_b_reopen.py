from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from demo_data import t1_evidence
from evidencebound.service import reopen_memory

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("memory_id")
    args = parser.parse_args()
    result = reopen_memory(args.memory_id, t1_evidence(), policy_version_t1="policy-1", now=datetime(2026, 8, 13, 13, 0, tzinfo=timezone.utc))
    print(json.dumps({"session": "B", "memory_id": result.memory_id, "historical_integrity": result.historical_integrity, "current_applicability": result.current_applicability, "diffs": [d.__dict__ for d in result.diffs]}, sort_keys=True))
