from registries.nngla.spatial_realization.contracts import FabricInputRole
from registries.nngla.spatial_realization.source import (
    administrative_children,
    administrative_geometry_payload,
    administrative_input,
    administrative_row,
)


def test_delivery1_frozen_admin_input_is_hash_bound_and_root_neutral():
    row = administrative_row("NG-ADM-000032")
    item = administrative_input("NG-ADM-000032", FabricInputRole.PARENT)
    assert row.canonical_name == "Northgate"
    assert item.canonical_name == row.canonical_name
    assert item.source_candidate_id == row.boundary_candidate_id
    assert len(item.geometry_checksum_sha256) == 64
    assert administrative_geometry_payload("NG-ADM-000032").startswith('{"coordinates"')


def test_delivery1_direct_children_preserve_city_district_and_overlay_roles_for_later_scope_resolution():
    children = administrative_children("NG-ADM-000032")
    assert len(children) == 9
    assert sum(row.administrative_type_code == "CITY_DISTRICT" for row in children) == 8
    assert sum(row.administrative_type_code == "INDUSTRIAL_ZONE" for row in children) == 1


def test_delivery1_region_children_include_city_and_municipality_peers():
    children = administrative_children("NG-ADM-000004")
    assert [(row.administrative_area_id, row.administrative_type_code) for row in children] == [
        ("NG-ADM-000078", "CITY"),
        ("NG-ADM-000079", "MUNICIPALITY"),
        ("NG-ADM-000080", "MUNICIPALITY"),
        ("NG-ADM-000081", "MUNICIPALITY"),
    ]
