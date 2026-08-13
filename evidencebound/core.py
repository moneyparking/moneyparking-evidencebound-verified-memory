from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Iterable

TRUSTED_DECISION_VERIFIED = "VERIFIED"
INTEGRITY_VERIFIED = "VERIFIED"
FAIL_CLOSED = "FAIL_CLOSED"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
CHANGE_UNCHANGED = "UNCHANGED"
CHANGE_NEW = "NEW"
CHANGE_CHANGED = "CHANGED"
CHANGE_STALE = "STALE"
CHANGE_MISSING = "MISSING"
CHANGE_REFUTED = "REFUTED"
REVIEW_CHANGE_TYPES = {CHANGE_NEW, CHANGE_CHANGED, CHANGE_STALE, CHANGE_MISSING, CHANGE_REFUTED}


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    raise TypeError(f"Unsupported canonical type: {type(value)!r}")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_json_default)


def sha256_hex(value: Any) -> str:
    payload = value if isinstance(value, str) else canonical_json(value)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_timestamp(value: str | datetime) -> str:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalized_evidence(item: dict[str, Any]) -> dict[str, Any]:
    required = {"evidence_id", "claim", "value", "source_uri", "source_class", "source_authority", "claim_type", "observed_at", "valid_until"}
    missing = required - item.keys()
    if missing:
        raise ValueError(f"Evidence item missing fields: {sorted(missing)}")
    normalized = dict(item)
    normalized["observed_at"] = normalize_timestamp(normalized["observed_at"])
    normalized["valid_until"] = normalize_timestamp(normalized["valid_until"]) if normalized["valid_until"] is not None else None
    normalized["contradicts_evidence_id"] = normalized.get("contradicts_evidence_id")
    return normalized


def normalize_evidence(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = [_normalized_evidence(item) for item in items]
    ids = [item["evidence_id"] for item in normalized]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate evidence_id")
    return sorted(normalized, key=lambda item: item["evidence_id"])


def build_snapshot(*, memory_id: str, session_id: str, decision_state: str, evidence: Iterable[dict[str, Any]], policy_version: str, proof_version: str, created_at: str | datetime, previous_record_hash: str | None = None) -> dict[str, Any]:
    normalized = normalize_evidence(evidence)
    snapshot: dict[str, Any] = {"memory_id": memory_id, "session_id": session_id, "decision_state": decision_state, "policy_version": policy_version, "proof_version": proof_version, "created_at": normalize_timestamp(created_at), "previous_record_hash": previous_record_hash, "evidence": normalized}
    snapshot["evidence_hash"] = sha256_hex(normalized)
    snapshot["record_hash"] = sha256_hex(snapshot)
    return snapshot


def verify_snapshot(snapshot: dict[str, Any], *, expected_policy_version: str | None = None, expected_proof_version: str | None = None) -> dict[str, str]:
    try:
        provided_record_hash = str(snapshot["record_hash"])
        provided_evidence_hash = str(snapshot["evidence_hash"])
        normalized_evidence = normalize_evidence(snapshot["evidence"])
    except (KeyError, TypeError, ValueError) as exc:
        return {"state": FAIL_CLOSED, "reason": f"malformed_snapshot:{type(exc).__name__}"}
    if sha256_hex(normalized_evidence) != provided_evidence_hash:
        return {"state": FAIL_CLOSED, "reason": "evidence_hash_mismatch"}
    payload = dict(snapshot)
    payload["evidence"] = normalized_evidence
    payload.pop("record_hash", None)
    if sha256_hex(payload) != provided_record_hash:
        return {"state": FAIL_CLOSED, "reason": "record_hash_mismatch"}
    if expected_policy_version and snapshot.get("policy_version") != expected_policy_version:
        return {"state": FAIL_CLOSED, "reason": "policy_version_mismatch"}
    if expected_proof_version and snapshot.get("proof_version") != expected_proof_version:
        return {"state": FAIL_CLOSED, "reason": "proof_version_mismatch"}
    return {"state": INTEGRITY_VERIFIED, "reason": "hashes_and_versions_match"}


def _is_stale(item: dict[str, Any], evaluated_at: str | datetime) -> bool:
    valid_until = item.get("valid_until")
    if valid_until is None:
        return False
    return datetime.fromisoformat(normalize_timestamp(valid_until).replace("Z", "+00:00")) < datetime.fromisoformat(normalize_timestamp(evaluated_at).replace("Z", "+00:00"))


def _comparison_payload(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if key not in {"valid_until", "contradicts_evidence_id"}}


def _is_valid_refutation(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    return bool(previous.get("claim_type") == "factual_assertion" and current.get("claim_type") == "factual_assertion" and current.get("contradicts_evidence_id") == previous.get("evidence_id") and current.get("source_authority") == previous.get("source_authority") and current.get("claim") == previous.get("claim"))


def diff_evidence(historical: Iterable[dict[str, Any]], current: Iterable[dict[str, Any]], *, evaluated_at: str | datetime) -> list[dict[str, Any]]:
    before = {item["evidence_id"]: item for item in normalize_evidence(historical)}
    after = {item["evidence_id"]: item for item in normalize_evidence(current)}
    results: list[dict[str, Any]] = []
    for evidence_id in sorted(before):
        previous = before[evidence_id]
        present = after.get(evidence_id)
        if present is None:
            change = CHANGE_MISSING
        elif _is_stale(present, evaluated_at):
            change = CHANGE_STALE
        elif _comparison_payload(previous) == _comparison_payload(present):
            change = CHANGE_UNCHANGED
        elif _is_valid_refutation(previous, present):
            change = CHANGE_REFUTED
        else:
            change = CHANGE_CHANGED
        results.append({"evidence_id": evidence_id, "change": change, "historical_hash": sha256_hex(previous), "current_hash": sha256_hex(present) if present is not None else None})
    for evidence_id in sorted(set(after) - set(before)):
        present = after[evidence_id]
        results.append({"evidence_id": evidence_id, "change": CHANGE_STALE if _is_stale(present, evaluated_at) else CHANGE_NEW, "historical_hash": None, "current_hash": sha256_hex(present)})
    return results


def current_applicability(integrity_state: str, changes: Iterable[dict[str, Any]]) -> str:
    if integrity_state != INTEGRITY_VERIFIED:
        return FAIL_CLOSED
    if any(change["change"] in REVIEW_CHANGE_TYPES for change in changes):
        return REVIEW_REQUIRED
    return TRUSTED_DECISION_VERIFIED
