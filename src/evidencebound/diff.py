from __future__ import annotations

from datetime import datetime, timezone

from .integrity import evidence_hash
from .models import DiffEntry, EvidenceItem


def _parse_time(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def compare_evidence(
    historical: tuple[EvidenceItem, ...],
    current: tuple[EvidenceItem, ...],
    *,
    now: datetime | None = None,
) -> tuple[DiffEntry, ...]:
    now = now or datetime.now(timezone.utc)
    previous = {item.evidence_key: item for item in historical}
    latest = {item.evidence_key: item for item in current}
    result: list[DiffEntry] = []

    for key in sorted(set(previous) | set(latest)):
        old = previous.get(key)
        new = latest.get(key)
        if old is None and new is not None:
            result.append(DiffEntry(key, "NEW", None, evidence_hash(new), "new evidence at T1"))
            continue
        if old is not None and new is None:
            state = "MISSING" if old.expected else "CHANGED"
            result.append(DiffEntry(key, state, evidence_hash(old), None, "expected evidence unavailable at T1"))
            continue
        assert old is not None and new is not None
        old_hash = evidence_hash(old)
        new_hash = evidence_hash(new)
        if new.valid_until and _parse_time(new.valid_until) < now:
            result.append(DiffEntry(key, "STALE", old_hash, new_hash, "current evidence validity expired"))
            continue
        if new.refutes_evidence_hash == old_hash and new.provenance_valid and new_hash != old_hash:
            result.append(DiffEntry(key, "REFUTED", old_hash, new_hash, "valid T1 evidence explicitly contradicts T0 claim"))
            continue
        if new_hash == old_hash:
            result.append(DiffEntry(key, "UNCHANGED", old_hash, new_hash, "canonical evidence is identical"))
        else:
            result.append(DiffEntry(key, "CHANGED", old_hash, new_hash, "material canonical evidence difference"))
    return tuple(result)
