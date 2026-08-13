from __future__ import annotations

import json
from typing import Any

CANONICALIZATION_VERSION = "eb-c14n-v1"


def canonical_json(value: Any) -> str:
    """Return stable UTF-8 JSON used by EvidenceBound integrity hashes."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
