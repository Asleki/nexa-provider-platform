import pytest

from registries.nngla.migration_ready.orchestrator import (
    MigrationReadyExecutionError,
    build_spatial_preview,
    confirmation_token,
    execute_spatial,
)
from registries.nngla.spatial_fabric.bundle17e.persistence import MemorySpatialRepository


class DisconnectingRepository(MemorySpatialRepository):
    def __init__(self, *args, fail_after=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fail_after = fail_after
        self.write_attempts = 0
    def persist_point(self, crosswalk, geometry):
        self.write_attempts += 1
        if self.fail_after is not None and self.write_attempts > self.fail_after:
            raise ConnectionError("simulated internet/connection loss")
        return super().persist_point(crosswalk, geometry)


def _execute(repo, preview):
    return execute_spatial(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev",
        approved_fingerprint=preview.fingerprint,
        confirmation=confirmation_token("memory_novegeo", preview.fingerprint),
        submitter_actor_id="actor:submitter",
        approver_actor_id="actor:approver",
    )


def test_initial_profile_executes_11_800_800_800_and_rerun_reuses_all():
    repo = MemorySpatialRepository()
    preview = build_spatial_preview(
        repo, database_name="memory_novegeo", environment_name="test", repository_revision="rev"
    )
    results = _execute(repo, preview)
    assert [x.selected_count for x in results] == [11, 800, 800, 800]
    assert sum(x.inserted_count for x in results) == 2411
    rerun = build_spatial_preview(
        repo, database_name="memory_novegeo", environment_name="test", repository_revision="rev"
    )
    assert (rerun.insert_count, rerun.reuse_count, rerun.conflict_count) == (0, 2411, 0)
    rerun_results = _execute(repo, rerun)
    assert sum(x.reused_count for x in rerun_results) == 2411
    assert {x.status for x in rerun_results} == {"REUSED"}


def test_connection_loss_rolls_back_only_active_batch_and_postgresql_state_drives_resume():
    repo = DisconnectingRepository(fail_after=16)
    preview = build_spatial_preview(
        repo, database_name="memory_novegeo", environment_name="test", repository_revision="rev"
    )
    with pytest.raises(ConnectionError, match="simulated"):
        _execute(repo, preview)
    # Batch 1 committed. The partial work from batch 2 was rolled back.
    assert len(repo.spatial_points) == 11
    assert len(repo.geometries) == 11
    assert len(repo.crosswalks) == 11

    repo.fail_after = None
    resumed = build_spatial_preview(
        repo, database_name="memory_novegeo", environment_name="test", repository_revision="rev"
    )
    assert (resumed.reuse_count, resumed.insert_count) == (11, 2400)
    results = _execute(repo, resumed)
    assert results[0].status == "REUSED"
    assert results[0].reused_count == 11
    assert sum(x.inserted_count for x in results) == 2400
    assert len(repo.spatial_points) == 2411


def test_stale_fingerprint_or_same_actor_fails_closed():
    repo = MemorySpatialRepository()
    preview = build_spatial_preview(
        repo, database_name="memory_novegeo", environment_name="test", repository_revision="rev"
    )
    with pytest.raises(MigrationReadyExecutionError, match="stale"):
        execute_spatial(
            repo, database_name="memory_novegeo", environment_name="test", repository_revision="rev",
            approved_fingerprint="0" * 64, confirmation="wrong",
            submitter_actor_id="actor:a", approver_actor_id="actor:b",
        )
    with pytest.raises(MigrationReadyExecutionError, match="remain separate"):
        execute_spatial(
            repo, database_name="memory_novegeo", environment_name="test", repository_revision="rev",
            approved_fingerprint=preview.fingerprint,
            confirmation=confirmation_token("memory_novegeo", preview.fingerprint),
            submitter_actor_id="actor:a", approver_actor_id="actor:a",
        )
