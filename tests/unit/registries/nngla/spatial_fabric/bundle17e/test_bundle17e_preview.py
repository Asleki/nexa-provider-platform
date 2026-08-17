from registries.nngla.spatial_fabric.bundle17e import (
    MemorySpatialRepository,
    SpatialMigrationAction,
    TargetSpatialSnapshot,
    build_spatial_preview,
    offline_spatial_preview,
)
from registries.nngla.spatial_fabric.bundle17e._shared import REQUIRED_SCHEMA_CAPABILITIES


def test_offline_preview_is_zero_write_and_honestly_not_execution_ready_without_live_target():
    preview = offline_spatial_preview()
    assert preview.selected_count == 2411
    assert preview.qualified_count == 2411
    assert preview.quarantined_count == 0
    assert preview.database_writes == 0
    assert preview.schema_ready is False
    assert preview.execution_ready is False
    assert {item.database_writes for item in preview.items} == {0}


def test_empty_qualified_target_makes_entire_batch_execution_ready_as_one_fail_closed_unit():
    repository = MemorySpatialRepository()
    preview = build_spatial_preview(repository.snapshot())
    assert preview.schema_ready is True
    assert preview.execution_ready is True
    assert preview.insert_new_count == 2411
    assert preview.reuse_count == 0
    assert {item.migration_action for item in preview.items} == {SpatialMigrationAction.INSERT_NEW}


def test_any_target_identifier_collision_quarantines_row_and_blocks_entire_batch():
    target = TargetSpatialSnapshot(
        "db", "dev", REQUIRED_SCHEMA_CAPABILITIES,
        frozenset({"NG-SPT-000001"}), frozenset(), {}, {}, True,
    )
    preview = build_spatial_preview(target)
    assert preview.quarantined_count == 1
    assert preview.execution_ready is False
    quarantined = [item for item in preview.items if item.quarantined]
    assert len(quarantined) == 1
    assert quarantined[0].migration_action is SpatialMigrationAction.QUARANTINE


def test_spatial_fingerprint_is_bound_to_target_state_not_only_source_content():
    first = build_spatial_preview(MemorySpatialRepository().snapshot())
    target = TargetSpatialSnapshot(
        "memory_novegeo", "test", REQUIRED_SCHEMA_CAPABILITIES,
        frozenset({"NG-SPT-999999"}), frozenset(), {}, {}, True,
    )
    second = build_spatial_preview(target)
    assert first.content_fingerprint == second.content_fingerprint
    assert first.target_snapshot_digest != second.target_snapshot_digest
    assert first.fingerprint != second.fingerprint
