from registries.nngla.migration_ready.record_execution import (
    PLAN_VERSION,
    _record_receipt_fingerprint,
    build_record_preview,
    execute_records,
    record_confirmation_token,
)
from registries.nngla.spatial_fabric.bundle17e.persistence import MemorySpatialRepository


def _run(repo, preview, *, count, start=None):
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


def test_record_receipt_fingerprint_is_deterministic_and_unique_per_ordinal():
    common = dict(
        logical_batch_id="nnglabatch:spatial:mr:" + "a" * 24,
        candidate_id="coordcand:nngla:" + "b" * 64,
        canonical_id="NG-SPT-000001",
        geometry_id="NG-GEO-000022",
        source_sha256="c" * 64,
    )
    first = _record_receipt_fingerprint(migration_ordinal=1, **common)
    assert first == _record_receipt_fingerprint(migration_ordinal=1, **common)
    assert first != _record_receipt_fingerprint(migration_ordinal=2, **common)
    assert PLAN_VERSION == 3


def test_each_insert_gets_its_own_receipt_and_duplicate_verification_creates_no_new_import_receipts():
    repo = MemorySpatialRepository()
    preview = build_record_preview(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev3",
        requested_count=3,
        start_ordinal=1,
    )
    result = _run(repo, preview, count=3, start=1)
    assert (result.inserted_count, result.reused_count) == (3, 0)
    assert len(repo.receipts) == 3
    assert all(receipt.plan_version == 3 for receipt in repo.receipts)
    assert all(receipt.selected_count == receipt.inserted_count == 1 for receipt in repo.receipts)
    first_completed = repo.receipts[0].completed_at

    duplicate = build_record_preview(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev3",
        requested_count=3,
        start_ordinal=1,
    )
    assert (duplicate.insert_count, duplicate.reuse_count) == (0, 3)
    rerun = _run(repo, duplicate, count=3, start=1)
    assert (rerun.inserted_count, rerun.reused_count, rerun.status) == (0, 3, "REUSED")
    assert len(repo.receipts) == 3
    assert repo.receipts[0].completed_at == first_completed


def test_record_history_can_show_when_each_coordinate_was_imported():
    repo = MemorySpatialRepository()
    preview = build_record_preview(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev3",
        requested_count=2,
        start_ordinal=1,
    )
    _run(repo, preview, count=2, start=1)
    from registries.nngla.migration_ready.record_persistence import RecordAtomicPersistence

    history = RecordAtomicPersistence(repo).record_history(
        plan_id="P006.7.11.7.0MR-SPATIAL-BATCH",
        database_name="memory_novegeo",
        environment_name="test",
        start_ordinal=1,
        count=2,
    )
    assert [row["migration_ordinal"] for row in history] == [1, 2]
    assert all(row["completed_at"] for row in history)


def test_dead_connection_rollback_does_not_hide_original_record_failure():
    from registries.nngla.migration_ready.record_persistence import RecordAtomicPersistence

    class DeadConnection:
        def commit(self):
            raise AssertionError("commit should not be reached")
        def rollback(self):
            raise ConnectionError("socket already dead")

    class Repo:
        connection = DeadConnection()

    persistence = RecordAtomicPersistence(Repo())
    try:
        with persistence.transaction():
            raise RuntimeError("original record failure")
    except RuntimeError as exc:
        assert str(exc) == "original record failure"
    else:
        raise AssertionError("original error was not re-raised")
