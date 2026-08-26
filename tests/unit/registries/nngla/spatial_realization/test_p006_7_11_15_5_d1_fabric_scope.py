from registries.nngla.spatial_realization.contracts import FabricLevel
from registries.nngla.spatial_realization.fabric_scope import (
    build_recursive_child_scope,
    resolve_initial_fabric_scope,
)


def test_delivery1_northgate_resolves_complete_city_district_fabric_and_excludes_overlay():
    scope = resolve_initial_fabric_scope("NG-PLC-000086")
    assert scope.parent.subject_id == "NG-ADM-000032"
    assert scope.level is FabricLevel.CITY_DISTRICTS
    assert [item.subject_id for item in scope.exhaustive_siblings] == [
        "NG-ADM-000036", "NG-ADM-000037", "NG-ADM-000038", "NG-ADM-000039",
        "NG-ADM-000040", "NG-ADM-000041", "NG-ADM-000042", "NG-ADM-000043",
    ]
    assert [item.subject_id for item in scope.overlays] == ["NG-ADM-000053"]


def test_delivery1_silvermere_material_parent_failure_escalates_first_scope_to_nyara_region():
    scope = resolve_initial_fabric_scope(
        "NG-PLC-000258",
        material_rule_codes=("CITY_PARENT_CONTAINMENT_FAILED", "CITY_DISTRICT_OVERSHOOT"),
    )
    assert scope.parent.subject_id == "NG-ADM-000004"
    assert scope.level is FabricLevel.REGION_LOCAL_AREAS
    assert [(item.subject_id, item.administrative_type_code) for item in scope.exhaustive_siblings] == [
        ("NG-ADM-000078", "CITY"),
        ("NG-ADM-000079", "MUNICIPALITY"),
        ("NG-ADM-000080", "MUNICIPALITY"),
        ("NG-ADM-000081", "MUNICIPALITY"),
    ]
    assert scope.overlays == ()


def test_delivery1_recursive_silvermere_child_scope_binds_qualified_parent_hash_and_keeps_lakeport_overlay_non_exhaustive():
    region_scope = resolve_initial_fabric_scope(
        "NG-PLC-000258", material_rule_codes=("CITY_PARENT_CONTAINMENT_FAILED",)
    )
    child = build_recursive_child_scope(
        region_scope,
        "NG-ADM-000078",
        qualified_parent_geometry_sha256="a" * 64,
        qualified_parent_candidate_id="fabric-candidate:test:silvermere",
    )
    assert child.parent.subject_id == "NG-ADM-000078"
    assert child.parent.geometry_checksum_sha256 == "a" * 64
    assert child.parent.source_candidate_id == "fabric-candidate:test:silvermere"
    assert child.level is FabricLevel.CITY_DISTRICTS
    assert len(child.exhaustive_siblings) == 8
    assert [item.subject_id for item in child.overlays] == ["NG-ADM-000099"]
    assert child.input_digest != region_scope.input_digest


def test_delivery1_scope_fingerprint_is_repeatable():
    a = resolve_initial_fabric_scope("NG-PLC-000086")
    b = resolve_initial_fabric_scope("NG-PLC-000086")
    assert a.input_digest == b.input_digest
    assert a.fingerprint == b.fingerprint
