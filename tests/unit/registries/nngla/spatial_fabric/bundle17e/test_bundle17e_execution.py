import pytest

from registries.nngla.spatial_fabric.bundle17e import (
    MemorySpatialRepository,
    SpatialExecutionBlocked,
    StaleSpatialPreviewError,
    build_spatial_preview,
    execute_spatial_batch,
)


def test_governed_execution_inserts_all_2411_points_atomically_then_reruns_as_reuse_only():
    repo = MemorySpatialRepository()
    first_preview = build_spatial_preview(repo.snapshot())
    first = execute_spatial_batch(
        repo,
        first_preview,
        confirmation_fingerprint=first_preview.fingerprint,
        submitter_actor_id="actor:nexadevs:submitter",
        approver_actor_id="actor:nngla:approver",
    )
    assert first.status == "APPLIED"
    assert first.inserted_count == 2411
    assert first.reused_count == 0
    assert len(repo.spatial_points) == 2411
    assert len(repo.geometries) == 2411
    assert len(repo.crosswalks) == 2411

    rerun_preview = build_spatial_preview(repo.snapshot())
    assert rerun_preview.insert_new_count == 0
    assert rerun_preview.reuse_count == 2411
    rerun = execute_spatial_batch(
        repo,
        rerun_preview,
        confirmation_fingerprint=rerun_preview.fingerprint,
        submitter_actor_id="actor:nexadevs:submitter",
        approver_actor_id="actor:nngla:approver",
    )
    assert rerun.status == "REUSED"
    assert rerun.inserted_count == 0
    assert rerun.reused_count == 2411
    assert len(repo.spatial_points) == 2411
    assert len(repo.geometries) == 2411


def test_stale_preview_is_rejected_after_target_state_changes():
    repo = MemorySpatialRepository()
    preview = build_spatial_preview(repo.snapshot())
    repo.spatial_points["NG-SPT-999999"] = {"feature_id": "NG-SPT-999999"}
    with pytest.raises(StaleSpatialPreviewError):
        execute_spatial_batch(
            repo,
            preview,
            confirmation_fingerprint=preview.fingerprint,
            submitter_actor_id="actor:a",
            approver_actor_id="actor:b",
        )


def test_wrong_confirmation_or_same_actor_fails_before_any_write():
    repo = MemorySpatialRepository()
    preview = build_spatial_preview(repo.snapshot())
    with pytest.raises(SpatialExecutionBlocked):
        execute_spatial_batch(
            repo,
            preview,
            confirmation_fingerprint="0" * 64,
            submitter_actor_id="actor:a",
            approver_actor_id="actor:b",
        )
    assert not repo.spatial_points
    with pytest.raises(SpatialExecutionBlocked):
        execute_spatial_batch(
            repo,
            preview,
            confirmation_fingerprint=preview.fingerprint,
            submitter_actor_id="actor:a",
            approver_actor_id="actor:a",
        )
    assert not repo.spatial_points
