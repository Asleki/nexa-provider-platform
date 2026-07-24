import pytest
from shared.audit.audit_api_operation import AuditApiOperation
from shared.audit.audit_errors import AuditApiValidationError

def test_values_are_stable():
    assert [x.value for x in AuditApiOperation] == [
        "query", "validate_integrity", "export"
    ]

def test_parse_accepts_enum_and_normalized_string():
    assert AuditApiOperation.parse(AuditApiOperation.QUERY) is AuditApiOperation.QUERY
    assert AuditApiOperation.parse(" EXPORT ") is AuditApiOperation.EXPORT

@pytest.mark.parametrize("value", [None, 1, "", "unknown"])
def test_parse_rejects_invalid_values(value):
    with pytest.raises(AuditApiValidationError):
        AuditApiOperation.parse(value)
