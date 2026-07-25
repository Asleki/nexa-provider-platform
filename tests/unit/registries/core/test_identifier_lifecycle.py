import pytest
from registries.core import IdentifierLifecycle


def test_identifier_lifecycle_members_are_exact_stable_and_unique():
    assert [(x.name, x.value) for x in IdentifierLifecycle] == [
        ("REQUESTED", "requested"), ("VALIDATED", "validated"),
        ("ISSUED", "issued"), ("ACTIVE", "active"),
        ("SUSPENDED", "suspended"), ("RETIRED", "retired"),
    ]
    assert len({x.value for x in IdentifierLifecycle}) == 6
    assert isinstance(IdentifierLifecycle.ACTIVE, str)


def test_unknown_lifecycle_is_rejected():
    with pytest.raises(ValueError):
        IdentifierLifecycle("revoked")
