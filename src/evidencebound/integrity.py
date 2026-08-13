from __future__ import annotations

import hashlib
from typing import Any

from .canonical import canonical_json
from .models import EvidenceItem, Snapshot


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def evidence_hash(item: EvidenceItem) -> str:
    return sha256_hex(item.canonical_dict())


def compute_snapshot_hash(snapshot: Snapshot) -> str:
    return sha256_hex(snapshot.canonical_dict())


def verify_snapshot(snapshot: Snapshot, stored_hash: str) -> str:
    return "VERIFIED" if compute_snapshot_hash(snapshot) == stored_hash else "FAIL_CLOSED"
