"""17.1MR integration proof for the live-style 11/2400 predecessor resume state."""
from registries.nngla.migration_ready.batching import ordered_candidate_ids
from registries.nngla.migration_ready.orchestrator import (
    PLAN_ID,
    build_spatial_preview,
    confirmation_token,
    execute_spatial,
)
from registries.nngla.spatial_fabric.bundle17e.canonical import canonical_by_candidate
from registries.nngla.spatial_fabric.bundle17e.contracts import (
    SpatialExecutionItem,
    SpatialExecutionReceipt,
)
from registries.nngla.spatial_fabric.bundle17e.geometry import geometry_by_candidate
from registries.nngla.spatial_fabric.bundle17e.persistence import MemorySpatialRepository


class UniqueTargetReceiptRepository(MemorySpatialRepository):
    def persist_execution_receipt(self, receipt):
        key = (receipt.fingerprint, receipt.database_name, receipt.environment_name)
        existing = {
            (row.fingerprint, row.database_name, row.environment_name)
            for row in self.receipts
        }
        if key in existing:
            raise ValueError("duplicate execution fingerprint target")
        super().persist_execution_receipt(receipt)


def _seed_17_0mr_batch_one(repo):
    crosswalks = canonical_by_candidate()
    geometries = geometry_by_candidate()
    first_ids = ordered_candidate_ids(crosswalks)[:11]
    items = []
    for candidate_id in first_ids:
        crosswalk = crosswalks[candidate_id]
        geometry = geometries[candidate_id]
        assert repo.persist_point(crosswalk, geometry) == "INSERTED"
        items.append(
            SpatialExecutionItem(
                coordinate_candidate_id=candidate_id,
                canonical_spatial_point_id=crosswalk.canonical_spatial_point_id,
                geometry_id=geometry.geometry_id,
                outcome="INSERTED",
                detail="batch=1;profile=initial-spatial-2411",
            )
        )
    predecessor = SpatialExecutionReceipt(
        execution_id="nnglarun:spatial:mr:12f88a3af5ef4a63f3315139",
        plan_id=PLAN_ID,
        plan_version=1,
        fingerprint="28ecfe98db78e5be0e35318af976e10e338f8567b3c88a03d39e0dc7785c0028",
        content_fingerprint="1" * 64,
        database_name="memory_novegeo",
        environment_name="test",
        runtime_mode="simulation",
        repository_revision="0426462d541eed5b556f14ec355937e26da91d4c",
        source_sha256="2" * 64,
        submitter_actor_id="ASLEKI-DEV",
        approver_actor_id="ASLEKI-ADMIN",
        selected_count=11,
        inserted_count=11,
        reused_count=0,
        quarantined_count=0,
        failed_count=0,
        status="APPLIED",
        started_at="2026-08-20T07:35:53+00:00",
        completed_at="2026-08-20T07:36:19+00:00",
        items=tuple(items),
    )
    repo.persist_execution_receipt(predecessor)
    return predecessor


def _execute(repo, preview):
    return execute_spatial(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev17.1mr",
        approved_fingerprint=preview.fingerprint,
        confirmation=confirmation_token("memory_novegeo", preview.fingerprint),
        submitter_actor_id="ASLEKI-DEV",
        approver_actor_id="ASLEKI-ADMIN",
    )


def test_live_style_predecessor_receipt_is_preserved_and_remaining_2400_resume_cleanly():
    repo = UniqueTargetReceiptRepository()
    predecessor = _seed_17_0mr_batch_one(repo)

    preview = build_spatial_preview(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev17.1mr",
    )
    assert (preview.reuse_count, preview.insert_count, preview.conflict_count) == (11, 2400, 0)

    results = _execute(repo, preview)
    assert results[0].status == "REUSED"
    assert results[0].inserted_count == 0
    assert results[0].reused_count == 11
    assert sum(row.inserted_count for row in results) == 2400
    assert len(repo.crosswalks) == 2411

    # The 17.0MR receipt remains historical truth; only the three remaining
    # transactional batches receive 17.1MR plan-version-2 receipts.
    assert repo.receipts[0] is predecessor
    assert predecessor.plan_version == 1
    assert len(repo.receipts) == 4
    assert [row.plan_version for row in repo.receipts] == [1, 2, 2, 2]
    target_keys = [
        (row.fingerprint, row.database_name, row.environment_name)
        for row in repo.receipts
    ]
    assert len(target_keys) == len(set(target_keys)) == 4

    final_preview = build_spatial_preview(
        repo,
        database_name="memory_novegeo",
        environment_name="test",
        repository_revision="rev17.1mr",
    )
    assert (final_preview.insert_count, final_preview.reuse_count, final_preview.conflict_count) == (0, 2411, 0)
    receipt_count_before = len(repo.receipts)
    rerun = _execute(repo, final_preview)
    assert {row.status for row in rerun} == {"REUSED"}
    assert sum(row.reused_count for row in rerun) == 2411
    assert len(repo.receipts) == receipt_count_before
