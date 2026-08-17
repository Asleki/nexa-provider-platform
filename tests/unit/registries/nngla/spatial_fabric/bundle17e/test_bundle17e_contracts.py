from dataclasses import replace
import pytest

from registries.nngla.spatial_fabric.bundle17e.contracts import (
    SpatialCanonicalCrosswalk,
    SpatialExecutionReceipt,
    SpatialMigrationAction,
    TargetSpatialSnapshot,
)


def test_migration_action_vocabulary_is_complete_and_fail_closed_capable():
    assert {item.value for item in SpatialMigrationAction} == {
        "INSERT_NEW", "RECONCILE_ONLY", "ASSOCIATE_ONLY", "REUSE_CANONICAL",
        "SUPERSEDE_GEOMETRY", "QUARANTINE", "NO_ACTION",
    }


def test_canonical_crosswalk_requires_governed_shared_reference_identity():
    row = SpatialCanonicalCrosswalk(
        "crosswalk:nngla:" + "a" * 64,
        "coordcand:nngla:" + "b" * 64,
        "NG-SPT-000001",
        1,
        "EXACT",
        "EXISTING_GOVERNED_SOURCE_IDENTITY",
        "dataset:novegeo:spatial-fabric:coordinate-candidates",
        "2",
        "1" * 64,
        "2" * 64,
        "production",
        "SHARED_REFERENCE",
        "QUALIFIED_FOR_PERSISTENCE",
    )
    assert row.canonical_spatial_point_id == "NG-SPT-000001"
    with pytest.raises(ValueError):
        replace(row, runtime_mode="simulation")


def test_target_snapshot_digest_changes_with_target_state():
    empty = TargetSpatialSnapshot("db", "dev")
    occupied = TargetSpatialSnapshot("db", "dev", occupied_spatial_ids=frozenset({"NG-SPT-000001"}))
    assert empty.digest != occupied.digest


def test_execution_receipt_enforces_governance_separation_and_count_reconciliation():
    kwargs = dict(
        execution_id="nnglarun:spatial:" + "c" * 64,
        plan_id="P006.7.11.7.7-8-BUNDLE17E",
        plan_version=1,
        fingerprint="d" * 64,
        content_fingerprint="e" * 64,
        database_name="db",
        environment_name="dev",
        runtime_mode="production",
        repository_revision="rev",
        source_sha256="f" * 64,
        submitter_actor_id="actor:a",
        approver_actor_id="actor:b",
        selected_count=1,
        inserted_count=1,
        reused_count=0,
        quarantined_count=0,
        failed_count=0,
        status="APPLIED",
        started_at="2026-08-17T00:00:00+00:00",
        completed_at="2026-08-17T00:00:01+00:00",
        items=(),
    )
    assert SpatialExecutionReceipt(**kwargs).status == "APPLIED"
    with pytest.raises(ValueError):
        SpatialExecutionReceipt(**{**kwargs, "approver_actor_id": "actor:a"})
