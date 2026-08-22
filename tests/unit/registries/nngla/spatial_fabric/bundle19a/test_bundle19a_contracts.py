import pytest

from registries.nngla.spatial_fabric.bundle19a.contracts import (
    GeometryRole, PlaceSpatialExecutionReceipt, SpatialOutcomeStatus,
)


def valid_receipt(**overrides):
    data = dict(
        execution_id="nnglarun:place-spatial:" + "a" * 32,
        fingerprint_sha256="b" * 64,
        database_name="novegeo",
        environment_name="test",
        repository_revision="c" * 40,
        submitter_actor_id="actor:submitter",
        approver_actor_id="actor:approver",
        selected_place_count=700,
        associated_place_count=700,
        geometry_insert_count=1119,
        footprint_insert_count=419,
        point_only_count=281,
        status="APPLIED",
        replayed=False,
    )
    data.update(overrides)
    return PlaceSpatialExecutionReceipt(**data)


def test_geometry_roles_are_semantically_distinct():
    assert GeometryRole.PLACE_REFERENCE_POINT.value != GeometryRole.SETTLEMENT_FOOTPRINT.value
    assert "ADMINISTRATIVE" not in {x.value for x in GeometryRole}


def test_execution_receipt_requires_exact_bundle_counts():
    assert valid_receipt().geometry_insert_count == 1119
    with pytest.raises(ValueError):
        valid_receipt(selected_place_count=699, associated_place_count=699)
    with pytest.raises(ValueError):
        valid_receipt(geometry_insert_count=1118)
    with pytest.raises(ValueError):
        valid_receipt(point_only_count=280)


def test_execution_receipt_enforces_actor_separation_and_replay_semantics():
    with pytest.raises(ValueError):
        valid_receipt(approver_actor_id="actor:submitter")
    reused = valid_receipt(status="REUSED", replayed=True)
    assert reused.replayed is True
    with pytest.raises(ValueError):
        valid_receipt(status="REUSED", replayed=False)
