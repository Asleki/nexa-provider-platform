import pytest

from registries.nngla.spatial_fabric.bundle19a.contracts import GeometryRole
from registries.nngla.spatial_fabric.bundle19a.execution import execute_place_spatialization
from registries.nngla.spatial_fabric.bundle19a.persistence import MemoryPlaceSpatialRepository, point_geojson
from registries.nngla.spatial_fabric.bundle19a.siting import derive_place_reference_points


def test_memory_execution_maps_all_700_places_and_persists_independent_geometry_roles():
    repo = MemoryPlaceSpatialRepository()
    receipt = execute_place_spatialization(repo, submitter_actor_id="actor:submitter", approver_actor_id="actor:approver")
    assert receipt.status == "APPLIED"
    assert receipt.selected_place_count == receipt.associated_place_count == 700
    assert receipt.geometry_insert_count == len(repo.geometries) == 1119
    assert receipt.footprint_insert_count == 419
    assert receipt.point_only_count == 281
    assert all(r["spatial_assignment_status"] == "AUTHORITATIVE_GEOMETRY_ASSIGNED" for r in repo.places.values())
    assert all(r["geometry_reference"] for r in repo.places.values())
    assert len(repo.execution_items[receipt.execution_id]) == 700
    for place_id, place in repo.places.items():
        geom = repo.geometries[place["geometry_reference"]]
        assert geom["subject_id"] == place_id
        assert geom["geometry_role_code"] == GeometryRole.PLACE_REFERENCE_POINT.value


def test_execution_is_idempotent_by_fingerprint():
    repo = MemoryPlaceSpatialRepository()
    first = execute_place_spatialization(repo, submitter_actor_id="actor:s", approver_actor_id="actor:a")
    geometry_ids = set(repo.geometries)
    replay = execute_place_spatialization(repo, submitter_actor_id="actor:s", approver_actor_id="actor:a")
    assert replay.status == "REUSED" and replay.replayed is True
    assert replay.execution_id == first.execution_id
    assert set(repo.geometries) == geometry_ids


def test_preflight_fails_closed_on_already_mapped_place():
    repo = MemoryPlaceSpatialRepository()
    repo.places["NG-PLC-000001"]["spatial_assignment_status"] = "AUTHORITATIVE_GEOMETRY_ASSIGNED"
    repo.places["NG-PLC-000001"]["geometry_reference"] = "NG-GEO-999999"
    with pytest.raises(RuntimeError):
        execute_place_spatialization(repo, submitter_actor_id="actor:s", approver_actor_id="actor:a")


def test_transaction_rolls_back_place_geometry_and_allocator_on_failure():
    repo = MemoryPlaceSpatialRepository()
    point = derive_place_reference_points()[0]
    occupied_before = set(repo.allocator._occupied)
    next_before = repo.allocator._next
    with pytest.raises(RuntimeError):
        with repo.transaction():
            gid = repo.reserve_geometry(point.place_id, GeometryRole.PLACE_REFERENCE_POINT, point.geometry_reservation_key)
            repo.persist_geometry(
                geometry_id=gid, subject_id=point.place_id, role=GeometryRole.PLACE_REFERENCE_POINT,
                payload=point_geojson(point), source_candidate_id=point.reference_candidate_id,
            )
            repo.associate_place_reference(place_id=point.place_id, source_place_code=point.source_place_code, geometry_id=gid)
            raise RuntimeError("injected rollback")
    assert repo.places[point.place_id]["geometry_reference"] is None
    assert repo.geometries == {}
    assert repo.allocator._occupied == occupied_before
    assert repo.allocator._next == next_before


def test_submitter_and_approver_must_be_distinct():
    repo = MemoryPlaceSpatialRepository()
    with pytest.raises(ValueError):
        execute_place_spatialization(repo, submitter_actor_id="actor:x", approver_actor_id="actor:x")
