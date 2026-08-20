import pytest

from registries.nngla.migration_ready.record_execution import (
    RecordExecutionInterrupted,
    build_record_preview,
    execute_records,
    record_confirmation_token,
)
from registries.nngla.spatial_fabric.bundle17e.persistence import MemorySpatialRepository


class DisconnectAfterRepository(MemorySpatialRepository):
    def __init__(self, fail_on_attempt):
        super().__init__()
        self.fail_on_attempt = fail_on_attempt
        self.attempts = 0

    def persist_point(self, crosswalk, geometry):
        self.attempts += 1
        if self.fail_on_attempt is not None and self.attempts == self.fail_on_attempt:
            raise ConnectionError("simulated connection loss")
        return super().persist_point(crosswalk, geometry)


def _execute(repo, preview, count=800, start=None):
    return execute_records(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev3",
        requested_count=count,
        start_ordinal=start,
        approved_fingerprint=preview.fingerprint,
        confirmation=record_confirmation_token(
            "memory_novegeo",
            None if preview.window is None else preview.window.logical_batch_id,
            preview.fingerprint,
        ),
        submitter_actor_id="ASLEKI-DEV",
        approver_actor_id="ASLEKI-ADMIN",
    )


def test_800_logical_window_preserves_first_600_and_resumes_at_601():
    repo = DisconnectAfterRepository(fail_on_attempt=601)
    initial = build_record_preview(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev3",
        requested_count=800,
    )
    assert (initial.window.window_start_ordinal, initial.window.window_end_ordinal) == (1, 800)

    with pytest.raises(RecordExecutionInterrupted) as caught:
        _execute(repo, initial)
    assert caught.value.failed_ordinal == 601
    assert caught.value.inserted_count == 600
    assert len(repo.crosswalks) == 600
    assert len(repo.receipts) == 600

    # A fresh process/preview uses PostgreSQL state + durable record receipts and
    # resumes the same logical 1..800 window at the first missing ordinal.
    repo.fail_on_attempt = None
    resumed = build_record_preview(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev3",
        requested_count=500,
    )
    assert resumed.progress.contiguous_completed_ordinal == 600
    assert resumed.progress.first_unfulfilled_ordinal == 601
    assert resumed.window.resumed is True
    assert resumed.window.requested_count == 800
    assert (resumed.window.execution_start_ordinal, resumed.window.execution_end_ordinal) == (601, 800)
    assert (resumed.insert_count, resumed.reuse_count) == (200, 0)

    finished = _execute(repo, resumed, count=500)
    assert (finished.inserted_count, finished.reused_count) == (200, 0)
    assert len(repo.crosswalks) == 800
    assert len(repo.receipts) == 800

    # Once 1..800 is complete the next normal 800 begins at 801, saving the
    # duplicate scan.  An explicit old range still supports deliberate proof.
    next_window = build_record_preview(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev3",
        requested_count=800,
    )
    assert (next_window.window.window_start_ordinal, next_window.window.window_end_ordinal) == (801, 1600)

    duplicate = build_record_preview(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev3",
        requested_count=800,
        start_ordinal=1,
    )
    assert (duplicate.insert_count, duplicate.reuse_count, duplicate.conflict_count) == (0, 800, 0)
    receipt_count = len(repo.receipts)
    duplicate_result = _execute(repo, duplicate, count=800, start=1)
    assert (duplicate_result.inserted_count, duplicate_result.reused_count) == (0, 800)
    assert len(repo.receipts) == receipt_count


def test_existing_predecessor_coordinates_can_be_reused_while_new_records_are_record_atomic():
    repo = MemorySpatialRepository()
    # Simulate the currently proven 11 predecessor coordinates without v3 metadata.
    from registries.nngla.migration_ready.batching import ordered_candidate_ids
    from registries.nngla.spatial_fabric.bundle17e.canonical import canonical_by_candidate
    from registries.nngla.spatial_fabric.bundle17e.geometry import geometry_by_candidate

    crosswalks = canonical_by_candidate()
    geometries = geometry_by_candidate()
    for candidate_id in ordered_candidate_ids(crosswalks)[:11]:
        repo.persist_point(crosswalks[candidate_id], geometries[candidate_id])

    proof = build_record_preview(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev3",
        requested_count=20,
        start_ordinal=1,
    )
    assert (proof.reuse_count, proof.insert_count, proof.conflict_count) == (11, 9, 0)
    result = _execute(repo, proof, count=20, start=1)
    assert (result.reused_count, result.inserted_count) == (11, 9)
    assert len(repo.crosswalks) == 20
    assert len(repo.receipts) == 9

    recheck = build_record_preview(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev3",
        requested_count=20,
        start_ordinal=1,
    )
    assert (recheck.reuse_count, recheck.insert_count) == (20, 0)
