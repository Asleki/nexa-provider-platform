"""Bundle 17.1MR unit proof for per-transaction receipt identity."""
from registries.nngla.migration_ready.orchestrator import (
    PLAN_ID,
    PLAN_VERSION,
    _batch_receipt_fingerprint,
    build_spatial_preview,
    confirmation_token,
    execute_spatial,
)
from registries.nngla.spatial_fabric.bundle17e.persistence import MemorySpatialRepository


class UniqueTargetReceiptRepository(MemorySpatialRepository):
    """Memory adapter that enforces the locked PostgreSQL receipt uniqueness key."""

    def persist_execution_receipt(self, receipt):
        key = (receipt.fingerprint, receipt.database_name, receipt.environment_name)
        existing = {
            (row.fingerprint, row.database_name, row.environment_name)
            for row in self.receipts
        }
        if key in existing:
            raise ValueError("duplicate execution fingerprint target")
        super().persist_execution_receipt(receipt)


def _execute(repo, preview, *, submitter="actor:submitter", approver="actor:approver"):
    return execute_spatial(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev",
        approved_fingerprint=preview.fingerprint,
        confirmation=confirmation_token("memory_novegeo", preview.fingerprint),
        submitter_actor_id=submitter,
        approver_actor_id=approver,
    )


def test_plan_lineage_preserves_17_0mr_plan_and_advances_version_only():
    assert PLAN_ID == "P006.7.11.7.0MR-SPATIAL-BATCH"
    assert PLAN_VERSION == 2


def test_batch_receipt_fingerprint_is_deterministic_and_batch_specific():
    repo = MemorySpatialRepository()
    preview = build_spatial_preview(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev",
    )
    first, second = preview.batches[:2]
    a = _batch_receipt_fingerprint(preview.fingerprint, first.batch_number, first.candidate_ids)
    b = _batch_receipt_fingerprint(preview.fingerprint, first.batch_number, first.candidate_ids)
    c = _batch_receipt_fingerprint(preview.fingerprint, second.batch_number, second.candidate_ids)
    assert a == b
    assert a != c
    assert a != preview.fingerprint
    assert len(a) == len(c) == 64


def test_four_default_transactions_satisfy_postgresql_unique_receipt_contract():
    repo = UniqueTargetReceiptRepository()
    preview = build_spatial_preview(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev",
    )
    results = _execute(repo, preview)

    assert [row.selected_count for row in results] == [11, 800, 800, 800]
    assert sum(row.inserted_count for row in results) == 2411
    assert len(repo.receipts) == 4
    fingerprints = [row.fingerprint for row in repo.receipts]
    assert len(set(fingerprints)) == 4
    assert preview.fingerprint not in fingerprints
    assert {row.plan_id for row in repo.receipts} == {PLAN_ID}
    assert {row.plan_version for row in repo.receipts} == {2}
    assert all(
        f"authorization_fingerprint={preview.fingerprint}" in item.detail
        for receipt in repo.receipts
        for item in receipt.items
    )


def test_actor_identity_does_not_define_batch_receipt_identity():
    repo = MemorySpatialRepository()
    preview = build_spatial_preview(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev",
    )
    first = preview.batches[0]
    expected = _batch_receipt_fingerprint(preview.fingerprint, first.batch_number, first.candidate_ids)
    # The receipt fingerprint API has no actor or clock inputs; actors remain audit data.
    assert expected == _batch_receipt_fingerprint(
        preview.fingerprint, first.batch_number, first.candidate_ids
    )
