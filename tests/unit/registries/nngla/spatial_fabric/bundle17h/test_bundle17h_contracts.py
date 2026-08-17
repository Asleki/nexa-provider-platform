import pytest
from registries.nngla.spatial_fabric.bundle17h import (
    AddressSeriesDefinition, AddressableSiteCandidate, SiteLifecycleStage,
    allocation_policies, site_lifecycle_rows, structure_reference_type_rows,
)


def test_bundle17h_policy_vocabulary_has_all_locked_address_modes_and_fail_closed_collisions():
    policies = allocation_policies()
    assert {p.policy_code.value for p in policies} == {"CONTINUOUS","LOCAL_RESET","SEGMENT_RESET","ODD_EVEN","SEQUENTIAL","CUSTOM_GOVERNED"}
    assert all(p.same_scope_collision_policy == "FAIL_CLOSED" for p in policies)
    assert all(p.duplicate_visible_number_cross_scope_allowed for p in policies)


def test_bundle17h_site_lifecycle_never_claims_construction_or_residence_ownership():
    rows = site_lifecycle_rows()
    assert len(rows) == 6
    assert all(row["construction_state_owned_by_nngla"] == "false" for row in rows)
    assert all(row["citizen_residence_owned_by_nngla"] == "false" for row in rows)
    assert len(structure_reference_type_rows()) >= 9


def test_address_series_requires_road_not_competing_street_identity_and_odd_even_step_two():
    with pytest.raises(ValueError):
        AddressSeriesDefinition("addrseries:nngla:x", "street:1", "", "SEQUENTIAL", "ROAD", "street:1", 1, 1, "INTEGER", "NONE", False)
    with pytest.raises(ValueError):
        AddressSeriesDefinition("addrseries:nngla:x", "NG-RD-000001", "", "ODD_EVEN", "ROAD", "NG-RD-000001", 1, 1, "INTEGER", "ODD", False)
    series = AddressSeriesDefinition("addrseries:nngla:x", "NG-RD-000001", "", "ODD_EVEN", "ROAD", "NG-RD-000001", 1, 2, "INTEGER", "ODD", False)
    assert series.sequence_step == 2


def test_site_identity_is_opaque_stable_and_does_not_masquerade_as_parcel_or_address():
    site = AddressableSiteCandidate("site:nngla:abc", "NG-PLC-000001", "NG-ADM-000001", "NV-01-001-0001", "NG-GEO-000001", "NG-RD-000001", "roadseg:nngla:abc", SiteLifecycleStage.CANDIDATE, "simulation", "test")
    assert not site.site_id.startswith("NG-ADR-")
    assert not site.site_id.startswith("NV-")
