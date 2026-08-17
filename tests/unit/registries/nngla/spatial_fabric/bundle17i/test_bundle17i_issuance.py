from datetime import date
import pytest
from registries.nngla.spatial_fabric.bundle17i import (
    MemoryTitleReferenceAllocator, form_title_issuance_candidate, issue_qualified_title,
    load_title_series, qualify_title_issuance,
)


def test_reserved_title_identity_is_reused_at_legal_issuance_not_regenerated():
    reservation = MemoryTitleReferenceAllocator().reserve(load_title_series(), idempotency_key="issue:1")
    candidate = form_title_issuance_candidate(
        reservation, parcel_id="NV-01-001-0001", title_type_code="FREEHOLD_TITLE", tenure_type_code="FREEHOLD",
        holder_reference="citizen:000001", source_reference="test:issuance",
    )
    result = qualify_title_issuance(reservation, candidate)
    assert result.issuance_ready
    title = issue_qualified_title(reservation, candidate, effective_on=date(2026,8,17), source_reference="test:issued")
    assert title.title_id == reservation.reserved_title_id
    assert title.parcel_id == "NV-01-001-0001"


def test_title_type_and_tenure_must_match_governed_vocabularies():
    reservation = MemoryTitleReferenceAllocator().reserve(load_title_series(), idempotency_key="issue:2")
    candidate = form_title_issuance_candidate(
        reservation, parcel_id="NV-01-001-0001", title_type_code="FREEHOLD_TITLE", tenure_type_code="LEASEHOLD",
        holder_reference="citizen:000002", source_reference="test:mismatch",
    )
    result = qualify_title_issuance(reservation, candidate)
    assert not result.issuance_ready
    assert "TENURE_TYPE_INVALID_OR_MISMATCH" in result.findings
    with pytest.raises(ValueError):
        issue_qualified_title(reservation, candidate, effective_on=date(2026,8,17), source_reference="test:bad")
