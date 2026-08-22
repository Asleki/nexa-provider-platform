from registries.nngla.spatial_fabric.bundle17n.contracts import RuntimeCommand, RuntimePrincipal
from registries.nngla.spatial_fabric.bundle17n.dispatcher import RuntimeCommandDispatcher
from registries.nngla.spatial_fabric.bundle19a.contracts import GeometryRole
from registries.nngla.spatial_fabric.bundle19a.handlers import register_bundle19a_runtime_handlers
from registries.nngla.spatial_fabric.bundle19a.persistence import MemoryPlaceSpatialRepository, point_geojson
from registries.nngla.spatial_fabric.bundle19a.siting import derive_place_reference_points


def test_bundle19a_plugs_existing_geometry_associate_command_without_allocating_identity():
    repo = MemoryPlaceSpatialRepository()
    point = derive_place_reference_points()[0]
    gid = repo.reserve_geometry(point.place_id, GeometryRole.PLACE_REFERENCE_POINT, point.geometry_reservation_key)
    repo.persist_geometry(
        geometry_id=gid, subject_id=point.place_id, role=GeometryRole.PLACE_REFERENCE_POINT,
        payload=point_geojson(point), source_candidate_id=point.reference_candidate_id,
    )
    allocated_before = set(repo.geometries)
    dispatcher = register_bundle19a_runtime_handlers(RuntimeCommandDispatcher(), repo)
    command = RuntimeCommand(
        command_code="ASSOCIATE_GEOMETRY", command_version=1, runtime_mode="production",
        effect_scope="SHARED_REFERENCE", principal_id="actor:nngla", idempotency_key="bundle19a-handler-test",
        correlation_id="corr:bundle19a-handler-test", payload={"subject_id": point.place_id, "geometry_id": gid},
    )
    principal = RuntimePrincipal("actor:nngla", "production", frozenset({"nngla.associate_geometry"}))
    receipt = dispatcher.execute(command, principal, approval_granted=True)
    assert receipt.status.value == "COMPLETED"
    assert dict(receipt.references) == {"geometry_id": gid, "place_id": point.place_id}
    assert set(repo.geometries) == allocated_before
    assert repo.places[point.place_id]["geometry_reference"] == gid
