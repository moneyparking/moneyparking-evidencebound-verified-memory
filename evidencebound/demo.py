from datetime import datetime, timedelta, timezone


def _ts(value):
    return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def demo_evidence(now=None):
    base = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    t1 = base + timedelta(hours=2)
    common = {'source_uri': 'urn:evidencebound:controlled-demo:v1', 'source_class': 'controlled_demo', 'source_authority': 'evidencebound_demo_fixture', 'claim_type': 'factual_assertion', 'observed_at': _ts(base)}
    t0 = [
        {**common, 'evidence_id': 'review-policy', 'claim': 'Review policy requires cited provenance', 'value': True, 'valid_until': None},
        {**common, 'evidence_id': 'availability-status', 'claim': 'Controlled availability state', 'value': 'available', 'valid_until': _ts(base + timedelta(hours=6))},
        {**common, 'evidence_id': 'weather-window', 'claim': 'Controlled freshness window', 'value': 'clear', 'valid_until': _ts(base + timedelta(hours=1))},
    ]
    current = [
        dict(t0[0]),
        {**common, 'evidence_id': 'availability-status', 'claim': 'Controlled availability state', 'value': 'unavailable', 'valid_until': _ts(base + timedelta(hours=6)), 'observed_at': _ts(t1)},
        dict(t0[2]),
        {**common, 'evidence_id': 'lineup-confirmation', 'claim': 'Controlled new confirmation', 'value': 'published', 'valid_until': _ts(t1 + timedelta(hours=1)), 'observed_at': _ts(t1)},
    ]
    return t0, current, t1
