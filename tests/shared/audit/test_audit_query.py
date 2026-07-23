from datetime import datetime, timezone
import pytest
from shared.audit import AuditAction, AuditOutcome, AuditQuery, AuditQueryValidationError

def test_query_normalizes_text_and_time():
    query = AuditQuery(
        actor_id=" OP-1 ",
        action=AuditAction.READ,
        outcome=AuditOutcome.SUCCESS,
        recorded_from=datetime(2026, 7, 1, tzinfo=timezone.utc),
    )
    assert query.actor_id == "OP-1"
    assert query.action is AuditAction.READ
    assert not query.is_unfiltered

def test_empty_query_is_unfiltered():
    assert AuditQuery().is_unfiltered

def test_invalid_range_is_rejected():
    with pytest.raises(AuditQueryValidationError):
        AuditQuery(
            recorded_from=datetime(2026, 7, 2, tzinfo=timezone.utc),
            recorded_to=datetime(2026, 7, 1, tzinfo=timezone.utc),
        )
